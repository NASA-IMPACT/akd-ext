"""Functional tests for Experiment Implementation Agent."""

import pytest

from akd._base import TextOutput
from akd_ext.agents.research_partner import (
    ExperimentImplementationAgent,
    ExperimentImplementationConfig,
    ExperimentImplementationInputSchema,
    ExperimentImplementationOutputSchema,
)


def _make_input(**overrides) -> ExperimentImplementationInputSchema:
    """Helper to create input schema with default placeholder values."""
    defaults = {
        "experiment_spec": (
            "# Metadata\nmodel: CM1\nstatus: draft\n\n"
            "# Experiment Matrix\n"
            "| exp_id | EXP_TC_baseline | EXP_TC_001 |\n"
            "| namelist_deltas | -- | cecd=1; sfcmodel=1 |"
        ),
        "cm1_readme_context": "CM1 README: Cloud Model 1, supports namelist.input configuration.",
        "research_question": "RQ-001: Does increasing surface roughness length affect boundary layer depth?",
    }
    defaults.update(overrides)
    return ExperimentImplementationInputSchema(**defaults)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "experiment_spec",
    [
        (
            "# Metadata\nmodel: CM1\nstatus: draft\n\n"
            "# Experiment Matrix\n"
            "EXP_TC_baseline: baseline tropical cyclone\n"
            "EXP_TC_001: increased surface roughness z0=0.01"
        ),
        (
            "# Metadata\nmodel: CM1\nstatus: draft\n\n"
            "# Experiment Matrix\n"
            "EXP_BL_baseline: baseline boundary layer\n"
            "EXP_BL_001: modified PBL scheme ipbl=2"
        ),
        (
            "# Metadata\nmodel: CM1\nstatus: draft\n\n"
            "# Experiment Matrix\n"
            "EXP_CI_baseline: baseline convective initiation\n"
            "EXP_CI_001: SST perturbation +2K\n"
            "EXP_CI_002: SST perturbation -2K"
        ),
    ],
)
async def test_experiment_implementation_agent(experiment_spec: str, reasoning_effort: str):
    """Test Experiment Implementation Agent.

    Args:
        experiment_spec: Stage-3 experiment design output
        reasoning_effort: CLI param --reasoning-effort (low/medium/high)
    """
    config = ExperimentImplementationConfig(reasoning_effort=reasoning_effort)
    agent = ExperimentImplementationAgent(config=config, debug=True)
    result = await agent.arun(_make_input(experiment_spec=experiment_spec))

    assert isinstance(result, (ExperimentImplementationOutputSchema, TextOutput))
    if isinstance(result, ExperimentImplementationOutputSchema):
        assert result.report.strip(), "Report should not be empty"
