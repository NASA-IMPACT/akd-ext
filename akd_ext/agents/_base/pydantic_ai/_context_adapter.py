"""Helpers that extracts what pydantic_ai expects from AKD run-context values .

Both ``akd.RunContext`` and ``pydantic_ai.RunContext`` satisfy the
``RunContextProtocol`` structurally for the shared fields, but the types of
``usage`` and ``messages`` differ between the two sides:

- AKD stores messages as OpenAI-style dicts; pydantic_ai stores typed
  ``ModelMessage`` objects.
- AKD has its own ``RunUsage`` Pydantic BaseModel; pydantic_ai has its own
  ``RunUsage`` dataclass.

Because these difference in message and run_usage type in RunContext (which is pulled from core)
We needed to put pydanticAI runcontext as pai_run_context inside AKDRunContext.

The application which might be expecting messages and usage information will cease to work,
so, here we create adapters that fills the gap.
"""

from __future__ import annotations

from typing import Any

from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    TextPart,
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.result import RunUsage as PAIRunUsage

from akd._base.structures import RunUsage as AKDRunUsage


def _pai_messages_to_akd_dicts(messages: list[ModelMessage]) -> list[dict[str, Any]]:
    """
    Why this exists: pai's live ``RunContext.messages`` is ``list[ModelMessage]``,
    but AKD's ``RunContext.messages`` is typed ``list[dict[str, Any]] | None``
    and is pydantic-validated — assigning pai objects would be rejected. We
    reflect the pai messages onto AKD's dict-shaped slot so application logic
    reading ``run_context.messages`` (typically as read-only inspection for
    logs / UI / debugging, etc or already built application) sees useful content instead of ``None``.

    TLDR; For compatibility of RunContext in existing applications, in presence of
    PydnaticAI RunContext

    Produces OpenAI-style role-tagged dicts suitable for AKD's
    ``RunContext.messages: list[dict[str, Any]]`` field. Lossy for multi-part
    responses (text + thinking + tool calls collapse into one assistant dict),
    tool-argument dicts become JSON strings, and some part kinds (e.g. binary
    content in ``UserPromptPart``) are stringified. The lossless path remains
    available via ``run_context.pai_run_context.messages``.

    Note: Drop this helper once akd-core widens ``RunContext.messages`` to accept pai message
    types or Any — at that point ``_wrap_pai_ctx`` can assign ``pai_ctx.messages``
    directly.
    """
    out: list[dict[str, Any]] = []
    for msg in messages:
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, SystemPromptPart):
                    out.append({"role": "system", "content": part.content})
                elif isinstance(part, UserPromptPart):
                    content = part.content if isinstance(part.content, str) else str(part.content)
                    out.append({"role": "user", "content": content})
                elif isinstance(part, ToolReturnPart):
                    out.append(
                        {
                            "role": "tool",
                            "tool_call_id": part.tool_call_id,
                            "name": part.tool_name,
                            "content": str(part.content),
                        },
                    )
        elif isinstance(msg, ModelResponse):
            texts: list[str] = []
            tool_calls: list[dict[str, Any]] = []
            for part in msg.parts:
                if isinstance(part, TextPart):
                    texts.append(part.content)
                elif isinstance(part, ThinkingPart):
                    texts.append(f"[thinking] {part.content}")
                elif isinstance(part, ToolCallPart):
                    tool_calls.append(
                        {
                            "id": part.tool_call_id,
                            "type": "function",
                            "function": {
                                "name": part.tool_name,
                                "arguments": part.args_as_json_str(),
                            },
                        },
                    )
            assistant: dict[str, Any] = {
                "role": "assistant",
                "content": "\n".join(texts) if texts else "",
            }
            if tool_calls:
                assistant["tool_calls"] = tool_calls
            out.append(assistant)
    return out


def _pai_usage_to_akd_usage(pai_usage: PAIRunUsage) -> AKDRunUsage:
    """Map a ``pydantic_ai.RunUsage`` onto AKD's ``RunUsage``.

    For compatibility of RunContext in existing applications, in presence of
    PydnaticAI RunContext

    The three structural fields (``input_tokens`` / ``output_tokens`` /
    ``requests``) round-trip exactly. Pai's overflow fields (cache / audio
    token counts, ``tool_calls``) plus its own ``details`` dict collapse into
    AKD's ``details`` so no information is lost when this AKD view is the
    only thing a consumer inspects.

    Why this exists: pai's ``RunUsage`` is a distinct class from AKD's (fewer
    fields, different layout), and AKD's ``RunContext.usage`` is typed
    strictly. We reflect pai usage onto an AKD ``RunUsage`` so application
    logic reading ``run_context.usage`` (again, typically read-only
    inspection for billing / telemetry / UI) sees live counts instead of an
    empty default.

    Note: Drop this helper once akd-core's ``RunContext.usage``
    accepts pai's ``RunUsage`` directly — ``_wrap_pai_ctx`` can then forward
    ``pai_ctx.usage`` verbatim.
    """
    details: dict[str, int] = dict(pai_usage.details or {})
    for key in (
        "cache_write_tokens",
        "cache_read_tokens",
        "input_audio_tokens",
        "cache_audio_read_tokens",
        "output_audio_tokens",
        "tool_calls",
    ):
        val = getattr(pai_usage, key, 0) or 0
        if val:
            details[key] = val
    return AKDRunUsage(
        input_tokens=pai_usage.input_tokens,
        output_tokens=pai_usage.output_tokens,
        requests=pai_usage.requests,
        details=details,
    )


def _message_history_from_run_context(run_context: Any | None) -> list[ModelMessage] | None:
    """Extract a pydantic_ai-shaped message history from any ``RunContextProtocol``.

    For compatibility of RunContext in existing applications, in presence of
    PydnaticAI RunContext

    Returns ``None`` if the context has no messages.

    Lookup order:

    If the ctx has a populated ``pai_run_context`` extra (set by a previous
       ``PydanticAIBaseAgent`` run), return its ``messages`` verbatim — a
       lossless list of ``ModelMessage`` objects, no re-conversion needed.
    else, return None
    """
    if run_context is None:
        return None
    pai_ctx = getattr(run_context, "pai_run_context", None)
    if pai_ctx is not None and getattr(pai_ctx, "messages", None):
        return list(pai_ctx.messages)
    return None


def _usage_from_run_context(run_context: Any | None) -> PAIRunUsage | None:
    """Extract a pydantic_ai ``RunUsage`` from any ``RunContextProtocol``.

    Prefers ``run_context.pai_run_context.usage`` (a pai ``RunUsage``,
    returned verbatim — no conversion, no overflow loss). Falls back to the
    """
    if run_context is None:
        return None
    pai_ctx = getattr(run_context, "pai_run_context", None)
    if pai_ctx is not None and pai_ctx.usage is not None:
        return pai_ctx.usage
    return None


__all__ = [
    "_pai_messages_to_akd_dicts",
    "_pai_usage_to_akd_usage",
    "_usage_from_run_context",
    "_message_history_from_run_context",
]
