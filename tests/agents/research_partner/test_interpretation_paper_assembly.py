"""Functional tests for Interpretation & Paper Assembly Agent."""

import pytest

from akd._base import TextOutput
from akd_ext.agents.research_partner import (
    InterpretationPaperAssemblyAgent,
    InterpretationPaperAssemblyConfig,
    InterpretationPaperAssemblyInputSchema,
    InterpretationPaperAssemblyOutputSchema,
)


def _make_input(**overrides) -> InterpretationPaperAssemblyInputSchema:
    """Helper to create input schema with default placeholder values."""
    defaults = {
        "research_question": "RQ-001: Does increasing surface roughness length affect boundary layer depth?",
        "experiment_output_dir": "/path/to/experiment_output",
    }
    defaults.update(overrides)
    return InterpretationPaperAssemblyInputSchema(**defaults)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "research_question,experiment_output_dir",
    [
        (
            "RQ-001: Does increasing surface roughness length affect boundary layer depth in tropical cyclones?",
            "/path/to/tc_experiment_output",
        ),
        (
            "RQ-001: What is the sensitivity of boundary layer structure to PBL scheme choice?",
            "/path/to/bl_experiment_output",
        ),
        (
            "RQ-001: How does convective initiation timing depend on SST perturbation?",
            "/path/to/ci_experiment_output",
        ),
    ],
)
async def test_interpretation_paper_assembly_agent(
    research_question: str, experiment_output_dir: str, reasoning_effort: str
):
    """Test Interpretation & Paper Assembly Agent.

    Args:
        research_question: Research question content
        experiment_output_dir: Path to experiment artifacts directory
        reasoning_effort: CLI param --reasoning-effort (low/medium/high)
    """
    config = InterpretationPaperAssemblyConfig(reasoning_effort=reasoning_effort)
    agent = InterpretationPaperAssemblyAgent(config=config, debug=True)
    result = await agent.arun(
        _make_input(research_question=research_question, experiment_output_dir=experiment_output_dir)
    )

    assert isinstance(result, (InterpretationPaperAssemblyOutputSchema, TextOutput))
    if isinstance(result, InterpretationPaperAssemblyOutputSchema):
        assert result.report.strip(), "Report should not be empty"


@pytest.mark.asyncio
async def test_interpretation_paper_assembly_with_figures(reasoning_effort: str):
    """Test that providing figures_dir triggers report generation.

    Args:
        reasoning_effort: CLI param --reasoning-effort (low/medium/high)
    """
    config = InterpretationPaperAssemblyConfig(reasoning_effort=reasoning_effort)
    agent = InterpretationPaperAssemblyAgent(config=config, debug=True)
    result = await agent.arun(_make_input(figures_dir="/path/to/figures_experiment01"))

    assert isinstance(result, (InterpretationPaperAssemblyOutputSchema, TextOutput))
    if isinstance(result, InterpretationPaperAssemblyOutputSchema):
        assert result.report.strip(), "Report should not be empty"
