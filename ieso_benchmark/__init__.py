"""Lightweight per-turn logging for the GeoUI vs VLM-baseline comparison.

Sibling to ``ieso_w_geoui`` and ``ieso_w_vlm``. Both chat notebooks
call :func:`append_turn_record` after each completed (or errored)
agent turn; records are appended as JSON Lines to
``benchmarks/runs.jsonl`` at the worktree root. A separate analysis
script (or notebook cell) can then read the file and produce
poster-ready summaries — see :func:`load_runs`.
"""

from ieso_benchmark.log import (
    DEFAULT_ERROR_LOG_PATH,
    DEFAULT_LOG_PATH,
    ErrorRecord,
    TurnRecord,
    TurnUsage,
    append_error_record,
    append_turn_record,
    extract_usage,
    load_runs,
    new_session_id,
)

__all__ = [
    "DEFAULT_ERROR_LOG_PATH",
    "DEFAULT_LOG_PATH",
    "ErrorRecord",
    "TurnRecord",
    "TurnUsage",
    "append_error_record",
    "append_turn_record",
    "extract_usage",
    "load_runs",
    "new_session_id",
]
