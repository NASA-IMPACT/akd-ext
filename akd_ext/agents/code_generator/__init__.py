"""Code Generator Pipeline — design → generate → validate → retry.

Public API:

    Pipeline (top-level entry point):
        CodeGeneratorPipeline, CodeGeneratorPipelineConfig

    Sub-agents (usable standalone):
        CodeDesignerAgent, CodeDesignerConfig
        CodeGeneratorAgent, CodeGeneratorConfig
        IntentCheckerAgent, IntentCheckerConfig

    Schemas:
        CodeGeneratorPipelineInputSchema, CodeGeneratorPipelineOutputSchema
        CodeDesignerInputSchema, CodeDesignerOutputSchema
        CodeGeneratorInputSchema, CodeGeneratorOutputSchema
        IntentCheckerInputSchema, IntentCheckerOutputSchema
        VettedCode, ValidationResult

    Code Validators (pure functions):
        ALLOWED_IMPORTS, check_allowlist, check_bandit
"""

from __future__ import annotations

from akd_ext.agents.code_generator.validator import (
    ALLOWED_IMPORTS,
    AllowlistResult,
    BanditResult,
    IntentCheckerAgent,
    IntentCheckerConfig,
    check_allowlist,
    check_bandit,
)
from akd_ext.agents.code_generator.schemas import (
    CodeDesignerInputSchema,
    FigurePlan,
    CodeDesignerOutputSchema,
    CodeGeneratorInputSchema,
    CodeGeneratorOutputSchema,
    CodeGeneratorPipelineInputSchema,
    CodeGeneratorPipelineOutputSchema,
    IntentCheckerInputSchema,
    IntentCheckerOutputSchema,
    ValidationResult,
    VettedCode,
)
from akd_ext.agents.code_generator.designer import (
    CodeDesignerAgent,
    CodeDesignerConfig,
    render_figure_plan,
)
from akd_ext.agents.code_generator.generator import (
    CodeGeneratorAgent,
    CodeGeneratorConfig,
)
from akd_ext.agents.code_generator.code_gen import (
    CodeGeneratorPipeline,
    CodeGeneratorPipelineConfig,
)

__all__ = [
    # Pipeline
    "CodeGeneratorPipeline",
    "CodeGeneratorPipelineConfig",
    # Sub-agents
    "CodeDesignerAgent",
    "CodeDesignerConfig",
    "CodeGeneratorAgent",
    "CodeGeneratorConfig",
    "IntentCheckerAgent",
    "IntentCheckerConfig",
    # Schemas
    "CodeGeneratorPipelineInputSchema",
    "CodeGeneratorPipelineOutputSchema",
    "CodeDesignerInputSchema",
    "CodeDesignerOutputSchema",
    "CodeGeneratorInputSchema",
    "CodeGeneratorOutputSchema",
    "IntentCheckerInputSchema",
    "IntentCheckerOutputSchema",
    "VettedCode",
    "ValidationResult",
    "FigurePlan",
    "render_figure_plan",
    # Code Validators
    "ALLOWED_IMPORTS",
    "AllowlistResult",
    "BanditResult",
    "check_allowlist",
    "check_bandit",
]
