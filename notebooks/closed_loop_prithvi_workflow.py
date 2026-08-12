import marimo

__generated_with = "0.23.3"
app = marimo.App(
    width="full",
    app_title="AKD-EXT Closed Loop FM_Prithvi Workflow",
)


@app.cell(hide_code=True)
def header():
    import marimo as mo

    mo.output.replace(
        mo.md(
            """
            # AKD-EXT — Closed-Loop FM-Prithvi Workflow

            End-to-end notebook for the **Prithvi foundation-model closed-loop
            pipeline**.  Each stage builds on the previous one — run them
            top-to-bottom, or skip ahead using cached artifacts on disk.

            | Stage | Name | What it does |
            |:-----:|------|--------------|
            | 1 | **Gap Analysis** | Reads a research corpus and surfaces knowledge gaps / candidate research questions |
            | 2 | **Capability-Feasibility Mapping** | Maps each RQ against Prithvi's capabilities and rates feasibility |
            | 3 | **Workflow Spec Builder** | Generates an experiment specification + pipeline config YAML |
            | 4 | **Experiment Implementation** | Interactive (HITL) — selects events, screens HLS imagery, submits the HPC job |
            | 5 | **Experiment Analysis** | Polls job status, fetches result artifacts, produces structured per-figure analyses |
            | 6 | **Research Report** | Generates a structured research report from all upstream outputs |

            > **Tip:** Each stage saves its output to disk (`notebooks/*.md`, `*.yaml`, `*.json`).
            > If you restart the notebook, stages will load cached results automatically so
            > you don't have to re-run everything.
            """
        )
    )
    return (mo,)


@app.cell(hide_code=True)
def intro(mo):
    mo.output.replace(
        mo.md(
            """
            ---
            ## Stage 1 — Gap Analysis

            The gap agent ingests a corpus of research papers and identifies
            **knowledge gaps**, **contradictions**, and **candidate research
            questions** ranked by novelty and potential impact.

            - **Input:** raw paper text or structured corpus
            - **Output:** a markdown report with prioritized RQs, linked gaps,
              and hypothesis framings

            For this demo, a pre-loaded research question (RQ2 from the Prithvi
            flood-crop corpus) is used directly.  Uncomment the cell below to
            run the full gap agent on your own corpus.
            """
        )
    )
    return


@app.cell
def common_imports():
    from pathlib import Path

    # marimo may run with cwd at the repo root rather than the notebook
    # directory.  Ensure relative data-file paths resolve correctly.
    if not Path("closed_loop_prithvi_workflow.py").exists():
        import os as _os

        _nb = Path("notebooks")
        if _nb.is_dir():
            _os.chdir(_nb)
    return (Path,)


@app.cell
def stage_1_imports():
    from akd_ext.agents.closed_loop.prithvi import (
        FMPrithviGapAgent,
        FMPrithviGapAgentConfig,
    )
    from akd_ext.agents.gap import GapAgentInputSchema

    return FMPrithviGapAgent, FMPrithviGapAgentConfig, GapAgentInputSchema


@app.cell(hide_code=True)
def stage_1_run(
    FMPrithviGapAgent,
    FMPrithviGapAgentConfig,
    GapAgentInputSchema,
    Path,
    mo,
):
    """Chat-based Gap Agent. Loads cached result or lets you interact."""
    _report_path = Path("prithvi_gap_report.md")
    mo.stop(
        _report_path.exists(),
        mo.callout(mo.md("**Stage 1 cached** — using `prithvi_gap_report.md`. Delete it to re-run."), kind="success"),
    )

    _corpus_path = Path("../scripts/corpus.txt")
    if not _corpus_path.exists():
        _corpus_path = Path("scripts/corpus.txt")
    mo.stop(
        not _corpus_path.exists(),
        mo.callout(mo.md("No corpus found. Place `corpus.txt` in `scripts/`."), kind="warn"),
    )

    _corpus = _corpus_path.read_text(encoding="utf-8")
    _agent = FMPrithviGapAgent(FMPrithviGapAgentConfig())

    async def _model(messages):
        _user_instructions = "\n".join(
            m.content for m in messages if getattr(m, "role", "user") == "user"
        )
        _query = _corpus + "\n\n---\nUser instructions:\n" + _user_instructions
        _r = await _agent.arun(GapAgentInputSchema(query=_query))
        if hasattr(_r, "report"):
            Path("prithvi_gap_report.md").write_text(_r.report, encoding="utf-8")
            return f"**Saved to `prithvi_gap_report.md`.**\n\n{_r.report}"
        return _r.content

    mo.output.replace(
        mo.vstack([
            mo.callout(mo.md(f"**Corpus:** {len(_corpus):,} chars. Type instructions (e.g. 'use all papers, cross-hazard scope') or just 'go' to run with defaults."), kind="info"),
            mo.ui.chat(_model, show_configuration_controls=False),
        ])
    )
    return


