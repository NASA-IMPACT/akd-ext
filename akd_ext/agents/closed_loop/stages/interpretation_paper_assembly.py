"""Generic Interpretation & Paper Assembly stage for closed-loop workflows.

This module provides the base InterpretationPaperAssemblyAgent that can be
specialized for any domain by providing a system prompt and context files.

Public API:
    InterpretationPaperAssemblyAgent,
    InterpretationPaperAssemblyInputSchema,
    InterpretationPaperAssemblyOutputSchema,
    InterpretationPaperAssemblyConfig
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from agents import Agent

from akd._base import InputSchema, OutputSchema, TextOutput
from akd_ext.agents._base import OpenAIBaseAgent
from akd_ext.agents.closed_loop._base import ClosedLoopStageConfig, append_context_to_agent


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------


class InterpretationPaperAssemblyConfig(ClosedLoopStageConfig):
    """Configuration for Interpretation & Paper Assembly Agent.

    Subclass and override system_prompt, context_files, and description
    to specialize for a specific domain.
    """

    system_prompt: str = Field(default="")
    model_name: str = Field(default="gpt-5.2")
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(default="medium")
    description: str = Field(default="")


# -----------------------------------------------------------------------------
# Public Input/Output Schemas
# -----------------------------------------------------------------------------


class InterpretationPaperAssemblyInputSchema(InputSchema):
    """Input schema for Interpretation & Paper Assembly Agent."""

    research_question: str = Field(..., description="Research question content as a string")
    experiment_output_dir: str = Field(
        ..., description="Path to directory containing experiment artifacts from the previous stage"
    )
    figures_dir: str | None = Field(
        default=None, description="Optional path to figures directory; triggers report generation when provided"
    )


class InterpretationPaperAssemblyOutputSchema(OutputSchema):
    """Use this schema to return the analysis and assembly report.
    Put the full report describing artifacts created in the report field.
    Use TextOutput for approval gates, clarifications, or when inputs are missing."""

    __response_field__ = "report"
    report: str = Field(
        default="",
        description="Full report describing artifacts created (manifest, analysis plan, notebook, README, "
        "markdown report)",
    )


# -----------------------------------------------------------------------------
# Interpretation & Paper Assembly Agent (Generic)
# -----------------------------------------------------------------------------


class InterpretationPaperAssemblyAgent(
    OpenAIBaseAgent[InterpretationPaperAssemblyInputSchema, InterpretationPaperAssemblyOutputSchema]
):
    """Generic Interpretation & Paper Assembly Agent.

    Transforms experiment outputs and research questions into structured
    scientific analysis artifacts including manifests, notebooks, and reports.

    Subclass or configure with domain-specific system_prompt and context_files.
    """

    input_schema = InterpretationPaperAssemblyInputSchema
    output_schema = InterpretationPaperAssemblyOutputSchema | TextOutput
    config_schema = InterpretationPaperAssemblyConfig

    def _create_agent(self) -> Agent:
        agent = super()._create_agent()
        return append_context_to_agent(agent, self.config.context_files)

    def check_output(self, output) -> str | None:
        if isinstance(output, InterpretationPaperAssemblyOutputSchema) and not output.report.strip():
            return "Report is empty. Provide a detailed report describing the artifacts created."
        return super().check_output(output)
