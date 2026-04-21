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
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.result import RunUsage as PAIRunUsage

from akd._base.protocols import TokenCounts
from akd._base.structures import RunUsage as AKDRunUsage


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


def _usage_to_pai(usage: TokenCounts) -> PAIRunUsage:
    """Build a ``pydantic_ai.RunUsage`` from anything matching ``TokenCounts``.

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


def _pai_messages_to_akd_dicts(messages: list[ModelMessage]) -> list[dict[str, Any]]:
    """Best-effort inverse of :func:`_akd_dicts_to_pai_messages`.

    Produces OpenAI-style role-tagged dicts suitable for AKD's
    ``RunContext.messages: list[dict[str, Any]]`` field. Lossy for multi-part
    responses (text + thinking + tool calls collapse into one assistant dict),
    tool-argument dicts become JSON strings, and some part kinds (e.g. binary
    content in ``UserPromptPart``) are stringified. The lossless path remains
    available via ``run_context.pai_run_context.messages``.

    Why this exists: pai's live ``RunContext.messages`` is ``list[ModelMessage]``,
    but AKD's ``RunContext.messages`` is typed ``list[dict[str, Any]] | None``
    and is pydantic-validated — assigning pai objects would be rejected. We
    reflect the pai messages onto AKD's dict-shaped slot so application logic
    reading ``run_context.messages`` (typically as read-only inspection for
    logs / UI / debugging) sees useful content instead of ``None``. Drop this
    helper once akd-core widens ``RunContext.messages`` to accept pai message
    types — at that point ``_wrap_pai_ctx`` can assign ``pai_ctx.messages``
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
    empty default. Drop this helper once akd-core's ``RunContext.usage``
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

    Returns ``None`` if the context has no messages.

    Lookup order:

    1. If the ctx has a populated ``pai_run_context`` extra (set by a previous
       ``PydanticAIBaseAgent`` run), return its ``messages`` verbatim — a
       lossless list of ``ModelMessage`` objects, no re-conversion needed.
    2. Otherwise, fall through to the historical shape-discriminating path:
       dicts get converted via :func:`_akd_dicts_to_pai_messages`, existing
       ``ModelMessage`` instances pass through.
    """
    if run_context is None:
        return None
    pai_ctx = getattr(run_context, "pai_run_context", None)
    if pai_ctx is not None and getattr(pai_ctx, "messages", None):
        return list(pai_ctx.messages)
    msgs = getattr(run_context, "messages", None)
    if not msgs:
        return None
    first = msgs[0]
    if isinstance(first, dict):
        return _akd_dicts_to_pai_messages(msgs)
    return msgs  # already pydantic_ai ModelMessage objects


def _usage_from_run_context(run_context: Any | None) -> PAIRunUsage | None:
    """Extract a pydantic_ai ``RunUsage`` from any ``RunContextProtocol``.

    Prefers ``run_context.pai_run_context.usage`` (a pai ``RunUsage``,
    returned verbatim — no conversion, no overflow loss). Falls back to the
    AKD-shape path via :func:`_usage_to_pai` when the extra is absent.
    """
    if run_context is None:
        return None
    pai_ctx = getattr(run_context, "pai_run_context", None)
    if pai_ctx is not None and pai_ctx.usage is not None:
        return pai_ctx.usage
    usage = getattr(run_context, "usage", None)
    if usage is None:
        return None
    return _usage_to_pai(usage)


__all__ = [
    "_akd_dicts_to_pai_messages",
    "_message_history_from_run_context",
    "_pai_messages_to_akd_dicts",
    "_pai_usage_to_akd_usage",
    "_usage_from_run_context",
    "_usage_to_pai",
]
