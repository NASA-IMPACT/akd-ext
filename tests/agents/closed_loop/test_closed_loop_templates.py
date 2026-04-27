"""Unit tests for the closed-loop templates architecture.

These tests verify the template structure, inheritance, config defaults,
schema validation, context loading, and check_output logic — all without
making any GPT/API calls.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from akd_ext.agents._base import OpenAIBaseAgentConfig
from akd_ext.agents.closed_loop._base import ClosedLoopStageConfig, append_context_to_agent

# -- Generic stage classes --
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

# -- CM1-specialized classes --
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


# =============================================================================
# A. Import & Structure Tests
# =============================================================================


class TestImports:
    """Verify all modules are importable from the expected paths."""

    @pytest.mark.unit
    def test_generic_classes_importable_from_closed_loop(self):
        """Generic stage classes are importable from akd_ext.agents.closed_loop."""
        from akd_ext.agents.closed_loop import (
            CapabilityFeasibilityMapperAgent,
            WorkflowSpecBuilderAgent,
            ExperimentImplementationAgent,
            ResearchReportGeneratorAgent,
            InterpretationPaperAssemblyAgent,
        )

        assert CapabilityFeasibilityMapperAgent is not None
        assert WorkflowSpecBuilderAgent is not None
        assert ExperimentImplementationAgent is not None
        assert ResearchReportGeneratorAgent is not None
        assert InterpretationPaperAssemblyAgent is not None

    @pytest.mark.unit
    def test_cm1_classes_importable_from_closed_loop_cm1(self):
        """CM1 classes are importable from akd_ext.agents.closed_loop.cm1."""
        from akd_ext.agents.closed_loop.cm1 import (
            CM1CapabilityFeasibilityMapperAgent,
            CM1WorkflowSpecBuilderAgent,
            CM1ExperimentImplementationAgent,
            CM1ResearchReportGeneratorAgent,
            CM1InterpretationPaperAssemblyAgent,
        )

        assert CM1CapabilityFeasibilityMapperAgent is not None
        assert CM1WorkflowSpecBuilderAgent is not None
        assert CM1ExperimentImplementationAgent is not None
        assert CM1ResearchReportGeneratorAgent is not None
        assert CM1InterpretationPaperAssemblyAgent is not None


# =============================================================================
# B. Inheritance Tests
# =============================================================================

_GENERIC_TO_CM1_AGENTS = [
    (CapabilityFeasibilityMapperAgent, CM1CapabilityFeasibilityMapperAgent),
    (WorkflowSpecBuilderAgent, CM1WorkflowSpecBuilderAgent),
    (ExperimentImplementationAgent, CM1ExperimentImplementationAgent),
    (ResearchReportGeneratorAgent, CM1ResearchReportGeneratorAgent),
    (InterpretationPaperAssemblyAgent, CM1InterpretationPaperAssemblyAgent),
]

_GENERIC_TO_CM1_CONFIGS = [
    (CapabilityFeasibilityMapperConfig, CM1CapabilityFeasibilityMapperConfig),
    (WorkflowSpecBuilderConfig, CM1WorkflowSpecBuilderConfig),
    (ExperimentImplementationConfig, CM1ExperimentImplementationConfig),
    (ResearchReportGeneratorConfig, CM1ResearchReportGeneratorConfig),
    (InterpretationPaperAssemblyConfig, CM1InterpretationPaperAssemblyConfig),
]


class TestInheritance:
    """Verify the class hierarchy is correct."""

    @pytest.mark.unit
    @pytest.mark.parametrize("generic_cls,cm1_cls", _GENERIC_TO_CM1_AGENTS)
    def test_cm1_agent_subclasses_generic(self, generic_cls, cm1_cls):
        assert issubclass(cm1_cls, generic_cls)

    @pytest.mark.unit
    @pytest.mark.parametrize("generic_cls,cm1_cls", _GENERIC_TO_CM1_CONFIGS)
    def test_cm1_config_subclasses_generic(self, generic_cls, cm1_cls):
        assert issubclass(cm1_cls, generic_cls)

    @pytest.mark.unit
    @pytest.mark.parametrize("generic_cls,_", _GENERIC_TO_CM1_CONFIGS)
    def test_generic_config_subclasses_closed_loop_stage_config(self, generic_cls, _):
        assert issubclass(generic_cls, ClosedLoopStageConfig)

    @pytest.mark.unit
    def test_closed_loop_stage_config_subclasses_openai_base(self):
        assert issubclass(ClosedLoopStageConfig, OpenAIBaseAgentConfig)


# =============================================================================
# C. Config Tests
# =============================================================================


class TestGenericConfigDefaults:
    """Generic configs should have empty system_prompt by default."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "config_cls",
        [
            CapabilityFeasibilityMapperConfig,
            WorkflowSpecBuilderConfig,
            ExperimentImplementationConfig,
            ResearchReportGeneratorConfig,
            InterpretationPaperAssemblyConfig,
        ],
    )
    def test_generic_config_empty_system_prompt(self, config_cls):
        config = config_cls()
        assert config.system_prompt == ""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "config_cls",
        [
            CapabilityFeasibilityMapperConfig,
            WorkflowSpecBuilderConfig,
            ExperimentImplementationConfig,
            ResearchReportGeneratorConfig,
            InterpretationPaperAssemblyConfig,
        ],
    )
    def test_generic_config_empty_context_files(self, config_cls):
        config = config_cls()
        assert config.context_files == {}

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "config_cls",
        [
            CapabilityFeasibilityMapperConfig,
            WorkflowSpecBuilderConfig,
            ExperimentImplementationConfig,
            ResearchReportGeneratorConfig,
            InterpretationPaperAssemblyConfig,
        ],
    )
    def test_generic_config_model_defaults(self, config_cls):
        config = config_cls()
        assert config.model_name == "gpt-5.2"
        assert config.reasoning_effort == "medium"


