"""Functional tests for CARE Capability & Feasibility Mapper Agent."""

import pytest

from akd._base import TextOutput
from akd_ext.agents.research_partner import (
    CapabilityFeasibilityMapperAgent,
    CapabilityFeasibilityMapperConfig,
    CapabilityFeasibilityMapperInputSchema,
    CapabilityFeasibilityMapperOutputSchema,
)


def _make_input(**overrides) -> CapabilityFeasibilityMapperInputSchema:
    """Helper to create input schema with default placeholder values."""
    defaults = {
        "research_question": "RQ-001: Does increasing surface roughness length affect boundary layer depth?",
        "cluster_it_context": "Cluster IT documentation: 128 nodes, 64 cores each, SLURM scheduler, 48h max walltime.",
        "cm1_readme_context": "CM1 README: Cloud Model 1, supports namelist.input configuration, key parameters include z0.",
    }
    defaults.update(overrides)
    return CapabilityFeasibilityMapperInputSchema(**defaults)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "research_question",
    [
        "RQ-001: Does increasing surface roughness length affect boundary layer depth in tropical cyclones?",
        "RQ-001: How does convective initiation timing depend on SST perturbation?",
        "RQ-001: What is the sensitivity of boundary layer structure to PBL scheme choice?",
    ],
)
async def test_capability_feasibility_mapper_agent(research_question: str, reasoning_effort: str):
    """Test CARE Capability & Feasibility Mapper Agent.

    Args:
        research_question: Research question content
        reasoning_effort: CLI param --reasoning-effort (low/medium/high)
    """
    config = CapabilityFeasibilityMapperConfig(reasoning_effort=reasoning_effort)
    agent = CapabilityFeasibilityMapperAgent(config=config, debug=True)
    result = await agent.arun(_make_input(research_question=research_question))

    assert isinstance(result, (CapabilityFeasibilityMapperOutputSchema, TextOutput))
    if isinstance(result, CapabilityFeasibilityMapperOutputSchema):
        assert result.report.strip(), "Report should not be empty"
