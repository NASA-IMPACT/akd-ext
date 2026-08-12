"""Stage-6 Interpretation & Paper Assembly Agent (closed-loop).

Stage 6 is a pure LLM writing agent. It receives the outputs of all prior
stages as text and synthesizes a publication-style scientific report:

- **Stage 1** — hypothesis / feasibility report
- **Stage 3** — workflow spec (experiment design)
- **Stage 4** — implementation report (what experiments were run)
- **Stage 5** — experiment analysis (figure-level analysis markdown)

No MCP calls, no tool use, no filesystem access. The system prompt
(injected by the domain-specific subclass) guides the model to produce
the paper structure.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from agents import Agent

from akd._base import InputSchema, OutputSchema, TextOutput
from akd_ext.agents._base import OpenAIBaseAgent
from akd_ext.agents.closed_loop._base import ClosedLoopStageConfig, append_context_to_agent

__all__ = [
    "InterpretationPaperAssemblyAgent",
    "InterpretationPaperAssemblyConfig",
    "InterpretationPaperAssemblyInputSchema",
    "InterpretationPaperAssemblyOutputSchema",
]


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------


class InterpretationPaperAssemblyConfig(ClosedLoopStageConfig):
    """Configuration for Stage-6 Interpretation & Paper Assembly Agent.

    Subclass and override ``system_prompt``, ``context_files``, and
    ``description`` to specialize for a specific domain.
    """

    system_prompt: str = Field(default="")
    model_name: str = Field(default="gpt-5.2")
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(default="medium")
    description: str = Field(default="")


# -----------------------------------------------------------------------------
# Input / Output Schemas
# -----------------------------------------------------------------------------


class InterpretationPaperAssemblyInputSchema(InputSchema):
    """Input schema for Stage-6 Interpretation & Paper Assembly Agent."""

    hypothesis: str = Field(
        ...,
        description="Stage-1 feasibility report (CapabilityFeasibilityMapper output).",
    )
    experiment_design: str = Field(
        ...,
        description="Stage-3 workflow spec (WorkflowSpecBuilder output).",
    )
    implementation_report: str = Field(
        default="",
        description="Stage-4 implementation report (ExperimentImplementation output).",
    )
    experiment_analysis: str = Field(
        ...,
        description="Stage-5 experiment analysis markdown (ExperimentAnalysis output).",
    )


class InterpretationPaperAssemblyOutputSchema(OutputSchema):
    """Stage-6 structured output — a publication-style scientific report.

    Use TextOutput for clarification questions, approval gates, or when
    inputs are missing.
    """

    __response_field__ = "report"
    report: str = Field(
        default="",
        description="Complete publication-style scientific report in Markdown.",
    )


# -----------------------------------------------------------------------------
# Interpretation & Paper Assembly Agent (Generic)
# -----------------------------------------------------------------------------


class InterpretationPaperAssemblyAgent(
    OpenAIBaseAgent[InterpretationPaperAssemblyInputSchema, InterpretationPaperAssemblyOutputSchema]
):
    """Stage-6 paper assembly agent.

    Takes outputs from Stages 1, 3, 4, and 5 and produces a publication-style
    scientific report. Domain-specific behavior is injected via the system
    prompt and context files in the config.
    """

    input_schema = InterpretationPaperAssemblyInputSchema
    output_schema = InterpretationPaperAssemblyOutputSchema | TextOutput
    config_schema = InterpretationPaperAssemblyConfig

    def _create_agent(self) -> Agent:
        agent = super()._create_agent()
        return append_context_to_agent(agent, self.config.context_files)

    def check_output(self, output) -> str | None:
        if isinstance(output, InterpretationPaperAssemblyOutputSchema) and not output.report.strip():
            return "Report is empty. Provide a complete publication-style scientific report."
        return super().check_output(output)
