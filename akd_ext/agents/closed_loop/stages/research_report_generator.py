"""Generic Research Report Generator stage for closed-loop workflows.

This module provides the base ResearchReportGeneratorAgent that can be
specialized for any domain by providing a system prompt and MCP tools.

Public API:
    ResearchReportGeneratorAgent,
    ResearchReportGeneratorInputSchema,
    ResearchReportGeneratorOutputSchema,
    ResearchReportGeneratorConfig
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


class ResearchReportGeneratorConfig(ClosedLoopStageConfig):
    """Configuration for Research Report Generator Agent.

    Subclass and override system_prompt, tools, and description
    to specialize for a specific domain.
    """

    system_prompt: str = Field(default="")
    model_name: str = Field(default="gpt-5.2")
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(default="medium")
    description: str = Field(default="")


# -----------------------------------------------------------------------------
# Public Input/Output Schemas
# -----------------------------------------------------------------------------


class ResearchReportGeneratorInputSchema(InputSchema):
    """Input schema for Research Report Generator Agent.

    Takes the workflow specification and job ID from the experiment stage.
    The agent uses MCP tools to check job status and fetch figure URLs.
    """

    workflow_spec: str = Field(
        ...,
        description=(
            "Stage 3 workflow specification markdown containing: research question, "
            "hypothesis, control definition, experiment matrix, feasibility notes, "
            "and feasibility summary. This is the primary source of scientific context."
        ),
    )
    job_id: str = Field(
        ...,
        description=(
            "Job ID from the experiment implementation stage. Represents the entire batch of experiments. "
            "The agent uses this to check batch completion status and fetch figure URLs via MCP tools."
        ),
    )


class ResearchReportGeneratorOutputSchema(OutputSchema):
    """Returns a publication-style scientific report in Markdown.

    The report references figures and interprets experiment results in
    the context of the hypothesis and workflow specification."""

    __response_field__ = "report"

    report: str = Field(
        default="",
        description=(
            "Complete publication-style scientific report in Markdown. "
            "Sections: Abstract, Introduction, Model and Methodology, "
            "Results, Discussion, Conclusion, Figures."
        ),
    )


# -----------------------------------------------------------------------------
# Research Report Generator Agent (Generic)
# -----------------------------------------------------------------------------


class ResearchReportGeneratorAgent(
    OpenAIBaseAgent[ResearchReportGeneratorInputSchema, ResearchReportGeneratorOutputSchema]
):
    """Generic Research Report Generator Agent.

    Takes the workflow specification and figure URLs to produce a
    publication-style scientific report interpreting experiment results.

    Subclass or configure with domain-specific system_prompt and tools.
    """

    input_schema = ResearchReportGeneratorInputSchema
    output_schema = ResearchReportGeneratorOutputSchema | TextOutput
    config_schema = ResearchReportGeneratorConfig

    def _create_agent(self) -> Agent:
        agent = super()._create_agent()
        return append_context_to_agent(agent, self.config.context_files)

    def check_output(self, output) -> str | None:
        if isinstance(output, ResearchReportGeneratorOutputSchema) and not output.report.strip():
            return "Report is empty. Provide a complete scientific report."
        return super().check_output(output)
