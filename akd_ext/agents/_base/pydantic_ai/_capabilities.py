"""Custom pydantic_ai Capabilities built from AKD scalar config fields.

Concrete implementations behind ``PydanticAIBaseAgent``'s
``_build_capabilities_from_scalars`` hook. Each factory here returns a
ready-to-use pydantic_ai ``Hooks`` capability; the base agent constructs
them at ``__init__`` time from the relevant ``BaseAgentConfig`` fields.
"""

from __future__ import annotations

from pydantic_ai.capabilities.hooks import Hooks


def ReflectionCapability(*, prompt: str) -> Hooks:
    """Build a ``Hooks`` capability that injects ``prompt`` before each model
    request after the first.

    Implementation: a counter tracks how many model requests have fired;
    from the second onwards, we prepend the reflection prompt as a system
    instruction to the pending request. The first request is skipped so
    the reflection prompt never leaks into the initial user-facing turn.
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


__all__ = [
    "ReflectionCapability",
]
