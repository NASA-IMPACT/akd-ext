"""This contains utility used by the PydanticAIBaseAgent

## 1. Translate pydantic_ai stream events into AKD ``StreamEvent`` objects.

``astream`` on ``PydanticAIBaseAgent`` wraps ``pydantic_ai.Agent.run_stream_events()``
and yields whatever we can translate. Events we can't faithfully map are
dropped (return ``None``); the caller iterator still terminates naturally when
the run completes, which is the AKD signal for end-of-stream anyway.

Translation table:

| pydantic_ai event                                | AKD event             |
|--------------------------------------------------|-----------------------|
| ``PartDeltaEvent(delta=TextPartDelta)``          | ``StreamingTokenEvent`` |
| ``PartStartEvent(part=ThinkingPart)``            | ``ThinkingEvent``       |
| ``PartDeltaEvent(delta=ThinkingPartDelta)``      | ``ThinkingEvent``       |
| ``FunctionToolCallEvent`` / ``BuiltinToolCallEvent`` | ``ToolCallingEvent`` |
| ``FunctionToolResultEvent`` / ``BuiltinToolResultEvent`` | ``ToolResultEvent`` |
| ``FinalResultEvent``                             | (dropped; iterator end signals completion) |
| ``PartStartEvent(part=TextPart)``, ``PartEndEvent`` | (dropped; no AKD analogue) |

A future ``CompletedEvent`` emission with the actual output value is the
responsibility of ``astream`` itself (after the iterator exhausts), not this
function — this translator is per-event.

## 2. Adapter from AKD ``BaseTool``-protocol instances to ``pydantic_ai.Tool``.

``BaseTool.as_function()`` already returns a typed async callable with the
right signature metadata for framework introspection. We only need to:

1. Wrap it so ``pydantic.ValidationError`` / ``akd.SchemaValidationError``
   become ``pydantic_ai.ModelRetry`` (so the LLM can self-correct on bad
   tool-call args); all other exceptions propagate and halt the run per
   pydantic_ai conventions.
2. Preserve the signature metadata that pydantic_ai introspects to build
   the tool's JSON schema.
3. Hand the callable to ``pydantic_ai.Tool`` with name/description pulled
   from the AKD tool.

``sequential``, ``timeout``, and per-tool ``max_retries`` stay at their
pydantic_ai defaults. AKD tools are stateless by design so parallel
execution is safe; per-tool knobs can arrive later via a dedicated
``PydanticAIBaseTool(BaseTool)`` that extends ``BaseToolConfig``.
"""

from pydantic import ValidationError
from pydantic_ai import ModelRetry
from pydantic_ai import Tool as PAITool
from akd._base.protocols import AKDTool

from akd._base.errors import SchemaValidationError

from pydantic_ai.messages import (
    BuiltinToolCallEvent,
    BuiltinToolResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
    ThinkingPart,
    ThinkingPartDelta,
    ToolCallPart,
    ToolCallPartDelta,
    ToolReturnPart,
)

from akd._base import (
    StreamEvent,
    StreamingEventData,
    StreamingTokenEvent,
    ThinkingEvent,
    ThinkingEventData,
    ToolCall,
    ToolCallingEvent,
    ToolCallingEventData,
    ToolResult,
    ToolResultEvent,
    ToolResultEventData,
)

from akd._base.structures import RunContext as AKDRunContext


def pai_event_to_akd_event(
    pai_event,
    run_context: AKDRunContext | None = None,
) -> StreamEvent | None:
    """Translate a single pydantic_ai stream event to an AKD ``StreamEvent``.

    Returns ``None`` for events we don't map; callers should skip those.

    ``run_context`` is an AKD ``RunContext`` built by the caller (typically
    wrapping the live ``pydantic_ai.RunContext`` under the ``pai_run_context``
    extra attribute); if supplied, it is attached to every constructed event
    so consumers can drive multi-turn continuation from any event.
    """
    ctx_kwargs = {"run_context": run_context} if run_context is not None else {}

    # Text delta → streaming token
    if isinstance(pai_event, PartDeltaEvent):
        delta = pai_event.delta
        if isinstance(delta, TextPartDelta):
            token = getattr(delta, "content_delta", "") or ""
            return StreamingTokenEvent(data=StreamingEventData(token=token), **ctx_kwargs)
        if isinstance(delta, ThinkingPartDelta):
            thinking = getattr(delta, "content_delta", "") or ""
            return ThinkingEvent(
                data=ThinkingEventData(thinking_content=thinking, streaming=True),
                **ctx_kwargs,
            )
        if isinstance(delta, ToolCallPartDelta):
            # Structured-output runs stream the args JSON of the final-output
            # tool call. Surface each chunk as a streaming token so UIs see
            # the model assembling its answer rather than nothing.
            args_delta = getattr(delta, "args_delta", None) or ""
            if isinstance(args_delta, dict):
                args_delta = str(args_delta)
            return StreamingTokenEvent(data=StreamingEventData(token=args_delta), **ctx_kwargs)
        return None

    # Thinking part started → emit a (non-streaming) thinking marker
    if isinstance(pai_event, PartStartEvent):
        part = pai_event.part
        if isinstance(part, ThinkingPart):
            content = getattr(part, "content", "") or ""
            return ThinkingEvent(data=ThinkingEventData(thinking_content=content), **ctx_kwargs)
        # TextPart start and other part kinds don't have a direct AKD analogue
        return None

    # Function tool call
    if isinstance(pai_event, (FunctionToolCallEvent, BuiltinToolCallEvent)):
        part = pai_event.part
        if isinstance(part, ToolCallPart):
            return ToolCallingEvent(
                data=ToolCallingEventData(
                    tool_call=ToolCall(
                        tool_call_id=part.tool_call_id or "",
                        tool_name=part.tool_name,
                        arguments=part.args_as_dict() if hasattr(part, "args_as_dict") else (part.args or {}),
                    ),
                ),
                **ctx_kwargs,
            )
        return None

    # Function tool result
    if isinstance(pai_event, (FunctionToolResultEvent, BuiltinToolResultEvent)):
        result = pai_event.result
        if isinstance(result, ToolReturnPart):
            return ToolResultEvent(
                data=ToolResultEventData(
                    result=ToolResult(
                        tool_call_id=result.tool_call_id or "",
                        tool_name=result.tool_name,
                        content=result.content,
                    ),
                ),
                **ctx_kwargs,
            )
        # RetryPromptPart results (tool retries) don't map to a success event
        return None

    return None


def akd_to_pai_tool(akd_tool: AKDTool) -> PAITool:
    """Adapt an AKD-protocol tool into a ``pydantic_ai.Tool``."""
    raw_fn = akd_tool.as_function()

    async def wrapped(*args, **kwargs):
        try:
            return await raw_fn(*args, **kwargs)
        except (ValidationError, SchemaValidationError) as e:
            raise ModelRetry(str(e)) from e

    wrapped.__name__ = raw_fn.__name__
    wrapped.__doc__ = raw_fn.__doc__
    wrapped.__signature__ = raw_fn.__signature__
    wrapped.__annotations__ = raw_fn.__annotations__

    return PAITool(
        wrapped,
        name=akd_tool.name,
        description=akd_tool.description or akd_tool.__class__.__doc__,
    )


__all__ = ["akd_to_pai_tool", "pai_event_to_akd_event"]
