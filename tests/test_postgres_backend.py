"""Real-DB integration tests for scripts.postgres_backend.PostgresBackend.

Skipped entirely when CARE_POSTGRES_TEST_URL is unset. No mocks: every test
opens a real psycopg connection and exercises the actual SQL.

Run:
    export CARE_POSTGRES_TEST_URL=postgresql://localhost/care_test
    uv run pytest tests/test_postgres_backend.py -v
"""

from __future__ import annotations

import os
import threading
import time
import uuid

import psycopg
import pytest

CARE_POSTGRES_TEST_URL = os.environ.get("CARE_POSTGRES_TEST_URL")

pytestmark = pytest.mark.skipif(
    not CARE_POSTGRES_TEST_URL,
    reason="CARE_POSTGRES_TEST_URL not set; integration tests require a real Postgres",
)

from scripts.postgres_backend import PostgresBackend, close_all_pools  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _ensure_schema() -> None:
    """Boot the schema once per session.

    PostgresBackend.__init__ does this too via auto_init=True, but doing it
    here means the table is guaranteed-present before any test starts and
    survives across function-scoped instances.
    """
    PostgresBackend(workspace="_schema_init", conninfo=CARE_POSTGRES_TEST_URL).close()


@pytest.fixture
def workspace() -> str:
    """Unique workspace name per test, isolated from other runs."""
    return f"test_{uuid.uuid4().hex[:12]}"