@app.cell
def stage_1_load(Path):
    """Load saved gap report for downstream stages."""
    _report_path = Path("prithvi_gap_report.md")
    research_question = (
        _report_path.read_text(encoding="utf-8") if _report_path.exists() else ""
    )
    return (research_question,)


@app.cell(hide_code=True)
def stage_2_header(mo):
    mo.output.replace(
        mo.md(
            """
            ---
            ## Stage 2 — Capability-Feasibility Mapping

            Takes the research questions from Stage 1 and evaluates each against
            **Prithvi's actual capabilities** — what sensor inputs it supports
            (HLS, Sentinel-2), what tasks it can perform (crop classification,
            flood mapping, burn scar detection), and what spatial/temporal
            constraints apply.

            - **Input:** Stage 1 research questions (markdown)
            - **Output:** feasibility report ranking each RQ by Prithvi fit,
              with specific capability mappings and risk flags

            The report is saved to `prithvi_feasibility_report.md`.
            """
        )
    )
    return


@app.cell
def stage_2_imports():
    from akd_ext.agents.closed_loop.prithvi import (
        FMPrithviCapabilityFeasibilityMapperAgent,
        FMPrithviCapabilityFeasibilityMapperConfig,
    )
    from akd_ext.agents.closed_loop.stages.capability_feasibility_mapper import (
        CapabilityFeasibilityMapperInputSchema,
    )

    return (
        CapabilityFeasibilityMapperInputSchema,
        FMPrithviCapabilityFeasibilityMapperAgent,
        FMPrithviCapabilityFeasibilityMapperConfig,
    )


@app.cell(hide_code=True)
def stage_2_run(
    CapabilityFeasibilityMapperInputSchema,
    FMPrithviCapabilityFeasibilityMapperAgent,
    FMPrithviCapabilityFeasibilityMapperConfig,
    Path,
    mo,
    research_question,
):
    """Chat-based Feasibility Mapper."""
    mo.stop(
        not research_question,
        mo.callout(mo.md("Waiting for Stage 1 output."), kind="warn"),
    )
    mo.stop(
        Path("prithvi_feasibility_report.md").exists(),
        mo.callout(mo.md("**Stage 2 cached** — using `prithvi_feasibility_report.md`. Delete it to re-run."), kind="success"),
    )

    _agent = FMPrithviCapabilityFeasibilityMapperAgent(
        FMPrithviCapabilityFeasibilityMapperConfig()
    )

    async def _model(messages):
        _user_instructions = "\n".join(
            m.content for m in messages if getattr(m, "role", "user") == "user"
        )
        _prior = [m.content for m in messages if getattr(m, "role", "") == "assistant"]
        _last = (
            "\n\n---\nYour previous output (continue from here — do not restart at Stage 1):\n"
            + _prior[-1]
        ) if _prior else ""
        _input_md = research_question + _last + "\n\n---\nUser instructions:\n" + _user_instructions
        _r = await _agent.arun(
            CapabilityFeasibilityMapperInputSchema(research_questions_md=_input_md)
        )
        if hasattr(_r, "report"):
            Path("prithvi_feasibility_report.md").write_text(_r.report, encoding="utf-8")
            return f"**Saved to `prithvi_feasibility_report.md`.**\n\n{_r.report}"
        return _r.content

    mo.output.replace(
        mo.vstack([
            mo.callout(mo.md("**Stage 2 — Feasibility Mapper.** Type 'go' to run all RQs, or steer (e.g. 'focus on RQ2 only')."), kind="info"),
            mo.ui.chat(_model, show_configuration_controls=False),
        ])
    )
    return


