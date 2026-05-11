"""Generic closed-loop workflow stage agents.

This package provides parameterized base classes for each stage of a
closed-loop scientific workflow. Specialize them for a domain (CM1, FM, etc.)
by subclassing with domain-specific system prompts, context files, and tools.

Layout:

- ``_base``: shared config + helper (``ClosedLoopStageConfig``, ``append_context_to_agent``)
- ``stages/``: generic stage classes (schemas + logic), no domain references
- ``cm1/``: CM1 specialization (prompts, context, tools)

See ``akd_ext.agents.closed_loop.cm1`` for the CM1 specialization.
"""

from akd_ext.agents.closed_loop._base import ClosedLoopStageConfig
from akd_ext.agents.closed_loop.stages import (
    CapabilityFeasibilityMapperAgent,
    CapabilityFeasibilityMapperConfig,
    CapabilityFeasibilityMapperInputSchema,
    CapabilityFeasibilityMapperOutputSchema,
    ExperimentImplementationAgent,
    ExperimentImplementationConfig,
    ExperimentImplementationInputSchema,
    ExperimentImplementationOutputSchema,
    ExperimentSpec,
    FileEdit,
    InterpretationPaperAssemblyAgent,
    InterpretationPaperAssemblyConfig,
    InterpretationPaperAssemblyInputSchema,
    InterpretationPaperAssemblyOutputSchema,
    ResearchReportGeneratorAgent,
    ResearchReportGeneratorConfig,
    ResearchReportGeneratorInputSchema,
    ResearchReportGeneratorOutputSchema,
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
