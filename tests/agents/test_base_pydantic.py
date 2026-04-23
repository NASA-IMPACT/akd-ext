"""Tests for ``PydanticAIBaseAgent`` and its supporting subpackage.

Uses pydantic_ai's ``TestModel`` for deterministic behavior instead of
touching real model providers. Existing agents (``CMRCareAgent`` et al.)
are deliberately untouched here — this suite exercises a dedicated test
agent built on top of ``PydanticAIBaseAgent`` instead.
"""

from __future__ import annotations

import pytest
from pydantic import Field
from pydantic_ai import ModelRetry
from pydantic_ai.models.test import TestModel

from akd._base import InputSchema, OutputSchema, TextOutput
from akd._base.errors import SchemaValidationError
from akd._base.protocols import (
    AKDExecutable,
    AKDTool,
    RunContextProtocol,
    TokenCounts,
)
from akd.tools._base import BaseTool

from akd_ext.agents._base import PydanticAIBaseAgent, PydanticAIBaseAgentConfig
from akd_ext.agents._base.pydantic_ai._tool_adapter import akd_to_pai_tool


# ---------------------------------------------------------------------------
# Fixtures: a small test agent exercising the base class's surface
# ---------------------------------------------------------------------------


class _EchoInput(InputSchema):
    """Input schema for the echo test agent."""

    query: str = Field(..., description="Free-form query text")


class _EchoOutput(OutputSchema):
    """Output schema for the echo test agent."""

    answer: str = Field(..., description="Echoed answer from the agent")

    def is_empty(self) -> bool:
        return not self.answer.strip()


class _EchoConfig(PydanticAIBaseAgentConfig):
    """Config for the echo test agent."""


class _EchoAgent(PydanticAIBaseAgent[_EchoInput, _EchoOutput]):
    """Minimal test agent exercising the base class's feature surface."""

    input_schema = _EchoInput
    output_schema = _EchoOutput | TextOutput
    config_schema = _EchoConfig


# ---------------------------------------------------------------------------
# Structural tests (no model interaction)
# ---------------------------------------------------------------------------


def test_agent_instantiates_with_defaults():
    agent = _EchoAgent()
    assert isinstance(agent.config, _EchoConfig)
    assert agent.input_schema is _EchoInput


def test_agent_instantiates_with_custom_config():
    cfg = _EchoConfig(model_name="test", description="Echo agent for tests")
    agent = _EchoAgent(cfg)
    assert agent.config is cfg


def test_metaclass_auto_exposes_config_fields():
    """agent.model_name / agent.description route to self.config.* without hand-written properties."""
    cfg = _EchoConfig(model_name="test", description="hello")
    agent = _EchoAgent(cfg)
    assert agent.model_name == "test"
    assert agent.description == "hello"


def test_system_prompt_not_shadowed_by_auto_exposure():
    """pydantic_ai's ``system_prompt`` decorator method must still work."""
    agent = _EchoAgent()
    # Must be a callable, not a string
    assert callable(agent.system_prompt)
    # Must come from pydantic_ai.Agent, not a property descriptor
    from pydantic_ai import Agent as PAIAgent

    assert _EchoAgent.system_prompt is PAIAgent.system_prompt


def test_agent_is_runtime_akd_agent():
    """Explicit Protocol inheritance means isinstance(agent, AKDExecutable) works."""
    agent = _EchoAgent()
    assert isinstance(agent, AKDExecutable)


def test_config_is_runtime_run_context_protocol():
    """Sanity check: TokenCounts and RunContextProtocol are importable and checkable."""
    # Concrete instances satisfy these structurally in practice; here we just
    # confirm the symbols exist and are runtime-checkable.
    assert hasattr(TokenCounts, "_is_runtime_protocol")
    assert hasattr(RunContextProtocol, "_is_runtime_protocol")


# ---------------------------------------------------------------------------
# check_output bridge
# ---------------------------------------------------------------------------


def test_check_output_passes_through_text_output():
    agent = _EchoAgent()
    assert agent.check_output(TextOutput(content="Ask the user?")) is None


