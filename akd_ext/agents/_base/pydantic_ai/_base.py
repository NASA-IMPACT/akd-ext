"""``PydanticAIBaseAgent`` — Pydantic AI-backed agent conforming to the AKD contract.

Subclasses ``pydantic_ai.Agent`` directly and also explicitly
inherits akd-core's ``AKDExecutable`` Protocol
so ``isinstance(agent, AKDExecutable)`` works at runtime.

Consumers use the same AKD pattern they're used to:

.. code-block:: python

    class MyAgent(PydanticAIBaseAgent[MyIn, MyOut]):
        input_schema = MyIn
        output_schema = MyOut | TextOutput
        config_schema = MyConfig

    agent = MyAgent(MyConfig(model_name="openai:gpt-5.2"))
    result = await agent.arun(MyIn(query="..."))

Config auto-exposure is handled by ``ConfigBindingMixin`` — ``agent.model_name``,
``agent.description``, etc. route to ``self.config.*`` without per-field
property definitions.

The single opt-out is ``system_prompt`` (re-bound to
pydantic_ai's decorator method so it isn't shadowed by an auto-property).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from pydantic import ConfigDict, Field, model_validator
from pydantic_ai import Agent as PAIAgent
from pydantic_ai import AgentRunResultEvent, ModelRetry
from pydantic_ai.capabilities import AbstractCapability, Thinking
from pydantic_ai.capabilities.hooks import Hooks

from akd._base import (
    CompletedEvent,
    CompletedEventData,
    ConfigBindingMixin,
    InputSchema,
    OutputSchema,
    StreamEvent,
    TextOutput,
)
from akd._base.protocols import AKDExecutable, RunContextProtocol
from akd._base.structures import RunContext as AKDRunContext
from akd._base.structures import RunUsage as AKDRunUsage
from akd.agents._base import BaseAgentConfig
from akd.tools._base import BaseTool

from ._context_adapter import (
    _message_history_from_run_context,
    _pai_messages_to_akd_dicts,
    _pai_usage_to_akd_usage,
    _usage_from_run_context,
)
from ._utils import akd_to_pai_tool, pai_event_to_akd_event

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


class PydanticAIBaseAgentConfig(BaseAgentConfig):
    """AKD-style config that is also a superset of ``pydantic_ai.Agent`` kwargs.

    Inherits the full ``BaseAgentConfig`` surface (``model_name``, ``system_prompt``,
    ``tools``, ``reasoning_effort``, etc.) and adds pydantic_ai-specific fields like capabilities.
    ``extra="allow"`` forwards any additional future pydantic_ai kwargs via
    ``model_extra`` without requiring this class to be updated.
    """

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)

    capabilities: list[Any] = Field(
        default_factory=list,
        description=(
            "Pydantic AI capabilities (Thinking, WebSearch, MCP, Hooks, custom). "
            "Merged with any capabilities auto-derived from AKD scalar fields."
        ),
    )

    # -- Silence AKD-core's litellm-based config validators --------------
    # The following validator help for lookups that expect
    # litellm's bare model names (e.g. ``gpt-5.2``), not the
    # ``provider:model`` format pydantic_ai requires (e.g. ``openai:gpt-5.2``),
    # so they emit misleading ERROR / WARNING logs for every construction.
    # pydantic_ai handles model resolution itself, so we override both to no-ops.

    @model_validator(mode="after")
    def validate_max_tokens_against_model(self):
        return self

    @model_validator(mode="after")
    def validate_reasoning_params(self):
        return self

    @model_validator(mode="after")
    def _wire_thinking_from_reasoning_effort(self):
        """Auto-append a ``Thinking`` capability when ``reasoning_effort`` is set.

        Skips if the user already supplied a ``Thinking`` capability —
        their explicit value wins over the scalar default.
        """
        if self.reasoning_effort and not any(isinstance(c, Thinking) for c in self.capabilities):
            self.capabilities.append(Thinking(effort=self.reasoning_effort))
        return self


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class PydanticAIBaseAgent[InSchema: InputSchema, OutSchema: OutputSchema](
    ConfigBindingMixin,
    PAIAgent,
    AKDExecutable,
):
    """Pydantic AI-backed agent conforming to the AKD ``AKDExecutable`` protocol.

    Subclass this class to build new agents. Subclasses override:

    - ``input_schema`` / ``output_schema`` / ``config_schema`` — class attrs
    - ``check_output`` — semantic output validation (optional)

    .. Note (warning)::

        As suggested by pydanticAI Agents we also follow Single-run-per-instance.
        Every stream event this agent emits carries
        pydantic_ai's live ``RunContext`` (captured via a ``Hooks`` capability
        and stored on ``self._live_pai_ctx``). Running two concurrent
        ``arun`` / ``astream`` calls on the *same* agent instance will cause
        the captured context to race between runs and misattribute
        ``event.run_context`` on emitted events.

        For batch or multi-tenant workloads, construct a fresh agent per run, or switch to the
        queue-based capture mechanism tracked in follow-up item
        "Concurrency-safe run_context capture".

        This is because of current (simple) _build_run_context_capture implementation.
    """

    # Subclasses override these three class attributes.
    input_schema: type[InSchema] = InputSchema
    output_schema: type[OutSchema] = OutputSchema
    config_schema: type[PydanticAIBaseAgentConfig] = PydanticAIBaseAgentConfig

    # ── Construction ──────────────────────────────────────────────────────

    def __init__(self, config: PydanticAIBaseAgentConfig | None = None) -> None:
        self.config = config or self.config_schema()

        # Forward-compat: any unknown fields the caller put on the config
        # (via ``extra="allow"``) pass straight through to pydantic_ai.
        extra_kwargs = dict(self.config.model_extra or {})

        # Latest pydantic_ai ``RunContext`` observed by our hooks. ``astream``
        # attaches this (wrapped in an AKD ``RunContext``) to every emitted
        # event so downstream consumers can drive multi-turn conversations.
        # See the class docstring for the concurrency caveat.
        self._live_pai_ctx: Any = None
        ctx_capture = self._build_run_context_capture()

        super().__init__(
            model=self.config.model_name,
            system_prompt=self.config.system_prompt,
            name=self.config.name,
            description=self.config.description,
            retries=self.config.num_retries,
            output_type=self.output_schema,
            tools=self._adapt_tools(self.config.tools),
            capabilities=[
                ctx_capture,
                *self._build_capabilities_from_scalars(),
                *self.config.capabilities,
            ],
            **extra_kwargs,
        )

        self._register_akd_output_validator()

    def _build_run_context_capture(self) -> Hooks:
        """Install a ``Hooks`` capability that captures pydantic_ai's live
        ``RunContext`` onto ``self._live_pai_ctx`` whenever the agent reaches a
        model request or a tool execution.

        The first hook fires *before* any stream event escapes the run, so by
        the time ``astream`` yields its first translated event we already
        have a populated context. Both hooks observe-and-return so they don't
        alter pydantic_ai's own request/argument flow.
        """
        hooks = Hooks()

        @hooks.on.before_model_request
        async def _grab_on_model_request(ctx, request_context):
            self._live_pai_ctx = ctx
            return request_context

        @hooks.on.before_tool_execute
        async def _grab_on_tool_execute(ctx, *, call, tool_def, args):
            self._live_pai_ctx = ctx
            return args

        return hooks

    # ── AKD contract: arun / astream ──────────────────────────────────────

    async def arun(
        self,
        params: InSchema,
        run_context: RunContextProtocol | None = None,
        **kwargs: Any,
    ) -> OutSchema:
        """AKD entry point. Bridges ``InputSchema`` → ``pydantic_ai.Agent.run`` → ``OutputSchema``.

        Any ``pydantic_ai.Agent.run`` kwarg (``deps``, ``message_history``,
        ``usage``, ``model_settings``, etc.) can be passed directly. For
        ``deps`` / ``message_history`` / ``usage``, ``run_context`` is used
        as a fallback when the caller doesn't pass an explicit value.
        ``deps`` is read via ``getattr(run_context, "deps", None)`` so both
        ``AKDRunContext`` (extras-stored) and ``pydantic_ai.RunContext``
        (typed field) work.
        """
        prompt = params.model_dump_json(indent=2)
        # backfill from run_context
        kwargs.setdefault(
            "deps",
            getattr(run_context, "deps", None) if run_context is not None else None,
        )
        kwargs.setdefault("message_history", _message_history_from_run_context(run_context))
        kwargs.setdefault("usage", _usage_from_run_context(run_context))
        result = await self.run(prompt, **kwargs)
        return result.output

    async def astream(
        self,
        params: InSchema,
        run_context: RunContextProtocol | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamEvent]:
        """AKD stream entry point. Translates pydantic_ai events → AKD ``StreamEvent``.

        See ``arun`` for the kwargs/run_context interplay — same rules apply
        to every ``pydantic_ai.Agent.run_stream_events`` kwarg.
        """
        # token_batch_size was a no-op on the OpenAI SDK runner; strip for back-compat.
        kwargs.pop("token_batch_size", None)

        prompt = params.model_dump_json(indent=2)
        # backfill from run_context
        kwargs.setdefault(
            "deps",
            getattr(run_context, "deps", None) if run_context is not None else None,
        )
        kwargs.setdefault("message_history", _message_history_from_run_context(run_context))
        kwargs.setdefault("usage", _usage_from_run_context(run_context))
        async for pai_event in self.run_stream_events(prompt, **kwargs):
            # Terminal result event → emit AKD CompletedEvent with the output.
            if isinstance(pai_event, AgentRunResultEvent):
                if pai_event.result.output is not None:
                    yield CompletedEvent(
                        data=CompletedEventData(output=pai_event.result.output),
                        run_context=self._wrap_pai_ctx,
                    )
                continue
            akd_event = pai_event_to_akd_event(
                pai_event,
                run_context=self._wrap_pai_ctx,
            )
            if akd_event is not None:
                yield akd_event

    # ── RunContext wrapping ───────────────────────────────────────────────

    @property
    def _wrap_pai_ctx(self) -> AKDRunContext:
        """Wrap ``self._live_pai_ctx`` in an AKD ``RunContext``.

        Populates all three AKD typed fields so consumers who only read
        ``run_context.messages`` / ``.usage`` / ``.run_id`` see useful values:

        - ``messages`` — best-effort OpenAI-style ``list[dict]`` produced from
          the pai ``ModelMessage`` list via
          :func:`_pai_messages_to_akd_dicts`. Lossy for multi-part responses
          (text + thinking + tool calls collapse into one assistant dict);
          the lossless path lives on the ``pai_run_context`` extra below.
        - ``usage`` — AKD ``RunUsage`` with the three structural fields mapped
          exactly and pai overflow (cache / audio / tool_calls tokens)
          preserved in ``details`` via :func:`_pai_usage_to_akd_usage`.
        - ``run_id`` — verbatim from the pai ctx.
        - ``pai_run_context`` extra — the live pai ``RunContext`` itself.
          The input-side helpers (``_message_history_from_run_context`` /
          ``_usage_from_run_context``) consult only this extra when the
          caller feeds a prior ``event.run_context`` back in for
          continuation, so round-trip stays lossless.
        """
        pai_ctx = self._live_pai_ctx
        if pai_ctx is None:
            return AKDRunContext()
        pai_messages = getattr(pai_ctx, "messages", None)
        pai_usage = getattr(pai_ctx, "usage", None)
        return AKDRunContext(
            messages=_pai_messages_to_akd_dicts(pai_messages) if pai_messages else None,
            usage=_pai_usage_to_akd_usage(pai_usage) if pai_usage is not None else AKDRunUsage(),
            run_id=getattr(pai_ctx, "run_id", None),
            pai_run_context=pai_ctx,
        )

    @property
    def last_run_context(self) -> AKDRunContext | None:
        """AKD ``RunContext`` reflecting the latest captured pai state.

        Returns ``None`` before any run has happened on this instance.

        ``arun`` returns only ``OutputSchema`` per the AKD contract, so this
        property is the canonical way for ``arun`` callers to obtain a
        continuation-ready context:

        .. code-block:: python

            output_1 = await agent.arun(InputSchema(query="first turn"))
            ctx = agent.last_run_context               # populated AKD ctx
            output_2 = await agent.arun(               # multi-turn
                InputSchema(query="follow-up"), run_context=ctx,
            )

        Each access re-wraps the current ``self._live_pai_ctx`` (pai mutates
        its own state in place during a run, so the property always reflects
        the latest hook firing). Never silently consulted as a fallback when
        the caller passes ``run_context=None`` — ``None`` means fresh
        conversation, explicit opt-in required for continuation.
        """
        if self._live_pai_ctx is None:
            return None
        return self._wrap_pai_ctx

    # ── Run-context helpers ───────────────────────────────────────────────

    # ── scalar-driven capability construction ────────────────────

    def _build_capabilities_from_scalars(self) -> list[AbstractCapability]:
        """Derive capabilities from (scalar) AKD config fields.

        Subclasses override to append their own scalar→capability mappings;
        call ``super()._build_capabilities_from_scalars()`` first to inherit
        future defaults.

        TLDR; this is to map configs to a capability in pydanticAI
        """
        return []

    # ── Tool adaptation ──────────────────────────────────────────────────

    def _adapt_tools(self, tools: list) -> list:
        """Convert AKD ``BaseTool`` instances to pydantic_ai ``Tool`` objects.

        Native pydantic_ai tools (``pydantic_ai.Tool`` instances, decorated
        functions, toolsets, etc.) pass through unchanged. Anything structurally
        conforming to ``AKDTool`` gets wrapped via ``akd_to_pai_tool``.
        """
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
    "PydanticAIBaseAgent",
    "PydanticAIBaseAgentConfig",
]
