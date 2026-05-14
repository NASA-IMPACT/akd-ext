"""Per-turn JSONL logging for the GeoUI vs VLM-baseline comparison.

One record per completed (or errored) ``agent.arun`` call. Writes are
append-only single-line JSON so the file can be tailed, grepped, or
loaded line-by-line without buffering issues.

Schema is a Pydantic model so the call sites can't silently drift —
adding a new field once here makes both notebooks log it consistently.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

AgentKind = Literal["geoui", "vlm"]
OutputKind = Literal["structured", "text", "error"]


def _default_log_path() -> Path:
    """Resolve ``benchmarks/runs.jsonl`` at the worktree root.

    ``BENCHMARK_LOG_PATH`` env var overrides. Falls back to the
    worktree root derived from this file's location
    (``<worktree>/ieso_benchmark/log.py`` → ``<worktree>``).
    """
    override = os.environ.get("BENCHMARK_LOG_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[1] / "benchmarks" / "runs.jsonl"


DEFAULT_LOG_PATH: Path = _default_log_path()


def new_session_id() -> str:
    """Return a short session id (uuid4 hex truncated) for grouping turns."""
    return uuid.uuid4().hex[:12]


class TurnUsage(BaseModel):
    """Per-turn token / request counts pulled from ``AKDRunUsage``."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    requests: int | None = None
    cache_read_tokens: int | None = None
    reasoning_tokens: int | None = None
    tool_calls: int | None = None


class TurnRecord(BaseModel):
    """One row of the benchmark log.

    A turn is a single ``agent.arun`` invocation — what the user
    perceives as one round-trip in the chat UI. The handler logs
    success and failure cases uniformly; the distinguishing field is
    ``output_kind`` (``"structured"`` / ``"text"`` / ``"error"``).
    """

    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agent: AgentKind
    session_id: str
    run_id: str | None = None
    turn_index: int
    user_prompt: str
    tool_calls: list[str] = Field(default_factory=list)
    tool_call_count: int = 0
    wall_clock_s: float
    usage: TurnUsage | None = None
    output_kind: OutputKind
    final_url: str | None = None
    error_type: str | None = None
    error_message: str | None = None


def extract_usage(usage_obj: Any) -> TurnUsage | None:
    """Pull the relevant fields out of an ``AKDRunUsage`` (or compatible) object.

    ``AKDRunUsage`` exposes ``input_tokens``, ``output_tokens``,
    ``requests``, ``total_tokens``, and a ``details`` dict that may
    carry ``cache_read_tokens``, ``reasoning_tokens``, and
    ``tool_calls``. Robust to missing fields — every value is
    ``Optional[int]``.
    """
    if usage_obj is None:
        return None
    details = getattr(usage_obj, "details", None) or {}
    return TurnUsage(
        input_tokens=getattr(usage_obj, "input_tokens", None),
        output_tokens=getattr(usage_obj, "output_tokens", None),
        total_tokens=getattr(usage_obj, "total_tokens", None),
        requests=getattr(usage_obj, "requests", None),
        cache_read_tokens=details.get("cache_read_tokens"),
        reasoning_tokens=details.get("reasoning_tokens"),
        tool_calls=details.get("tool_calls"),
    )


def append_turn_record(record: TurnRecord, path: Path | None = None) -> Path:
    """Append one JSONL row to ``path`` (default: ``DEFAULT_LOG_PATH``).

    Creates the parent directory on first call. Returns the path
    actually written so callers can surface it in the notebook UI.
    """
    target = (path or DEFAULT_LOG_PATH).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    line = record.model_dump_json(exclude_none=False)
    with target.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    return target


def load_runs(path: Path | None = None) -> list[TurnRecord]:
    """Read all turns from a JSONL log into a list of :class:`TurnRecord`.

    Skips blank lines; raises on malformed JSON or schema violations.
    Use this from a separate analysis script — the notebook handlers
    only append.
    """
    target = (path or DEFAULT_LOG_PATH).expanduser().resolve()
    if not target.exists():
        return []
    records: list[TurnRecord] = []
    with target.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(TurnRecord.model_validate_json(line))
    return records


__all__ = [
    "DEFAULT_LOG_PATH",
    "TurnRecord",
    "TurnUsage",
    "append_turn_record",
    "extract_usage",
    "load_runs",
    "new_session_id",
]
