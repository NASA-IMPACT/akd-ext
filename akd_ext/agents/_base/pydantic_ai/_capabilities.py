"""Custom pydantic_ai Capabilities built from AKD scalar config fields.

Concrete implementations behind ``PydanticAIBaseAgent``'s
``_build_capabilities_from_scalars`` hook. Each factory here returns a
ready-to-use pydantic_ai ``Hooks`` capability; the base agent constructs
them at ``__init__`` time from the relevant ``BaseAgentConfig`` fields.
"""

from __future__ import annotations

from pydantic_ai.capabilities.hooks import Hooks

from akd._base.errors import MaxToolCallsExceeded, MaxToolIterationsExceeded


def ToolCallLimits(
    *,
    max_iterations: int | None = None,
    max_calls: int | None = None,
) -> Hooks:
    """Build a ``Hooks`` capability that caps tool-loop iterations and total tool calls.

    Counters live in closure state; each agent instance gets its own
    ``Hooks`` via ``_build_capabilities_from_scalars``. Counters reset on
    agent construction, not per-run — which mirrors AKD's historical ReAct
    cap semantics. Callers who need per-run reset should reconstruct the
    agent.

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


__all__ = [
    "ToolCallLimits",
]
