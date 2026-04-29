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

from akd_ext.agents.gap import (
    GapAgent,
    GapAgentConfig,
    GapAgentInputSchema,
    GapAgentOutputSchema,
)

from akd_ext.agents.image_analyzer import (
    FigureAnalysis,
    ImageAnalyzerAgent,
    ImageAnalyzerConfig,
    ImageAnalyzerInputSchema,
    ImageAnalyzerOutputSchema,
)

from akd_ext.agents.closed_loop.cm1 import (
    CM1CapabilityFeasibilityMapperAgent,
    CM1CapabilityFeasibilityMapperConfig,
    CM1ExperimentImplementationAgent,
    CM1ExperimentImplementationConfig,
    CM1InterpretationPaperAssemblyAgent,
    CM1InterpretationPaperAssemblyConfig,
    CM1ResearchReportGeneratorAgent,
    CM1ResearchReportGeneratorConfig,
    CM1WorkflowSpecBuilderAgent,
    CM1WorkflowSpecBuilderConfig,
)

# Backward-compatible aliases for the old names
CapabilityFeasibilityMapperAgent = CM1CapabilityFeasibilityMapperAgent
CapabilityFeasibilityMapperConfig = CM1CapabilityFeasibilityMapperConfig
WorkflowSpecBuilderAgent = CM1WorkflowSpecBuilderAgent
WorkflowSpecBuilderConfig = CM1WorkflowSpecBuilderConfig
ExperimentImplementationAgent = CM1ExperimentImplementationAgent
ExperimentImplementationConfig = CM1ExperimentImplementationConfig
ResearchReportGeneratorAgent = CM1ResearchReportGeneratorAgent
ResearchReportGeneratorConfig = CM1ResearchReportGeneratorConfig

# Re-export input/output schemas from generic modules
from akd_ext.agents.closed_loop.stages.capability_feasibility_mapper import (  # noqa: E402
    CapabilityFeasibilityMapperInputSchema,
    CapabilityFeasibilityMapperOutputSchema,
)
from akd_ext.agents.closed_loop.stages.experiment_implementation import (  # noqa: E402
    ExperimentImplementationInputSchema,
    ExperimentImplementationOutputSchema,
)
from akd_ext.agents.closed_loop.stages.research_report_generator import (  # noqa: E402
    ResearchReportGeneratorInputSchema,
    ResearchReportGeneratorOutputSchema,
)
from akd_ext.agents.closed_loop.stages.workflow_spec_builder import (  # noqa: E402
    WorkflowSpecBuilderInputSchema,
    WorkflowSpecBuilderOutputSchema,
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
    "GapAgent",
    "GapAgentConfig",
    "GapAgentInputSchema",
    "GapAgentOutputSchema",
    # Generic image analyzer
    "ImageAnalyzerAgent",
    "ImageAnalyzerConfig",
    "ImageAnalyzerInputSchema",
    "ImageAnalyzerOutputSchema",
    "FigureAnalysis",
    # CM1-specialized agents
    "CM1CapabilityFeasibilityMapperAgent",
    "CM1CapabilityFeasibilityMapperConfig",
    "CM1WorkflowSpecBuilderAgent",
    "CM1WorkflowSpecBuilderConfig",
    "CM1ExperimentImplementationAgent",
    "CM1ExperimentImplementationConfig",
    "CM1ResearchReportGeneratorAgent",
    "CM1ResearchReportGeneratorConfig",
    "CM1InterpretationPaperAssemblyAgent",
    "CM1InterpretationPaperAssemblyConfig",
    # Backward-compatible aliases
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
    "PDSSearchAgent",
    "PDSSearchAgentInputSchema",
    "PDSSearchAgentOutputSchema",
    "PDSSearchConfig",
]