@app.cell
def stage_2_load(Path):
    """Load saved feasibility report."""
    _report_path = Path("prithvi_feasibility_report.md")
    report_md_content = (
        _report_path.read_text(encoding="utf-8") if _report_path.exists() else ""
    )
    return (report_md_content,)


@app.cell(hide_code=True)
def stage_3_header(mo):
    mo.output.replace(
        mo.md(
            """
            ---
            ## Stage 3 — Workflow Spec Builder

            Translates the feasibility report into a concrete **experiment
            specification** and a **pipeline config YAML** that downstream
            stages can execute.

            The spec includes:
            - Selected RQ and hypothesis framing
            - Hazard type (flood / burn), required Prithvi tasks
            - Event selection criteria (states, year range, min cropland %)
            - HLS date requirements and screening parameters
            - Expected output structure

            - **Input:** Stage 1 RQs + Stage 2 feasibility report
            - **Output:** `prithvi_workflow_spec.md` + `prithvi_pipeline_config.yaml`
            """
        )
    )
    return


@app.cell
def stage_3_imports():
    from akd_ext.agents.closed_loop.prithvi import (
        FMPrithviWorkflowSpecBuilderAgent,
        FMPrithviWorkflowSpecBuilderConfig,
    )
    from akd_ext.agents.closed_loop.stages.workflow_spec_builder import (
        WorkflowSpecBuilderInputSchema,
    )

    return (
        FMPrithviWorkflowSpecBuilderAgent,
        FMPrithviWorkflowSpecBuilderConfig,
        WorkflowSpecBuilderInputSchema,
    )


@app.cell(hide_code=True)
def stage_3_run(
    FMPrithviWorkflowSpecBuilderAgent,
    FMPrithviWorkflowSpecBuilderConfig,
    Path,
    WorkflowSpecBuilderInputSchema,
    mo,
    report_md_content,
    research_question,
):
    """Chat-based Workflow Spec Builder."""
    mo.stop(
        not report_md_content,
        mo.callout(mo.md("Waiting for Stage 2 output."), kind="warn"),
    )
    mo.stop(
        Path("prithvi_workflow_spec.md").exists(),
        mo.callout(mo.md("**Stage 3 cached** — using `prithvi_workflow_spec.md`. Delete it to re-run."), kind="success"),
    )

    _agent = FMPrithviWorkflowSpecBuilderAgent(
        FMPrithviWorkflowSpecBuilderConfig()
    )

    async def _model(messages):
        _user_instructions = "\n".join(
            m.content for m in messages if getattr(m, "role", "user") == "user"
        )
        _prior = [m.content for m in messages if getattr(m, "role", "") == "assistant"]
        _last = (
            "\n\n---\nYour previous output (continue from here — do not restart at Stage 1):\n"
            + _prior[-1]
        ) if _prior else ""
        _feasibility = report_md_content + _last + "\n\n---\nUser instructions:\n" + _user_instructions
        _r = await _agent.arun(
            WorkflowSpecBuilderInputSchema(
                stage_1_hypotheses=research_question,
                stage_2_feasibility=_feasibility,
            )
        )
        if hasattr(_r, "spec"):
            Path("prithvi_workflow_spec.md").write_text(
                _r.spec + "\n\n---\n\n# Reasoning\n\n" + _r.reasoning, encoding="utf-8"
            )
            if _r.config:
                Path("prithvi_pipeline_config.yaml").write_text(_r.config, encoding="utf-8")
            return f"**Saved spec + config YAML.**\n\n{_r.spec}"
        return _r.content

    mo.output.replace(
        mo.vstack([
            mo.callout(mo.md("**Stage 3 — Workflow Spec Builder.** Type 'go' to run, or steer (e.g. 'focus on RQ2, use US events only')."), kind="info"),
            mo.ui.chat(_model, show_configuration_controls=False),
        ])
    )
    return


@app.cell
def stage_3_load(Path):
    """Load saved spec + config (for testing without re-running Stage 3)."""
    _spec_path = Path("prithvi_workflow_spec.md")
    _config_path = Path("prithvi_pipeline_config.yaml")

    workflow_spec_content = (
        _spec_path.read_text(encoding="utf-8") if _spec_path.exists() else ""
    ) 
    config_content = (
        _config_path.read_text(encoding="utf-8") if _config_path.exists() else ""
    )
    return config_content, workflow_spec_content


