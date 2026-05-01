"""Postgres-backed implementation of pydantic_ai_backends.BackendProtocol.

Mirrors StateBackend semantics (flat absolute-style paths, implicit dirs,
identical return shapes) so it drops into ConsoleCapability without changes.

One row per file. Multi-tenant via the `workspace` column (= agent_name).
Directories are derived from path prefixes — no separate dirs table.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import psycopg
from pydantic_ai_backends.types import EditResult, FileInfo, GrepMatch, WriteResult
from wcmatch import glob as wcglob

DEFAULT_CONNINFO = "postgresql://postgres:postgres@localhost:5432/care_dev"

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def _validate_path(path: str) -> str | None:
    if ".." in path:
        return "Path cannot contain '..'"
    if path.startswith("~"):
        return "Path cannot start with '~'"
    if len(path) > 1 and path[1] == ":":
        return "Windows absolute paths are not allowed"
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


def redact_dsn(dsn: str) -> str:
    try:
        parsed = urlparse(dsn)
        if parsed.password:
            netloc = parsed.netloc.replace(f":{parsed.password}@", ":***@")
            return urlunparse(parsed._replace(netloc=netloc))
    except Exception:
        pass
    return dsn


class PostgresBackend:
    """Postgres-backed BackendProtocol implementation.

    Args:
        workspace: Tenant key (typically the agent_name); rows are scoped to it.
        conninfo: libpq DSN. Defaults to env CARE_POSTGRES_URL or
            "postgresql://localhost/care_dev".
        auto_init: If True, run schema.sql at construction (CREATE TABLE
            IF NOT EXISTS). Safe to call repeatedly.
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
        self.workspace = workspace
        self.conninfo = conninfo or os.environ.get("CARE_POSTGRES_URL", DEFAULT_CONNINFO)
        self._conn: psycopg.Connection | None = None
        if auto_init:
            self._init_schema()

    # ── connection plumbing ────────────────────────────────────────────────

    def _connect(self) -> psycopg.Connection:
        if self._conn is None or self._conn.closed:
            self._conn = psycopg.connect(self.conninfo, autocommit=True)
        return self._conn

    def _execute(self, sql: str, params: tuple = ()) -> list[tuple]:
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                if cur.description is None:
                    return []
                return cur.fetchall()
        except psycopg.OperationalError:
            self._conn = None
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute(sql, params)
                if cur.description is None:
                    return []
                return cur.fetchall()

    def _init_schema(self) -> None:
        ddl = _SCHEMA_PATH.read_text()
        conn = self._connect()
        with conn.cursor() as cur:
            cur.execute(ddl)

    def close(self) -> None:
        if self._conn is not None and not self._conn.closed:
            self._conn.close()
        self._conn = None

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    # ── core data fetches ──────────────────────────────────────────────────

    def _all_paths(self) -> list[tuple[str, int]]:
        """All (path, size_bytes) for this workspace."""
        rows = self._execute(
            "SELECT path, size_bytes FROM care_artifacts WHERE workspace=%s",
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
        error = _validate_path(path)
        if error:
            return []

        path = _normalize_path(path)
        prefix = path if path == "/" else path + "/"

        entries: dict[str, FileInfo] = {}
        for file_path, size in self._all_paths():
            if not file_path.startswith(prefix) and file_path != path:
                continue

            if file_path == path:
                name = file_path.split("/")[-1]
                entries[name] = FileInfo(
                    name=name,
                    path=file_path,
                    is_dir=False,
                    size=size,
                )
            else:
                rel_path = file_path[len(prefix) :]
                parts = rel_path.split("/")
                name = parts[0]

                if name not in entries:
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

        size_bytes = len(content.encode("utf-8", errors="replace"))

        self._execute(
            """
            INSERT INTO care_artifacts (workspace, path, content, size_bytes,
                                        created_at, modified_at)
            VALUES (%s, %s, %s, %s, now(), now())
            ON CONFLICT (workspace, path) DO UPDATE
            SET content = EXCLUDED.content,
                size_bytes = EXCLUDED.size_bytes,
                modified_at = now()
            """,
            (self.workspace, path, content, size_bytes),
        )
        return WriteResult(path=path)

    def edit(
        self, path: str, old_string: str, new_string: str, replace_all: bool = False
    ) -> EditResult:
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

        size_bytes = len(new_content.encode("utf-8", errors="replace"))
        self._execute(
            """
            UPDATE care_artifacts
            SET content = %s, size_bytes = %s, modified_at = now()
            WHERE workspace = %s AND path = %s
            """,
            (new_content, size_bytes, self.workspace, path),
        )
        return EditResult(path=path, occurrences=count)

    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        error = _validate_path(path)
        if error:
            return []

        path = _normalize_path(path)
        if path == "/":
            full_pattern = "/" + pattern.lstrip("/")
        else:
            full_pattern = path + "/" + pattern.lstrip("/")

        results: list[FileInfo] = []
        for file_path, size in self._all_paths():
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

        all_paths = self._all_paths()
        candidates = [p for p, _ in all_paths]
        if ignore_hidden:
            candidates = [p for p in candidates if _is_not_hidden_path(p)]

        if path:
            err = _validate_path(path)
            if err:
                return f"Error: {err}"
            normalized = _normalize_path(path)
            if normalized in candidates:
                files_to_search = [normalized]
            else:
                prefix = normalized if normalized == "/" else normalized + "/"
                files_to_search = [p for p in candidates if p.startswith(prefix)]
        else:
            files_to_search = candidates

        if glob:
            glob_pattern = "/" + glob.lstrip("/")
            files_to_search = [
                p
                for p in files_to_search
                if wcglob.globmatch(p, glob_pattern, flags=wcglob.GLOBSTAR)
            ]

        results: list[GrepMatch] = []
        for file_path in files_to_search:
            content = self._get_content(file_path)
            if content is None:
                continue
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
