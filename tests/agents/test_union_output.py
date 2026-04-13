"""Tests for union output schema support in OpenAIBaseAgent."""

import pytest
from unittest.mock import MagicMock

from pydantic import Field

from akd._base import InputSchema, OutputSchema, TextOutput
from akd_ext.agents._base import OpenAIBaseAgent, OpenAIBaseAgentConfig


# ── Test schemas ─────────────────────────────────────────────────────


class SimpleInput(InputSchema):
    """Test input schema."""

    query: str = Field(..., description="A query")


class OutputA(OutputSchema):
    """Output branch A."""

    answer: str = Field(..., description="The answer")


class OutputB(OutputSchema):
    """Output branch B."""

    items: list[str] = Field(..., description="List of items")


# ── Single schema agents (regression) ────────────────────────────────


class SingleSchemaAgent(OpenAIBaseAgent):
    """Agent with single output schema."""

    input_schema = SimpleInput
    output_schema = OutputA
    config_schema = OpenAIBaseAgentConfig


# ── Union schema agents ─────────────────────────────────────────────
# Note: We set output_schema as class attribute directly rather than using
# the generic syntax OpenAIBaseAgent[In, OutA | OutB] because akd-core's
# __class_getitem__ doesn't yet handle UnionType.__name__. The metaclass
# validates union output_schema correctly via get_origin/get_args.


class UnionMultiToolAgent(OpenAIBaseAgent):
    """Agent with union output schema, multi_tool mode (default)."""

    input_schema = SimpleInput
    output_schema = OutputA | OutputB
    config_schema = OpenAIBaseAgentConfig


class UnionUnifiedAgent(OpenAIBaseAgent):
    """Agent with union output schema, unified_schema mode."""

    input_schema = SimpleInput
    output_schema = OutputA | OutputB
    config_schema = OpenAIBaseAgentConfig


# ── Tests: output_schema_resolved ────────────────────────────────────


def test_single_schema_resolved():
    """Single schema agent resolves to one-element list."""
    agent = SingleSchemaAgent()
    assert agent.output_schema_resolved == [OutputA]


def test_union_schema_resolved():
    """Union schema agent resolves to list of branches."""
    agent = UnionMultiToolAgent()
    resolved = agent.output_schema_resolved
    assert len(resolved) == 2
    assert OutputA in resolved
    assert OutputB in resolved


# ── Tests: _create_agent output_type ─────────────────────────────────


def test_single_schema_creates_agent_with_output_type():
    """Single schema agent sets output_type on the SDK Agent."""
    agent = SingleSchemaAgent()
    assert agent._agent.output_type == OutputA


def test_union_multi_tool_creates_agent_with_no_output_type():
    """Union multi_tool agent sets output_type=None and adds output tools."""
    config = OpenAIBaseAgentConfig(output_mode="multi_tool")
    agent = UnionMultiToolAgent(config=config)
    assert agent._agent.output_type is None
    # Should have output tools added
    tool_names = [t.name for t in agent._agent.tools]
    assert "final_OutputA" in tool_names
    assert "final_OutputB" in tool_names


def test_union_unified_creates_agent_with_envelope():
    """Union unified_schema agent sets output_type to envelope model."""
    config = OpenAIBaseAgentConfig(output_mode="unified_schema")
    agent = UnionUnifiedAgent(config=config)
    envelope = agent._agent.output_type
    assert envelope is not None
    # Envelope should have 'kind' field and fields for each branch
    assert "kind" in envelope.model_fields
    assert "OutputA" in envelope.model_fields
    assert "OutputB" in envelope.model_fields


def test_check_output_accepts_valid():
    """check_output accepts valid output by default."""
    agent = UnionMultiToolAgent()
    assert agent.check_output(OutputA(answer="hello")) is None
    assert agent.check_output(OutputB(items=["a", "b"])) is None


