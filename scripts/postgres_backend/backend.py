"""Postgres-backed implementation of pydantic_ai_backends.BackendProtocol.

Mirrors StateBackend semantics (flat absolute-style paths, implicit dirs,
identical FileInfo size and return shapes) so it drops into ConsoleCapability
without changes.

One row per file. Multi-tenant via the ``workspace`` column (= agent_name).
Directories are derived from path prefixes — no separate dirs table.

Concurrency: a process-wide ``psycopg_pool.ConnectionPool`` is shared per DSN.
Every backend op grabs a connection out of the pool and returns it on
completion, so multiple ``PostgresBackend`` instances and multiple threads
can hit the same DSN safely. Schema bootstrap is also keyed by DSN and runs
at most once per process.
"""

from __future__ import annotations

import os
import re
import threading
from pathlib import Path
from urllib.parse import quote, urlparse, urlunparse

from psycopg_pool import ConnectionPool
from pydantic_ai_backends.types import EditResult, FileInfo, GrepMatch, WriteResult
from wcmatch import glob as wcglob

DEFAULT_CONNINFO = "postgresql://postgres:postgres@localhost:5432/care_dev"

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# ── Process-wide pool registry ─────────────────────────────────────────────
# One ConnectionPool per DSN, shared across every PostgresBackend instance
# bound to that DSN. Pools are lazily created on first use and live for the
# process lifetime; tests use close_all_pools() to reset between runs.

_POOL_LOCK = threading.Lock()
_POOLS: dict[str, ConnectionPool] = {}
_SCHEMA_INITIALIZED: set[str] = set()

_POOL_MIN_SIZE = int(os.environ.get("CARE_POSTGRES_POOL_MIN", "1"))
_POOL_MAX_SIZE = int(os.environ.get("CARE_POSTGRES_POOL_MAX", "10"))


def _get_pool(conninfo: str) -> ConnectionPool:
    """Return the (process-wide) pool for ``conninfo``, creating it on first use."""
    with _POOL_LOCK:
        pool = _POOLS.get(conninfo)
        if pool is None:
            pool = ConnectionPool(
                conninfo,
                min_size=_POOL_MIN_SIZE,
                max_size=_POOL_MAX_SIZE,
                kwargs={"autocommit": True},
                open=True,
            )
            _POOLS[conninfo] = pool
        return pool


def _ensure_schema(conninfo: str) -> None:
    """Run schema.sql at most once per DSN per process.

    The DDL is idempotent (``CREATE TABLE IF NOT EXISTS`` plus an ``ALTER
    TABLE ... DROP COLUMN IF EXISTS`` migration), so even if two threads
    race past the cache check, both runs are safe.
    """
    with _POOL_LOCK:
        if conninfo in _SCHEMA_INITIALIZED:
            return
    pool = _get_pool(conninfo)
    ddl = _SCHEMA_PATH.read_text()
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(ddl)
    with _POOL_LOCK:
        _SCHEMA_INITIALIZED.add(conninfo)


def close_all_pools() -> None:
    """Close every cached pool and clear schema-init memoization.

    Test-suite hook; production code does not need to call this — pools are
    intended to live for the process lifetime.
    """
    with _POOL_LOCK:
        pools = list(_POOLS.values())
        _POOLS.clear()
        _SCHEMA_INITIALIZED.clear()
    for p in pools:
        try:
            p.close()
        except Exception:
            pass


# ── Path / utility helpers (parity with StateBackend) ──────────────────────


def _validate_path(path: str) -> str | None:
    if ".." in path:
        return "Path cannot contain '..'"
    if path.startswith("~"):
        return "Path cannot start with '~'"
    if len(path) > 1 and path[1] == ":":
        return "Windows absolute paths are not allowed"
    if "\x00" in path:
        return "Path cannot contain null bytes"
    return None


def _normalize_path(path: str) -> str:
    # Treat "", ".", "./" as the workspace root.
    if path in ("", ".", "./"):
        return "/"
    # Strip a leading "./" so "./contexts/x" becomes "/contexts/x".
    if path.startswith("./"):
        path = path[2:]
    if not path.startswith("/"):
        path = "/" + path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    return path


def _is_not_hidden_path(path: str) -> bool:
    return not path.startswith(".") and "/." not in path


def _state_size(content: str) -> int:
    """StateBackend's size semantics: sum of line lengths after split('\\n').

    Equals ``len(content) - content.count('\\n')``. Matches the codepoint
    count returned by Postgres ``length(replace(content, chr(10), ''))``.
    """
    return len(content) - content.count("\n")


