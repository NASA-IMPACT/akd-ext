"""Unit tests for the Prithvi closed-loop stage agents.

Verifies instantiation, config defaults, context file loading, tool
availability, prompt content, and schema compatibility — all without
making any GPT/API calls.
"""

from __future__ import annotations


# ── Stage 1: Gap Agent ──────────────────────────────────────────────────


class TestStage1GapAgent:
    def test_instantiation(self):
        from akd_ext.agents.closed_loop.prithvi import FMPrithviGapAgent, FMPrithviGapAgentConfig

        agent = FMPrithviGapAgent(FMPrithviGapAgentConfig())
        assert agent is not None

    def test_config_defaults(self):
        from akd_ext.agents.closed_loop.prithvi import FMPrithviGapAgentConfig

        cfg = FMPrithviGapAgentConfig()
        assert cfg.model_name == "gpt-5.2"
        assert cfg.reasoning_effort == "medium"
        assert len(cfg.tools) == 0

    def test_context_files(self):
        from akd_ext.agents.closed_loop.prithvi import FMPrithviGapAgentConfig

        cfg = FMPrithviGapAgentConfig()
        assert len(cfg.context_files) == 2
        assert "Gap Detection Process" in cfg.context_files
        assert "Pipeline Capabilities" in cfg.context_files
        for name, content in cfg.context_files.items():
            assert len(content) > 100, f"Context file '{name}' is too short"

    def test_prompt_content(self):
        from akd_ext.agents.closed_loop.prithvi import FMPrithviGapAgentConfig

        cfg = FMPrithviGapAgentConfig()
        prompt = cfg.system_prompt
        assert "EXECUTION MODE" not in prompt
        assert "ask_human" not in prompt
        assert "PAUSE" in prompt
        assert "Gap Detection" in prompt or "Research Gap" in prompt

    def test_schema_compatibility(self):
        from akd_ext.agents.gap import GapAgentInputSchema, GapAgentOutputSchema

        inp = GapAgentInputSchema(query="test corpus")
        assert inp.query == "test corpus"
        out = GapAgentOutputSchema(report="test report")
        assert out.report == "test report"


# ── Stage 2: Capability & Feasibility Mapper ────────────────────────────


class TestStage2FeasibilityMapper:
    def test_instantiation(self):
        from akd_ext.agents.closed_loop.prithvi import (
            FMPrithviCapabilityFeasibilityMapperAgent,
            FMPrithviCapabilityFeasibilityMapperConfig,
        )

        agent = FMPrithviCapabilityFeasibilityMapperAgent(
            FMPrithviCapabilityFeasibilityMapperConfig()
        )
        assert agent is not None

    def test_config_defaults(self):
        from akd_ext.agents.closed_loop.prithvi import FMPrithviCapabilityFeasibilityMapperConfig

        cfg = FMPrithviCapabilityFeasibilityMapperConfig()
        assert cfg.model_name == "gpt-5.2"
        assert len(cfg.tools) == 0

    def test_context_files(self):
        from akd_ext.agents.closed_loop.prithvi import FMPrithviCapabilityFeasibilityMapperConfig

        cfg = FMPrithviCapabilityFeasibilityMapperConfig()
        assert len(cfg.context_files) == 4
        expected = {
            "Pipeline Capabilities",
            "Feasibility Mapper Reference",
            "Ancillary Dataset Inventory",
            "Feasibility Mapper Governance",
        }
        assert set(cfg.context_files.keys()) == expected

    def test_prompt_no_old_filenames(self):
        from akd_ext.agents.closed_loop.prithvi import FMPrithviCapabilityFeasibilityMapperConfig

        cfg = FMPrithviCapabilityFeasibilityMapperConfig()
        prompt = cfg.system_prompt
        assert "Pipeline_Capability_Envelope" not in prompt
        assert "Feasibility_Mapper_Full_Process" not in prompt
        assert "stage2_2_Feasibility" not in prompt
        assert "PAUSE" in prompt
        assert "ask_human" not in prompt


# ── Stage 3: Workflow Spec Builder ──────────────────────────────────────