def test_check_output_rejects_empty_text():
    """check_output rejects empty TextOutput."""
    agent = SingleSchemaAgent()
    assert agent.check_output(TextOutput(content="")) is not None
    assert agent.check_output(TextOutput(content="   ")) is not None


# ── Tests: output_tools from mixin ───────────────────────────────────


def test_single_schema_output_tools():
    """Single schema agent has one output tool."""
    agent = SingleSchemaAgent()
    assert len(agent.output_tools) == 1
    assert agent.output_tools[0].name == "final_answer"


def test_union_multi_tool_output_tools():
    """Union multi_tool agent has one output tool per branch."""
    config = OpenAIBaseAgentConfig(output_mode="multi_tool")
    agent = UnionMultiToolAgent(config=config)
    assert len(agent.output_tools) == 2
    names = {t.name for t in agent.output_tools}
    assert names == {"final_OutputA", "final_OutputB"}


def test_union_unified_output_tools():
    """Union unified_schema agent has one output tool (first schema)."""
    config = OpenAIBaseAgentConfig(output_mode="unified_schema")
    agent = UnionUnifiedAgent(config=config)
    # In unified mode, _build_output_tools returns [OutputTool(schemas[0])]
    assert len(agent.output_tools) == 1


# ── Tests: _resolve_final_output ─────────────────────────────────────


def test_resolve_single_schema_instance():
    """Resolves when output is already the correct schema."""
    agent = SingleSchemaAgent()
    output = OutputA(answer="hello")
    result = agent._resolve_final_output(output)
    assert isinstance(result, OutputA)
    assert result.answer == "hello"


def test_resolve_union_branch_a():
    """Resolves union output to branch A."""
    agent = UnionMultiToolAgent()
    output = OutputA(answer="hello")
    result = agent._resolve_final_output(output)
    assert isinstance(result, OutputA)


def test_resolve_union_branch_b():
    """Resolves union output to branch B."""
    agent = UnionMultiToolAgent()
    output = OutputB(items=["a", "b"])
    result = agent._resolve_final_output(output)
    assert isinstance(result, OutputB)


def test_resolve_unified_envelope():
    """Resolves unified envelope by unwrapping to concrete branch."""
    config = OpenAIBaseAgentConfig(output_mode="unified_schema")
    agent = UnionUnifiedAgent(config=config)
    envelope_cls = agent.effective_output_schema
    envelope = envelope_cls(kind="OutputA", OutputA=OutputA(answer="test"), OutputB=None)
    result = agent._resolve_final_output(envelope)
    assert isinstance(result, OutputA)
    assert result.answer == "test"


def test_resolve_model_dump_fallback():
    """Resolves output via model_dump when not an exact instance."""
    agent = SingleSchemaAgent()

    class FakeOutput:
        def model_dump(self):
            return {"answer": "from dump"}

    result = agent._resolve_final_output(FakeOutput())
    assert isinstance(result, OutputA)
    assert result.answer == "from dump"


def test_resolve_raises_on_unresolvable():
    """Raises UnexpectedModelBehavior when output can't be resolved."""
    agent = UnionMultiToolAgent()
    with pytest.raises(Exception, match="Could not resolve output"):
        agent._resolve_final_output(12345)


# ── Tests: _inject_human_response ────────────────────────────────────


def test_inject_human_response_noop_when_none():
    """No injection when there's no human_response."""
    from akd._base import RunContext

    agent = SingleSchemaAgent()
    messages = []
    ctx = RunContext()
    agent._inject_human_response(messages, ctx)
    assert messages == []


def test_inject_human_response_adds_messages():
    """Injects tool response and developer guidance."""
    from akd._base import RunContext

    agent = SingleSchemaAgent()
    messages = []
    ctx = RunContext()
    ctx.human_response = MagicMock(tool_call_id="tc_123", content="yes")
    agent._inject_human_response(messages, ctx)
    assert len(messages) == 2
    assert messages[0]["role"] == "tool"
    assert messages[0]["tool_call_id"] == "tc_123"
    assert messages[1]["role"] == "developer"