def redact_dsn(dsn: str) -> str:
    """Return ``dsn`` with the password replaced by ``***``.

    Robust to URL-encoded passwords: the netloc is reconstructed from the
    parsed components instead of relying on a substring match against
    ``parsed.password`` (which is the *decoded* form and can fail to appear
    verbatim in ``parsed.netloc``). Returns the original DSN unchanged when
    no password is present or parsing fails.
    """
    try:
        parsed = urlparse(dsn)
        if parsed.password is None:
            return dsn
        username = quote(parsed.username, safe="") if parsed.username else ""
        host = parsed.hostname or ""
        port = f":{parsed.port}" if parsed.port else ""
        netloc = f"{username}:***@{host}{port}" if username else f":***@{host}{port}"
        return urlunparse(parsed._replace(netloc=netloc))
    except Exception:
        return dsn


# ── Backend ────────────────────────────────────────────────────────────────


class PostgresBackend:
    """Postgres-backed BackendProtocol implementation.

    Args:
        workspace: Tenant key (typically the agent_name); rows are scoped to it.
        conninfo: libpq DSN. Falls back to env ``CARE_POSTGRES_URL`` or
            ``"postgresql://postgres:postgres@localhost:5432/care_dev"``.
        auto_init: If True, ensure the schema is bootstrapped (at most once
            per DSN per process). If False, only the pool is opened.
    """

    def __init__(
        self,
        workspace: str,
        *,
        conninfo: str | None = None,
        auto_init: bool = True,
    ):
        if not workspace:
            raise ValueError("workspace must be a non-empty string")
        if "\x00" in workspace:
            raise ValueError("workspace cannot contain null bytes")
        self.workspace = workspace
        self.conninfo = conninfo or os.environ.get("CARE_POSTGRES_URL", DEFAULT_CONNINFO)
        if auto_init:
            _ensure_schema(self.conninfo)
        else:
            _get_pool(self.conninfo)

    # ── pool plumbing ──────────────────────────────────────────────────────

    def _execute(self, sql: str, params: tuple = ()) -> list[tuple]:
        pool = _get_pool(self.conninfo)
        with pool.connection() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description is None:
                return []
            return cur.fetchall()

    def close(self) -> None:
        """No-op kept for API parity with the previous single-connection impl.

        The connection pool is process-wide; use :func:`close_all_pools` to
        shut it down (typically only useful in test teardown).
        """

    # ── core data fetches ──────────────────────────────────────────────────

    def _all_paths_with_size(self) -> list[tuple[str, int]]:
        """All ``(path, size)`` for this workspace, with StateBackend size semantics."""
        rows = self._execute(
            "SELECT path, length(replace(content, chr(10), '')) FROM care_artifacts WHERE workspace=%s",
            (self.workspace,),
        )
        return [(r[0], r[1]) for r in rows]

    def _all_paths_with_content(self) -> list[tuple[str, str]]:
        """All ``(path, content)`` for this workspace. Used by grep_raw."""
        rows = self._execute(
            "SELECT path, content FROM care_artifacts WHERE workspace=%s",
            (self.workspace,),
        )
        return [(r[0], r[1]) for r in rows]

    def _get_content(self, path: str) -> str | None:
        rows = self._execute(
            "SELECT content FROM care_artifacts WHERE workspace=%s AND path=%s",
            (self.workspace, path),
        )
        if not rows:
            return None
        return rows[0][0]

    # ── BackendProtocol surface ────────────────────────────────────────────

    def ls_info(self, path: str) -> list[FileInfo]:
        if _validate_path(path) is not None:
            return []

        path = _normalize_path(path)
        prefix = path if path == "/" else path + "/"

        entries: dict[str, FileInfo] = {}
        for file_path, size in self._all_paths_with_size():
            if not file_path.startswith(prefix) and file_path != path:
                continue

            if file_path == path:
                # `path` itself names a file (e.g. ls_info("/scope.md")).
                name = file_path.split("/")[-1]
                entries[name] = FileInfo(
                    name=name,
                    path=file_path,
                    is_dir=False,
                    size=size,
                )
                continue

            rel_path = file_path[len(prefix) :]
            parts = rel_path.split("/")
            name = parts[0]

            if name in entries:
                continue
            if len(parts) == 1:
                entries[name] = FileInfo(
                    name=name,
                    path=file_path,
                    is_dir=False,
                    size=size,
                )
            else:
                entries[name] = FileInfo(
                    name=name,
                    path=prefix + name,
                    is_dir=True,
                    size=None,
                )

        return sorted(entries.values(), key=lambda x: (not x["is_dir"], x["name"]))

    def _read_bytes(self, path: str) -> bytes:
        error = _validate_path(path)
        if error:
            return f"Error: {error}".encode()
        path = _normalize_path(path)
        content = self._get_content(path)
        if content is None:
            return b""
        return content.encode("utf-8", errors="replace")

    def read(self, path: str, offset: int = 0, limit: int = 2000) -> str:
        error = _validate_path(path)
        if error:
            return f"Error: {error}"

        path = _normalize_path(path)
        content = self._get_content(path)
        if content is None:
            return f"Error: File '{path}' not found"

        lines = content.split("\n")
        total_lines = len(lines)

        if offset >= total_lines:
            return f"Error: Offset {offset} exceeds file length ({total_lines} lines)"

        end = min(offset + limit, total_lines)
        result_lines = [f"{i + 1:>6}\t{lines[i]}" for i in range(offset, end)]
        result = "\n".join(result_lines)
        if end < total_lines:
            result += f"\n\n... ({total_lines - end} more lines)"
        return result

    def write(self, path: str, content: str | bytes) -> WriteResult:
        error = _validate_path(path)
        if error:
            return WriteResult(error=error)

        path = _normalize_path(path)
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        self._execute(
            """
            INSERT INTO care_artifacts (workspace, path, content,
                                        created_at, modified_at)
            VALUES (%s, %s, %s, now(), now())
            ON CONFLICT (workspace, path) DO UPDATE
            SET content = EXCLUDED.content,
                modified_at = now()
            """,
            (self.workspace, path, content),
        )
        return WriteResult(path=path)

    def edit(self, path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult:
        error = _validate_path(path)
        if error:
            return EditResult(error=error)

        path = _normalize_path(path)
        content = self._get_content(path)
        if content is None:
            return EditResult(error=f"File '{path}' not found")

        occurrences = content.count(old_string)
        if occurrences == 0:
            return EditResult(error=f"String '{old_string}' not found in file")

        if occurrences > 1 and not replace_all:
            return EditResult(
                error=f"String '{old_string}' found {occurrences} times. "
                "Use replace_all=True to replace all, or provide more context."
            )

        if replace_all:
            new_content = content.replace(old_string, new_string)
            count = occurrences
        else:
            new_content = content.replace(old_string, new_string, 1)
            count = 1

        self._execute(
            """
            UPDATE care_artifacts
            SET content = %s, modified_at = now()
            WHERE workspace = %s AND path = %s
            """,
            (new_content, self.workspace, path),
        )
        return EditResult(path=path, occurrences=count)

    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        if _validate_path(path) is not None:
            return []

        path = _normalize_path(path)
        if path == "/":
            full_pattern = "/" + pattern.lstrip("/")
        else:
            full_pattern = path + "/" + pattern.lstrip("/")

        results: list[FileInfo] = []
        for file_path, size in self._all_paths_with_size():
            if wcglob.globmatch(file_path, full_pattern, flags=wcglob.GLOBSTAR):
                name = file_path.split("/")[-1]
                results.append(
                    FileInfo(
                        name=name,
                        path=file_path,
                        is_dir=False,
                        size=size,
                    )
                )
        return sorted(results, key=lambda x: x["path"])

    def grep_raw(
        self,
        pattern: str,
        path: str | None = None,
        glob: str | None = None,
        ignore_hidden: bool = True,
    ) -> list[GrepMatch] | str:
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return f"Error: Invalid regex pattern: {e}"

        if path is not None:
            err = _validate_path(path)
            if err:
                return f"Error: {err}"
            normalized_path: str | None = _normalize_path(path)
        else:
            normalized_path = None

        # Single round-trip: pull (path, content) for every file in this
        # workspace, then filter and search in Python. This replaces the
        # previous N+1 pattern (one query for paths + one per matched file).
        all_rows = self._all_paths_with_content()

        if ignore_hidden:
            all_rows = [(p, c) for p, c in all_rows if _is_not_hidden_path(p)]

        if normalized_path is not None:
            paths_set = {p for p, _ in all_rows}
            if normalized_path in paths_set:
                rows = [(p, c) for p, c in all_rows if p == normalized_path]
            else:
                prefix = normalized_path if normalized_path == "/" else normalized_path + "/"
                rows = [(p, c) for p, c in all_rows if p.startswith(prefix)]
        else:
            rows = all_rows

        if glob:
            glob_pattern = "/" + glob.lstrip("/")
            rows = [(p, c) for p, c in rows if wcglob.globmatch(p, glob_pattern, flags=wcglob.GLOBSTAR)]

        results: list[GrepMatch] = []
        for file_path, content in rows:
            for i, line in enumerate(content.split("\n")):
                if regex.search(line):
                    results.append(
                        GrepMatch(
                            path=file_path,
                            line_number=i + 1,
                            line=line,
                        )
                    )
        return results