class TestStage3WorkflowSpecBuilder:
    def test_instantiation(self):
        from akd_ext.agents.closed_loop.prithvi import (
            FMPrithviWorkflowSpecBuilderAgent,
            FMPrithviWorkflowSpecBuilderConfig,
        )

        agent = FMPrithviWorkflowSpecBuilderAgent(
            FMPrithviWorkflowSpecBuilderConfig()
        )
        assert agent is not None

    def test_config_defaults(self):
        from akd_ext.agents.closed_loop.prithvi import FMPrithviWorkflowSpecBuilderConfig

        cfg = FMPrithviWorkflowSpecBuilderConfig()
        assert cfg.model_name == "gpt-5.2"

    def test_no_local_tools(self, monkeypatch):
        # Without an MCP key, Stage 3 has no tools attached.
        from akd_ext.agents.closed_loop.prithvi import FMPrithviWorkflowSpecBuilderConfig

        monkeypatch.delenv("PRITHVI_MCP_API_KEY", raising=False)
        assert len(FMPrithviWorkflowSpecBuilderConfig().tools) == 0

    def test_geocode_served_by_mcp(self, monkeypatch):
        # With an MCP key, Stage 3 gets geocode + reverse_geocode via MCP.
        from akd_ext.agents.closed_loop.prithvi.tools import get_default_spec_builder_tools

        monkeypatch.setenv("PRITHVI_MCP_API_KEY", "test-key")
        monkeypatch.setenv("PRITHVI_MCP_URL", "https://example.test/mcp")
        allowed = []
        for t in get_default_spec_builder_tools():
            cfg = getattr(t, "tool_config", None)
            if cfg:
                allowed.extend(cfg.get("allowed_tools", []))
        assert "geocode" in allowed
        assert "reverse_geocode" in allowed

    def test_no_tools_when_url_missing(self, monkeypatch):
        # Key set but URL unset → degrade to no tools, not a tool with empty url.
        from akd_ext.agents.closed_loop.prithvi.tools import get_default_spec_builder_tools

        monkeypatch.setenv("PRITHVI_MCP_API_KEY", "test-key")
        monkeypatch.delenv("PRITHVI_MCP_URL", raising=False)
        assert get_default_spec_builder_tools() == []

    def test_context_files(self):
        from akd_ext.agents.closed_loop.prithvi import FMPrithviWorkflowSpecBuilderConfig

        cfg = FMPrithviWorkflowSpecBuilderConfig()
        assert len(cfg.context_files) == 5
        expected = {
            "Workflow Spec Builder Reference",
            "Workflow Spec Config Schema",
            "Pipeline Capabilities",
            "Ancillary Dataset Inventory",
            "Workflow Spec Builder Governance",
        }
        assert set(cfg.context_files.keys()) == expected

    def test_prompt_no_old_filenames(self):
        from akd_ext.agents.closed_loop.prithvi import FMPrithviWorkflowSpecBuilderConfig

        cfg = FMPrithviWorkflowSpecBuilderConfig()
        prompt = cfg.system_prompt
        assert "Workflow_Spec_Builder_Full_Process" not in prompt
        assert "Workflow_Spec_Config_Schema" not in prompt
        assert "stage2_2_Worksflow" not in prompt
        assert "Full_Process" not in prompt
        assert "Envelope" not in prompt
        assert "PAUSE" in prompt
        assert "ask_human" not in prompt

    def test_output_schema_has_config(self):
        from akd_ext.agents.closed_loop.stages.workflow_spec_builder import (
            WorkflowSpecBuilderOutputSchema,
        )

        fields = set(WorkflowSpecBuilderOutputSchema.model_fields.keys())
        assert fields == {"spec", "config", "reasoning"}


# ── Stage 4: Experiment Implementation ──────────────────────────────────


class TestStage4ExperimentImplementation:
    def test_instantiation(self):
        from akd_ext.agents.closed_loop.prithvi import (
            FMPrithviExperimentImplementationAgent,
            FMPrithviExperimentImplementationConfig,
        )

        agent = FMPrithviExperimentImplementationAgent(
            FMPrithviExperimentImplementationConfig()
        )
        assert agent is not None

    def test_has_tools(self):
        from akd_ext.agents.closed_loop.prithvi import FMPrithviExperimentImplementationConfig

        cfg = FMPrithviExperimentImplementationConfig()
        tool_names = []
        for t in cfg.tools:
            if hasattr(t, "name"):
                tool_names.append(t.name)
        # No local function tools attached to the agent
        assert "ask_human" not in tool_names
        assert "geocode" not in tool_names
        assert "reverse_geocode" not in tool_names

    def test_screen_events_served_by_mcp(self, monkeypatch):
        from akd_ext.agents.closed_loop.prithvi.tools import get_default_impl_tools

        monkeypatch.setenv("PRITHVI_MCP_API_KEY", "test-key")
        monkeypatch.setenv("PRITHVI_MCP_URL", "https://example.test/mcp")
        tools = get_default_impl_tools()
        # One HostedMCPTool whose allowed_tools includes screen_events + job_submit
        allowed = []
        for t in tools:
            cfg = getattr(t, "tool_config", None)
            if cfg:
                allowed.extend(cfg.get("allowed_tools", []))
        assert "screen_events" in allowed
        assert "job_submit" in allowed

    def test_prompt_diversity_guidance(self):
        from akd_ext.agents.closed_loop.prithvi import FMPrithviExperimentImplementationConfig

        cfg = FMPrithviExperimentImplementationConfig()
        prompt = cfg.system_prompt
        assert "spread events across different" in prompt or "diverse" in prompt.lower()
        assert "crop_dates" in prompt
        assert "crop_clear_pcts" in prompt


# ── Stage 5: Experiment Analysis ────────────────────────────────────────