class TestCM1ConfigDefaults:
    """CM1 configs should have CM1-specific defaults populated."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "config_cls",
        [
            CM1CapabilityFeasibilityMapperConfig,
            CM1WorkflowSpecBuilderConfig,
            CM1ExperimentImplementationConfig,
            CM1ResearchReportGeneratorConfig,
            CM1InterpretationPaperAssemblyConfig,
        ],
    )
    def test_cm1_config_has_system_prompt(self, config_cls):
        config = config_cls()
        assert config.system_prompt != ""
        assert len(config.system_prompt) > 100  # Prompts are substantial

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "config_cls",
        [
            CM1CapabilityFeasibilityMapperConfig,
            CM1WorkflowSpecBuilderConfig,
            CM1ExperimentImplementationConfig,
        ],
    )
    def test_cm1_config_has_context_files(self, config_cls):
        config = config_cls()
        assert len(config.context_files) > 0
        assert "CM1 README Context" in config.context_files
        assert len(config.context_files["CM1 README Context"]) > 0

    @pytest.mark.unit
    def test_cm1_cfm_config_has_cluster_context(self):
        config = CM1CapabilityFeasibilityMapperConfig()
        assert "Cluster IT Context" in config.context_files
        assert len(config.context_files["Cluster IT Context"]) > 0

    @pytest.mark.unit
    def test_cm1_report_config_has_no_context_files(self):
        """Research report generator and interpretation don't load context files."""
        config = CM1ResearchReportGeneratorConfig()
        assert config.context_files == {}

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "config_cls",
        [
            CM1CapabilityFeasibilityMapperConfig,
            CM1WorkflowSpecBuilderConfig,
            CM1ExperimentImplementationConfig,
            CM1ResearchReportGeneratorConfig,
            CM1InterpretationPaperAssemblyConfig,
        ],
    )
    def test_cm1_config_has_description(self, config_cls):
        config = config_cls()
        assert config.description != ""


# =============================================================================
# D. Schema Tests
# =============================================================================


class TestInputSchemas:
    """Verify input schemas validate correctly."""

    @pytest.mark.unit
    def test_cfm_input_valid(self):
        schema = CapabilityFeasibilityMapperInputSchema(research_questions_md="RQ-001: test question")
        assert schema.research_questions_md == "RQ-001: test question"

    @pytest.mark.unit
    def test_cfm_input_missing_required(self):
        with pytest.raises(ValidationError):
            CapabilityFeasibilityMapperInputSchema()

    @pytest.mark.unit
    def test_wsb_input_valid(self):
        schema = WorkflowSpecBuilderInputSchema(
            stage_1_hypotheses="hypotheses text",
            stage_2_feasibility="feasibility text",
        )
        assert schema.stage_1_hypotheses == "hypotheses text"
        assert schema.stage_2_feasibility == "feasibility text"

    @pytest.mark.unit
    def test_wsb_input_missing_stage_2(self):
        with pytest.raises(ValidationError):
            WorkflowSpecBuilderInputSchema(stage_1_hypotheses="hypotheses text")

    @pytest.mark.unit
    def test_exp_impl_input_valid(self):
        schema = ExperimentImplementationInputSchema(stage_3_spec="spec markdown")
        assert schema.stage_3_spec == "spec markdown"

    @pytest.mark.unit
    def test_report_gen_input_valid(self):
        schema = ResearchReportGeneratorInputSchema(workflow_spec="spec", job_id="job-123")
        assert schema.job_id == "job-123"

    @pytest.mark.unit
    def test_report_gen_input_missing_job_id(self):
        with pytest.raises(ValidationError):
            ResearchReportGeneratorInputSchema(workflow_spec="spec")

    @pytest.mark.unit
    def test_interp_input_valid(self):
        schema = InterpretationPaperAssemblyInputSchema(
            research_question="question",
            experiment_output_dir="/tmp/output",
        )
        assert schema.figures_dir is None  # Optional

    @pytest.mark.unit
    def test_interp_input_with_figures_dir(self):
        schema = InterpretationPaperAssemblyInputSchema(
            research_question="question",
            experiment_output_dir="/tmp/output",
            figures_dir="/tmp/figures",
        )
        assert schema.figures_dir == "/tmp/figures"


