"""Custom pydantic_ai Capabilities built from AKD scalar config fields.

These are the concrete implementations behind ``PydanticAIBaseAgent``'s
``_build_capabilities_from_scalars`` / ``_build_history_processors_from_scalars``
hooks.

Factories in this module return ready-to-use pydantic_ai ``Capability`` or
``history_processor`` objects. The base agent constructs them at ``__init__``
time from the relevant ``BaseAgentConfig`` fields.

Contents:

- ``ToolCallLimits(max_iterations=..., max_calls=...)`` — Hooks-based cap on
  tool-loop iterations and total tool calls; raises AKD's ``UsageLimitExceeded``
  (which pydantic_ai surfaces via ``UnexpectedModelBehavior`` to the caller).
- ``ReflectionCapability(prompt=...)`` — Hooks-based injector that prepends
  ``prompt`` as a system-level nudge on every model request after the first.
- ``make_ratio_trimmer(trim_ratio=...)`` — stateless history processor that
  drops the oldest fraction of the conversation when invoked.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic_ai.capabilities.hooks import Hooks

from akd._base.errors import MaxToolCallsExceeded, MaxToolIterationsExceeded


def ToolCallLimits(
    *,
    max_iterations: int | None = None,
    max_calls: int | None = None,
) -> Hooks:
    """Build a Hooks capability that caps tool-loop iterations and tool calls.

    Counters live in closure state; each agent instance gets its own ``Hooks``
    via ``_build_capabilities_from_scalars``. Counters reset on agent
    construction, not per-run — which mirrors AKD's historical ReAct cap
    semantics. Callers who need per-run reset should reconstruct the agent.

    Raises:
        MaxToolIterationsExceeded: when ``max_iterations`` is set and the
            model-request loop would exceed the cap on the next round.
        MaxToolCallsExceeded: when ``max_calls`` is set and the total number
            of tool executions would exceed the cap.
    """
    hooks = Hooks()
    state = {"iterations": 0, "calls": 0}

    if max_iterations is not None:

        @hooks.on.before_model_request
        async def _cap_iterations(ctx, request_context):  # noqa: ARG001
            state["iterations"] += 1
            if state["iterations"] > max_iterations:
                raise MaxToolIterationsExceeded(
                    f"Exceeded max tool iterations ({max_iterations}).",
                )
            return request_context

    if max_calls is not None:

        @hooks.on.before_tool_execute
        async def _cap_calls(ctx, *, call, tool_def, args):  # noqa: ARG001
            state["calls"] += 1
            if state["calls"] > max_calls:
                raise MaxToolCallsExceeded(
                    f"Exceeded max tool calls ({max_calls}).",
                )
            return args

    return hooks


def ReflectionCapability(*, prompt: str) -> Hooks:
    """Build a Hooks capability that injects ``prompt`` before each model request
    after the first.

    Implementation: a counter tracks how many model requests have fired;
    from the second onwards, we prepend the reflection prompt as a system
    instruction to the pending request. The first request is skipped so the
    reflection prompt never leaks into the initial turn.
    """
    from pydantic_ai.messages import ModelRequest, SystemPromptPart

    hooks = Hooks()
    state = {"turn": 0}

    @hooks.on.before_model_request
    async def _inject_reflection(ctx, request_context):  # noqa: ARG001
        state["turn"] += 1
        if state["turn"] == 1:
            return request_context
        # Prepend the reflection as a system message on this turn
        request_context.messages = [
            ModelRequest(parts=[SystemPromptPart(content=prompt)]),
            *request_context.messages,
        ]
        return request_context

    return hooks


def make_ratio_trimmer(trim_ratio: float) -> Callable[[list[Any]], list[Any]]:
    """Return a stateless history processor that drops the oldest
    ``trim_ratio`` fraction of messages.

    A ``trim_ratio`` of ``0.3`` drops the oldest 30% of the message list on
    each call. ``0.0`` is a no-op; ``1.0`` drops everything (don't do that).
    The first message (usually the system prompt) is preserved so the agent's
    instructions survive trimming.
    """
    if not 0 <= trim_ratio < 1:
        raise ValueError(f"trim_ratio must be in [0, 1), got {trim_ratio!r}")

    def processor(messages: list[Any]) -> list[Any]:
        if not messages or trim_ratio == 0:
            return messages
        # Keep the first message (usually system), trim the oldest portion
        # of the rest, keep the tail.
        head, rest = messages[:1], messages[1:]
        drop_count = int(len(rest) * trim_ratio)
        return [*head, *rest[drop_count:]]

    return processor


__all__ = [
    "ReflectionCapability",
    "ToolCallLimits",
    "make_ratio_trimmer",
]
