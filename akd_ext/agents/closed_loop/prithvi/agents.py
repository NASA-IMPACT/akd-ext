"""FM_Prithvi-specialized closed-loop workflow agents.

Each agent is a subclass of the generic stage agent with FM_Prithvi-specific
system prompts, context files, tools, and descriptions pre-configured.

Public API:
    FMPrithviGapAgent, FMPrithviGapAgentConfig,
    FMPrithviCapabilityFeasibilityMapperAgent, FMPrithviCapabilityFeasibilityMapperConfig,
    FMPrithviWorkflowSpecBuilderAgent, FMPrithviWorkflowSpecBuilderConfig,
    FMPrithviExperimentImplementationAgent, FMPrithviExperimentImplementationConfig,
    FMPrithviResearchReportGeneratorAgent, FMPrithviResearchReportGeneratorConfig,
    FMPrithviInterpretationPaperAssemblyAgent, FMPrithviInterpretationPaperAssemblyConfig
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import Field

from akd_ext.agents.closed_loop.prithvi.prompts import (
    CAPABILITY_FEASIBILITY_MAPPER_SYSTEM_PROMPT,
    EXPERIMENT_IMPLEMENTER_SYSTEM_PROMPT,
    GAP_AGENT_SYSTEM_PROMPT,
    INTERPRETATION_PAPER_ASSEMBLY_SYSTEM_PROMPT,
    RESEARCH_REPORT_GENERATOR_SYSTEM_PROMPT,
    WORKFLOW_SPEC_BUILDER_SYSTEM_PROMPT,
)
from akd_ext.agents.closed_loop.prithvi.tools import get_default_impl_tools, get_default_report_tools
from akd_ext.agents.closed_loop.stages.capability_feasibility_mapper import (
    CapabilityFeasibilityMapperAgent,
    CapabilityFeasibilityMapperConfig,
)
from akd_ext.agents.closed_loop.stages.experiment_implementation import (
    ExperimentImplementationAgent,
    ExperimentImplementationConfig,
)
from akd_ext.agents.gap import (
    GapAgent,
    GapAgentConfig,
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


def _load_prithvi_feasibility_context() -> dict[str, str]:
    """Load Prithvi Capability & Feasibility Mapper context files."""
    return {
        "Pipeline Capability Envelope": (_CONTEXT_DIR / "Pipeline_Capability_Envelope.md").read_text(),
        "Feasibility Mapper Full Process": (_CONTEXT_DIR / "Feasibility_Mapper_Full_Process.md").read_text(),
        "Ancillary Dataset Inventory": (_CONTEXT_DIR / "Ancillary_Dataset_Inventory_Combined.md").read_text(),
        "Stage 2.2 Feasibility/Gap Testing": (_CONTEXT_DIR / "stage2_2_Feasibility_gap_agent_testing.md").read_text(),
    }


def _load_cm1_context() -> dict[str, str]:
    """Load CM1 README context file only."""
    return {
        "CM1 README Context": (_CONTEXT_DIR / "cm1_readme.md").read_text(),
    }


def _load_prithvi_gap_agent_context() -> dict[str, str]:
    """Load Prithvi Gap Agent context files."""
    return {
        "Stage 2.2 Gap Agent Context": (_CONTEXT_DIR / "Stage_2_2_Gap_Agent_Context_Modified.md").read_text(),
        "Pipeline Capability Envelope": (_CONTEXT_DIR / "Pipeline_Capability_Envelope.md").read_text(),
    }


def _load_prithvi_workflow_spec_context() -> dict[str, str]:
    """Load Prithvi Workflow Spec Builder context files."""
    return {
        "Workflow Spec Builder Full Process": (_CONTEXT_DIR / "Workflow_Spec_Builder_Full_Process.md").read_text(),
        "Workflow Spec Config Schema": (_CONTEXT_DIR / "Workflow_Spec_Config_Schema.md").read_text(),
        "Pipeline Capability Envelope": (_CONTEXT_DIR / "Pipeline_Capability_Envelope.md").read_text(),
        "Ancillary Dataset Inventory": (_CONTEXT_DIR / "Ancillary_Dataset_Inventory_Combined.md").read_text(),
        "Stage 2.2 Workflow Spec Builder": (_CONTEXT_DIR / "stage2_2_Worksflow_spec_builder.md").read_text(),
    }


# -----------------------------------------------------------------------------
# Stage 1: Gap Agent
# -----------------------------------------------------------------------------


class FMPrithviGapAgentConfig(GapAgentConfig):
    """FM_Prithvi-specific configuration for Gap Agent."""

    system_prompt: str = Field(default=GAP_AGENT_SYSTEM_PROMPT)
    context_files: dict[str, str] = Field(default_factory=_load_prithvi_gap_agent_context)
    description: str = Field(
        default="Stage-1 Research Gap Detection & Synthesis agent for the FM_Prithvi pipeline. Identifies "
        "defensible research gaps, contradictions, and candidate research questions strictly within a "
        "user-provided corpus of academic papers, with paragraph-level traceability and explicit uncertainty. "
        "Frames RQs concretely enough (variables, proxies, spatial/temporal scope) for the downstream "
        "Capability & Feasibility Mapper, but does not assess feasibility or filter by pipeline capability. "
        "May also produce free-form text responses to chat with the user for clarification, approval gates, "
        "or status updates."
    )


class FMPrithviGapAgent(GapAgent):
    """FM_Prithvi-specialized Gap Agent."""

    config_schema = FMPrithviGapAgentConfig


# -----------------------------------------------------------------------------
# Stage 2: Capability & Feasibility Mapper
# -----------------------------------------------------------------------------


class FMPrithviCapabilityFeasibilityMapperConfig(CapabilityFeasibilityMapperConfig):
    """FM_Prithvi-specific configuration for Capability & Feasibility Mapper."""

    system_prompt: str = Field(default=CAPABILITY_FEASIBILITY_MAPPER_SYSTEM_PROMPT)
    context_files: dict[str, str] = Field(default_factory=_load_prithvi_feasibility_context)
    description: str = Field(
        default="Capability & Feasibility Assessment agent for the Prithvi geospatial foundation-model "
        "pipeline. Maps approved research questions to atomic capability requirements across 5 dimensions, "
        "matches each requirement to a specific tool from the Pipeline Capability Envelope (Prithvi Tier 1 "
        "downstreams, region-aware baselines, NDVI severity, ancillary datasets, 86 statistical tests), "
        "and produces Go / Conditional-Go / No-Go recommendations with execution checklists. May also "
        "produce free-form text responses to chat with the user for clarification, approval gates, or "
        "status updates."
    )


class FMPrithviCapabilityFeasibilityMapperAgent(CapabilityFeasibilityMapperAgent):
    """FM_Prithvi-specialized Capability & Feasibility Mapper Agent."""

    config_schema = FMPrithviCapabilityFeasibilityMapperConfig


# -----------------------------------------------------------------------------
# Stage 3: Workflow Spec Builder
# -----------------------------------------------------------------------------


class FMPrithviWorkflowSpecBuilderConfig(WorkflowSpecBuilderConfig):
    """FM_Prithvi-specific configuration for Workflow Spec Builder."""

    system_prompt: str = Field(default=WORKFLOW_SPEC_BUILDER_SYSTEM_PROMPT)
    context_files: dict[str, str] = Field(default_factory=_load_prithvi_workflow_spec_context)
    description: str = Field(
        default="Stage-3 Workflow Spec Builder for the Prithvi geospatial foundation-model pipeline. "
        "Translates approved research questions and feasibility handoff packages into atomic, ordered "
        "workflow steps, region-aware data acquisition plans, and validation strategies, then compiles "
        "them into an execution-ready Markdown spec plus a machine-readable pipeline config YAML matching "
        "the executor schema. May also produce free-form text responses to chat with the user for "
        "clarification, approval gates, or status updates."
    )


class FMPrithviWorkflowSpecBuilderAgent(WorkflowSpecBuilderAgent):
    """FM_Prithvi-specialized Workflow Spec Builder Agent."""

    config_schema = FMPrithviWorkflowSpecBuilderConfig


# -----------------------------------------------------------------------------
# Stage 4: Experiment Implementation
# -----------------------------------------------------------------------------


class FMPrithviExperimentImplementationConfig(ExperimentImplementationConfig):
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


class FMPrithviExperimentImplementationAgent(ExperimentImplementationAgent):
    """CM1-specialized Experiment Implementation Agent."""

    config_schema = FMPrithviExperimentImplementationConfig


# -----------------------------------------------------------------------------
# Stage 5: Research Report Generator
# -----------------------------------------------------------------------------


class FMPrithviResearchReportGeneratorConfig(ResearchReportGeneratorConfig):
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


class FMPrithviResearchReportGeneratorAgent(ResearchReportGeneratorAgent):
    """CM1-specialized Research Report Generator Agent."""

    config_schema = FMPrithviResearchReportGeneratorConfig


# -----------------------------------------------------------------------------
# Stage 5 (alt): Interpretation & Paper Assembly
# -----------------------------------------------------------------------------


class FMPrithviInterpretationPaperAssemblyConfig(InterpretationPaperAssemblyConfig):
    """CM1-specific configuration for Interpretation & Paper Assembly."""

    system_prompt: str = Field(default=INTERPRETATION_PAPER_ASSEMBLY_SYSTEM_PROMPT)
    description: str = Field(
        default="Stage-5 interpretation and paper assembly agent that transforms CM1 atmospheric model "
        "experiment outputs into structured scientific analysis artifacts including YAML manifests, "
        "executable Jupyter analysis notebooks, and publication-style Markdown reports with matplotlib figures. "
        "May also produce free-form text responses to chat with the user for clarification, approval gates, "
        "or status updates."
    )


class FMPrithviInterpretationPaperAssemblyAgent(InterpretationPaperAssemblyAgent):
    """CM1-specialized Interpretation & Paper Assembly Agent."""

    config_schema = FMPrithviInterpretationPaperAssemblyConfig