class TestOutputSchemas:
    """Verify output schemas instantiate with defaults."""

    @pytest.mark.unit
    def test_cfm_output_defaults(self):
        schema = CapabilityFeasibilityMapperOutputSchema()
        assert schema.report == ""

    @pytest.mark.unit
    def test_wsb_output_defaults(self):
        schema = WorkflowSpecBuilderOutputSchema()
        assert schema.spec == ""
        assert schema.reasoning == ""

    @pytest.mark.unit
    def test_exp_impl_output(self):
        schema = ExperimentImplementationOutputSchema(job_id="job-123")
        assert schema.job_id == "job-123"
        assert schema.report == ""

    @pytest.mark.unit
    def test_report_gen_output_defaults(self):
        schema = ResearchReportGeneratorOutputSchema()
        assert schema.report == ""

    @pytest.mark.unit
    def test_interp_output_defaults(self):
        schema = InterpretationPaperAssemblyOutputSchema()
        assert schema.report == ""


# =============================================================================
# E. Context File Loading & append_context_to_agent Tests
# =============================================================================


class TestContextLoading:
    """Verify context files load and append_context_to_agent works."""

    @pytest.mark.unit
    def test_cm1_readme_context_loads(self):
        config = CM1CapabilityFeasibilityMapperConfig()
        cm1_readme = config.context_files.get("CM1 README Context", "")
        assert len(cm1_readme) > 1000  # Large file (~315KB)

    @pytest.mark.unit
    def test_cluster_it_context_loads(self):
        config = CM1CapabilityFeasibilityMapperConfig()
        cluster_it = config.context_files.get("Cluster IT Context", "")
        assert len(cluster_it) > 100  # ~6KB file

    @pytest.mark.unit
    def test_append_context_to_agent_adds_sections(self):
        """append_context_to_agent appends labeled sections to instructions."""
        mock_agent = MagicMock()
        mock_agent.instructions = "Base instructions."

        context = {
            "Section A": "Content A",
            "Section B": "Content B",
        }

        result = append_context_to_agent(mock_agent, context)

        assert result is mock_agent
        assert "## Section A" in mock_agent.instructions
        assert "Content A" in mock_agent.instructions
        assert "## Section B" in mock_agent.instructions
        assert "Content B" in mock_agent.instructions
        assert mock_agent.instructions.startswith("Base instructions.")

    @pytest.mark.unit
    def test_append_context_to_agent_skips_empty(self):
        """Empty context values are skipped."""
        mock_agent = MagicMock()
        mock_agent.instructions = "Base."

        context = {
            "Filled": "Content here",
            "Empty": "",
        }

        append_context_to_agent(mock_agent, context)

        assert "## Filled" in mock_agent.instructions
        assert "## Empty" not in mock_agent.instructions

    @pytest.mark.unit
    def test_append_context_to_agent_empty_dict(self):
        """Empty context_files dict leaves instructions unchanged."""
        mock_agent = MagicMock()
        mock_agent.instructions = "Base only."

        append_context_to_agent(mock_agent, {})

        assert mock_agent.instructions == "Base only."


# =============================================================================
# F. check_output() Tests
# =============================================================================


