from __future__ import annotations

from typing import Any

from agents import Agent, ModelSettings, RunConfig, Runner, trace
from openai.types.shared.reasoning import Reasoning
from pydantic import Field

from akd._base import InputSchema, OutputSchema
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


class OpenAIBaseAgent[InSchema: InputSchema, OutSchema: OutputSchema](BaseAgent):
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
