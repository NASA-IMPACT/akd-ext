from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

from agents import Agent, ModelSettings, RunConfig, Runner, trace
from agents.stream_events import (
    RawResponsesStreamEvent,
    RunItemStreamEvent,
)

from akd._base.streaming import StreamEvent, StreamingMixin
from openai.types.shared.reasoning import Reasoning
from pydantic import Field

from akd._base import (
    InputSchema,
    OutputSchema,
    StreamEventType,
    StartingEvent,
    StartingEventData,
    RunningEvent,
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
    FailedEvent,
    FailedEventData,
    HumanResponseEvent,
    HumanResponseEventData,
    HumanInputRequiredEvent,
    HumanInputRequiredEventData,
    RunContext,
    PartialOutputEvent,
    PartialEventData,
    Memory,
)
from akd.agents._base import BaseAgent, BaseAgentConfig
from akd.tools.human import HumanToolInput

from akd._base.errors import (
    UnexpectedModelBehavior,
)

from akd.utils import PartialModel
from litellm.utils import trim_messages


class OpenAIBaseAgentConfig(BaseAgentConfig):
    """Configuration for OpenAI Agents SDK based AKD Agents.

    Extends BaseAgentConfig with OpenAI-specific settings for agents
    built with OpenAI's platform agent builder.

    Inherits `reasoning_effort` and `reasoning_summary` from BaseAgentConfig.
    Defaults to `stateless=False` (stateful) for multi-turn conversations.
    """

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
        description="Tools for the agent (FunctionTool, HostedMCPTool, WebSearchTool, etc.)",
    )
    tracing_params: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for OpenAI Agents SDK traceability (trace_name, workflow_id, etc.)",
    )

    # Additional ModelSettings parameters
    top_p: float | None = Field(default=None, description="Nucleus sampling parameter.")
    frequency_penalty: float | None = Field(default=None, description="Frequency penalty for token repetition.")
    presence_penalty: float | None = Field(default=None, description="Presence penalty for new topics.")

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


