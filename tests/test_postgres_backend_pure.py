"""Pure unit tests for scripts.postgres_backend helpers — no DB required.

These cover ``redact_dsn`` and the internal ``_state_size`` /
``_normalize_path`` / ``_validate_path`` helpers. They run in every CI
configuration because they don't depend on ``CARE_POSTGRES_TEST_URL``.
"""

from __future__ import annotations

from scripts.postgres_backend.backend import (
    _normalize_path,
    _state_size,
    _validate_path,
    redact_dsn,
)


# ── redact_dsn ──────────────────────────────────────────────────────────────


def test_redact_simple_password() -> None:
    out = redact_dsn("postgresql://user:secret@host:5432/db")
    assert "secret" not in out
    assert ":***@host:5432/db" in out


def test_redact_url_encoded_password() -> None:
    """URL-encoded passwords broke the previous substring-replace impl.

    `parsed.password` returns the *decoded* form (`p@ss/word`); the netloc
    contains the *encoded* form (`p%40ss%2Fword`). The replace-by-substring
    approach silently failed and leaked the password. We rebuild netloc
    from parsed components instead.
    """
    dsn = "postgresql://user:p%40ss%2Fword@host:5432/db"
    out = redact_dsn(dsn)
    assert "p@ss" not in out
    assert "p%40ss" not in out
    assert "p%2F" not in out
    assert ":***@host:5432/db" in out


def test_redact_no_password_passthrough() -> None:
    dsn = "postgresql://localhost/care_dev"
    assert redact_dsn(dsn) == dsn


def test_redact_no_user_with_password() -> None:
    """Edge case: a DSN like ``://:pw@host`` — no username, only password."""
    out = redact_dsn("postgresql://:secret@host:5432/db")
    assert "secret" not in out
    assert ":***@host:5432/db" in out


def test_redact_non_dsn_garbage() -> None:
    # urlparse won't choke on arbitrary strings; result without a password
    # should round-trip unchanged.
    assert redact_dsn("not a url") == "not a url"


def test_redact_preserves_database_path() -> None:
    dsn = "postgresql://user:pw@host:5432/care_dev?sslmode=require"
    out = redact_dsn(dsn)
    assert "/care_dev" in out
    assert "sslmode=require" in out
    assert "pw" not in out


# ── _state_size: matches StateBackend's sum-of-line-lengths semantic ────────


def test_state_size_empty_string() -> None:
    assert _state_size("") == 0


def test_state_size_single_line() -> None:
    assert _state_size("hello") == 5


def test_state_size_with_newlines() -> None:
    # "abc\ndef" → split → ["abc","def"] → sum 6.
    assert _state_size("abc\ndef") == 6


def test_state_size_only_newlines() -> None:
    # "\n\n" → split → ["","",""] → sum 0.
    assert _state_size("\n\n") == 0


def test_state_size_unicode_codepoints_not_bytes() -> None:
    # "é" is 1 codepoint but 2 utf-8 bytes. StateBackend uses len(str), so
    # _state_size must report 1 to stay aligned.
    assert _state_size("é") == 1


# ── _validate_path / _normalize_path ────────────────────────────────────────


def test_validate_rejects_dotdot() -> None:
    assert _validate_path("../etc/passwd") == "Path cannot contain '..'"


def test_validate_rejects_tilde() -> None:
    assert _validate_path("~/secret") == "Path cannot start with '~'"


def test_validate_rejects_windows_drive() -> None:
    assert _validate_path("C:/Users") == "Windows absolute paths are not allowed"


def test_validate_rejects_null_byte() -> None:
    assert _validate_path("foo\x00bar") == "Path cannot contain null bytes"


def test_validate_accepts_normal_paths() -> None:
    for p in ("/", "/scope.md", "/contexts/index.md", "scope.md"):
        assert _validate_path(p) is None


def test_normalize_root_aliases() -> None:
    for alias in ("", ".", "./"):
        assert _normalize_path(alias) == "/"


def test_normalize_strips_trailing_slash_but_preserves_root() -> None:
    assert _normalize_path("/contexts/") == "/contexts"
    assert _normalize_path("/") == "/"


def test_normalize_prepends_slash() -> None:
    assert _normalize_path("scope.md") == "/scope.md"
    assert _normalize_path("./scope.md") == "/scope.md"
