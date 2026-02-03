from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Any

from agents import Agent, ModelSettings, RunConfig, Runner, trace
from agents.stream_events import (
    RawResponsesStreamEvent,
    RunItemStreamEvent,
)

from akd._base.streaming import StreamEvent, StreamEventType, StreamingMixin
from openai.types.shared.reasoning import Reasoning
from pydantic import Field

from akd._base import (
    Memory,
    RunContext,
    InputSchema,
    OutputSchema,
    StartingEvent,
    StartingEventData,
    RunningEvent,
    RunningEventData,
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
)
from akd.agents._base import BaseAgent, BaseAgentConfig


class OpenAIBaseAgentConfig(BaseAgentConfig):
    """Configuration for OpenAI Agents SDK based AKD Agents.

    Extends BaseAgentConfig with OpenAI-specific settings for agents
    built with OpenAI's platform agent builder.

    Inherits `reasoning_effort` and `reasoning_summary` from BaseAgentConfig.
    Defaults to `stateless=False` (stateful) for multi-turn conversations.
    """

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
        debug: bool = False,
    ) -> None:
        super().__init__(config=config, debug=debug)
        self._memory: list[dict[str, Any]] = []
        self._agent = self._create_agent()

    @property
    def memory(self) -> list[dict[str, Any]]:
        """Conversation history for multi-turn interactions."""
        return self._memory

    def reset_memory(self) -> None:
        """Clear conversation history."""
        self._memory.clear()

    def _create_agent(self) -> Agent:
        """Create the OpenAI Agent object.

        Uses tools and model settings from config.
        Override for custom agent creation logic.
        """
        return Agent(
            name=self.__class__.__name__,
            instructions=self.config.system_prompt,
            model=self.config.model_name or "gpt-4o",
            tools=self.config.tools,
            output_type=self.output_schema,
            model_settings=self.config.model_settings,
        )

    async def get_response_async(
        self,
        messages: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> Any:
        """Run the agent and return the RunResult.

        Args:
            messages: Conversation messages. If None, uses internal memory.

        Returns:
            RunResult from the agent execution.
        """
        agent_input = messages if messages is not None else self._memory

        with trace(self.__class__.__name__):
            return await Runner.run(
                self._agent,
                input=agent_input,
                run_config=self.config.run_config,
            )

    async def _arun(self, params: InSchema, **kwargs) -> OutSchema:
        """Run the agent workflow.

        Override for custom orchestration (e.g., multi-agent pipelines).
        """
        if self.config.stateless:
            self.reset_memory()

        # Add user input to memory
        self._memory.append({"role": "user", "content": params.model_dump_json()})

        # Run pipeline via get_response_async
        result = await self.get_response_async(messages=self._memory)

        # Update memory with full conversation
        self._memory = result.to_input_list()

        # Return typed output
        final_output = result.final_output
        if isinstance(final_output, self.output_schema):
            return final_output
        elif hasattr(final_output, "model_dump"):
            return self.output_schema(**final_output.model_dump())
        else:
            return self.output_schema.model_validate_json(str(final_output))

    async def _stream_llm_response(
        self,
        messages: list[dict[str, Any]],
        token_batch_size: int = 10,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream using Runner.run_streamed()."""

        token_buffer = ""

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
                    if len(token_buffer) >= token_batch_size:
                        yield {"type": StreamEventType.STREAMING, "token": token_buffer}
                        token_buffer = ""

                elif event_type == "response.output_text.done":
                    if token_buffer:
                        yield {"type": StreamEventType.STREAMING, "token": token_buffer}
                        token_buffer = ""

                elif "reasoning" in event_type:
                    content = getattr(event.data, "content", "") or getattr(event.data, "delta", "") or ""
                    if content:
                        yield {"type": StreamEventType.THINKING, "content": content}

            elif isinstance(event, RunItemStreamEvent):
                if event.name == "tool_called":
                    raw_item = getattr(event.item, "raw_item", None)
                    if raw_item:
                        tool_name = getattr(raw_item, "name", "")
                        tool_input = getattr(raw_item, "arguments", "{}")
                        tool_output = getattr(raw_item, "output", None)

                        yield {
                            "type": StreamEventType.TOOL_CALLING,
                            "tool_name": tool_name,
                            "tool_input": tool_input,
                        }

                        if tool_output:
                            yield {
                                "type": StreamEventType.TOOL_RESULT,
                                "tool_name": tool_name,
                                "tool_output": tool_output,
                            }

                elif event.name == "message_output_created":
                    if token_buffer:
                        yield {"type": StreamEventType.STREAMING, "token": token_buffer}
                        token_buffer = ""

        final_output = stream.final_output_as(self.output_schema, raise_if_incorrect_type=False)
        if final_output:
            yield {"type": StreamEventType.COMPLETED, "output": final_output}

    async def _astream(
        self,
        params: InSchema,
        context: dict[str, Any] | None = None,
        token_batch_size: int = 10,
        **kwargs: Any,
    ) -> AsyncIterator[StreamEvent]:
        """Stream execution with akd StreamEvent format."""

        class_name = self.__class__.__name__
        response_model = self.output_schema
        run_context = context.copy() if context else {}
        if "run_id" not in run_context:
            run_context["run_id"] = uuid.uuid4().hex[:8]

        yield StartingEvent(
            source=class_name,
            message=f"Starting {class_name}",
            data=StartingEventData[self.input_schema](params=params),
            run_context=run_context,
        )

        try:
            messages = [] if self.config.stateless else self._memory.copy()

            if params:
                messages.append({"role": "user", "content": params.model_dump_json(exclude={"type"})})

            yield RunningEvent(
                source=class_name,
                message=f"Running {class_name}",
                data=RunningEventData(),
                run_context=run_context,
            )

            final_output = None
            async for chunk in self._stream_llm_response(messages, token_batch_size=token_batch_size):
                if chunk["type"] == StreamEventType.STREAMING:
                    yield StreamingTokenEvent(
                        source=class_name,
                        message=f"Streaming {class_name}",
                        data=StreamingEventData(token=chunk["token"]),
                        run_context=run_context,
                    )

                elif chunk["type"] == StreamEventType.THINKING:
                    yield ThinkingEvent(
                        source=class_name,
                        message="Reasoning...",
                        data=ThinkingEventData(
                            thinking_content=chunk["content"]
                        ),  # check if reflection prompt is used and add reflection_content
                        run_context=run_context,
                    )

                elif chunk["type"] == StreamEventType.TOOL_CALLING:
                    yield ToolCallingEvent(
                        source=class_name,
                        message=f"Calling tool: {chunk['tool_name']}",
                        data=ToolCallingEventData(
                            tool_call=ToolCall(
                                tool_call_id=chunk.get("tool_call_id")
                                or uuid.uuid4().hex[:8],  # does chunk have a tool call id??
                                tool_name=chunk["tool_name"],
                                arguments=chunk["tool_input"],
                            )
                        ),
                        run_context=run_context,
                    )

                elif chunk["type"] == StreamEventType.TOOL_RESULT:
                    yield ToolResultEvent(
                        source=class_name,
                        message=f"Tool result: {chunk['tool_name']}",
                        result=ToolResultEventData(
                            tool_result=ToolResult(
                                tool_call_id=chunk.get("tool_call_id") or uuid.uuid4().hex[:8],
                                tool_name=chunk["tool_name"],
                                content=chunk["tool_output"],
                            )
                        ),
                        run_context=run_context,
                    )

                elif chunk["type"] == StreamEventType.COMPLETED:
                    final_output = chunk["output"]

            if final_output is None:
                raise ValueError("No output received from LLM")

            if not self.config.stateless:
                messages.append({"role": "assistant", "content": final_output.model_dump_json(exclude={"type"})})
                self._memory = messages

            output = response_model.model_validate_json(final_output)
            yield CompletedEvent(
                source=class_name,
                message=f"Completed {class_name}",
                data=CompletedEventData[self.output_schema](output=output),
                run_context=run_context,
            )

        except Exception as e:
            yield FailedEvent(
                source=class_name,
                message=f"Failed: {e!s}",
                data=FailedEventData(error=str(e), error_type=type(e).__name__),
                run_context=run_context,
            )
            raise


class FreeFormOutput(OutputSchema):
    """Default output schema for free-form agents."""

    response: str = Field(..., description="Free-form text response from agent")


class FreeFormOpenAIBaseAgent[InSchema: InputSchema](OpenAIBaseAgent[InSchema, FreeFormOutput]):
    """Base for OpenAI agents returning free-form text (no structured output_type).

    Use when the agent should return unstructured text that gets wrapped
    in FreeFormOutput. Does NOT set output_type on the OpenAI SDK Agent.

    Subclasses must define:
    - input_schema: Input schema class

    Subclasses can override:
    - output_schema: Defaults to FreeFormOutput
    - _create_agent(): For custom agent creation
    """

    output_schema = FreeFormOutput

    def __init__(
        self,
        config: OpenAIBaseAgentConfig | None = None,
        memory: Memory | None = None,
        **kwargs,
    ) -> None:
        super().__init__(config=config, **kwargs)
        self.memory = memory or Memory()

    def _create_agent(self) -> Agent:
        """Create agent WITHOUT output_type (free-form text output)."""
        return Agent(
            name=self.__class__.__name__,
            instructions=self.config.system_prompt,
            model=self.config.model_name or "gpt-4o",
            tools=self.config.tools,
            model_settings=self.config.model_settings,
            # NO output_type - returns free-form text
        )

    async def _arun(self, params: InSchema, **kwargs) -> FreeFormOutput:
        """Run agent and wrap string response in FreeFormOutput."""
        if self.config.stateless:
            self.reset_memory()

        self._memory.append({"role": "user", "content": params.model_dump_json()})
        result = await self.get_response_async(messages=self._memory)
        self._memory = result.to_input_list()

        # Wrap string response in output schema
        response_text = str(result.final_output)
        return self.output_schema(response=response_text)

    async def _astream(self, params: InSchema, **kwargs) -> AsyncIterator[StreamEvent]:
        """Stream agent response and yield events."""
        class_name = self.__class__.__name__
        run_context = kwargs.get("run_context")
        if run_context is None:
            run_context = RunContext()

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
                if params:
                    messages.append({"role": "user", "content": params.model_dump_json(exclude={"type"})})

                yield RunningEvent(
                    source=class_name,
                    message=f"Running {class_name}",
                    data=RunningEventData(),
                    run_context=run_context,
                )

                output: FreeFormOutput = await self._arun(params, **kwargs)
                yield CompletedEvent(
                    source=class_name,
                    message=f"Completed {class_name}",
                    data=CompletedEventData[self.output_schema](output=output),
                    run_context=run_context,
                )
        except Exception as e:
            yield FailedEvent(
                source=class_name,
                message=f"Failed: {e!s}",
                data=FailedEventData(error=str(e), error_type=type(e).__name__),
                run_context=run_context,
            )
            raise
