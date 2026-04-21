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
from akd.tools._base import BaseTool

from akd_ext.agents._base import PydanticAIBaseAgent, PydanticAIBaseAgentConfig
from akd._base.protocols import (
    AKDExecutable,
    AKDTool,
    RunContextProtocol,
    TokenCounts,
)

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
    """Config for the echo test agent; adds one subclass-specific scalar."""

    enable_extra_capability: bool = Field(default=False)


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
    captured ctx is retained on the instance so callers can inspect it if
    needed. Exposing it as a public property (``agent.last_run_context``)
    is a plausible future ergonomic; this test pins the internal hook in
    the meantime.
    """
    from pydantic_ai import RunContext as PAIRunContext

    agent = _EchoAgent()
    # Before any run, nothing has been captured.
    assert agent._live_pai_ctx is None

    with agent.override(model=TestModel()):
        result = await agent.arun(_EchoInput(query="hello"))

    assert isinstance(result, (_EchoOutput, TextOutput))
    assert agent._live_pai_ctx is not None
    assert isinstance(agent._live_pai_ctx, PAIRunContext)
    assert agent._live_pai_ctx.usage.requests >= 1


# ---------------------------------------------------------------------------
# RunContext reflection onto AKD typed fields
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_astream_reflects_pai_state_onto_akd_fields():
    """Terminal ``CompletedEvent.run_context`` must expose pai state on the
    AKD typed fields (``messages`` / ``usage`` / ``run_id``) *and* keep the
    lossless ``pai_run_context`` extra."""
    from akd._base import CompletedEvent
    from pydantic_ai import RunContext as PAIRunContext

    agent = _EchoAgent()
    with agent.override(model=TestModel()):
        events = [ev async for ev in agent.astream(_EchoInput(query="hello"))]

    completed = [ev for ev in events if isinstance(ev, CompletedEvent)]
    assert completed
    ctx = completed[-1].run_context

    # Reflected typed fields on the AKD RunContext:
    assert isinstance(ctx.messages, list) and ctx.messages
    for msg in ctx.messages:
        assert isinstance(msg, dict)
        assert "role" in msg
    assert ctx.usage.requests >= 1
    assert ctx.run_id is not None

    # Lossless pai extra still attached alongside the reflected view:
    assert isinstance(ctx.pai_run_context, PAIRunContext)


@pytest.mark.asyncio
async def test_arun_last_run_context_property():
    """``agent.last_run_context`` returns ``None`` before any run and a
    populated AKD ``RunContext`` after ``arun``."""
    from pydantic_ai import RunContext as PAIRunContext

    agent = _EchoAgent()
    assert agent.last_run_context is None

    with agent.override(model=TestModel()):
        out = await agent.arun(_EchoInput(query="hello"))
    assert isinstance(out, (_EchoOutput, TextOutput))

    ctx = agent.last_run_context
    assert ctx is not None
    assert ctx.messages  # non-empty list of dicts
    assert all(isinstance(m, dict) and "role" in m for m in ctx.messages)
    assert ctx.usage.requests >= 1
    assert ctx.run_id is not None
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


def test_input_side_prefers_pai_run_context():
    """When a ``run_context`` carries both stale AKD-shape messages *and* a
    populated ``pai_run_context`` extra, the pai path wins — the dict view is
    ignored in favor of the lossless pai ``ModelMessage`` list."""
    from akd._base.structures import RunContext as AKDRunContext
    from pydantic_ai import RunContext as PAIRunContext
    from pydantic_ai.messages import ModelRequest, UserPromptPart
    from pydantic_ai.result import RunUsage as PAIRunUsage

    from akd_ext.agents._base.pydantic_ai._context_adapter import (
        _message_history_from_run_context,
        _usage_from_run_context,
    )

    pai_messages = [ModelRequest(parts=[UserPromptPart(content="pai-truth")])]
    pai_usage = PAIRunUsage(input_tokens=10, output_tokens=20, requests=3)
    pai_ctx = PAIRunContext(deps=None, model=None, usage=pai_usage)
    pai_ctx.messages = pai_messages

    akd_ctx = AKDRunContext(
        messages=[{"role": "user", "content": "stale-akd-shape"}],
        pai_run_context=pai_ctx,
    )

    history = _message_history_from_run_context(akd_ctx)
    assert history is pai_messages or history == pai_messages
    assert history[0].parts[0].content == "pai-truth"

    usage = _usage_from_run_context(akd_ctx)
    assert usage is pai_usage
    assert usage.input_tokens == 10


def test_input_side_falls_back_to_akd_shape():
    """Pure AKD ``RunContext`` (no ``pai_run_context`` extra) still works
    through the historical conversion path."""
    from akd._base.structures import RunContext as AKDRunContext
    from akd._base.structures import RunUsage as AKDRunUsage
    from pydantic_ai.result import RunUsage as PAIRunUsage

    from akd_ext.agents._base.pydantic_ai._context_adapter import (
        _message_history_from_run_context,
        _usage_from_run_context,
    )

    akd_ctx = AKDRunContext(
        messages=[
            {"role": "system", "content": "you are helpful"},
            {"role": "user", "content": "hi"},
        ],
        usage=AKDRunUsage(input_tokens=5, output_tokens=7, requests=1),
    )

    history = _message_history_from_run_context(akd_ctx)
    assert history is not None
    assert len(history) == 2

    usage = _usage_from_run_context(akd_ctx)
    assert isinstance(usage, PAIRunUsage)
    assert usage.input_tokens == 5
    assert usage.requests == 1


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


# ---------------------------------------------------------------------------
# Zone 3: subclass extension via _build_capabilities_from_scalars
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# CMRCarePydanticAgent parity smoke test
# ---------------------------------------------------------------------------


def test_cmr_care_pydantic_agent_constructs():
    """CMRCarePydanticAgent builds cleanly on PydanticAIBaseAgent using the same
    schemas as the existing CMRCareAgent."""
    from akd_ext.agents.cmr_care import CMRCareAgentInputSchema, CMRCareAgentOutputSchema
    from examples.cmr_care_pydantic import CMRCarePydanticAgent, CMRCarePydanticConfig

    agent = CMRCarePydanticAgent(CMRCarePydanticConfig(debug=True))
    assert agent.input_schema is CMRCareAgentInputSchema
    assert agent.output_schema == CMRCareAgentOutputSchema | TextOutput
    assert isinstance(agent, AKDExecutable)
    # Config auto-exposure works through the subclass config:
    assert agent.reasoning_effort == "medium"
    assert "CMR" in (agent.description or "")


def test_cmr_care_pydantic_agent_check_output():
    """Subclass override of check_output dispatches via the late-bound bridge."""
    from akd_ext.agents.cmr_care import CMRCareAgentOutputSchema
    from examples.cmr_care_pydantic import CMRCarePydanticAgent, CMRCarePydanticConfig

    agent = CMRCarePydanticAgent(CMRCarePydanticConfig())
    # Empty result should be rejected by the subclass override
    msg = agent.check_output(CMRCareAgentOutputSchema(result="   "))
    assert isinstance(msg, str)
    assert "empty" in msg.lower()
    # Non-empty result passes
    assert agent.check_output(CMRCareAgentOutputSchema(result="found datasets")) is None
    # TextOutput still bubbles through per the base class default
    assert agent.check_output(TextOutput(content="need clarification")) is None


@pytest.mark.asyncio
async def test_cmr_care_pydantic_agent_arun_with_test_model():
    """End-to-end wiring check: CMRCarePydanticAgent.arun works against TestModel.

    The default config wires pydantic_ai's ``MCP`` capability at the CMR
    endpoint — pydantic_ai tries to fetch the tool list even when ``TestModel``
    stands in for the LLM, which would reach the real network. We override
    ``capabilities=[]`` here so the test runs hermetically.
    """
    from akd_ext.agents.cmr_care import CMRCareAgentInputSchema, CMRCareAgentOutputSchema
    from examples.cmr_care_pydantic import CMRCarePydanticAgent, CMRCarePydanticConfig

    agent = CMRCarePydanticAgent(CMRCarePydanticConfig(capabilities=[]))
    with agent.override(model=TestModel()):
        result = await agent.arun(CMRCareAgentInputSchema(query="sea ice datasets"))
    assert isinstance(result, (CMRCareAgentOutputSchema, TextOutput))


def test_subclass_can_extend_capabilities_hook():
    """Subclasses may override ``_build_capabilities_from_scalars`` and call super()."""

    class _MarkerCapability:
        """Stand-in capability used to assert the hook was invoked."""

    class _ExtAgent(_EchoAgent):
        """Echo agent that adds a marker capability when enabled."""

        def _build_capabilities_from_scalars(self):
            caps = super()._build_capabilities_from_scalars()
            if self.config.enable_extra_capability:
                caps.append(_MarkerCapability())
            return caps

    # Instantiation would normally require the capability to be a real one,
    # but construction-time pydantic_ai validation is model-side; we only
    # check the hook output directly here.
    agent = _ExtAgent.__new__(_ExtAgent)  # bypass __init__; we only want the method
    agent.config = _EchoConfig(enable_extra_capability=True)
    produced = agent._build_capabilities_from_scalars()
    assert any(isinstance(c, _MarkerCapability) for c in produced)


# ---------------------------------------------------------------------------
# Smoke tests for a PydanticAIBaseAgent derivative
# ---------------------------------------------------------------------------
#
# A self-contained derivative (mirrors the shape of an MCP-free CMR agent)
# defined inline so these smoke tests don't depend on any untracked
# scaffolding. Reuses the committed CMR input / output schemas so the
# agent-under-test matches the shape of a real AKD agent.

from akd_ext.agents.cmr_care import (  # noqa: E402
    CMRCareAgentInputSchema,
    CMRCareAgentOutputSchema,
)

_SMOKE_SYSTEM_PROMPT = "You are a helpful agent spacializing in CMR and Earth Science."


class _SmokeCMRConfig(PydanticAIBaseAgentConfig):
    """Minimal CMR-shaped config: no MCP (hermetic), placeholder prompt."""

    description: str = Field(default="Smoke-test CMR agent on PydanticAIBaseAgent.")
    system_prompt: str = Field(default=_SMOKE_SYSTEM_PROMPT)
    model_name: str = Field(default="openai:gpt-4o-mini")
    # capabilities default to [] via PydanticAIBaseAgentConfig — no MCP.


class _SmokeCMRAgent(PydanticAIBaseAgent[CMRCareAgentInputSchema, CMRCareAgentOutputSchema]):
    """Self-contained PydanticAIBaseAgent derivative for smoke tests."""

    input_schema = CMRCareAgentInputSchema
    output_schema = CMRCareAgentOutputSchema | TextOutput
    config_schema = _SmokeCMRConfig

    def check_output(self, output):
        if isinstance(output, CMRCareAgentOutputSchema) and not output.result.strip():
            return "Result is empty. Provide search reasoning and details."
        return super().check_output(output)


@pytest.mark.asyncio
async def test_smoke_arun_and_last_run_context():
    """End-to-end arun smoke test: return matches output schema; getter
    exposes a populated AKD RunContext for the next turn."""
    from pydantic_ai import RunContext as PAIRunContext

    agent = _SmokeCMRAgent()
    with agent.override(model=TestModel()):
        result = await agent.arun(CMRCareAgentInputSchema(query="sea ice datasets"))

    assert isinstance(result, (CMRCareAgentOutputSchema, TextOutput))

    ctx = agent.last_run_context
    assert ctx is not None
    assert ctx.messages and all(isinstance(m, dict) and "role" in m for m in ctx.messages)
    assert ctx.usage.requests >= 1
    assert ctx.run_id is not None
    assert isinstance(ctx.pai_run_context, PAIRunContext)


@pytest.mark.asyncio
async def test_smoke_astream_no_run_context():
    """astream tolerates ``run_context=None`` and still attaches a populated
    run_context (messages + usage + run_id + pai_run_context) to at least
    one emitted event."""
    from akd._base import StreamEvent
    from pydantic_ai import RunContext as PAIRunContext

    agent = _SmokeCMRAgent()
    with agent.override(model=TestModel()):
        events = [
            ev
            async for ev in agent.astream(
                CMRCareAgentInputSchema(query="ocean carbon observations"),
            )
        ]

    assert events, "astream should produce at least one event"
    assert all(isinstance(ev, StreamEvent) for ev in events)
    assert all(ev.run_context is not None for ev in events)

    populated = [ev for ev in events if ev.run_context.messages and ev.run_context.usage.requests >= 1]
    assert populated, "expected at least one event with populated messages + usage"

    sample = populated[-1]
    assert sample.run_context.run_id is not None
    assert isinstance(sample.run_context.pai_run_context, PAIRunContext)


def test_smoke_pai_agent_surface_available():
    """Path B single inheritance: pydantic_ai.Agent's public surface must
    still be reachable on a PydanticAIBaseAgent derivative instance."""
    from pydantic_ai import Agent as PAIAgent

    agent = _SmokeCMRAgent()
    assert isinstance(agent, PAIAgent)

    for attr in (
        "run",
        "run_stream_events",
        "iter",
        "override",
        "output_validator",
        "tool",
        "system_prompt",
    ):
        assert callable(getattr(agent, attr)), f"{attr} missing or not callable"

    # name / description come from config via ConfigBindingMixin auto-exposure.
    assert isinstance(agent.description, str) and agent.description
    # name may be None by default; just confirm attribute access doesn't raise.
    _ = agent.name
