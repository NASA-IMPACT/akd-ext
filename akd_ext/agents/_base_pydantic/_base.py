"""``PydanticAIBaseAgent`` — Pydantic AI-backed agent conforming to the AKD contract.

Subclasses ``pydantic_ai.Agent`` directly (Path B) and also explicitly
inherits the ``AKDAgent`` Protocol so ``isinstance(agent, AKDAgent)`` works
at runtime. When akd-core ships its Protocol hierarchy and MRO fix, the
swap to Path A (multi-inheriting ``BaseAgent`` for shared machinery) is a
small diff; see ``docs/pydantic_ai_base_agent_implementation_plan.md``.

Consumers use the same AKD pattern they're used to:

.. code-block:: python

    class MyAgent(PydanticAIBaseAgent[MyIn, MyOut]):
        input_schema = MyIn
        output_schema = MyOut | TextOutput
        config_schema = MyConfig

    agent = MyAgent(MyConfig(model_name="openai:gpt-5.2", reasoning_effort="high"))
    result = await agent.arun(MyIn(query="..."))

Config auto-exposure is handled by ``AbstractBaseMeta`` — ``agent.model_name``,
``agent.description``, etc. route to ``self.config.*`` without per-field
property definitions. The single opt-out is ``system_prompt`` (re-bound to
pydantic_ai's decorator method so it isn't shadowed by an auto-property).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, _ProtocolMeta

from pydantic import ConfigDict, Field, model_validator
from pydantic_ai import Agent as PAIAgent
from pydantic_ai import AgentRunResultEvent, ModelRetry
from pydantic_ai.capabilities import AbstractCapability

from akd._base import (
    CompletedEvent,
    CompletedEventData,
    InputSchema,
    OutputSchema,
    StreamEvent,
    TextOutput,
)
from akd._base._base import AbstractBaseMeta
from akd.agents._base import BaseAgentConfig

from ._capabilities import ReflectionCapability, ToolCallLimits, make_ratio_trimmer
from ._context_adapter import _message_history_from_run_context, _usage_from_run_context
from ._event_translator import pai_event_to_akd_event
from ._protocols import AKDAgent, RunContextProtocol
from ._tool_adapter import akd_to_pai_tool

# ---------------------------------------------------------------------------
# Joint metaclass
# ---------------------------------------------------------------------------
# Explicit Protocol inheritance (AKDAgent) drags in ``_ProtocolMeta``;
# AKD's config auto-exposure is driven by ``AbstractBaseMeta``. Both subclass
# ``ABCMeta`` but neither subclasses the other, so combining them on a single
# class raises ``TypeError: metaclass conflict``. The small joint subclass
# below resolves the MRO: a PydanticAIBaseAgent subclass can satisfy both.


class PydanticAIAgentMeta(_ProtocolMeta, AbstractBaseMeta):
    """Joint metaclass: Protocol introspection + AKD config auto-exposure.

    AKD's ``AbstractBaseMeta`` auto-creates a property per config field on
    every subclass, which would shadow attributes like pydantic_ai.Agent's
    ``system_prompt`` decorator method on every inheritor. The ``SKIP_AUTO_EXPOSE``
    set names fields that must never get an auto-property — after the base
    metaclass runs, we restore the inherited attribute from the MRO.
    """

    SKIP_AUTO_EXPOSE: frozenset[str] = frozenset({"system_prompt"})

    def __new__(mcs, name, bases, dct):
        cls = super().__new__(mcs, name, bases, dct)
        # Undo auto-exposure for skipped fields: replace any property the
        # base metaclass installed with the inherited attribute from an MRO base.
        for field_name in mcs.SKIP_AUTO_EXPOSE:
            current = cls.__dict__.get(field_name)
            if isinstance(current, property):
                for base in cls.__mro__[1:]:
                    if field_name in vars(base):
                        setattr(cls, field_name, vars(base)[field_name])
                        break
        return cls


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


class PydanticAIBaseAgentConfig(BaseAgentConfig):
    """AKD-style config that is also a superset of ``pydantic_ai.Agent`` kwargs.

    Inherits the full ``BaseAgentConfig`` surface (``model_name``, ``system_prompt``,
    ``tools``, ``reasoning_effort``, etc.) and adds pydantic_ai-specific fields.
    ``extra="allow"`` forwards any additional future pydantic_ai kwargs via
    ``model_extra`` without requiring this class to be updated.
    """

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)

    capabilities: list[Any] = Field(
        default_factory=list,
        description=(
            "Pydantic AI capabilities (Thinking, WebSearch, Hooks, custom). "
            "Merged with any capabilities auto-derived from AKD scalar fields."
        ),
    )
    history_processors: list[Any] = Field(
        default_factory=list,
        description="Pydantic AI history processor callables; merged with config-derived processors.",
    )

    # -- Silence AKD-core's litellm-based config validators --------------
    # BaseAgentConfig defines ``validate_max_tokens_against_model`` and
    # ``validate_reasoning_params`` as @model_validator(mode="after") hooks
    # that call ``litellm.get_model_info(self.model_name)`` and
    # ``litellm.supports_reasoning(model=self.model_name)``. Those lookups
    # expect litellm's bare model names (e.g. ``gpt-5.2``), not the
    # ``provider:model`` format pydantic_ai requires (e.g. ``openai:gpt-5.2``),
    # so they emit misleading ERROR / WARNING logs for every construction.
    # pydantic_ai handles model resolution itself, so we override both to no-ops.

    @model_validator(mode="after")
    def validate_max_tokens_against_model(self):
        return self

    @model_validator(mode="after")
    def validate_reasoning_params(self):
        return self


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class PydanticAIBaseAgent[InSchema: InputSchema, OutSchema: OutputSchema](
    PAIAgent,
    AKDAgent,
    metaclass=PydanticAIAgentMeta,
):
    """Pydantic AI-backed agent conforming to the AKD ``AKDAgent`` protocol.

    Subclass this class to build new agents. Subclasses override:

    - ``input_schema`` / ``output_schema`` / ``config_schema`` — class attrs
    - ``check_output`` — semantic output validation (optional)
    - ``_build_capabilities_from_scalars`` — additional scalar→capability mappings
    - ``_build_history_processors_from_scalars`` — additional history processors
    - ``_to_prompt`` — custom prompt rendering from ``InputSchema``
    - ``_adapt_tools`` — custom tool adapter logic (rarely needed)
    """

    # Subclasses override these three class attributes.
    input_schema: type[InSchema] = InputSchema  # type: ignore[assignment]
    output_schema: type[OutSchema] = OutputSchema  # type: ignore[assignment]
    config_schema: type[PydanticAIBaseAgentConfig] = PydanticAIBaseAgentConfig

    # Opt out of metaclass auto-exposure for ``system_prompt``: pydantic_ai's
    # ``system_prompt`` is a decorator method used to register dynamic system
    # prompts, and we must not shadow it with a config-routing property.
    # Re-binding here puts ``system_prompt`` in the class dict, which
    # ``AbstractBaseMeta`` treats as "already defined, skip auto-exposure".
    system_prompt = PAIAgent.system_prompt

    # ── Construction ──────────────────────────────────────────────────────

    def __init__(self, config: PydanticAIBaseAgentConfig | None = None) -> None:
        self.config = config or self.config_schema()

        # Forward-compat: any unknown fields the caller put on the config
        # (via ``extra="allow"``) pass straight through to pydantic_ai.
        extra_kwargs = dict(self.config.model_extra or {})

        super().__init__(
            model=self.config.model_name,
            system_prompt=self.config.system_prompt,
            name=self.config.name,
            description=self.config.description,
            retries=self.config.num_retries,
            output_type=self.output_schema,
            tools=self._adapt_tools(self.config.tools),
            capabilities=[
                *self._build_capabilities_from_scalars(),
                *self.config.capabilities,
            ],
            history_processors=[
                *self._build_history_processors_from_scalars(),
                *self.config.history_processors,
            ],
            **extra_kwargs,
        )

        self._register_akd_output_validator()

    # ── AKD contract: arun / astream ──────────────────────────────────────

    async def arun(
        self,
        params: InSchema,
        run_context: RunContextProtocol | None = None,
        **kwargs: Any,
    ) -> OutSchema:
        """AKD entry point. Bridges ``InputSchema`` → ``pydantic_ai.Agent.run`` → ``OutputSchema``."""
        prompt = self._to_prompt(params)
        result = await self.run(
            prompt,
            deps=self._deps_from_run_context(run_context),
            message_history=_message_history_from_run_context(run_context),
            usage=_usage_from_run_context(run_context),
            **kwargs,
        )
        return result.output

    async def astream(
        self,
        params: InSchema,
        run_context: RunContextProtocol | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamEvent]:
        """AKD stream entry point. Translates pydantic_ai events → AKD ``StreamEvent``s.

        Uses ``pydantic_ai.Agent.run_stream_events`` rather than ``self.iter``
        because it is a plain async iterator with no ``async with`` at the
        call site. Pydantic_ai handles the anyio-backed task decoupling
        internally, so wrapping it in this async generator is safe even when
        the consumer cancels mid-stream (e.g. marimo cancelling an in-flight
        stream when the user sends a follow-up). Using ``iter()`` here is
        unsafe in that setting because its context manager must exit in the
        same task that entered it.

        ``run_stream_events`` emits an :class:`AgentRunResultEvent` as its
        final event, carrying the run's ``output`` — we unwrap that into
        AKD's :class:`CompletedEvent` so callers that rely on the AKD
        contract (like ``agent_chat.py``) see the final answer.
        """
        # Drop legacy AKD kwargs that pydantic_ai's run_stream_events
        # doesn't accept. ``token_batch_size`` was a no-op on the OpenAI SDK
        # runner; nothing in pydantic_ai batches events by count. Call sites
        # should stop passing it, but we strip defensively for backward compat.
        kwargs.pop("token_batch_size", None)

        prompt = self._to_prompt(params)
        async for pai_event in self.run_stream_events(
            prompt,
            deps=self._deps_from_run_context(run_context),
            message_history=_message_history_from_run_context(run_context),
            usage=_usage_from_run_context(run_context),
            **kwargs,
        ):
            # Terminal result event → emit AKD CompletedEvent with the output.
            if isinstance(pai_event, AgentRunResultEvent):
                if pai_event.result.output is not None:
                    yield CompletedEvent(
                        data=CompletedEventData(output=pai_event.result.output),
                    )
                continue
            akd_event = pai_event_to_akd_event(pai_event)
            if akd_event is not None:
                yield akd_event

    # ── Prompt rendering ──────────────────────────────────────────────────

    def _to_prompt(self, params: InSchema) -> str:
        """Convert an ``InputSchema`` instance to the prompt string pydantic_ai expects.

        Default: pretty-printed JSON dump. Subclasses override for custom
        templates or more readable renderings.
        """
        return params.model_dump_json(indent=2)

    # ── Run-context helpers ───────────────────────────────────────────────

    def _deps_from_run_context(self, run_context: RunContextProtocol | None) -> Any:
        """Extract pydantic_ai ``deps`` from the run context, if any.

        AKD run contexts don't carry deps. If a caller passes a
        ``pydantic_ai.RunContext`` directly, forward its ``deps`` field so
        tool authors can use pydantic_ai-native dependency injection.
        Subclasses override to inject their own deps construction.
        """
        from pydantic_ai import RunContext as PAIRunContext

        if isinstance(run_context, PAIRunContext):
            return run_context.deps
        return None

    # ── Zone 1: scalar-driven capability / history-processor construction ─

    def _build_capabilities_from_scalars(self) -> list[AbstractCapability]:
        """Derive capabilities from AKD scalar config fields shared by all agents.

        Subclasses override to append their own scalar→capability mappings; call
        ``super()._build_capabilities_from_scalars()`` first to inherit the defaults.
        """
        caps: list[AbstractCapability] = []

        if self.config.reasoning_effort:
            from pydantic_ai.capabilities import Thinking

            # pydantic_ai's Thinking currently only accepts `effort`.
            # AKD's `reasoning_summary` is dormant for now; if pydantic_ai
            # adds a summary knob later, expose it here.
            caps.append(Thinking(effort=self.config.reasoning_effort))

        if self.config.max_tool_iterations or self.config.max_tool_calls:
            caps.append(
                ToolCallLimits(
                    max_iterations=self.config.max_tool_iterations,
                    max_calls=self.config.max_tool_calls,
                ),
            )

        if self.config.reflection_prompt:
            caps.append(ReflectionCapability(prompt=self.config.reflection_prompt))

        return caps

    def _build_history_processors_from_scalars(self) -> list:
        """Derive history processors from AKD scalar config fields.

        Subclasses override to append their own; call ``super()`` first.
        """
        procs: list = []
        if self.config.enable_trimming:
            procs.append(make_ratio_trimmer(1 - self.config.trim_ratio))
            # ``trim_ratio`` in AKD is the *target retention* ratio (0.75 = keep 75%).
            # The trimmer we pass expects the *drop* fraction, hence 1 - ratio.
        return procs

    # ── Tool adaptation ──────────────────────────────────────────────────

    def _adapt_tools(self, tools: list) -> list:
        """Convert AKD ``BaseTool`` instances to pydantic_ai ``Tool`` objects.

        Native pydantic_ai tools (``pydantic_ai.Tool`` instances, decorated
        functions, toolsets, etc.) pass through unchanged. Anything structurally
        conforming to ``AKDTool`` gets wrapped via ``akd_to_pai_tool``.
        """
        from akd.tools._base import BaseTool

        adapted = []
        for tool in tools:
            if isinstance(tool, BaseTool):
                adapted.append(akd_to_pai_tool(tool))
            else:
                adapted.append(tool)
        return adapted

    # ── check_output bridge ──────────────────────────────────────────────

    def _register_akd_output_validator(self) -> None:
        """Wire ``self.check_output`` up as a pydantic_ai output validator.

        Runs once at ``__init__`` time. The closure captures ``self`` and
        late-binds ``self.check_output``, so subclass overrides are picked
        up polymorphically.
        """

        @self.output_validator
        def _akd_check(output):
            msg = self.check_output(output)
            if msg is not None:
                raise ModelRetry(msg)
            return output

    def check_output(self, output) -> str | None:
        """Semantic output validation beyond pydantic_ai's schema enforcement.

        Default:

        - ``TextOutput`` instances pass through untouched (agent is asking a
          clarifying question; the outer caller handles the multi-turn loop).
        - Structured outputs are rejected if they define ``is_empty()`` and
          it returns ``True`` (an empty answer is never a valid terminal
          output). The ``hasattr`` guard keeps this backward-compatible with
          schemas that don't declare ``is_empty``.

        Return ``None`` to accept; return a string to ask the model for a
        retry with that message as the prompt.
        """
        if isinstance(output, TextOutput):
            return None
        is_empty = getattr(output, "is_empty", None)
        if callable(is_empty) and is_empty():
            return (
                "Output is empty. Provide a complete structured answer with meaningful content in all required fields."
            )
        return None


__all__ = [
    "PydanticAIAgentMeta",
    "PydanticAIBaseAgent",
    "PydanticAIBaseAgentConfig",
]
