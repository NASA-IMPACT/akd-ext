"""Generic closed-loop workflow stages.

Each module defines the parameterized base class for one stage of the
closed-loop pipeline: schemas, validation, and agent wiring — without any
domain-specific prompts, context, or tools. Domain packages (e.g.
``akd_ext.agents.closed_loop.cm1``) subclass these and inject specialization
via config defaults.
"""

from akd_ext.agents.closed_loop.stages.capability_feasibility_mapper import (
    CapabilityFeasibilityMapperAgent,
    CapabilityFeasibilityMapperConfig,
    CapabilityFeasibilityMapperInputSchema,
    CapabilityFeasibilityMapperOutputSchema,
)
from akd_ext.agents.closed_loop.stages.experiment_implementation import (
    ExperimentImplementationAgent,
    ExperimentImplementationConfig,
    ExperimentImplementationInputSchema,
    ExperimentImplementationOutputSchema,
    ExperimentSpec,
    FileEdit,
)
from akd_ext.agents.closed_loop.stages.interpretation_paper_assembly import (
    InterpretationPaperAssemblyAgent,
    InterpretationPaperAssemblyConfig,
    InterpretationPaperAssemblyInputSchema,
    InterpretationPaperAssemblyOutputSchema,
)
from akd_ext.agents.closed_loop.stages.research_report_generator import (
    ResearchReportGeneratorAgent,
    ResearchReportGeneratorConfig,
    ResearchReportGeneratorInputSchema,
    ResearchReportGeneratorOutputSchema,
)
from akd_ext.agents.closed_loop.stages.workflow_spec_builder import (
    WorkflowSpecBuilderAgent,
    WorkflowSpecBuilderConfig,
    WorkflowSpecBuilderInputSchema,
    WorkflowSpecBuilderOutputSchema,
)

__all__ = [
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
]