@pytest.fixture
def backend(workspace: str):
    """Per-test PostgresBackend; cleans the workspace's rows on teardown."""
    be = PostgresBackend(workspace=workspace, conninfo=CARE_POSTGRES_TEST_URL)
    yield be
    with psycopg.connect(CARE_POSTGRES_TEST_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM care_artifacts WHERE workspace=%s", (workspace,))
    be.close()


# ── round-trips ─────────────────────────────────────────────────────────────


def test_write_then_read_round_trip(backend: PostgresBackend) -> None:
    res = backend.write("/scope.md", "# Scope\n\nhello world")
    assert res.path == "/scope.md"
    assert res.error is None

    out = backend.read("/scope.md")
    assert "1\t# Scope" in out
    assert "hello world" in out


def test_write_normalizes_path_without_leading_slash(backend: PostgresBackend) -> None:
    backend.write("scope.md", "x")
    assert backend.read("/scope.md").endswith("\tx")


def test_write_overwrite_updates_modified_at(backend: PostgresBackend, workspace: str) -> None:
    backend.write("/a.md", "v1")
    time.sleep(0.05)
    backend.write("/a.md", "v2")

    with psycopg.connect(CARE_POSTGRES_TEST_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT created_at, modified_at, content FROM care_artifacts WHERE workspace=%s AND path=%s",
                (workspace, "/a.md"),
            )
            created_at, modified_at, content = cur.fetchone()

    assert content == "v2"
    assert modified_at > created_at


def test_read_missing_returns_error_string(backend: PostgresBackend) -> None:
    out = backend.read("/nope.md")
    assert out == "Error: File '/nope.md' not found"


# ── ls_info ────────────────────────────────────────────────────────────────


def test_ls_root_shows_files_and_implicit_dirs(backend: PostgresBackend) -> None:
    backend.write("/scope.md", "x")
    backend.write("/contexts/index.md", "y")
    backend.write("/contexts/cmr.md", "z")
    backend.write("/tools/ts/index.md", "t")

    entries = backend.ls_info("/")
    by_name = {e["name"]: e for e in entries}

    assert by_name["scope.md"]["is_dir"] is False
    assert by_name["contexts"]["is_dir"] is True
    assert by_name["tools"]["is_dir"] is True


def test_ls_subdir_descends(backend: PostgresBackend) -> None:
    backend.write("/contexts/index.md", "y")
    backend.write("/contexts/cmr.md", "z")

    entries = backend.ls_info("/contexts")
    names = sorted(e["name"] for e in entries)
    assert names == ["cmr.md", "index.md"]
    assert all(e["is_dir"] is False for e in entries)


def test_ls_dot_is_root(backend: PostgresBackend) -> None:
    """The agent commonly calls ls('.') — must behave like ls('/')."""
    backend.write("/scope.md", "x")
    backend.write("/contexts/index.md", "y")

    expected = sorted((e["name"], e["is_dir"]) for e in backend.ls_info("/"))
    for alias in (".", "./", ""):
        got = sorted((e["name"], e["is_dir"]) for e in backend.ls_info(alias))
        assert got == expected, f"ls_info({alias!r}) diverged from ls_info('/')"


def test_read_with_dot_prefix(backend: PostgresBackend) -> None:
    backend.write("/scope.md", "hello")
    assert "hello" in backend.read("./scope.md")


# ── edit ───────────────────────────────────────────────────────────────────


def test_edit_single_occurrence(backend: PostgresBackend) -> None:
    backend.write("/a.md", "alpha beta gamma")
    res = backend.edit("/a.md", "beta", "BETA")
    assert res.error is None
    assert res.occurrences == 1
    assert "alpha BETA gamma" in backend.read("/a.md")


def test_edit_multiple_without_replace_all_errors(backend: PostgresBackend) -> None:
    backend.write("/a.md", "foo foo foo")
    res = backend.edit("/a.md", "foo", "bar")
    assert res.path is None
    assert res.error is not None
    assert "found 3 times" in res.error


def test_edit_replace_all(backend: PostgresBackend) -> None:
    backend.write("/a.md", "foo foo foo")
    res = backend.edit("/a.md", "foo", "bar", replace_all=True)
    assert res.error is None
    assert res.occurrences == 3
    assert "bar bar bar" in backend.read("/a.md")


def test_edit_missing_file(backend: PostgresBackend) -> None:
    res = backend.edit("/nope.md", "x", "y")
    assert res.error is not None and "not found" in res.error


# ── glob ───────────────────────────────────────────────────────────────────


def test_glob_finds_md_recursively(backend: PostgresBackend) -> None:
    backend.write("/scope.md", "x")
    backend.write("/contexts/index.md", "y")
    backend.write("/contexts/cmr.md", "z")
    backend.write("/data.json", '{"k":1}')

    results = backend.glob_info("**/*.md")
    paths = sorted(r["path"] for r in results)
    assert paths == ["/contexts/cmr.md", "/contexts/index.md", "/scope.md"]


# ── grep ───────────────────────────────────────────────────────────────────


def test_grep_finds_matches_with_line_numbers(backend: PostgresBackend) -> None:
    backend.write("/a.md", "hello world\nfoo bar\nfoo again")
    backend.write("/b.md", "no match here")

    matches = backend.grep_raw("foo")
    assert isinstance(matches, list)
    assert {(m["path"], m["line_number"]) for m in matches} == {
        ("/a.md", 2),
        ("/a.md", 3),
    }


def test_grep_invalid_regex_returns_error_string(backend: PostgresBackend) -> None:
    out = backend.grep_raw("(unclosed")
    assert isinstance(out, str)
    assert out.startswith("Error: Invalid regex pattern")


# ── isolation & validation ─────────────────────────────────────────────────


def test_workspace_isolation() -> None:
    ws_a = f"test_a_{uuid.uuid4().hex[:8]}"
    ws_b = f"test_b_{uuid.uuid4().hex[:8]}"
    a = PostgresBackend(workspace=ws_a, conninfo=CARE_POSTGRES_TEST_URL)
    b = PostgresBackend(workspace=ws_b, conninfo=CARE_POSTGRES_TEST_URL)
    try:
        a.write("/shared.md", "from A")
        assert b.read("/shared.md") == "Error: File '/shared.md' not found"
        assert "from A" in a.read("/shared.md")
    finally:
        with psycopg.connect(CARE_POSTGRES_TEST_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM care_artifacts WHERE workspace IN (%s, %s)",
                    (ws_a, ws_b),
                )
        a.close()
        b.close()


def test_path_validation_rejects_dotdot(backend: PostgresBackend) -> None:
    out = backend.read("../etc/passwd")
    assert out == "Error: Path cannot contain '..'"


def test_path_validation_rejects_tilde(backend: PostgresBackend) -> None:
    out = backend.read("~/secrets")
    assert out == "Error: Path cannot start with '~'"


def test_write_path_validation(backend: PostgresBackend) -> None:
    res = backend.write("../etc/passwd", "pwn")
    assert res.path is None
    assert res.error == "Path cannot contain '..'"


def test_path_validation_rejects_null_byte(backend: PostgresBackend) -> None:
    out = backend.read("foo\x00bar")
    assert out == "Error: Path cannot contain null bytes"


def test_workspace_rejects_empty_string() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        PostgresBackend(workspace="", conninfo=CARE_POSTGRES_TEST_URL)


def test_workspace_rejects_null_byte() -> None:
    with pytest.raises(ValueError, match="null"):
        PostgresBackend(workspace="abc\x00def", conninfo=CARE_POSTGRES_TEST_URL)


# ── size semantics (StateBackend parity) ──────────────────────────────────


def test_ls_size_matches_state_backend_semantics(backend: PostgresBackend) -> None:
    """size = sum(len(line) for line in content.split('\\n')) — matches StateBackend.

    For "abc\\ndef" that's 3+3=6, NOT 7 (utf-8 byte length including newline).
    """
    backend.write("/a.md", "abc\ndef")
    entries = backend.ls_info("/")
    by_name = {e["name"]: e for e in entries}
    assert by_name["a.md"]["size"] == 6


def test_ls_size_unicode_codepoints(backend: PostgresBackend) -> None:
    """``é`` is 1 codepoint but 2 utf-8 bytes; we report codepoints (= len(str))."""
    backend.write("/a.md", "é")
    entries = backend.ls_info("/")
    by_name = {e["name"]: e for e in entries}
    assert by_name["a.md"]["size"] == 1


def test_ls_size_empty_and_only_newlines(backend: PostgresBackend) -> None:
    backend.write("/empty.md", "")
    backend.write("/newlines.md", "\n\n\n")
    entries = backend.ls_info("/")
    by_name = {e["name"]: e for e in entries}
    assert by_name["empty.md"]["size"] == 0
    assert by_name["newlines.md"]["size"] == 0


def test_glob_size_matches_state_backend_semantics(backend: PostgresBackend) -> None:
    backend.write("/a.md", "abc\ndef")
    [hit] = backend.glob_info("**/*.md")
    assert hit["size"] == 6


# ── empty / round-trip edges ──────────────────────────────────────────────


def test_write_empty_string_round_trips(backend: PostgresBackend) -> None:
    backend.write("/empty.md", "")
    # An empty file has 1 line (the empty string), so read() returns the
    # numbered single line.
    out = backend.read("/empty.md")
    assert out == "     1\t"


def test_read_offset_at_or_past_end(backend: PostgresBackend) -> None:
    backend.write("/a.md", "one\ntwo")
    out = backend.read("/a.md", offset=5)
    assert out.startswith("Error: Offset 5 exceeds")


def test_read_with_limit_truncates(backend: PostgresBackend) -> None:
    backend.write("/a.md", "one\ntwo\nthree\nfour")
    out = backend.read("/a.md", offset=0, limit=2)
    assert "1\tone" in out
    assert "2\ttwo" in out
    assert "three" not in out
    assert "(2 more lines)" in out


def test_edit_no_op_when_old_equals_new_bumps_modified_at(backend: PostgresBackend, workspace: str) -> None:
    """``old==new`` is a degenerate no-op rewrite. We still touch modified_at —
    same as StateBackend, which calls ``_get_timestamp()`` unconditionally.
    """
    backend.write("/a.md", "hello")
    time.sleep(0.05)
    res = backend.edit("/a.md", "hello", "hello")
    assert res.error is None
    assert res.occurrences == 1

    with psycopg.connect(CARE_POSTGRES_TEST_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT created_at, modified_at FROM care_artifacts WHERE workspace=%s AND path=%s",
                (workspace, "/a.md"),
            )
            created_at, modified_at = cur.fetchone()
    assert modified_at > created_at


def test_read_bytes_round_trip(backend: PostgresBackend) -> None:
    backend.write("/a.md", "héllo")
    assert backend._read_bytes("/a.md") == "héllo".encode("utf-8")


def test_read_bytes_missing_returns_empty(backend: PostgresBackend) -> None:
    assert backend._read_bytes("/missing.md") == b""


def test_read_bytes_validation_error(backend: PostgresBackend) -> None:
    out = backend._read_bytes("../etc/passwd")
    assert out.decode().startswith("Error: Path cannot contain")


def test_ls_on_a_file_path_returns_that_file(backend: PostgresBackend) -> None:
    backend.write("/scope.md", "content")
    entries = backend.ls_info("/scope.md")
    assert len(entries) == 1
    assert entries[0]["name"] == "scope.md"
    assert entries[0]["is_dir"] is False


# ── grep edges ────────────────────────────────────────────────────────────


def test_grep_with_path_filter_to_specific_file(backend: PostgresBackend) -> None:
    backend.write("/a.md", "match me\nnope")
    backend.write("/b.md", "match me too")
    matches = backend.grep_raw("match", path="/a.md")
    assert isinstance(matches, list)
    assert {m["path"] for m in matches} == {"/a.md"}


def test_grep_with_directory_path(backend: PostgresBackend) -> None:
    backend.write("/sub/a.md", "match")
    backend.write("/sub/b.md", "match")
    backend.write("/other.md", "match")
    matches = backend.grep_raw("match", path="/sub")
    assert isinstance(matches, list)
    assert {m["path"] for m in matches} == {"/sub/a.md", "/sub/b.md"}


def test_grep_glob_filter(backend: PostgresBackend) -> None:
    backend.write("/a.md", "match")
    backend.write("/a.txt", "match")
    matches = backend.grep_raw("match", glob="**/*.md")
    assert isinstance(matches, list)
    assert {m["path"] for m in matches} == {"/a.md"}


def test_grep_ignore_hidden(backend: PostgresBackend) -> None:
    backend.write("/visible.md", "needle")
    # Note: leading-dot path components live under "/.../" — emulate by
    # writing into a "hidden" subdir.
    backend.write("/.hidden/secret.md", "needle")
    visible = backend.grep_raw("needle", ignore_hidden=True)
    all_files = backend.grep_raw("needle", ignore_hidden=False)
    assert isinstance(visible, list) and isinstance(all_files, list)
    assert {m["path"] for m in visible} == {"/visible.md"}
    assert {m["path"] for m in all_files} == {"/visible.md", "/.hidden/secret.md"}


def test_grep_invalid_path(backend: PostgresBackend) -> None:
    out = backend.grep_raw("foo", path="../etc")
    assert isinstance(out, str)
    assert out.startswith("Error: Path cannot contain")


# ── concurrency (proves the ConnectionPool works) ─────────────────────────


def test_concurrent_writes_distinct_paths(backend: PostgresBackend) -> None:
    """Spawn many threads writing distinct files. Pool must serialize on
    distinct connections without garbling cursor state.
    """
    n = 20
    errors: list[BaseException] = []

    def write_one(i: int) -> None:
        try:
            backend.write(f"/concurrent_{i}.md", f"content {i}")
        except BaseException as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=write_one, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    entries = backend.ls_info("/")
    written = {e["name"] for e in entries if e["name"].startswith("concurrent_")}
    assert written == {f"concurrent_{i}.md" for i in range(n)}


def test_concurrent_read_after_write(backend: PostgresBackend) -> None:
    """Many threads reading the same file simultaneously should all succeed."""
    backend.write("/shared.md", "shared content")
    results: list[str] = []
    lock = threading.Lock()

    def read_one() -> None:
        out = backend.read("/shared.md")
        with lock:
            results.append(out)

    threads = [threading.Thread(target=read_one) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 20
    assert all("shared content" in r for r in results)


def test_concurrent_writes_same_path_last_writer_wins(backend: PostgresBackend) -> None:
    """N threads writing the same key — final value should be one of the
    written values; no exceptions; no missing row.
    """
    n = 10
    errors: list[BaseException] = []

    def write_one(i: int) -> None:
        try:
            backend.write("/contended.md", f"value_{i}")
        except BaseException as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=write_one, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    final = backend.read("/contended.md")
    assert any(f"value_{i}" in final for i in range(n))


# ── schema bootstrap idempotency ──────────────────────────────────────────


def test_repeated_construction_does_not_error() -> None:
    """``auto_init=True`` must be safe to call repeatedly (cached per DSN)."""
    ws = f"test_repeat_{uuid.uuid4().hex[:8]}"
    for _ in range(5):
        be = PostgresBackend(workspace=ws, conninfo=CARE_POSTGRES_TEST_URL)
        be.write("/a.md", "x")
        assert "x" in be.read("/a.md")
    with psycopg.connect(CARE_POSTGRES_TEST_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM care_artifacts WHERE workspace=%s", (ws,))


def test_close_all_pools_then_reuse() -> None:
    """``close_all_pools`` must leave the module reusable — re-constructing a
    backend afterwards should re-bootstrap the pool transparently.
    """
    ws = f"test_pool_{uuid.uuid4().hex[:8]}"
    a = PostgresBackend(workspace=ws, conninfo=CARE_POSTGRES_TEST_URL)
    a.write("/before.md", "before")

    close_all_pools()

    b = PostgresBackend(workspace=ws, conninfo=CARE_POSTGRES_TEST_URL)
    b.write("/after.md", "after")
    assert "before" in b.read("/before.md")
    assert "after" in b.read("/after.md")

    with psycopg.connect(CARE_POSTGRES_TEST_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM care_artifacts WHERE workspace=%s", (ws,))


def test_auto_init_false_skips_schema_but_pool_still_works() -> None:
    """``auto_init=False`` opens the pool but doesn't run schema. The schema
    is already there from the session-level fixture, so writes still work.
    """
    ws = f"test_noinit_{uuid.uuid4().hex[:8]}"
    be = PostgresBackend(workspace=ws, conninfo=CARE_POSTGRES_TEST_URL, auto_init=False)
    be.write("/x.md", "y")
    assert "y" in be.read("/x.md")
    with psycopg.connect(CARE_POSTGRES_TEST_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM care_artifacts WHERE workspace=%s", (ws,))
