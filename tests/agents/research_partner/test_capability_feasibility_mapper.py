"""Functional tests for CARE Capability & Feasibility Mapper Agent."""

import pytest

from akd._base import TextOutput
from akd_ext.agents.closed_loop_cm1 import (
    CapabilityFeasibilityMapperAgent,
    CapabilityFeasibilityMapperConfig,
    CapabilityFeasibilityMapperInputSchema,
    CapabilityFeasibilityMapperOutputSchema,
)


def _make_input(**overrides) -> CapabilityFeasibilityMapperInputSchema:
    """Helper to create input schema with default placeholder values."""
    defaults = {
        "research_questions_md": "RQ-001: Does increasing surface roughness length affect boundary layer depth?",
    }
    defaults.update(overrides)
    return CapabilityFeasibilityMapperInputSchema(**defaults)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "research_questions_md",
    [
        "RQ-001: Does increasing surface roughness length affect boundary layer depth in tropical cyclones?",
        "RQ-001: How does convective initiation timing depend on SST perturbation?",
        "RQ-001: What is the sensitivity of boundary layer structure to PBL scheme choice?",
    ],
)
async def test_capability_feasibility_mapper_agent(research_questions_md: str, reasoning_effort: str):
    """Test CARE Capability & Feasibility Mapper Agent.

    Args:
        research_questions_md: Research question content
        reasoning_effort: CLI param --reasoning-effort (low/medium/high)
    """
    config = CapabilityFeasibilityMapperConfig(reasoning_effort=reasoning_effort)
    agent = CapabilityFeasibilityMapperAgent(config=config, debug=True)
    result = await agent.arun(_make_input(research_questions_md=research_questions_md))

    assert isinstance(result, (CapabilityFeasibilityMapperOutputSchema, TextOutput))
    if isinstance(result, CapabilityFeasibilityMapperOutputSchema):
        assert result.report.strip(), "Report should not be empty"
