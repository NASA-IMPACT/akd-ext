"""Helpers that reshape AKD run-context values to what pydantic_ai expects.

Both ``akd.RunContext`` and ``pydantic_ai.RunContext`` satisfy the
``RunContextProtocol`` structurally for the shared fields, but the types of
``usage`` and ``messages`` differ between the two sides:

- AKD stores messages as OpenAI-style dicts; pydantic_ai stores typed
  ``ModelMessage`` objects.
- AKD has its own ``RunUsage`` Pydantic BaseModel; pydantic_ai has its own
  ``RunUsage`` dataclass.

These helpers detect the incoming shape and convert when necessary, so a
caller can pass *either* an AKD ``RunContext`` or a ``pydantic_ai.RunContext``
to ``PydanticAIBaseAgent.arun`` / ``.astream`` and get the right thing wired
through to ``super().run(...)``.
"""

from __future__ import annotations

from typing import Any

from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.result import RunUsage as PAIRunUsage

from ._protocols import SupportsUsage


def _akd_dicts_to_pai_messages(messages: list[dict[str, Any]]) -> list[ModelMessage]:
    """Convert AKD OpenAI-style message dicts to pydantic_ai ``ModelMessage`` objects.

    Each dict is expected to have ``{"role": "...", "content": "..."}``.

    - ``system`` / ``user`` / ``tool`` → ``ModelRequest`` with the matching part
    - ``assistant`` → ``ModelResponse`` with a ``TextPart``
    """
    out: list[ModelMessage] = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "system":
            out.append(ModelRequest(parts=[SystemPromptPart(content=content)]))
        elif role == "user":
            out.append(ModelRequest(parts=[UserPromptPart(content=content)]))
        elif role == "assistant":
            out.append(ModelResponse(parts=[TextPart(content=content)]))
        # Roles we don't know how to translate (e.g. "tool" returns) are
        # skipped silently; the caller is expected to pass history we can
        # faithfully represent. Extending this map is a local change.
    return out


def _usage_to_pai(usage: SupportsUsage) -> PAIRunUsage:
    """Build a ``pydantic_ai.RunUsage`` from anything matching ``SupportsUsage``.

    Pass-through if the value is already a ``pydantic_ai.RunUsage``. Otherwise
    copy the three structural fields; all other ``RunUsage`` fields default to 0.
    """
    if isinstance(usage, PAIRunUsage):
        return usage
    return PAIRunUsage(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        requests=usage.requests,
    )


def _message_history_from_run_context(run_context: Any | None) -> list[ModelMessage] | None:
    """Extract a pydantic_ai-shaped message history from any ``RunContextProtocol``.

    Returns ``None`` if the context has no messages.

    Detects whether the incoming ``messages`` are dicts (AKD) or already
    ``ModelMessage`` instances (pydantic_ai) and adapts accordingly.
    """
    if run_context is None or not getattr(run_context, "messages", None):
        return None
    msgs = run_context.messages
    first = msgs[0]
    if isinstance(first, dict):
        return _akd_dicts_to_pai_messages(msgs)
    return msgs  # already pydantic_ai ModelMessage objects


def _usage_from_run_context(run_context: Any | None) -> PAIRunUsage | None:
    """Extract a pydantic_ai ``RunUsage`` from any ``RunContextProtocol``."""
    if run_context is None:
        return None
    usage = getattr(run_context, "usage", None)
    if usage is None:
        return None
    return _usage_to_pai(usage)


__all__ = [
    "_akd_dicts_to_pai_messages",
    "_message_history_from_run_context",
    "_usage_from_run_context",
    "_usage_to_pai",
]
