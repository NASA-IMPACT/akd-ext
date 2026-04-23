"""Custom pydantic_ai capabilities and history processors built from AKD
scalar config fields.

Concrete implementations behind ``PydanticAIBaseAgent``'s
``_build_capabilities_from_scalars`` and
``_build_history_processors_from_scalars`` hooks. Factories here return
ready-to-use pydantic_ai objects (``Hooks`` capabilities or plain
history-processor callables); the base agent constructs them at
``__init__`` time from the relevant ``BaseAgentConfig`` fields.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def make_ratio_trimmer(trim_ratio: float) -> Callable[[list[Any]], list[Any]]:
    """Return a stateless history processor that drops the oldest
    ``trim_ratio`` fraction of messages on every invocation.

    A ``trim_ratio`` of ``0.3`` drops the oldest 30% of the message list;
    ``0.0`` is a no-op; ratios ≥ ``1.0`` are rejected (would drop
    everything). The first message is preserved so a system-prompt-style
    preamble survives trimming.

    .. warning::

        Naive drop-from-the-middle trimming can strand pydantic_ai
        ``ToolReturnPart`` messages that were paired with an earlier
        ``ToolCallPart``. OpenAI's API rejects such histories. This
        trimmer is safe only when callers know their history shape
        (e.g. no tool calls, or a custom trimmer hook manages pairing).
        ``PydanticAIBaseAgentConfig`` defaults ``enable_trimming=False``
        for exactly that reason — callers opt in.
    """
    if not 0 <= trim_ratio < 1:
        raise ValueError(f"trim_ratio must be in [0, 1), got {trim_ratio!r}")

    def processor(messages: list[Any]) -> list[Any]:
        if not messages or trim_ratio == 0:
            return messages
        head, rest = messages[:1], messages[1:]
        drop_count = int(len(rest) * trim_ratio)
        return [*head, *rest[drop_count:]]

    return processor


__all__ = [
    "make_ratio_trimmer",
]
