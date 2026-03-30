"""Functional tests for Workflow Spec Builder Agent."""

import pytest

from akd._base import TextOutput
from akd_ext.agents.closed_loop_cm1 import (
    WorkflowSpecBuilderAgent,
    WorkflowSpecBuilderConfig,
    WorkflowSpecBuilderInputSchema,
    WorkflowSpecBuilderOutputSchema,
)


def _make_input(**overrides) -> WorkflowSpecBuilderInputSchema:
    """Helper to create input schema with default placeholder values."""
    defaults = {
        "stage_1_hypotheses": "RQ-001: Does increasing surface roughness length affect boundary layer depth?",
    }
    defaults.update(overrides)
    return WorkflowSpecBuilderInputSchema(**defaults)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "stage_1_hypotheses,model_name",
    [
        (
            "RQ-001: Does increasing surface roughness length affect boundary layer depth in tropical cyclones?",
            "CM1",
        ),
        (
            "RQ-001: How does SST perturbation influence convective initiation timing?",
            "CM1",
        ),
        (
            "RQ-001: What is the sensitivity of precipitation to microphysics scheme choice?",
            "WRF",
        ),
    ],
)
async def test_workflow_spec_builder_agent(stage_1_hypotheses: str, model_name: str, reasoning_effort: str):
    """Test Workflow Spec Builder Agent.

    Args:
        stage_1_hypotheses: Stage-1 hypotheses artifact
        model_name: Target model
        reasoning_effort: CLI param --reasoning-effort (low/medium/high)
    """
    config = WorkflowSpecBuilderConfig(reasoning_effort=reasoning_effort)
    agent = WorkflowSpecBuilderAgent(config=config, debug=True)
    result = await agent.arun(_make_input(stage_1_hypotheses=stage_1_hypotheses, model_name=model_name))

    assert isinstance(result, (WorkflowSpecBuilderOutputSchema, TextOutput))
    if isinstance(result, WorkflowSpecBuilderOutputSchema):
        assert result.spec.strip(), "Spec should not be empty"