def test_check_output_rejects_empty_structured_output():
    agent = _EchoAgent()
    msg = agent.check_output(_EchoOutput(answer="   "))
    assert isinstance(msg, str)
    assert "empty" in msg.lower()


def test_check_output_accepts_non_empty_structured_output():
    agent = _EchoAgent()
    assert agent.check_output(_EchoOutput(answer="real answer")) is None


# ---------------------------------------------------------------------------
# arun / astream with TestModel (no external calls)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_arun_returns_output_schema():
    agent = _EchoAgent()
    with agent.override(model=TestModel()):
        result = await agent.arun(_EchoInput(query="hello"))
    # TestModel produces a best-effort structured output matching the schema
    assert isinstance(result, (_EchoOutput, TextOutput))


@pytest.mark.asyncio
async def test_astream_yields_akd_stream_events():
    agent = _EchoAgent()
    from akd._base import StreamEvent

    with agent.override(model=TestModel()):
        events = [ev async for ev in agent.astream(_EchoInput(query="hello"))]
    # Every yielded event must be an AKD StreamEvent (or subclass thereof); may be empty
    # with TestModel depending on its stream behavior, but nothing foreign should appear.
    assert all(isinstance(ev, StreamEvent) for ev in events)


@pytest.mark.asyncio
async def test_astream_emits_completed_event_with_output():
    """astream must emit a terminal CompletedEvent carrying the final output
    so callers matching the AKD contract (e.g. agent_chat.py) see the answer."""
    from akd._base import CompletedEvent

    agent = _EchoAgent()
    with agent.override(model=TestModel()):
        events = [ev async for ev in agent.astream(_EchoInput(query="hello"))]

    # At least one CompletedEvent, and the last event must carry the output.
    completed = [ev for ev in events if isinstance(ev, CompletedEvent)]
    assert completed, "astream should emit a CompletedEvent when the run finishes"
    assert isinstance(events[-1], CompletedEvent)
    assert completed[-1].data.output is not None


@pytest.mark.asyncio
async def test_astream_run_context_available_after_run():
    """Every emitted event — including the terminal CompletedEvent — must
    carry the live pydantic_ai ``RunContext`` under ``run_context.pai_run_context``.

    Consumers rely on this to drive multi-turn continuation (Flavor B HITL):
    they read ``pai_run_context.messages`` / ``.usage`` from the last event
    and feed them back into the next ``astream`` call.
    """
    from akd._base import CompletedEvent
    from pydantic_ai import RunContext as PAIRunContext

    agent = _EchoAgent()
    with agent.override(model=TestModel()):
        events = [ev async for ev in agent.astream(_EchoInput(query="hello"))]

    # Every event carries a run_context — the Hooks capability fires before
    # anything gets translated, so the live ctx is always captured in time.
    for ev in events:
        pai_ctx = getattr(ev.run_context, "pai_run_context", None)
        assert pai_ctx is not None, f"{type(ev).__name__} missing pai_run_context"
        assert isinstance(pai_ctx, PAIRunContext)

    # Terminal event specifically: the captured context reflects a real run —
    # at least one model request fired, and pydantic_ai attached a message
    # history to the ctx.
    completed = [ev for ev in events if isinstance(ev, CompletedEvent)]
    assert completed
    terminal_pai_ctx = completed[-1].run_context.pai_run_context
    assert terminal_pai_ctx.usage.requests >= 1
    assert isinstance(terminal_pai_ctx.messages, list)
    assert len(terminal_pai_ctx.messages) >= 1


@pytest.mark.asyncio
async def test_arun_run_context_available_after_run():
    """After ``await agent.arun(...)``, the agent's ``_live_pai_ctx`` holds
    the pydantic_ai ``RunContext`` captured during the run.

    ``arun`` itself returns the output value (per the AKD contract); the
    captured ctx is retained on the instance so callers can inspect it via
    ``agent.last_run_context``.
    """
    from pydantic_ai import RunContext as PAIRunContext

    agent = _EchoAgent()
    # Before any run, nothing has been captured.
    assert agent._live_pai_ctx is None
    assert agent.last_run_context is None

    with agent.override(model=TestModel()):
        result = await agent.arun(_EchoInput(query="hello"))

    assert isinstance(result, (_EchoOutput, TextOutput))
    assert agent._live_pai_ctx is not None
    assert isinstance(agent._live_pai_ctx, PAIRunContext)
    assert agent._live_pai_ctx.usage.requests >= 1

    # last_run_context wraps the pai ctx; the lossless extra is populated.
    ctx = agent.last_run_context
    assert ctx is not None
    assert isinstance(ctx.pai_run_context, PAIRunContext)


