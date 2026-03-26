from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any, Literal, cast

from agents import (
    Agent,
    ModelSettings,
    RunConfig,
    Runner,
    ToolsToFinalOutputResult,
    function_tool,
    trace,
)
from agents.stream_events import (
    RawResponsesStreamEvent,
    RunItemStreamEvent,
)
from openai.types.shared.reasoning import Reasoning

from loguru import logger
from pydantic import Field, field_validator

from akd._base.streaming import StreamEvent, StreamingMixin
from akd._base.structures import RunUsage
from akd._base import (
    InputSchema,
    OutputSchema,
    StreamingTokenEvent,
    StreamingEventData,
    ThinkingEvent,
    ThinkingEventData,
    ToolCallingEvent,
    ToolCallingEventData,
    ToolCall,
    ToolResultEvent,
    ToolResultEventData,
    ToolResult,
    CompletedEvent,
    CompletedEventData,
    HumanResponseEvent,
    HumanResponseEventData,
    HumanInputRequiredEvent,
    HumanInputRequiredEventData,
    RunContext,
    PartialOutputEvent,
    PartialEventData,
    TextOutput,
)
from akd.agents._base import BaseAgent, BaseAgentConfig, OutputRoutingMixin
from akd.tools.human import HumanToolInput

from akd._base.errors import (
    HumanInputRequired,
    UnexpectedModelBehavior,
)

from akd.utils import PartialModel

from akd_ext.agents._mixins import FileAttachmentMixin

from akd_ext._types import AKDTool, OPENAI_TOOL_TYPES
from akd_ext.mcp.converter import tool_converter


class OpenAIBaseAgentConfig(BaseAgentConfig):
    """Configuration for OpenAI Agents SDK based AKD Agents.

    Extends BaseAgentConfig with OpenAI-specific settings for agents
    built with OpenAI's platform agent builder.

    Inherits `reasoning_effort` and `reasoning_summary` from BaseAgentConfig.
    Defaults to `stateless=False` (stateful) for multi-turn conversations.
    """

    output_mode: Literal["multi_tool", "unified_schema"] = Field(
        default="unified_schema",
        description="Output mode for union schemas. unified_schema (default) uses response_format envelope; "
        "multi_tool uses one final tool per schema branch.",
    )
    model_name: str = Field(
        default="gpt-5-nano",
        description="Model name for the agent.",
    )
    stateless: bool = Field(
        default=False,
        description="Whether to maintain conversation history. False = stateful (default for OpenAI agents).",
    )
    tools: list[Any] = Field(
        default_factory=list,
        description="Tools for the agent (OpenAITool, AKDTool(akd.tools._base.BaseTool) — AKDTools auto-converted to FunctionTool).",
    )
    tracing_params: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for OpenAI Agents SDK traceability (trace_name, workflow_id, etc.)",
    )

    # Additional ModelSettings parameters
    top_p: float | None = Field(default=None, description="Nucleus sampling parameter.")
    frequency_penalty: float | None = Field(default=None, description="Frequency penalty for token repetition.")
    presence_penalty: float | None = Field(default=None, description="Presence penalty for new topics.")

    @field_validator("tools", mode="before")
    @classmethod
    def _validate_and_convert_tools(cls, v: list) -> list:
        """Validate tool types and convert AKDTool instances to OpenAI FunctionTool."""
        converted = []
        for t in v:
            if isinstance(t, AKDTool):
                converted.append(function_tool(tool_converter(t)))
            elif isinstance(t, OPENAI_TOOL_TYPES):
                converted.append(t)
            else:
                raise ValueError(f"Invalid tool type: {type(t).__name__}. Expected OpenAITool or AKDTool.")
        return converted

    @property
    def model_settings(self) -> ModelSettings:
        """ModelSettings built from config values.

        Note: Reasoning models (o1, o3, gpt-5.2, etc.) don't support sampling
        parameters like temperature, top_p, frequency_penalty, presence_penalty.
        These are excluded when reasoning_effort is set.
        """
        reasoning = None
        if self.reasoning_effort:
            # Reasoning models don't support sampling parameters
            reasoning = Reasoning(
                effort=self.reasoning_effort,
                summary=self.reasoning_summary or "auto",
            )
            return ModelSettings(
                store=True,
                max_tokens=self.max_tokens,
                reasoning=reasoning,
            )
        # Non-reasoning models use standard sampling parameters
        return ModelSettings(
            store=True,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
        )

    @property
    def run_config(self) -> RunConfig:
        """RunConfig with tracing parameters."""
        return RunConfig(trace_metadata=self.tracing_params or {})