class TestStage5ExperimentAnalysis:
    def test_instantiation(self):
        from akd_ext.agents.closed_loop.prithvi import (
            FMPrithviExperimentAnalysisAgent,
            FMPrithviExperimentAnalysisConfig,
        )

        agent = FMPrithviExperimentAnalysisAgent(FMPrithviExperimentAnalysisConfig())
        assert agent is not None

    def test_output_schema_fields(self):
        from akd_ext.agents.closed_loop.stages.experiment_analysis import (
            ExperimentAnalysisOutputSchema,
        )

        fields = set(ExperimentAnalysisOutputSchema.model_fields.keys())
        expected = {"status", "message", "analyses", "text_content", "experiment_map", "image_urls", "markdown"}
        assert fields == expected

    def test_output_schema_no_old_markdown_only(self):
        """Output schema should have structured fields, not just markdown."""
        from akd_ext.agents.closed_loop.stages.experiment_analysis import (
            ExperimentAnalysisOutputSchema,
        )

        schema = ExperimentAnalysisOutputSchema()
        assert hasattr(schema, "analyses")
        assert hasattr(schema, "text_content")
        assert hasattr(schema, "experiment_map")
        assert isinstance(schema.analyses, list)

    def test_url_classification(self):
        from akd_ext.agents.closed_loop.stages.experiment_analysis import _classify_url

        assert _classify_url("https://example.com/fig.png") == "image"
        assert _classify_url("https://example.com/data.csv") == "csv"
        assert _classify_url("https://example.com/report.md") == "text"
        assert _classify_url("https://example.com/unknown.xyz") == "unknown"

    def test_extensionless_image_routed_by_content_type(self, monkeypatch):
        """An extensionless image URL must route to the analyzer via Content-Type,
        not be decoded as mojibake text (httpx.Response.text never raises on bytes)."""
        import asyncio

        from akd_ext.agents.closed_loop.stages import experiment_analysis as ea

        class _Resp:
            def __init__(self, text, ctype):
                self.text = text
                self.headers = {"content-type": ctype}

            def raise_for_status(self):
                pass

        class _Client:
            def __init__(self, *a, **k):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                pass

            async def get(self, url):
                if "figure" in url:
                    return _Resp("\x89PNG-bytes", "image/png")
                return _Resp("# Report", "text/markdown")

        monkeypatch.setattr(ea.httpx, "AsyncClient", _Client)
        imgs, text = asyncio.run(
            ea._categorize_and_fetch(["https://x/figure_nodot", "https://x/report.md"])
        )
        assert "https://x/figure_nodot" in imgs
        assert "PNG-bytes" not in text
        assert "Report" in text


# ── Stage 6: Research Report Generator ──────────────────────────────────


class TestStage6ResearchReportGenerator:
    def test_instantiation(self):
        from akd_ext.agents.closed_loop.prithvi import (
            FMPrithviResearchReportGeneratorAgent,
            FMPrithviResearchReportGeneratorConfig,
        )

        agent = FMPrithviResearchReportGeneratorAgent(
            FMPrithviResearchReportGeneratorConfig()
        )
        assert agent is not None

    def test_no_tools(self):
        from akd_ext.agents.closed_loop.prithvi import FMPrithviResearchReportGeneratorConfig

        cfg = FMPrithviResearchReportGeneratorConfig()
        assert len(cfg.tools) == 0

    def test_input_schema_no_job_id(self):
        # Prithvi uses its OWN input schema (no job_id, no MCP tools).
        from akd_ext.agents.closed_loop.prithvi import (
            FMPrithviResearchReportGeneratorInputSchema,
        )

        fields = set(FMPrithviResearchReportGeneratorInputSchema.model_fields.keys())
        assert "job_id" not in fields
        expected = {"research_question", "workflow_spec", "figure_analysis", "pipeline_text_output"}
        assert fields == expected

    def test_shared_schema_still_has_job_id_for_cm1(self):
        # The shared/generic schema must keep job_id intact — CM1's Stage 6
        # depends on it. Prithvi must not mutate the shared schema.
        from akd_ext.agents.closed_loop.stages.research_report_generator import (
            ResearchReportGeneratorInputSchema,
        )

        fields = set(ResearchReportGeneratorInputSchema.model_fields.keys())
        assert "job_id" in fields
        assert "workflow_spec" in fields

    def test_agent_uses_prithvi_input_schema(self):
        from akd_ext.agents.closed_loop.prithvi import (
            FMPrithviResearchReportGeneratorAgent,
            FMPrithviResearchReportGeneratorInputSchema,
        )

        assert (
            FMPrithviResearchReportGeneratorAgent.input_schema
            is FMPrithviResearchReportGeneratorInputSchema
        )

    def test_prompt_no_mcp_tools(self):
        from akd_ext.agents.closed_loop.prithvi import FMPrithviResearchReportGeneratorConfig

        cfg = FMPrithviResearchReportGeneratorConfig()
        prompt = cfg.system_prompt
        assert "job_status" not in prompt
        assert "job_plot" not in prompt
        assert "job_id" not in prompt
        assert "Stage 6" in prompt
        assert "Interpret" in prompt or "interpret" in prompt

    def test_prompt_has_table_rules(self):
        from akd_ext.agents.closed_loop.prithvi import FMPrithviResearchReportGeneratorConfig

        cfg = FMPrithviResearchReportGeneratorConfig()
        prompt = cfg.system_prompt
        assert "table" in prompt.lower()