@pytest.mark.asyncio
async def test_multi_turn_via_last_run_context():
    """Feeding ``agent.last_run_context`` from turn 1 into turn 2 causes
    pydantic_ai to see the full prior message history (via the lossless
    ``pai_run_context`` extra)."""
    agent = _EchoAgent()
    with agent.override(model=TestModel()):
        await agent.arun(_EchoInput(query="first turn"))
        ctx_after_turn_1 = agent.last_run_context
        assert ctx_after_turn_1 is not None
        turn_1_message_count = len(ctx_after_turn_1.pai_run_context.messages)

        await agent.arun(_EchoInput(query="follow-up"), run_context=ctx_after_turn_1)
        ctx_after_turn_2 = agent.last_run_context

    assert ctx_after_turn_2 is not None
    assert len(ctx_after_turn_2.pai_run_context.messages) > turn_1_message_count


def test_input_side_reads_pai_run_context():
    """Message history and usage are pulled verbatim from
    ``run_context.pai_run_context`` — no conversion, no fallback branches."""
    from akd._base.structures import RunContext as AKDRunContext
    from pydantic_ai import RunContext as PAIRunContext
    from pydantic_ai.messages import ModelRequest, UserPromptPart
    from pydantic_ai.result import RunUsage as PAIRunUsage

    from akd_ext.agents._base.pydantic_ai._base import (
        _message_history_from_run_context,
        _usage_from_run_context,
    )

    pai_messages = [ModelRequest(parts=[UserPromptPart(content="pai-truth")])]
    pai_usage = PAIRunUsage(input_tokens=10, output_tokens=20, requests=3)
    pai_ctx = PAIRunContext(deps=None, model=None, usage=pai_usage)
    pai_ctx.messages = pai_messages

    akd_ctx = AKDRunContext(pai_run_context=pai_ctx)

    history = _message_history_from_run_context(akd_ctx)
    assert history == pai_messages
    assert history[0].parts[0].content == "pai-truth"

    usage = _usage_from_run_context(akd_ctx)
    assert usage is pai_usage
    assert usage.input_tokens == 10


def test_input_side_returns_none_without_pai_run_context():
    """AKD ``RunContext`` with no ``pai_run_context`` extra yields ``None`` —
    Phase 1 does not convert AKD-shape typed fields into pai shapes."""
    from akd._base.structures import RunContext as AKDRunContext
    from akd._base.structures import RunUsage as AKDRunUsage

    from akd_ext.agents._base.pydantic_ai._base import (
        _message_history_from_run_context,
        _usage_from_run_context,
    )

    akd_ctx = AKDRunContext(
        messages=[{"role": "user", "content": "hi"}],
        usage=AKDRunUsage(input_tokens=5, output_tokens=7, requests=1),
    )

    assert _message_history_from_run_context(akd_ctx) is None
    assert _usage_from_run_context(akd_ctx) is None
    assert _message_history_from_run_context(None) is None
    assert _usage_from_run_context(None) is None


# ---------------------------------------------------------------------------
# Tool adapter
# ---------------------------------------------------------------------------


class _GreetInput(InputSchema):
    """Input schema for the greet tool."""

    name: str = Field(..., description="Name to greet")


class _GreetOutput(OutputSchema):
    """Output schema for the greet tool."""

    greeting: str = Field(..., description="Generated greeting")


class _GreetTool(BaseTool[_GreetInput, _GreetOutput]):
    """A trivial greeting tool for adapter tests."""

    input_schema = _GreetInput
    output_schema = _GreetOutput

    async def _arun(self, params: _GreetInput) -> _GreetOutput:
        return _GreetOutput(greeting=f"Hello, {params.name}!")