@app.cell(hide_code=True)
def stage_4_header(config_content, mo):
    config_content
    mo.output.replace(
        mo.md(
            """
            ---
            ## Stage 4 — Experiment Implementation

            The agent screens events, validates the config, and submits the job.

            1. Reads the experiment config from Stage 3
            2. Asks you for region/year preferences
            3. Screens flood/burn events (CDL cropland → HLS clear-sky → crop phenology)
            4. Presents candidates — you approve, reject, or refine
            5. Builds the final config and submits to the MCP server

            - **Input:** Stage 3 spec + config YAML
            - **Output:** `prithvi_stage4_report.md` with experiment details, job ID, and workspace
            """
        )
    )
    return


@app.cell
def stage_4_imports():
    from akd_ext.agents.closed_loop.prithvi import (
        FMPrithviExperimentImplementationAgent,
        FMPrithviExperimentImplementationConfig,
    )
    from akd_ext.agents.closed_loop.stages.experiment_implementation import (
        ExperimentImplementationInputSchema,
        ExperimentImplementationOutputSchema,
    )

    return (
        ExperimentImplementationInputSchema,
        ExperimentImplementationOutputSchema,
        FMPrithviExperimentImplementationAgent,
        FMPrithviExperimentImplementationConfig,
    )


@app.cell(hide_code=True)
def stage_4_run(
    ExperimentImplementationInputSchema,
    ExperimentImplementationOutputSchema,
    FMPrithviExperimentImplementationAgent,
    FMPrithviExperimentImplementationConfig,
    Path,
    config_content,
    mo,
    workflow_spec_content,
):
    """Chat-based Stage 4. Agent screens events and submits job via tools."""
    mo.stop(
        not workflow_spec_content,
        mo.callout(mo.md("Waiting for Stage 3 output."), kind="warn"),
    )
    mo.stop(
        Path("prithvi_stage4_report.md").exists(),
        mo.callout(mo.md("**Stage 4 cached** — using `prithvi_stage4_report.md`. Delete it to re-run."), kind="success"),
    )

    _agent = FMPrithviExperimentImplementationAgent(
        FMPrithviExperimentImplementationConfig()
    )
    # Persist the agent's conversation across chat turns so the screening
    # task_id (held in the tool-call history) survives between "go" and
    # "is it done?". Without this, each turn re-runs screening from scratch.
    _state = {"ctx": None}

    async def _model(messages):
        _new_msg = messages[-1].content if messages else ""
        if _state["ctx"] is None:
            # First turn: send the full Stage-3 spec + config.
            _r = await _agent.arun(
                ExperimentImplementationInputSchema(
                    stage_3_spec=workflow_spec_content,
                    config=config_content,
                )
            )
        else:
            # Continuation: send only the new user message, reuse prior context.
            _r = await _agent.arun(
                ExperimentImplementationInputSchema(
                    stage_3_spec=_new_msg,
                    config="",
                ),
                run_context=_state["ctx"],
            )
        _state["ctx"] = getattr(_r, "_run_context", _state["ctx"])
        if isinstance(_r, ExperimentImplementationOutputSchema):
            _md = (
                f"# Stage 4 — Experiment Implementation\n\n"
                f"- Job ID: `{_r.job_id}`\n"
                f"- Workspace: `{_r.workspace_name}`\n\n"
                f"{_r.report}"
            )
            Path("prithvi_stage4_report.md").write_text(_md, encoding="utf-8")
            return (
                f"**Job submitted!**\n\n{_md}\n\n"
                f"**Stage 4 complete. Ready for Stage 5.**"
            )
        return _r.content

    mo.output.replace(
        mo.vstack([
            mo.callout(mo.md("**Stage 4 — Experiment Implementation.** Type 'go' to start screening, or provide region/year preferences (e.g. 'Iowa and Nebraska, 2023-2025')."), kind="info"),
            mo.ui.chat(_model, show_configuration_controls=False),
        ])
    )
    return


