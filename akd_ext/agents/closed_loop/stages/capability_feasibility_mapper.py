"""Generic Capability & Feasibility Mapper stage for closed-loop workflows.

This module provides the base CapabilityFeasibilityMapperAgent that can be
specialized for any domain (CM1, FM Inference, etc.) by providing a system
prompt and context files via config.

Public API:
    CapabilityFeasibilityMapperAgent,
    CapabilityFeasibilityMapperInputSchema,
    CapabilityFeasibilityMapperOutputSchema,
    CapabilityFeasibilityMapperConfig
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


class CapabilityFeasibilityMapperConfig(ClosedLoopStageConfig):
    """Configuration for Capability & Feasibility Mapper Agent.

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


class CapabilityFeasibilityMapperInputSchema(InputSchema):
    """Input schema for Capability & Feasibility Mapper Agent."""

    research_questions_md: str = Field(
        ...,
        description="Markdown string from the Gap Agent containing research question(s), hypotheses, variables, and causality guardrails.",
    )


class CapabilityFeasibilityMapperOutputSchema(OutputSchema):
    """Use this schema to return the structured feasibility assessment report.
    Put the full markdown report in the report field.
    Use TextOutput for clarification questions or when inputs are missing."""

    __response_field__ = "report"
    report: str = Field(
        default="",
        description="Full structured markdown feasibility assessment report, to be seen by sme before proceeding",
    )


# -----------------------------------------------------------------------------
# Capability & Feasibility Mapper Agent (Generic)
# -----------------------------------------------------------------------------


class CapabilityFeasibilityMapperAgent(
    OpenAIBaseAgent[CapabilityFeasibilityMapperInputSchema, CapabilityFeasibilityMapperOutputSchema]
):
    """Generic Capability & Feasibility Mapper Agent.

    Evaluates whether research questions and hypotheses can be realistically
    tested using available numerical models, codebases, and cluster resources.
    Produces structured capability-feasibility assessment reports with evidence paths.

    Subclass or configure with domain-specific system_prompt and context_files.
    """

    input_schema = CapabilityFeasibilityMapperInputSchema
    output_schema = CapabilityFeasibilityMapperOutputSchema | TextOutput
    config_schema = CapabilityFeasibilityMapperConfig

    def _create_agent(self) -> Agent:
        agent = super()._create_agent()
        return append_context_to_agent(agent, self.config.context_files)

    def check_output(self, output) -> str | None:
        if isinstance(output, CapabilityFeasibilityMapperOutputSchema) and not output.report.strip():
            return "Report is empty. Provide a structured feasibility assessment with evidence paths."
        return super().check_output(output)