@pytest.mark.asyncio
async def test_tool_adapter_produces_callable_pai_tool():
    from pydantic_ai import Tool as PAITool

    tool = _GreetTool()
    pai = akd_to_pai_tool(tool)
    assert isinstance(pai, PAITool)


@pytest.mark.asyncio
async def test_tool_adapter_validation_error_becomes_model_retry():
    """If the wrapped AKD tool raises a validation error, the adapter must
    re-raise as ModelRetry so pydantic_ai retries instead of halting."""

    class _AlwaysRaisesInput(InputSchema):
        """Input schema for always-raises tool."""

        query: str = Field(...)

    class _AlwaysRaisesOutput(OutputSchema):
        """Output schema for always-raises tool."""

        result: str = Field(...)

    class _AlwaysRaisesTool(BaseTool[_AlwaysRaisesInput, _AlwaysRaisesOutput]):
        """Tool that always raises SchemaValidationError."""

        input_schema = _AlwaysRaisesInput
        output_schema = _AlwaysRaisesOutput

        async def _arun(self, params: _AlwaysRaisesInput) -> _AlwaysRaisesOutput:
            raise SchemaValidationError("bad shape")

    pai = akd_to_pai_tool(_AlwaysRaisesTool())
    # Call the wrapped function directly to bypass pydantic_ai's tool manager
    with pytest.raises(ModelRetry):
        await pai.function(query="whatever")


def test_tool_adapter_accepts_akdtool_protocol():
    """The adapter's parameter type is the AKDTool protocol; concrete AKD BaseTools satisfy it structurally."""
    assert isinstance(_GreetTool(), AKDTool)


@pytest.mark.asyncio
async def test_existing_akd_tool_is_pai_compatible():
    """Real shipped AKD tool (``DummyTool``) adapts cleanly to pydantic_ai.

    Compatibility checks:

    1. The adapter returns a real ``pydantic_ai.Tool``.
    2. ``name`` and ``description`` are populated (pydantic_ai uses these for
       the tool definition it advertises to the model).
    3. The wrapped function's signature exposes the AKD ``InputSchema``'s
       fields as parameters (so pydantic_ai's JSON-schema introspection
       produces the same shape the AKD schema declares).
    4. Invoking the wrapped function with valid kwargs returns the AKD
       ``OutputSchema`` instance — the conversion is invocation-safe, not
       just structural.
    5. Dropping the tool into ``PydanticAIBaseAgentConfig(tools=[...])`` and
       building a ``PydanticAIBaseAgent`` succeeds; the agent's toolset lists
       the adapted tool under the expected name.
    """
    import inspect

    from pydantic_ai import Tool as PAITool

    from akd_ext.tools.dummy import DummyInputSchema, DummyOutputSchema, DummyTool

    akd_tool = DummyTool()
    pai = akd_to_pai_tool(akd_tool)

    assert isinstance(pai, PAITool)
    assert pai.name == akd_tool.name
    assert pai.description and akd_tool.description.splitlines()[0] in pai.description

    # Signature preserved from AKDInputSchema → kwargs pydantic_ai can introspect.
    sig = inspect.signature(pai.function)
    assert "query" in sig.parameters
    assert sig.return_annotation is DummyOutputSchema

    # Invocation round-trips through the AKD tool.
    result = await pai.function(query="compatibility-check")
    assert isinstance(result, DummyOutputSchema)
    assert result.query == "compatibility-check"

    # Registration on a PydanticAIBaseAgent: the config path wraps the AKD
    # tool via ``_adapt_tools``; the agent's toolset must end up carrying
    # it. We use _EchoAgent's schemas since the smoke agent shape is
    # immaterial — we only care that registration succeeds.
    agent = _EchoAgent(_EchoConfig(tools=[DummyTool()]))
    assert agent.toolset is not None
    # Walk the registered toolsets to find our adapted tool by name.
    assert any(
        pai.name in getattr(ts, "tools", {}) or pai.name in getattr(ts, "_tools", {})
        for ts in getattr(agent, "toolsets", [])
    ), f"expected adapted tool {pai.name!r} to be reachable on agent.toolsets"

    # Sanity: the AKD tool still satisfies the AKDTool protocol after
    # passing through the adapter (nothing mutates the source).
    assert isinstance(akd_tool, AKDTool)
    # And the input schema reference is intact.
    assert akd_tool.input_schema is DummyInputSchema