@app.cell
def stage_4_result(Path, mo):
    """Load Stage-4 result from disk."""

    from akd_ext.agents.closed_loop.stages.experiment_implementation import (
        ExperimentImplementationOutputSchema as _EIOut,
    )

    _md_path = Path("prithvi_stage4_report.md")
    impl_result = None
    if _md_path.exists():
        _text = _md_path.read_text(encoding="utf-8")
        # Extract job_id and workspace from the report markdown.
        # The report contains "Job ID: `<id>`" and "Workspace: `<name>`".
        import re as _re

        _job_match = _re.search(r"Job ID:\s*`([^`]+)`", _text)
        _ws_match = _re.search(r"Workspace:\s*`([^`]+)`", _text)
        if _job_match and _ws_match:
            impl_result = _EIOut(
                job_id=_job_match.group(1),
                workspace_name=_ws_match.group(1),
                report=_text,
            )
            mo.output.replace(
                mo.callout(
                    mo.md(
                        f"**Stage 4 result loaded.**\n\n"
                        f"- Job ID: `{impl_result.job_id}`\n"
                        f"- Workspace: `{impl_result.workspace_name}`"
                    ),
                    kind="success",
                )
            )
    return (impl_result,)


@app.cell(hide_code=True)
def stage_5_header(mo):
    mo.output.replace(
        mo.md(
            """
            ---
            ## Stage 5 — Experiment Analysis

            Polls the MCP server for the submitted job's status.  Once the job
            completes, fetches all result artifacts (figures, CSVs, reports) and
            runs the **ImageAnalyzerAgent** (GPT vision) to produce structured
            per-figure analyses (axes, legend, spatial patterns, anomalies).

            This stage does **not** generate a report — it returns structured
            data for Stage 6 to consume.

            - **Input:** job ID + workspace from Stage 4, hypothesis + spec
            - **Output:** structured `FigureAnalysis[]` + fetched text data + experiment map
            """
        )
    )
    return


@app.cell
def stage_5_imports():
    from akd_ext.agents.closed_loop.prithvi import (
        FMPrithviExperimentAnalysisAgent,
        FMPrithviExperimentAnalysisConfig,
    )
    from akd_ext.agents.closed_loop.stages import (
        ExperimentAnalysisInputSchema,
        ExperimentAnalysisOutputSchema,
    )

    return (
        ExperimentAnalysisInputSchema,
        ExperimentAnalysisOutputSchema,
        FMPrithviExperimentAnalysisAgent,
        FMPrithviExperimentAnalysisConfig,
    )


@app.cell(hide_code=True)
def stage_5_run(
    ExperimentAnalysisInputSchema,
    ExperimentAnalysisOutputSchema,
    FMPrithviExperimentAnalysisAgent,
    FMPrithviExperimentAnalysisConfig,
    Path,
    impl_result,
    mo,
    research_question,
    workflow_spec_content,
):
    """Chat-based Stage 5. Same pattern as Stages 1-4."""

    from akd_ext.agents.closed_loop.stages.experiment_implementation import (
        ExperimentImplementationOutputSchema as _EIOut,
    )

    mo.stop(
        not isinstance(impl_result, _EIOut),
        mo.callout(mo.md("Waiting for Stage 4 to complete."), kind="warn"),
    )
    mo.stop(
        Path("prithvi_stage5_analysis.md").exists(),
        mo.callout(mo.md("**Stage 5 cached** — using `prithvi_stage5_analysis.md`. Delete it to re-run."), kind="success"),
    )

    _job_id = impl_result.job_id
    _workspace = impl_result.workspace_name
    _agent = FMPrithviExperimentAnalysisAgent(FMPrithviExperimentAnalysisConfig())

    async def _model(messages):
        _user_instructions = "\n".join(
            m.content for m in messages if getattr(m, "role", "user") == "user"
        )
        _spec = workflow_spec_content + "\n\n---\nUser instructions:\n" + _user_instructions
        _r = await _agent.arun(
            ExperimentAnalysisInputSchema(
                job_id=_job_id,
                workspace_name=_workspace,
                hypothesis=research_question,
                experiment_spec=_spec,
            ),
        )
        if isinstance(_r, ExperimentAnalysisOutputSchema):
            if _r.markdown:
                Path("prithvi_stage5_analysis.md").write_text(
                    _r.markdown, encoding="utf-8"
                )
            _n = len(_r.analyses)
            return (
                f"**Analysis complete — {_n} figure(s) analyzed.** "
                f"Saved to `prithvi_stage5_analysis.md`.\n\n{_r.markdown or ''}"
            )
        return _r.content

    mo.output.replace(
        mo.vstack([
            mo.callout(mo.md(f"**Stage 5 — Experiment Analysis.** Job `{_job_id}`. Type 'check status' to see if the job is done, or 'go' once ready."), kind="info"),
            mo.ui.chat(_model, show_configuration_controls=False),
        ])
    )
    return