class OpenAIBaseAgent[InSchema: InputSchema, OutSchema: OutputSchema](BaseAgent, StreamingMixin):
    """Base class for OpenAI Agents SDK based agents.

    Provides:
    - Agent created in __init__ via `_create_agent()`
    - Memory via `memory` property (list[dict] - consistent with akd-core)
    - Stateful by default, clears memory each run if stateless=True

    Subclasses must define:
    - `input_schema`: Input schema class
    - `output_schema`: Output schema class

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
        memory: Memory | None = None,
        debug: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(config=config, memory=memory, debug=debug)
        self._agent = self._create_agent()

    def _create_agent(self) -> Agent:
        """Create the OpenAI Agent object.

        Uses tools and model settings from config.
        Override for custom agent creation logic.
        """
        return Agent(
            name=self.__class__.__name__,
            instructions=self.config.system_prompt,
            model=self.config.model_name or "gpt-5-nano",
            tools=self.config.tools,
            output_type=self.output_schema,
            model_settings=self.config.model_settings,
        )

    def _try_parse_json(self, content: str) -> dict[str, Any] | None:
        """Try to parse content as JSON."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None

    async def get_response_async(
        self,
        messages: list[dict[str, Any]],
        **kwargs,
    ) -> Any:
        """Run the agent and return the RunResult.

        Args:
            messages: Conversation messages. If None, uses internal memory.

        Returns:
            RunResult from the agent execution.
        """
        if self.enable_trimming:
            messages = trim_messages(
                messages, model=self.model_name, max_tokens=self.max_tokens, trim_ratio=self.trim_ratio
            )

        with trace(self.__class__.__name__):
            return await Runner.run(
                self._agent,
                input=messages,
                run_config=self.config.run_config,
            )

    async def _arun(self, params: InSchema, run_context: dict[str, Any] | None = None, **kwargs) -> OutSchema:
        """Run the agent workflow.

        Override for custom orchestration (e.g., multi-agent pipelines).
        """
        async with self.memory.asession(
            stateless=self.stateless,
            run_context=run_context,
            enable_trimming=self.enable_trimming,
            model_name=self.model_name,
            max_tokens=self.max_tokens,
            trim_ratio=self.trim_ratio,
        ) as messages:
            if not messages:
                messages.append(self._default_system_message())

            # because human response run context messages handled by _stream_llm_response
            if params and not (run_context and run_context.human_response):
                messages.append({"role": "user", "content": params.model_dump_json()})

            # Run pipeline via get_response_async
            result = await self.get_response_async(messages=messages)

            # Return typed output
            final_output = result.final_output

            # add final assistant response message
            messages.append(
                {
                    "role": "assistant",
                    "content": final_output.model_dump_json(exclude={"type"}),
                }
            )

            if isinstance(final_output, self.output_schema):
                return final_output
            elif hasattr(final_output, "model_dump"):
                return self.output_schema(**final_output.model_dump())
            else:
                return self.output_schema.model_validate_json(str(final_output))

    async def _stream_llm_response(
        self,
        messages: list[dict[str, Any]],
        run_context: RunContext,
        token_batch_size: int = 10,
    ) -> AsyncIterator[StreamEvent]:
        """Stream using Runner.run_streamed()."""

        class_name = self.__class__.__name__
        run_context.messages = messages

        if self.enable_trimming:
            messages = trim_messages(
                messages, model=self.model_name, max_tokens=self.max_tokens, trim_ratio=self.trim_ratio
            )

        # check for human response
        human_response = run_context.human_response
        if human_response:
            tool_call_id = human_response.tool_call_id
            content = human_response.content

            # Inject human response into messages. # update messages by reference
            messages.append({"role": "tool", "tool_call_id": tool_call_id, "content": json.dumps(content)})

            # Emit event to notify that human response has been injected
            yield HumanResponseEvent(
                source=class_name,
                message="Resumed with human input",
                data=HumanResponseEventData(tool_call_id=tool_call_id, response=content),
                run_context=run_context,
            )

        # For partial output validation (only for final answer)
        PartialResponseModel = PartialModel[self.output_schema]

        # LLM Call
        accumulated = ""
        token_buffer = ""
        last_partial_dict = None
        tool_calls_for_message: list[dict[str, Any]] = []  # message history of tool calls.

        stream = Runner.run_streamed(
            self._agent,
            input=messages,
            run_config=self.config.run_config,
        )

        async for event in stream.stream_events():
            if isinstance(event, RawResponsesStreamEvent):
                event_type = getattr(event.data, "type", "")

                if event_type == "response.output_text.delta":
                    delta = getattr(event.data, "delta", "") or ""

                    token_buffer += delta
                    accumulated += delta
                    if len(token_buffer) >= token_batch_size:
                        # yield {"type": StreamEventType.STREAMING, "token": token_buffer}
                        yield StreamingTokenEvent(
                            source=class_name,
                            message=f"Streaming {class_name}",
                            data=StreamingEventData(token=token_buffer),
                            run_context=run_context,
                        )

                        token_buffer = ""

                    parsed = self._try_parse_json(accumulated)
                    if parsed and parsed != last_partial_dict:
                        last_partial_dict = parsed
                        try:
                            partial = PartialResponseModel.model_validate(parsed)
                            yield PartialOutputEvent(
                                source=class_name,
                                message="Partial...",
                                data=PartialEventData(partial_output=partial),
                                run_context=run_context,
                            )
                        except Exception:
                            pass

                elif event_type == "response.output_text.done":
                    if token_buffer:
                        # yield {"type": StreamEventType.STREAMING, "token": token_buffer}
                        yield StreamingTokenEvent(
                            source=class_name,
                            message=f"Streaming {class_name}",
                            data=StreamingEventData(token=token_buffer),
                            run_context=run_context,
                        )
                        token_buffer = ""

                elif "reasoning" in event_type:
                    content = getattr(event.data, "content", "") or getattr(event.data, "delta", "") or ""
                    if content:
                        yield ThinkingEvent(
                            source=class_name,
                            message="Reasoning...",
                            data=ThinkingEventData(thinking_content=content),
                            run_context=run_context,
                        )
                        # yield {"type": StreamEventType.THINKING, "content": content}

            elif isinstance(event, RunItemStreamEvent):
                if event.name == "tool_called":
                    raw_item = getattr(event.item, "raw_item", None)
                    if raw_item:
                        tool_name = getattr(raw_item, "name", "")
                        tool_input_raw = getattr(raw_item, "arguments", "{}")
                        tool_input = json.loads(tool_input_raw) if isinstance(tool_input_raw, str) else tool_input_raw
                        tool_output = getattr(raw_item, "output", None)
                        tool_call_id = getattr(raw_item, "id", uuid.uuid4().hex[:8])

                        # Parse JSON string arguments into dict for ToolCall

                        tool_calls_for_message.append(
                            {
                                "id": tool_call_id,
                                "type": "function",  # TODO: check if other types available via raw_item
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

                        if tool_name == "ask_human":  # TODO: what if the tool_name is other than ask_human?
                            try:
                                human_input = HumanToolInput(**tool_input)
                            except Exception:
                                human_input = HumanToolInput(question=tool_input.get("question", "Input needed"))

                            # Yield HUMAN_INPUT_REQUIRED with full state for resumption
                            messages.append(
                                {
                                    "role": "assistant",
                                    "content": accumulated or None,
                                    "tool_calls": tool_calls_for_message,
                                }
                            )
                            run_context.messages = list(messages)
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
                            # End generator gracefully, replicating an interruption to HumanToolInput
                            return

                        if tool_output:
                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call_id,
                                    "content": tool_output,
                                }
                            )
                            yield ToolResultEvent(
                                source=class_name,
                                message=f"Tool result: {tool_name}",
                                data=ToolResultEventData(
                                    result=ToolResult(
                                        tool_call_id=tool_call_id,
                                        tool_name=tool_name,
                                        content=tool_output,
                                    )
                                ),
                                run_context=run_context,
                            )
                            # yield {
                            #     "type": StreamEventType.TOOL_RESULT,
                            #     "tool_name": tool_name,
                            #     "tool_output": tool_output,
                            # }

                elif event.name == "message_output_created":
                    if token_buffer:
                        yield StreamingTokenEvent(
                            source=class_name,
                            message=f"Streaming {class_name}",
                            data=StreamingEventData(token=token_buffer),
                            run_context=run_context,
                        )
                        # yield {"type": StreamEventType.STREAMING, "token": token_buffer}
                        token_buffer = ""

        final_output = stream.final_output_as(self.output_schema, raise_if_incorrect_type=False)
        if final_output:
            messages.append(
                {
                    "role": "assistant",
                    "content": accumulated or None,
                    "tool_calls": tool_calls_for_message,
                }
            )
            yield CompletedEvent(
                source=class_name,
                message=f"Completed {class_name}",
                data=CompletedEventData[self.output_schema](output=final_output),
                run_context=run_context,
            )
            # yield {"type": StreamEventType.COMPLETED, "output": final_output}

        # TODO: Check how to add reflection_prompt to the Runner after the output is generated.

    async def _astream(
        self,
        params: InSchema,
        run_context: dict[str, Any] | None = None,
        token_batch_size: int = 10,
        **kwargs: Any,
    ) -> AsyncIterator[StreamEvent]:
        """Stream execution with akd StreamEvent format."""

        class_name = self.__class__.__name__
        run_context = (run_context or RunContext()).model_copy()
        if "run_id" not in run_context:
            run_context.run_id = uuid.uuid4().hex[:8]

        yield StartingEvent(
            source=class_name,
            message=f"Starting {class_name}",
            data=StartingEventData[self.input_schema](params=params),
            run_context=run_context,
        )

        try:
            async with self.memory.asession(
                stateless=self.stateless,
                run_context=run_context,
                enable_trimming=self.enable_trimming,
                model_name=self.model_name,
                max_tokens=self.max_tokens,
                trim_ratio=self.trim_ratio,
            ) as messages:
                # Add system message if empty
                if not messages:
                    messages.append(self._default_system_message())

                # because human response run context messages handled by _stream_llm_response
                if params and not (run_context and run_context.human_response):
                    messages.append(
                        {
                            "role": "user",
                            "content": params.model_dump_json(exclude={"type"}),
                        },
                    )

                yield RunningEvent(
                    source=class_name,
                    message=f"Running {class_name}",
                    run_context=run_context,
                )

                final_output = None
                # interact with the LLM and yield events
                async for event in self._stream_llm_response(
                    messages=messages, run_context=run_context, token_batch_size=token_batch_size
                ):
                    if isinstance(event, CompletedEvent):
                        final_output = event.data.output
                    yield event
                    if isinstance(event, HumanInputRequiredEvent):
                        # ask the human for input and interrupt the stream
                        return

                if final_output is None:
                    raise UnexpectedModelBehavior("No output received from LLM")

                messages.append({"role": "assistant", "content": final_output.model_dump_json(exclude={"type"})})

        except Exception as e:
            yield FailedEvent(
                source=class_name,
                message=f"Failed: {e!s}",
                data=FailedEventData(error=str(e), error_type=type(e).__name__),
                run_context=run_context,
            )
            raise

    # TODO: check if this is need at all
    async def astream(
        self,
        params: Any,
        run_context: RunContext | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamEvent]:
        """
        Overriding the BaseAgent astream to include possible return formats from OpenAI SDK
        """
        # Input validation (before any events are yielded)
        params = self._validate_input(params)

        # Stream from internal implementation
        async for event in self._astream(params, run_context, **kwargs):
            if event.event_type == StreamEventType.COMPLETED:
                # Validate output before yielding COMPLETED
                event_output = event.output
                response_model = self.output_schema
                output: response_model | None = None

                # possible return formats from OpenAI SDK result
                if isinstance(event_output, response_model):
                    output = event_output
                elif isinstance(event_output, str):
                    output = response_model.model_validate_json(event_output)
                else:
                    output = response_model.model_validate(event_output)

                if output is not None:
                    output = self._validate_output(output)
                    yield CompletedEvent(
                        source=event.source,
                        message=event.message,
                        data=CompletedEventData(output=output),
                        run_context=event.run_context,
                    )
                    continue
            yield event
