"""Agents module for akd_ext."""

from akd_ext.agents._base import OpenAIBaseAgent, OpenAIBaseAgentConfig
from akd_ext.agents._mixins import FileAttachmentMixin
from akd_ext.agents.astro_search_care import (
    AstroSearchAgent,
    AstroSearchAgentInputSchema,
    AstroSearchAgentOutputSchema,
    AstroSearchConfig,
)
from akd_ext.agents.cmr_care import (
    CMRCareAgent,
    CMRCareAgentInputSchema,
    CMRCareAgentOutputSchema,
    CMRCareConfig,
)
from akd_ext.agents.pds_search_care import (
    PDSSearchAgent,
    PDSSearchAgentInputSchema,
    PDSSearchAgentOutputSchema,
    PDSSearchConfig,
)

from akd_ext.agents.code_search_care import (
    CodeSearchCareAgent,
    CodeSearchCareAgentInputSchema,
    CodeSearchCareAgentOutputSchema,
    CodeSearchCareConfig,
)
from akd_ext.agents.gap import (
    GapAgent,
    GapAgentConfig,
    GapAgentInputSchema,
    GapAgentOutputSchema,
)

from akd_ext.agents.closed_loop_cm1 import (
    CapabilityFeasibilityMapperAgent,
    CapabilityFeasibilityMapperConfig,
    CapabilityFeasibilityMapperInputSchema,
    CapabilityFeasibilityMapperOutputSchema,
    WorkflowSpecBuilderAgent,
    WorkflowSpecBuilderConfig,
    WorkflowSpecBuilderInputSchema,
    WorkflowSpecBuilderOutputSchema,
    ExperimentImplementationAgent,
    ExperimentImplementationConfig,
    ExperimentImplementationInputSchema,
    ExperimentImplementationOutputSchema,
    ResearchReportGeneratorAgent,
    ResearchReportGeneratorConfig,
    ResearchReportGeneratorInputSchema,
    ResearchReportGeneratorOutputSchema,
    # InterpretationPaperAssemblyAgent,
    # InterpretationPaperAssemblyConfig,
    # InterpretationPaperAssemblyInputSchema,
    # InterpretationPaperAssemblyOutputSchema,
)

__all__ = [
    "OpenAIBaseAgent",
    "OpenAIBaseAgentConfig",
    "FileAttachmentMixin",
    "AstroSearchAgent",
    "AstroSearchAgentInputSchema",
    "AstroSearchAgentOutputSchema",
    "AstroSearchConfig",
    "CMRCareAgent",
    "CMRCareAgentInputSchema",
    "CMRCareAgentOutputSchema",
    "CMRCareConfig",
    "CodeSearchCareAgent",
    "CodeSearchCareAgentInputSchema",
    "CodeSearchCareAgentOutputSchema",
    "CodeSearchCareConfig",
    "GapAgent",
    "GapAgentConfig",
    "GapAgentInputSchema",
    "GapAgentOutputSchema",
    "CapabilityFeasibilityMapperAgent",
    "CapabilityFeasibilityMapperConfig",
    "CapabilityFeasibilityMapperInputSchema",
    "CapabilityFeasibilityMapperOutputSchema",
    "WorkflowSpecBuilderAgent",
    "WorkflowSpecBuilderConfig",
    "WorkflowSpecBuilderInputSchema",
    "WorkflowSpecBuilderOutputSchema",
    "ExperimentImplementationAgent",
    "ExperimentImplementationConfig",
    "ExperimentImplementationInputSchema",
    "ExperimentImplementationOutputSchema",
    "ResearchReportGeneratorAgent",
    "ResearchReportGeneratorConfig",
    "ResearchReportGeneratorInputSchema",
    "ResearchReportGeneratorOutputSchema",
    # "InterpretationPaperAssemblyAgent",
    # "InterpretationPaperAssemblyConfig",
    # "InterpretationPaperAssemblyInputSchema",
    # "InterpretationPaperAssemblyOutputSchema",
    "PDSSearchAgent",
    "PDSSearchAgentInputSchema",
    "PDSSearchAgentOutputSchema",
    "PDSSearchConfig",
]