@app.cell
def stage_5_load(Path):
    """Load saved Stage-5 analysis for Stage 6 (disk handoff)."""
    _md_path = Path("prithvi_stage5_analysis.md")
    stage5_markdown = (
        _md_path.read_text(encoding="utf-8") if _md_path.exists() else ""
    )
    return (stage5_markdown,)


@app.cell(hide_code=True)
def stage_6_header(mo):
    mo.output.replace(
        mo.md(
            """
            ---
            ## Stage 6 — Research Report

            Generates a **structured research report** from the workflow spec
            and Stage 5's structured figure analyses.  The LLM receives per-figure
            descriptions (axes, patterns, anomalies), pipeline text outputs (CSVs,
            reports), and the experiment context to produce a publication-style
            narrative.

            This stage runs automatically when Stage 5 results are available.

            - **Input:** Stage 1 research question + Stage 3 workflow spec + Stage 5 figure analyses + pipeline text output
            - **Output:** `prithvi_stage6_report.md`
            """
        )
    )
    return


@app.cell
def stage_6_imports():
    from akd_ext.agents.closed_loop.prithvi import (
        FMPrithviResearchReportGeneratorAgent,
        FMPrithviResearchReportGeneratorConfig,
        FMPrithviResearchReportGeneratorInputSchema,
    )
    from akd_ext.agents.closed_loop.stages.research_report_generator import (
        ResearchReportGeneratorOutputSchema,
    )

    return (
        FMPrithviResearchReportGeneratorAgent,
        FMPrithviResearchReportGeneratorConfig,
        FMPrithviResearchReportGeneratorInputSchema,
        ResearchReportGeneratorOutputSchema,
    )


@app.cell(hide_code=True)
def stage_6_run(
    FMPrithviResearchReportGeneratorAgent,
    FMPrithviResearchReportGeneratorConfig,
    FMPrithviResearchReportGeneratorInputSchema,
    Path,
    ResearchReportGeneratorOutputSchema,
    mo,
    research_question,
    stage5_markdown,
    workflow_spec_content,
):
    """Chat-based Stage 6. Same pattern as Stages 1-5."""
    mo.stop(
        not stage5_markdown,
        mo.callout(mo.md("Waiting for Stage 5 analysis."), kind="warn"),
    )
    mo.stop(
        Path("prithvi_stage6_report.md").exists(),
        mo.callout(mo.md("**Stage 6 cached** — using `prithvi_stage6_report.md`. Delete it to re-run."), kind="success"),
    )

    _agent = FMPrithviResearchReportGeneratorAgent(
        FMPrithviResearchReportGeneratorConfig()
    )

    async def _model(messages):
        _user_instructions = "\n".join(
            m.content for m in messages if getattr(m, "role", "user") == "user"
        )
        _rq = research_question + "\n\n---\nUser instructions:\n" + _user_instructions
        _r = await _agent.arun(
            FMPrithviResearchReportGeneratorInputSchema(
                research_question=_rq,
                workflow_spec=workflow_spec_content,
                figure_analysis=stage5_markdown,
            ),
        )
        if isinstance(_r, ResearchReportGeneratorOutputSchema):
            Path("prithvi_stage6_report.md").write_text(
                _r.report, encoding="utf-8"
            )
            return f"**Saved to `prithvi_stage6_report.md`.**\n\n{_r.report}"
        return _r.content

    mo.output.replace(
        mo.vstack([
            mo.callout(mo.md("**Stage 6 — Research Report.** Type 'go' to generate the report, or provide instructions (e.g. 'focus on RQ2 results, embed all figures inline')."), kind="info"),
            mo.ui.chat(_model, show_configuration_controls=False),
        ])
    )
    return


@app.cell
def _():
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
