"""Real-DB integration tests for scripts.postgres_backend.PostgresBackend.

Skipped entirely when CARE_POSTGRES_TEST_URL is unset. No mocks: every test
opens a real psycopg connection and exercises the actual SQL.

Run:
    export CARE_POSTGRES_TEST_URL=postgresql://localhost/care_test
    uv run pytest tests/test_postgres_backend.py -v
"""

from __future__ import annotations

import os
import time
import uuid

import psycopg
import pytest

CARE_POSTGRES_TEST_URL = os.environ.get("CARE_POSTGRES_TEST_URL")

pytestmark = pytest.mark.skipif(
    not CARE_POSTGRES_TEST_URL,
    reason="CARE_POSTGRES_TEST_URL not set; integration tests require a real Postgres",
)

from scripts.postgres_backend import PostgresBackend  # noqa: E402


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
                "SELECT created_at, modified_at, content FROM care_artifacts "
                "WHERE workspace=%s AND path=%s",
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

    expected = sorted(
        (e["name"], e["is_dir"]) for e in backend.ls_info("/")
    )
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