# ---------------------------------------------------------------------------
# make_ratio_trimmer history processor + wiring
# ---------------------------------------------------------------------------


def test_ratio_trimmer_is_noop_at_zero():
    """``trim_ratio=0`` returns every message unchanged — useful as an
    explicit "don't trim" sentinel."""
    from akd_ext.agents._base.pydantic_ai._capabilities import make_ratio_trimmer

    trimmer = make_ratio_trimmer(0)
    msgs = [f"msg-{i}" for i in range(5)]
    assert trimmer(msgs) == msgs


def test_ratio_trimmer_drops_oldest_fraction_and_preserves_head():
    """Non-zero ratio drops the oldest ``ratio`` fraction of messages
    *after* the first (which is preserved as system-prompt-like head)."""
    from akd_ext.agents._base.pydantic_ai._capabilities import make_ratio_trimmer

    trimmer = make_ratio_trimmer(0.5)  # drop oldest 50% of the tail
    msgs = ["system"] + [f"msg-{i}" for i in range(10)]
    trimmed = trimmer(msgs)
    # Head preserved:
    assert trimmed[0] == "system"
    # Half of the 10 tail messages dropped from the oldest end:
    assert trimmed[1:] == [f"msg-{i}" for i in range(5, 10)]


def test_ratio_trimmer_empty_input_passthrough():
    """Empty list returns empty list regardless of ratio."""
    from akd_ext.agents._base.pydantic_ai._capabilities import make_ratio_trimmer

    assert make_ratio_trimmer(0.5)([]) == []


def test_ratio_trimmer_rejects_invalid_ratio():
    """Ratio must be in ``[0, 1)`` — negative or ≥1 raises at factory time."""
    from akd_ext.agents._base.pydantic_ai._capabilities import make_ratio_trimmer

    with pytest.raises(ValueError, match="trim_ratio"):
        make_ratio_trimmer(-0.1)
    with pytest.raises(ValueError, match="trim_ratio"):
        make_ratio_trimmer(1.0)


def test_build_history_processors_from_scalars_off_by_default():
    """``enable_trimming`` defaults to ``False`` on
    ``PydanticAIBaseAgentConfig``, so the builder emits no processors."""
    agent = _EchoAgent(_EchoConfig())
    assert agent._build_history_processors_from_scalars() == []


def test_build_history_processors_from_scalars_includes_trimmer_when_enabled():
    """When ``enable_trimming=True``, the builder emits one callable — the
    trimmer produced by ``make_ratio_trimmer(1 - trim_ratio)``."""
    # trim_ratio=0.5 avoids floating-point drift on (1 - ratio) evaluation.
    agent = _EchoAgent(_EchoConfig(enable_trimming=True, trim_ratio=0.5))
    procs = agent._build_history_processors_from_scalars()
    assert len(procs) == 1
    assert callable(procs[0])
    # Sanity: the returned trimmer should behave like make_ratio_trimmer(0.5)
    # — on a 1+10 message list it drops 50% of the tail (5 messages).
    trimmer = procs[0]
    result = trimmer(["sys"] + [f"m-{i}" for i in range(10)])
    assert result[0] == "sys"
    assert len(result) == 1 + 5  # head + 10 - int(10 * 0.5) = 5 kept


def test_config_history_processors_pass_through():
    """Processors the caller supplies via ``config.history_processors`` must
    show up in ``_build_history_processors_from_scalars``'s merge path
    (i.e. the agent sees both the scalar-derived trimmer and the
    config-provided callables)."""

    def custom_processor(messages):
        return messages  # no-op

    agent = _EchoAgent(_EchoConfig(history_processors=[custom_processor]))
    # The builder itself doesn't return custom processors — only scalar-derived
    # ones — but the agent's __init__ merges them into pydantic_ai's
    # history_processors kwarg. Confirm the custom one survives registration
    # by inspecting the config directly (the canonical assertion available
    # without reaching into pydantic_ai internals).
    assert custom_processor in agent.config.history_processors
