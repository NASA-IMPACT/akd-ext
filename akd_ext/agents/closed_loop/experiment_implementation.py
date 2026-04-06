"""Generic Experiment Implementation stage for closed-loop workflows.

This module provides the base ExperimentImplementationAgent that can be
specialized for any domain by providing a system prompt, context files,
and MCP tools.

Public API:
    ExperimentImplementationAgent,
    ExperimentImplementationInputSchema,
    ExperimentImplementationOutputSchema,
    ExperimentImplementationConfig,
    FileEdit,
    ExperimentSpec
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from agents import Agent

from akd._base import InputSchema, OutputSchema, TextOutput
from akd_ext.agents._base import OpenAIBaseAgent
from akd_ext.agents.closed_loop._base import ClosedLoopStageConfig, append_context_to_agent


# -----------------------------------------------------------------------------
# Data Models
# -----------------------------------------------------------------------------


class FileEdit(BaseModel):
    """A single edit to a model input file."""

    target_file: str = Field(..., description="Target filename: 'namelist.input' or 'input_sounding'")
    edit_type: Literal["namelist_param", "sounding_profile", "file_replace"] = Field(
        ..., description="Type of edit to apply"
    )

    # -- namelist_param fields
    namelist_group: str = Field(default="", description="Namelist group name without & prefix (e.g. 'param9')")
    parameter: str = Field(default="", description="Parameter key name (e.g. 'output_cape')")
    value: int | float | str | bool = Field(default="", description="New value for the parameter")

    # -- sounding_profile fields
    variable: str = Field(default="", description="Sounding column: 'theta', 'qv', 'u', or 'v'")
    operation: str = Field(default="", description="Operation: 'add', 'subtract', 'multiply', or 'set'")
    magnitude: float = Field(default=0.0, description="Numerical magnitude of the change")
    z_min: float = Field(default=0.0, description="Lower height bound in metres")
    z_max: float = Field(default=0.0, description="Upper height bound in metres")
    profile: str = Field(default="", description="Profile shape: 'linear_ramp', 'constant', or 'gaussian'")


class ExperimentSpec(BaseModel):
    """Complete specification for one experiment."""

    experiment_id: str = Field(..., description="Experiment ID from Stage 3 spec (e.g. 'EXP_stability_baseline')")
    description: str = Field(..., description="What this experiment tests")
    is_baseline: bool = Field(default=False, description="Whether this is the baseline experiment")
    feasibility_flag: str = Field(default="OK", description="Feasibility flag from Stage 3")
    edits: list[FileEdit] = Field(default_factory=list, description="Ordered list of file edits for this experiment")


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------


class ExperimentImplementationConfig(ClosedLoopStageConfig):
    """Configuration for Experiment Implementation Agent.

    Subclass and override system_prompt, context_files, tools, and description
    to specialize for a specific domain.
    """

    system_prompt: str = Field(default="")
    model_name: str = Field(default="gpt-5.2")
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(default="medium")
    description: str = Field(default="")


# -----------------------------------------------------------------------------
# Public Input/Output Schemas
# -----------------------------------------------------------------------------


class ExperimentImplementationInputSchema(InputSchema):
    """Input schema for Experiment Implementation Agent."""

    stage_3_spec: str = Field(
        ..., description="Stage-3 workflow specification markdown with experiment matrix and control definition."
    )


class ExperimentImplementationOutputSchema(OutputSchema):
    """Output from the Experiment Implementation Agent.
    Contains the job_id from the MCP job_submit call and an implementation report.
    Use TextOutput for clarification questions or when inputs are insufficient."""

    __response_field__ = "report"
    job_id: str = Field(..., description="Job ID returned by the job_submit MCP tool after submitting experiments.")
    report: str = Field(default="", description="Markdown implementation summary report")


# -----------------------------------------------------------------------------
# Experiment Implementation Agent (Generic)
# -----------------------------------------------------------------------------


class ExperimentImplementationAgent(
    OpenAIBaseAgent[ExperimentImplementationInputSchema, ExperimentImplementationOutputSchema]
):
    """Generic Experiment Implementation Agent.

    Translates Stage-3 workflow specs into structured FileEdit JSON.
    Does NOT create files or execute commands — produces structured output
    that a deterministic engine can execute.

    Subclass or configure with domain-specific system_prompt, context_files, and tools.
    """

    input_schema = ExperimentImplementationInputSchema
    output_schema = ExperimentImplementationOutputSchema | TextOutput
    config_schema = ExperimentImplementationConfig

    def _create_agent(self) -> Agent:
        agent = super()._create_agent()
        return append_context_to_agent(agent, self.config.context_files)

    def check_output(self, output) -> str | None:
        if isinstance(output, ExperimentImplementationOutputSchema):
            if not output.job_id.strip():
                return "job_id is empty. You must call job_submit and include the returned job_id."
            if not output.report.strip():
                return "Report is empty. Provide an implementation summary."
        return super().check_output(output)