class OpenAIBaseAgent[InSchema: InputSchema, OutSchema: OutputSchema](
    FileAttachmentMixin, OutputRoutingMixin, BaseAgent, StreamingMixin
):
    """Base class for OpenAI Agents SDK based agents.

    Follows the akd-core BaseAgent template pattern:
    - `arun()` / `astream()` / `_astream()` are templates in BaseAgent
    - `_run_engine_stream()` is the provider-specific streaming engine (OpenAI SDK)
    - `_arun()` routes: no-tools → `get_response_async()`, tools → `_run_engine_stream()`
    - `OutputRoutingMixin` provides union output schema support

    Subclasses must define:
    - `input_schema`: Input schema class
    - `output_schema`: Output schema class (supports unions: `SchemaA | SchemaB`)

    Subclasses can override:
    - `_create_agent()`: For custom agent creation logic
    - `_arun()`: For complex multi-agent workflows
    """

    # Placeholders - subclasses must override
    input_schema = InputSchema
    output_schema = OutputSchema
    config_schema = OpenAIBaseAgentConfig

    def __init__(
        self,
        config: OpenAIBaseAgentConfig | None = None,
        debug: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(config=config, debug=debug)
        self._agent = self._create_agent()

    # ── Agent creation ───────────────────────────────────────────────

    def _create_agent(self) -> Agent:
        """Create the OpenAI Agent object, handling union output schemas.

        - Single schema: output_type=schema (or None for TextOutput)
        - Union + unified_schema: output_type=envelope model, unwrap after
        - Union + multi_tool: output_type=None, output tools converted to FunctionTools, StopAtTools
        """
        schemas = self.output_schema_resolved
        is_union = len(schemas) > 1
        is_text = not is_union and issubclass(schemas[0], TextOutput)

        if not is_union:
            return Agent(
                name=self.__class__.__name__,
                instructions=self.config.system_prompt,
                model=self.config.model_name or "gpt-5-nano",
                tools=self.config.tools,
                output_type=None if is_text else self.output_schema,
                model_settings=self.config.model_settings,
            )

        if self.output_mode == "unified_schema":
            envelope = self.effective_output_schema
            return Agent(
                name=self.__class__.__name__,
                instructions=self.config.system_prompt,
                model=self.config.model_name or "gpt-5-nano",
                tools=self.config.tools,
                output_type=envelope,
                model_settings=self.config.model_settings,
            )

        # multi_tool mode: use mode="json" so the SDK gets a valid JSON string
        # (not str(dict) which produces Python repr with single quotes)
        sdk_output_tools = [function_tool(t.as_function(mode="json")) for t in self.output_tools]
        all_tools = list(self.config.tools) + sdk_output_tools
        return Agent(
            name=self.__class__.__name__,
            instructions=self.config.system_prompt,
            model=self.config.model_name or "gpt-5-nano",
            tools=all_tools,
            output_type=None,
            model_settings=self.config.model_settings,
            tool_use_behavior=self._output_tool_behavior,
        )

    async def _output_tool_behavior(self, _ctx, results) -> ToolsToFinalOutputResult:
        """SDK tool_use_behavior callback: validate output tools via check_output.

        Adapts SDK's FunctionToolResult to akd-core ToolResult, then reuses
        the mixin's _resolve_output_tool_result + check_output.
        """
        output_names = {t.name for t in self.output_tools}
        for r in results:
            if r.tool.name not in output_names:
                continue
            adapted = ToolResult(tool_call_id="", tool_name=r.tool.name, content=r.output)
            parsed = self._resolve_output_tool_result(adapted)
            if parsed is not None and self.check_output(parsed) is None:
                return ToolsToFinalOutputResult(is_final_output=True, final_output=r.output)
            return ToolsToFinalOutputResult(is_final_output=False)
        return ToolsToFinalOutputResult(is_final_output=False)

    # ── Message format converters ────────────────────────────────────

    def _try_parse_json(self, content: str) -> dict[str, Any] | None:
        """Try to parse content as JSON."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _extract_usage(raw_responses: list[Any]) -> RunUsage:
        """Aggregate token usage from OpenAI SDK ModelResponse list into RunUsage."""
        run_usage = RunUsage()
        for response in raw_responses:
            usage = response.usage
            details: dict[str, int] = {}
            cached = usage.input_tokens_details.cached_tokens or 0
            if cached > 0:
                details["input_tokens_details.cached_tokens"] = cached
            reasoning = usage.output_tokens_details.reasoning_tokens or 0
            if reasoning > 0:
                details["output_tokens_details.reasoning_tokens"] = reasoning
            run_usage += RunUsage(
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                requests=1,
                details=details,
            )
        return run_usage

    @staticmethod
    def _to_runner_input(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert Chat Completions messages to Responses API format for Runner input.

        The internal messages list uses Chat Completions format (akd-core standard),
        but Runner.run_streamed() expects Responses API format for tool calls/results.
        """
        runner_input: list[dict[str, Any]] = []
        for msg in messages:
            role = msg.get("role")
            if role in ("system", "user", "developer"):
                runner_input.append({"role": role, "content": msg["content"]})
            elif role == "assistant":
                if msg.get("content"):
                    runner_input.append({"role": "assistant", "content": msg["content"]})
                for tc in msg.get("tool_calls", []):
                    func = tc.get("function", {})
                    arguments = func.get("arguments", {})
                    runner_input.append(
                        {
                            "type": "function_call",
                            "call_id": tc["id"],
                            "name": func["name"],
                            "arguments": json.dumps(arguments) if isinstance(arguments, dict) else str(arguments),
                        }
                    )
            elif role == "tool":
                runner_input.append(
                    {
                        "type": "function_call_output",
                        "call_id": msg["tool_call_id"],
                        "output": msg["content"],
                    }
                )
        return runner_input

    @staticmethod
    def _from_runner_output(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert Responses_API_format back to Chat_Completions_API messages format.

        The inverse of _to_runner_input(). Converts Runner output items
        (Responses API format) back to Chat Completions format (akd-core standard).
        This is done to enable reusability across AKD core. AKD core uses Chat_Completions_API(old) via litellm.
        TODO: later, make the akd-core accept both the API message format.
        """
        messages: list[dict[str, Any]] = []
        pending_tool_calls: list[dict[str, Any]] = []

        def _flush_tool_calls() -> None:
            if pending_tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": list(pending_tool_calls),
                    }
                )
                pending_tool_calls.clear()

        for item in items:
            item_type = item.get("type")
            role = item.get("role")
            if role in ("system", "user", "developer"):
                _flush_tool_calls()
                messages.append({"role": role, "content": item["content"]})
            elif role == "assistant":
                _flush_tool_calls()
                messages.append({"role": "assistant", "content": item.get("content", "")})
            elif item_type == "message" and item.get("role") == "assistant":
                _flush_tool_calls()
                content_parts = item.get("content", [])
                text = ""
                if isinstance(content_parts, list):
                    text = "".join(
                        part.get("text", "")
                        for part in content_parts
                        if isinstance(part, dict) and part.get("type") == "output_text"
                    )
                elif isinstance(content_parts, str):
                    text = content_parts
                messages.append({"role": "assistant", "content": text})
            elif item_type in ("function_call", "mcp_call"):
                arguments = item.get("arguments", "{}")
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        pass
                pending_tool_calls.append(
                    {
                        "id": item.get("call_id") or item.get("id", ""),
                        "type": "function",
                        "function": {
                            "name": item["name"],
                            "arguments": arguments,
                        },
                    }
                )
                if item_type == "mcp_call" and "output" in item:
                    _flush_tool_calls()
                    mcp_output = item["output"]
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": item.get("call_id") or item.get("id", ""),
                            "content": mcp_output if isinstance(mcp_output, str) else json.dumps(mcp_output),
                        }
                    )
            elif item_type in ("function_call_output", "mcp_call_output"):
                _flush_tool_calls()
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": item["call_id"],
                        "content": item.get("output", ""),
                    }
                )
        _flush_tool_calls()
        return messages

    # ── HITL helpers ─────────────────────────────────────────────────

    def _inject_human_response(self, messages: list[dict[str, Any]], run_context: RunContext) -> None:
        """Inject human response into messages for HITL resume.

        BaseAgent._append_user_turn() skips appending the user message on resume,
        but the actual tool response + developer guidance must be injected by the provider.
        """
        human_response = run_context.human_response
        if not human_response:
            return
        messages.append(
            {"role": "tool", "tool_call_id": human_response.tool_call_id, "content": json.dumps(human_response.content)}
        )
        messages.append(
            {
                "role": "developer",
                "content": (
                    "The human has responded. Continue your workflow based on their input. "
                    "If you still need clarification or more details, ask the human again."
                ),
            }
        )

    # ── Non-streaming path ───────────────────────────────────────────

    async def get_response_async(
        self,
        *,
        run_context: RunContext,
        **kwargs,
    ) -> Any:
        """Run the agent via Runner.run() and return the RunResult."""
        class_name = self.__class__.__name__
        messages = run_context.messages

        self._inject_human_response(messages, run_context)

        with trace(class_name):
            result = await Runner.run(
                self._agent,
                input=self._to_runner_input(messages),
                run_config=self.config.run_config,
            )
            messages[:] = self._from_runner_output(result.to_input_list())
            run_context.usage += self._extract_usage(result.raw_responses)
            return result

    # ── _arun: routes between direct call and streaming engine ───────

    async def _arun(self, params: InSchema, run_context: RunContext, **kwargs) -> OutSchema:
        """Run the agent workflow.

        Routes between:
        - Direct mode (no tools, no union multi_tool): Runner.run() via get_response_async
        - Tool/union mode: consumes _run_engine_stream() watching for CompletedEvent
        """
        # Resolve and inject file attachments before LLM call
        await self._resolve_and_inject_files(run_context.messages, run_context)

        has_union = len(self.output_schema_resolved) > 1
        use_tool_loop = bool(self.config.tools) or (has_union and self.output_mode == "multi_tool")

        if not use_tool_loop:
            result = await self.get_response_async(run_context=run_context)
            return self._resolve_final_output(result.final_output)

        async for event in self._run_engine_stream(run_context=run_context):
            if isinstance(event, CompletedEvent):
                return cast(OutSchema, event.data.output)
            if isinstance(event, HumanInputRequiredEvent):
                raise HumanInputRequired(str(event.data.human_input))

        raise UnexpectedModelBehavior("Tool loop completed without producing output")

    # overriding astream to include file upload mixin functionality
    async def astream(
        self,
        params: Any,
        run_context: RunContext | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamEvent]:
        # Resolve and inject file attachments before LLM call
        await self._resolve_and_inject_files(run_context.messages, run_context)
        async for event in super().astream(params=params, run_context=run_context, **kwargs):
            yield event

    # ── Output resolution ────────────────────────────────────────────

    def _resolve_final_output(self, final_output: Any) -> OutSchema:
        """Resolve raw SDK output to the correct output schema type.

        Handles single schemas, union unified_schema (envelope unwrapping),
        and union multi_tool (already resolved by FunctionTool callback).
        """
        schemas = self.output_schema_resolved

        # Check if it's already a valid output
        for schema in schemas:
            if isinstance(final_output, schema):
                return cast(OutSchema, final_output)

        # TextOutput handling (single schema only)
        if len(schemas) == 1 and issubclass(schemas[0], TextOutput):
            return cast(OutSchema, schemas[0](content=final_output))

        # Unified schema envelope unwrapping
        if len(schemas) > 1 and self.output_mode == "unified_schema":
            unwrapped = self._unwrap_unified_output(final_output)
            if unwrapped is not None:
                return cast(OutSchema, unwrapped)

        # Try model_dump conversion
        if hasattr(final_output, "model_dump"):
            data = final_output.model_dump()
            for schema in schemas:
                try:
                    return cast(OutSchema, schema.model_validate(data))
                except Exception:
                    continue

        # Raw string fallback: try JSON parsing first, then TextOutput for plain text
        if isinstance(final_output, str):
            for schema in schemas:
                try:
                    return cast(OutSchema, schema.model_validate_json(final_output))
                except Exception:
                    continue
            text_schemas = [s for s in schemas if issubclass(s, TextOutput)]
            if text_schemas:
                return cast(OutSchema, text_schemas[0](content=final_output))

        raise UnexpectedModelBehavior(f"Could not resolve output to any of: {[s.__name__ for s in schemas]}")

    # ── _run_engine_stream: OpenAI SDK streaming engine ──────────────

    async def _run_engine_stream(
        self,
        run_context: RunContext,
        **kwargs: Any,
    ) -> AsyncIterator[StreamEvent]:
        """OpenAI SDK streaming engine using Runner.run_streamed().

        Provider-specific implementation of the akd-core _run_engine_stream() contract.
        Yields StreamEvents for tool calls, reasoning, tokens, and final output.
        """
        class_name = self.__class__.__name__
        messages = run_context.messages

        # HITL resume
        human_response = run_context.human_response
        if human_response:
            self._inject_human_response(messages, run_context)
            yield HumanResponseEvent(
                source=class_name,
                message="Resumed with human input",
                data=HumanResponseEventData(tool_call_id=human_response.tool_call_id, response=human_response.content),
                run_context=run_context,
            )

        # Partial output model — for unified_schema use envelope, skip for multi_tool
        partial_model = None
        if len(self.output_schema_resolved) > 1:
            if self.output_mode == "unified_schema":
                partial_model = PartialModel[self.effective_output_schema]
        else:
            partial_model = PartialModel[self.output_schema]

        # LLM Call
        accumulated = ""
        last_partial_dict = None
        current_turn_tool_calls: list[dict[str, Any]] = []
        current_turn_has_outputs: bool = False
        current_trace = trace(class_name)
        current_trace.__enter__()
        try:
            stream = Runner.run_streamed(
                self._agent,
                input=self._to_runner_input(messages),
                run_config=self.config.run_config,
            )

            async for event in stream.stream_events():
                if self.debug:
                    if isinstance(event, RawResponsesStreamEvent):
                        logger.debug(f"[{class_name}] RawEvent: {getattr(event.data, 'type', 'unknown')}")
                    elif isinstance(event, RunItemStreamEvent):
                        logger.debug(f"[{class_name}] RunItemEvent: {event.name}")

                if isinstance(event, RawResponsesStreamEvent):
                    event_type = getattr(event.data, "type", "")

                    if event_type == "response.output_text.delta":
                        delta = getattr(event.data, "delta", "") or ""
                        accumulated += delta
                        if delta:
                            yield StreamingTokenEvent(
                                source=class_name,
                                message=f"Streaming {class_name}",
                                data=StreamingEventData(token=delta),
                                run_context=run_context,
                            )

                        if partial_model is not None:
                            parsed = self._try_parse_json(accumulated)
                            if parsed and parsed != last_partial_dict:
                                last_partial_dict = parsed
                                try:
                                    partial = partial_model.model_validate(parsed)
                                    yield PartialOutputEvent(
                                        source=class_name,
                                        message="Partial...",
                                        data=PartialEventData(partial_output=partial),
                                        run_context=run_context,
                                    )
                                except Exception:
                                    pass

                    elif event_type == "response.output_text.done":
                        done_text = getattr(event.data, "text", "") or ""
                        if done_text and not accumulated:
                            accumulated = done_text

                    elif "reasoning" in event_type:
                        content = getattr(event.data, "content", "") or getattr(event.data, "delta", "") or ""
                        if content:
                            yield ThinkingEvent(
                                source=class_name,
                                message="Reasoning...",
                                data=ThinkingEventData(thinking_content=content),
                                run_context=run_context,
                            )

                elif isinstance(event, RunItemStreamEvent):
                    if event.name == "tool_called":
                        raw_item = getattr(event.item, "raw_item", None)
                        if raw_item:
                            tool_name = getattr(raw_item, "name", "")
                            tool_input_raw = getattr(raw_item, "arguments", "{}")
                            tool_input = (
                                json.loads(tool_input_raw) if isinstance(tool_input_raw, str) else tool_input_raw
                            )
                            tool_call_id = getattr(raw_item, "call_id", None) or getattr(
                                raw_item, "id", uuid.uuid4().hex[:8]
                            )

                            # Turn boundary: new tool_called after previous turn's outputs → reset
                            if current_turn_has_outputs:
                                current_turn_tool_calls = []
                                current_turn_has_outputs = False

                            current_turn_tool_calls.append(
                                {
                                    "id": tool_call_id,
                                    "type": "function",
                                    "function": {"name": tool_name, "arguments": tool_input},
                                }
                            )
                            yield ToolCallingEvent(
                                source=class_name,
                                message=f"Calling tool: {tool_name}",
                                data=ToolCallingEventData(
                                    tool_call=ToolCall(
                                        tool_call_id=tool_call_id,
                                        tool_name=tool_name,
                                        arguments=tool_input,
                                    )
                                ),
                                run_context=run_context,
                            )

                            # HostedMCPTool: server-side execution, output on the raw_item itself
                            if getattr(raw_item, "type", "") == "mcp_call":
                                mcp_output = getattr(raw_item, "output", None)
                                if mcp_output is not None:
                                    if not current_turn_has_outputs and current_turn_tool_calls:
                                        messages.append(
                                            {
                                                "role": "assistant",
                                                "content": None,
                                                "tool_calls": list(current_turn_tool_calls),
                                            }
                                        )
                                        current_turn_has_outputs = True

                                    serialized = mcp_output if isinstance(mcp_output, str) else json.dumps(mcp_output)
                                    messages.append(
                                        {"role": "tool", "tool_call_id": tool_call_id, "content": serialized}
                                    )
                                    yield ToolResultEvent(
                                        source=class_name,
                                        message="Tool result",
                                        data=ToolResultEventData(
                                            result=ToolResult(
                                                tool_call_id=tool_call_id,
                                                tool_name=tool_name,
                                                content=mcp_output,
                                            )
                                        ),
                                        run_context=run_context,
                                    )

                            if tool_name == "ask_human":
                                try:
                                    human_input = HumanToolInput(**tool_input)
                                except Exception:
                                    human_input = HumanToolInput(question=tool_input.get("question", "Input needed"))

                                messages.append(
                                    {
                                        "role": "assistant",
                                        "content": None,
                                        "tool_calls": list(current_turn_tool_calls),
                                    }
                                )
                                run_context.messages = list(messages)
                                run_context.usage += self._extract_usage(stream.raw_responses)
                                stream.cancel()
                                current_trace.finish(reset_current=True)
                                yield HumanInputRequiredEvent(
                                    source=class_name,
                                    message=f"Human input required: {tool_input.get('question', 'Input needed')}",
                                    data=HumanInputRequiredEventData(
                                        human_input=human_input,
                                        tool_call_id=tool_call_id,
                                        tool_name=tool_name,
                                    ),
                                    run_context=run_context,
                                )
                                return

                    elif event.name == "tool_output":
                        raw_item = getattr(event.item, "raw_item", None)
                        tool_output_content = getattr(event.item, "output", None)
                        tool_call_id = (
                            raw_item.get("call_id", "")
                            if isinstance(raw_item, dict)
                            else getattr(raw_item, "call_id", "")
                        ) or uuid.uuid4().hex[:8]
                        if tool_output_content is not None:
                            if not current_turn_has_outputs and current_turn_tool_calls:
                                messages.append(
                                    {
                                        "role": "assistant",
                                        "content": None,
                                        "tool_calls": list(current_turn_tool_calls),
                                    }
                                )
                                current_turn_has_outputs = True

                            serialized = (
                                tool_output_content
                                if isinstance(tool_output_content, str)
                                else json.dumps(tool_output_content)
                            )
                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call_id,
                                    "content": serialized,
                                }
                            )

                            yield ToolResultEvent(
                                source=class_name,
                                message="Tool result",
                                data=ToolResultEventData(
                                    result=ToolResult(
                                        tool_call_id=tool_call_id,
                                        tool_name=getattr(raw_item, "name", "unknown"),
                                        content=tool_output_content,
                                    )
                                ),
                                run_context=run_context,
                            )

            run_context.usage += self._extract_usage(stream.raw_responses)

            if self.debug:
                logger.debug(
                    f"[{class_name}] accumulated={len(accumulated)} chars, "
                    f"stream.final_output={type(stream.final_output).__name__}"
                )

            # Resolve final output
            final_output = self._resolve_final_output(stream.final_output)

            if final_output:
                yield CompletedEvent(
                    source=class_name,
                    message=f"Completed {class_name}",
                    data=CompletedEventData(output=final_output),
                    run_context=run_context,
                )
        finally:
            try:
                current_trace.__exit__(None, None, None)
            except (ValueError, RuntimeError):
                pass
