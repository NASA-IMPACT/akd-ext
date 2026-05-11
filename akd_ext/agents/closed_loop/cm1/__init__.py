"""CM1-specialized closed-loop workflow agents.

Provides CM1-specific subclasses of the generic closed-loop stage agents,
pre-configured with CM1 system prompts, context files, and MCP tools.
"""

from akd_ext.agents.closed_loop.cm1.agents import (
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

__all__ = [
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
]
