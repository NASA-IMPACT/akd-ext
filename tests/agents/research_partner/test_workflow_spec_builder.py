"""Functional tests for Workflow Spec Builder Agent."""

import pytest

from akd._base import TextOutput
from akd_ext.agents.closed_loop_cm1 import (
    WorkflowSpecBuilderAgent,
    WorkflowSpecBuilderConfig,
    WorkflowSpecBuilderInputSchema,
    WorkflowSpecBuilderOutputSchema,
)


_DEFAULT_FEASIBILITY = (
    "# Feasibility Report\n\n"
    "**Model**: CM1\n"
    "**Capability score**: 0.85 (high)\n\n"
    "The proposed experiment is feasible with the chosen model. "
    "Required parameters are available in the model configuration."
)


def _make_input(**overrides) -> WorkflowSpecBuilderInputSchema:
    """Helper to create input schema with default placeholder values."""
    defaults = {
        "stage_1_hypotheses": "RQ-001: Does increasing surface roughness length affect boundary layer depth?",
        "stage_2_feasibility": _DEFAULT_FEASIBILITY,
    }
    defaults.update(overrides)
    return WorkflowSpecBuilderInputSchema(**defaults)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "stage_1_hypotheses",
    [
        "RQ-001: Does increasing surface roughness length affect boundary layer depth in tropical cyclones?",
        "RQ-001: How does SST perturbation influence convective initiation timing?",
        "RQ-001: What is the sensitivity of precipitation to microphysics scheme choice?",
    ],
)
async def test_workflow_spec_builder_agent(stage_1_hypotheses: str, reasoning_effort: str):
    """Test Workflow Spec Builder Agent."""
    config = WorkflowSpecBuilderConfig(reasoning_effort=reasoning_effort)
    agent = WorkflowSpecBuilderAgent(config=config, debug=True)
    result = await agent.arun(_make_input(stage_1_hypotheses=stage_1_hypotheses))

    assert isinstance(result, (WorkflowSpecBuilderOutputSchema, TextOutput))
    if isinstance(result, WorkflowSpecBuilderOutputSchema):
        assert result.spec.strip(), "Spec should not be empty"
