"""CM1-specialized closed-loop workflow agents.

Each agent is a subclass of the generic stage agent with CM1-specific
system prompts, context files, tools, and descriptions pre-configured.

Public API:
    CM1CapabilityFeasibilityMapperAgent, CM1CapabilityFeasibilityMapperConfig,
    CM1WorkflowSpecBuilderAgent, CM1WorkflowSpecBuilderConfig,
    CM1ExperimentImplementationAgent, CM1ExperimentImplementationConfig,
    CM1ResearchReportGeneratorAgent, CM1ResearchReportGeneratorConfig,
    CM1InterpretationPaperAssemblyAgent, CM1InterpretationPaperAssemblyConfig
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import Field

from akd_ext.agents.closed_loop.cm1.prompts import (
    CAPABILITY_FEASIBILITY_MAPPER_SYSTEM_PROMPT,
    EXPERIMENT_IMPLEMENTER_SYSTEM_PROMPT,
    INTERPRETATION_PAPER_ASSEMBLY_SYSTEM_PROMPT,
    RESEARCH_REPORT_GENERATOR_SYSTEM_PROMPT,
    WORKFLOW_SPEC_BUILDER_SYSTEM_PROMPT,
)
from akd_ext.agents.closed_loop.cm1.tools import get_default_impl_tools, get_default_report_tools
from akd_ext.agents.closed_loop.stages.capability_feasibility_mapper import (
    CapabilityFeasibilityMapperAgent,
    CapabilityFeasibilityMapperConfig,
)
from akd_ext.agents.closed_loop.stages.experiment_implementation import (
    ExperimentImplementationAgent,
    ExperimentImplementationConfig,
)
from akd_ext.agents.closed_loop.stages.interpretation_paper_assembly import (
    InterpretationPaperAssemblyAgent,
    InterpretationPaperAssemblyConfig,
)
from akd_ext.agents.closed_loop.stages.research_report_generator import (
    ResearchReportGeneratorAgent,
    ResearchReportGeneratorConfig,
)
from akd_ext.agents.closed_loop.stages.workflow_spec_builder import (
    WorkflowSpecBuilderAgent,
    WorkflowSpecBuilderConfig,
)

_CONTEXT_DIR = Path(__file__).parent / "context"


def _load_cm1_and_cluster_context() -> dict[str, str]:
    """Load both CM1 README and Cluster IT context files."""
    return {
        "Cluster IT Context": (_CONTEXT_DIR / "cluster_it.md").read_text(),
        "CM1 README Context": (_CONTEXT_DIR / "cm1_readme.md").read_text(),
    }


def _load_cm1_context() -> dict[str, str]:
    """Load CM1 README context file only."""
    return {
        "CM1 README Context": (_CONTEXT_DIR / "cm1_readme.md").read_text(),
    }


# -----------------------------------------------------------------------------
# Stage 2: Capability & Feasibility Mapper
# -----------------------------------------------------------------------------


class CM1CapabilityFeasibilityMapperConfig(CapabilityFeasibilityMapperConfig):
    """CM1-specific configuration for Capability & Feasibility Mapper."""

    system_prompt: str = Field(default=CAPABILITY_FEASIBILITY_MAPPER_SYSTEM_PROMPT)
    context_files: dict[str, str] = Field(default_factory=_load_cm1_and_cluster_context)
    description: str = Field(
        default="Research-analysis agent that evaluates whether research questions and hypotheses can be "
        "realistically tested using available numerical models (CM1, WRF, HWRF, OLAM), codebases, and "
        "cluster resources. Produces structured capability-feasibility assessment reports with evidence "
        "paths and capability vs feasibility matrices. May also produce free-form text responses to "
        "chat with the user for clarification, approval gates, or status updates."
    )


class CM1CapabilityFeasibilityMapperAgent(CapabilityFeasibilityMapperAgent):
    """CM1-specialized Capability & Feasibility Mapper Agent."""

    config_schema = CM1CapabilityFeasibilityMapperConfig


# -----------------------------------------------------------------------------
# Stage 3: Workflow Spec Builder
# -----------------------------------------------------------------------------


class CM1WorkflowSpecBuilderConfig(WorkflowSpecBuilderConfig):
    """CM1-specific configuration for Workflow Spec Builder."""

    system_prompt: str = Field(default=WORKFLOW_SPEC_BUILDER_SYSTEM_PROMPT)
    context_files: dict[str, str] = Field(default_factory=_load_cm1_context)
    description: str = Field(
        default="Stage-3 experiment design agent that converts research questions into scientifically "
        "traceable, feasibility-aware simulation workflow specifications for CM1 or WRF. Proposes "
        "baseline plus perturbation experiments, parameter sweeps, and namelist changes as execution-ready "
        "Markdown documents. May also produce free-form text responses to chat with the user for "
        "clarification, approval gates, or status updates."
    )


class CM1WorkflowSpecBuilderAgent(WorkflowSpecBuilderAgent):
    """CM1-specialized Workflow Spec Builder Agent."""

    config_schema = CM1WorkflowSpecBuilderConfig


# -----------------------------------------------------------------------------
# Stage 4: Experiment Implementation
# -----------------------------------------------------------------------------


class CM1ExperimentImplementationConfig(ExperimentImplementationConfig):
    """CM1-specific configuration for Experiment Implementation."""

    system_prompt: str = Field(default=EXPERIMENT_IMPLEMENTER_SYSTEM_PROMPT)
    context_files: dict[str, str] = Field(default_factory=_load_cm1_context)
    tools: list[Any] = Field(default_factory=get_default_impl_tools)
    description: str = Field(
        default="Stage-4A implementation planner that translates Stage-3 workflow specs into structured "
        "FileEdit JSON and submits experiment batches as jobs via MCP tool calls. Produces deterministic "
        "edit definitions (namelist_param, sounding_profile, file_replace) without directly creating files "
        "or executing commands. May also produce free-form text responses to chat with the user for "
        "clarification, approval gates, or status updates."
    )


class CM1ExperimentImplementationAgent(ExperimentImplementationAgent):
    """CM1-specialized Experiment Implementation Agent."""

    config_schema = CM1ExperimentImplementationConfig


# -----------------------------------------------------------------------------
# Stage 5: Research Report Generator
# -----------------------------------------------------------------------------


class CM1ResearchReportGeneratorConfig(ResearchReportGeneratorConfig):
    """CM1-specific configuration for Research Report Generator."""

    system_prompt: str = Field(default=RESEARCH_REPORT_GENERATOR_SYSTEM_PROMPT)
    tools: list[Any] = Field(default_factory=get_default_report_tools)
    description: str = Field(
        default="Stage-5 report generator that produces publication-style scientific reports interpreting "
        "CM1 experiment results. Checks job status via MCP tools, fetches figure URLs, and generates "
        "Markdown reports with Abstract, Methodology, Results, Discussion, and Conclusion sections. "
        "May also produce free-form text responses to chat with the user for clarification, approval gates, "
        "or status updates."
    )


class CM1ResearchReportGeneratorAgent(ResearchReportGeneratorAgent):
    """CM1-specialized Research Report Generator Agent."""

    config_schema = CM1ResearchReportGeneratorConfig


# -----------------------------------------------------------------------------
# Stage 5 (alt): Interpretation & Paper Assembly
# -----------------------------------------------------------------------------


class CM1InterpretationPaperAssemblyConfig(InterpretationPaperAssemblyConfig):
    """CM1-specific configuration for Interpretation & Paper Assembly."""

    system_prompt: str = Field(default=INTERPRETATION_PAPER_ASSEMBLY_SYSTEM_PROMPT)
    description: str = Field(
        default="Stage-5 interpretation and paper assembly agent that transforms CM1 atmospheric model "
        "experiment outputs into structured scientific analysis artifacts including YAML manifests, "
        "executable Jupyter analysis notebooks, and publication-style Markdown reports with matplotlib figures. "
        "May also produce free-form text responses to chat with the user for clarification, approval gates, "
        "or status updates."
    )


class CM1InterpretationPaperAssemblyAgent(InterpretationPaperAssemblyAgent):
    """CM1-specialized Interpretation & Paper Assembly Agent."""

    config_schema = CM1InterpretationPaperAssemblyConfig