class TestCheckOutput:
    """Verify check_output returns error for empty reports and None for valid ones."""

    @pytest.mark.unit
    def test_cfm_check_output_empty_report(self):
        agent = CapabilityFeasibilityMapperAgent(config=CapabilityFeasibilityMapperConfig(system_prompt="test"))
        output = CapabilityFeasibilityMapperOutputSchema(report="")
        result = agent.check_output(output)
        assert result is not None
        assert "empty" in result.lower()

    @pytest.mark.unit
    def test_cfm_check_output_valid_report(self):
        agent = CapabilityFeasibilityMapperAgent(config=CapabilityFeasibilityMapperConfig(system_prompt="test"))
        output = CapabilityFeasibilityMapperOutputSchema(report="A valid feasibility report.")
        result = agent.check_output(output)
        assert result is None

    @pytest.mark.unit
    def test_wsb_check_output_empty_spec(self):
        agent = WorkflowSpecBuilderAgent(config=WorkflowSpecBuilderConfig(system_prompt="test"))
        output = WorkflowSpecBuilderOutputSchema(spec="", reasoning="some reasoning")
        result = agent.check_output(output)
        assert result is not None
        assert "empty" in result.lower()

    @pytest.mark.unit
    def test_wsb_check_output_valid_spec(self):
        agent = WorkflowSpecBuilderAgent(config=WorkflowSpecBuilderConfig(system_prompt="test"))
        output = WorkflowSpecBuilderOutputSchema(spec="# Metadata\n...", reasoning="reasoning")
        result = agent.check_output(output)
        assert result is None

    @pytest.mark.unit
    def test_exp_impl_check_output_empty_job_id(self):
        agent = ExperimentImplementationAgent(config=ExperimentImplementationConfig(system_prompt="test"))
        output = ExperimentImplementationOutputSchema(job_id="", report="some report")
        result = agent.check_output(output)
        assert result is not None
        assert "job_id" in result.lower()

    @pytest.mark.unit
    def test_exp_impl_check_output_empty_report(self):
        agent = ExperimentImplementationAgent(config=ExperimentImplementationConfig(system_prompt="test"))
        output = ExperimentImplementationOutputSchema(job_id="job-123", report="")
        result = agent.check_output(output)
        assert result is not None
        assert "empty" in result.lower()

    @pytest.mark.unit
    def test_exp_impl_check_output_valid(self):
        agent = ExperimentImplementationAgent(config=ExperimentImplementationConfig(system_prompt="test"))
        output = ExperimentImplementationOutputSchema(job_id="job-123", report="Implementation summary")
        result = agent.check_output(output)
        assert result is None

    @pytest.mark.unit
    def test_report_gen_check_output_empty(self):
        agent = ResearchReportGeneratorAgent(config=ResearchReportGeneratorConfig(system_prompt="test"))
        output = ResearchReportGeneratorOutputSchema(report="")
        result = agent.check_output(output)
        assert result is not None

    @pytest.mark.unit
    def test_report_gen_check_output_valid(self):
        agent = ResearchReportGeneratorAgent(config=ResearchReportGeneratorConfig(system_prompt="test"))
        output = ResearchReportGeneratorOutputSchema(report="# Abstract\n...")
        result = agent.check_output(output)
        assert result is None

    @pytest.mark.unit
    def test_interp_check_output_empty(self):
        agent = InterpretationPaperAssemblyAgent(config=InterpretationPaperAssemblyConfig(system_prompt="test"))
        output = InterpretationPaperAssemblyOutputSchema(report="")
        result = agent.check_output(output)
        assert result is not None

    @pytest.mark.unit
    def test_interp_check_output_valid(self):
        agent = InterpretationPaperAssemblyAgent(config=InterpretationPaperAssemblyConfig(system_prompt="test"))
        output = InterpretationPaperAssemblyOutputSchema(report="Artifacts created successfully.")
        result = agent.check_output(output)
        assert result is None


# =============================================================================
# G. Data Model Tests
# =============================================================================


class TestDataModels:
    """Verify FileEdit and ExperimentSpec data models."""

    @pytest.mark.unit
    def test_file_edit_namelist_param(self):
        edit = FileEdit(
            target_file="namelist.input",
            edit_type="namelist_param",
            namelist_group="param9",
            parameter="output_cape",
            value=1,
        )
        assert edit.edit_type == "namelist_param"
        assert edit.value == 1

    @pytest.mark.unit
    def test_file_edit_sounding_profile(self):
        edit = FileEdit(
            target_file="input_sounding",
            edit_type="sounding_profile",
            variable="theta",
            operation="add",
            magnitude=2.0,
            z_min=1500.0,
            z_max=12000.0,
            profile="linear_ramp",
        )
        assert edit.edit_type == "sounding_profile"
        assert edit.magnitude == 2.0

    @pytest.mark.unit
    def test_experiment_spec(self):
        spec = ExperimentSpec(
            experiment_id="EXP_test_baseline",
            description="Baseline experiment",
            is_baseline=True,
            edits=[
                FileEdit(target_file="namelist.input", edit_type="namelist_param", parameter="output_cape", value=1),
            ],
        )
        assert spec.is_baseline is True
        assert len(spec.edits) == 1
        assert spec.feasibility_flag == "OK"
