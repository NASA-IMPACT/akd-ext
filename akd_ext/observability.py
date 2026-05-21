"""Minimal Logfire setup for pydantic-ai and OpenAI Agents SDK auto-instrumentation."""

from __future__ import annotations

import os
import sys

import logfire

_INITIALIZED = False


def _enabled() -> bool:
    return os.getenv("LOGFIRE_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _warn_instrument(name: str, exc: Exception) -> None:
    msg = str(exc).strip().split("\n")[0]
    print(f"warning: logfire.{name} skipped ({msg}).", file=sys.stderr)


def init_observability(service_name: str = "akd-ext") -> None:
    """Configure Logfire and instrument agent frameworks (call before agent imports)."""
    global _INITIALIZED
    if _INITIALIZED or not _enabled():
        _INITIALIZED = True
        return

    token = os.getenv("LOGFIRE_TOKEN")
    kwargs: dict[str, object] = {
        "service_name": service_name,
        "environment": os.getenv("LOGFIRE_ENV", os.getenv("ENV", "local")),
        "inspect_arguments": False,
    }
    if token:
        kwargs["token"] = token
    logfire.configure(**kwargs)

    for instrument_name in ("instrument_pydantic_ai", "instrument_openai_agents"):
        try:
            getattr(logfire, instrument_name)()
        except Exception as exc:
            _warn_instrument(instrument_name, exc)

    if _env_flag("LOGFIRE_INSTRUMENT_HTTPX", default=True):
        try:
            logfire.instrument_httpx(capture_headers=False)
        except Exception as exc:
            _warn_instrument("instrument_httpx", exc)

    _INITIALIZED = True
