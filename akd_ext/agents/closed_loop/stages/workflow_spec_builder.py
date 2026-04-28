"""Generic Workflow Spec Builder stage for closed-loop workflows.

This module provides the base WorkflowSpecBuilderAgent that can be
specialized for any domain by providing a system prompt and context files.

Public API:
    WorkflowSpecBuilderAgent,
    WorkflowSpecBuilderInputSchema,
    WorkflowSpecBuilderOutputSchema,
    WorkflowSpecBuilderConfig
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


class WorkflowSpecBuilderConfig(ClosedLoopStageConfig):
    """Configuration for Workflow Spec Builder Agent.

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


class WorkflowSpecBuilderInputSchema(InputSchema):
    """Input schema for Workflow Spec Builder Agent."""

    stage_1_hypotheses: str = Field(
        ...,
        description="Gap Agent output — research hypotheses markdown with RQ IDs, variables, and causality guardrails.",
    )
    stage_2_feasibility: str = Field(
        ...,
        description="Stage-2 feasibility report from CapabilityFeasibilityMapperAgent with capability analysis and scoring.",
    )


class WorkflowSpecBuilderOutputSchema(OutputSchema):
    """Use this schema to return the workflow specification and design reasoning.
    Put the full markdown workflow spec in the spec field and design choices explanation in the reasoning field.
    Use TextOutput for clarification questions or when inputs are insufficient."""

    __response_field__ = "spec"
    spec: str = Field(default="", description="Full markdown workflow specification document.")
    reasoning: str = Field(
        default="", description="Structured reasoning behind design choices, assumptions, and feasibility handling."
    )


# -----------------------------------------------------------------------------
# Workflow Spec Builder Agent (Generic)
# -----------------------------------------------------------------------------


class WorkflowSpecBuilderAgent(OpenAIBaseAgent[WorkflowSpecBuilderInputSchema, WorkflowSpecBuilderOutputSchema]):
    """Generic Workflow Spec Builder Agent.

    Designs scientifically traceable, feasibility-aware simulation experiments
    and documents them as execution-ready Markdown workflow specifications.

    Subclass or configure with domain-specific system_prompt and context_files.
    """

    input_schema = WorkflowSpecBuilderInputSchema
    output_schema = WorkflowSpecBuilderOutputSchema | TextOutput
    config_schema = WorkflowSpecBuilderConfig

    def _create_agent(self) -> Agent:
        agent = super()._create_agent()
        return append_context_to_agent(agent, self.config.context_files)

    def check_output(self, output) -> str | None:
        if isinstance(output, WorkflowSpecBuilderOutputSchema) and not output.spec.strip():
            return "Spec is empty. Provide a complete draft workflow specification."
        return super().check_output(output)
