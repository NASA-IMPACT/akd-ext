"""Generic closed-loop workflow stage agents.

This package provides parameterized base classes for each stage of a
closed-loop scientific workflow. Specialize them for a domain (CM1, FM, etc.)
by subclassing with domain-specific system prompts, context files, and tools.

See ``akd_ext.agents.closed_loop.cm1`` for the CM1 specialization.
"""

from akd_ext.agents.closed_loop._base import ClosedLoopStageConfig
from akd_ext.agents.closed_loop.capability_feasibility_mapper import (
    CapabilityFeasibilityMapperAgent,
    CapabilityFeasibilityMapperConfig,
    CapabilityFeasibilityMapperInputSchema,
    CapabilityFeasibilityMapperOutputSchema,
)
from akd_ext.agents.closed_loop.experiment_implementation import (
    ExperimentImplementationAgent,
    ExperimentImplementationConfig,
    ExperimentImplementationInputSchema,
    ExperimentImplementationOutputSchema,
    ExperimentSpec,
    FileEdit,
)
from akd_ext.agents.closed_loop.interpretation_paper_assembly import (
    InterpretationPaperAssemblyAgent,
    InterpretationPaperAssemblyConfig,
    InterpretationPaperAssemblyInputSchema,
    InterpretationPaperAssemblyOutputSchema,
)
from akd_ext.agents.closed_loop.research_report_generator import (
    ResearchReportGeneratorAgent,
    ResearchReportGeneratorConfig,
    ResearchReportGeneratorInputSchema,
    ResearchReportGeneratorOutputSchema,
)
from akd_ext.agents.closed_loop.workflow_spec_builder import (
    WorkflowSpecBuilderAgent,
    WorkflowSpecBuilderConfig,
    WorkflowSpecBuilderInputSchema,
    WorkflowSpecBuilderOutputSchema,
)

__all__ = [
    "ClosedLoopStageConfig",
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
    "FileEdit",
    "ExperimentSpec",
    "ResearchReportGeneratorAgent",
    "ResearchReportGeneratorConfig",
    "ResearchReportGeneratorInputSchema",
    "ResearchReportGeneratorOutputSchema",
    "InterpretationPaperAssemblyAgent",
    "InterpretationPaperAssemblyConfig",
    "InterpretationPaperAssemblyInputSchema",
    "InterpretationPaperAssemblyOutputSchema",
]
