import marimo

__generated_with = "0.23.3"
app = marimo.App(width="full", app_title="AKD-EXT Closed Loop CM1 Workflow")


@app.cell(hide_code=True)
def header():
    import marimo as mo

    mo.output.replace(
        mo.md(
            """
            # AKD-EXT — Closed-Loop CM1 Workflow

            End-to-end notebook for the **CM1 closed-loop pipeline** with the
            harness-executed analysis-module architecture. Run top-to-bottom;
            stages cache their artifacts on disk and skip when already done.

            | Stage | Name | Interaction |
            |:-----:|------|-------------|
            | 1 | **Research Question** | edit the text area |
            | 2 | **Capability-Feasibility Mapping** | button |
            | 3 | **Workflow Spec Builder** | button |
            | 4 | **Experiment Implementation** | **chat** — screening + job submission (HITL) |
            | 5 | **Experiment Analysis Agent** | **chat** — design the figures (review every figure & WHY), approve to generate, then poll & vision-analyze results |
            | 6 | **Interpretation & Paper** | button |

            > Delete a stage's cached file (`cm1_*.md` / `cm1_*.json`) to re-run it.
            """
        )
    )
    return (mo,)


@app.cell(hide_code=True)
def common_imports():
    import os
    from pathlib import Path

    # marimo may run with cwd at the repo root rather than the notebook dir.
    if not Path("closed_loop_cm1_workflow.py").exists():
        _nb = Path("notebooks")
        if _nb.is_dir():
            os.chdir(_nb)

    # Load credentials from the repo-root .env so the MCP-backed agents
    # (Stage 4 job_submit, Stage 5 job_status / job_plot) pick up CM1_MCP_URL,
    # CM1_MCP_API_KEY, and CM1_MCP_AUTH. Without this they'd fall back to the
    # production default with no key — the cause of "couldn't read status".
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(usecwd=True))
    # FastMCP Cloud tokens (fmcp_...) use bearer auth; let .env override.
    os.environ.setdefault("CM1_MCP_AUTH", "bearer")
    return (Path,)


@app.cell
def cm1_imports():
    from akd_ext.agents.closed_loop.cm1 import (
        CM1CapabilityFeasibilityMapperAgent,
        CM1CapabilityFeasibilityMapperConfig,
        CM1ExperimentAnalysisAgent,
        CM1ExperimentAnalysisConfig,
        CM1ExperimentImplementationAgent,
        CM1ExperimentImplementationConfig,
        CM1InterpretationPaperAssemblyAgent,
        CM1InterpretationPaperAssemblyConfig,
        CM1WorkflowSpecBuilderAgent,
        CM1WorkflowSpecBuilderConfig,
    )
    from akd_ext.agents.closed_loop.stages.capability_feasibility_mapper import (
        CapabilityFeasibilityMapperInputSchema,
    )
    from akd_ext.agents.closed_loop.stages.experiment_analysis import (
        ExperimentAnalysisInputSchema,
        ExperimentAnalysisOutputSchema,
    )
    from akd_ext.agents.closed_loop.stages.experiment_implementation import (
        ExperimentImplementationInputSchema,
        ExperimentImplementationOutputSchema,
    )
    from akd_ext.agents.closed_loop.stages.interpretation_paper_assembly import (
        InterpretationPaperAssemblyInputSchema,
        InterpretationPaperAssemblyOutputSchema,
    )
    from akd_ext.agents.closed_loop.stages.workflow_spec_builder import (
        WorkflowSpecBuilderInputSchema,
    )

    return (
        CM1CapabilityFeasibilityMapperAgent,
        CM1CapabilityFeasibilityMapperConfig,
        CM1ExperimentAnalysisAgent,
        CM1ExperimentAnalysisConfig,
        CM1ExperimentImplementationAgent,
        CM1ExperimentImplementationConfig,
        CM1InterpretationPaperAssemblyAgent,
        CM1InterpretationPaperAssemblyConfig,
        CM1WorkflowSpecBuilderAgent,
        CM1WorkflowSpecBuilderConfig,
        CapabilityFeasibilityMapperInputSchema,
        ExperimentAnalysisInputSchema,
        ExperimentAnalysisOutputSchema,
        ExperimentImplementationInputSchema,
        ExperimentImplementationOutputSchema,
        InterpretationPaperAssemblyInputSchema,
        InterpretationPaperAssemblyOutputSchema,
        WorkflowSpecBuilderInputSchema,
    )


@app.cell(hide_code=True)
def stage_1_header(mo):
    mo.output.replace(
        mo.md(
            """
            ---
            ## Stage 1 — Research Question & Hypothesis

            Edit the research question below (normally produced by the Gap
            Agent). Every downstream stage builds on this text.
            """
        )
    )
    return


@app.cell
def stage_1_input(Path, mo):
    # The research question / hypothesis is CACHED in cm1_research_question.md.
    # Edit that file to change the hypothesis; the text area is seeded from it
    # and stays editable in the UI. (Mirrors how the other stages cache to disk.)
    _rq_cache = Path("cm1_research_question.md")
    _default = (
        _rq_cache.read_text(encoding="utf-8")
        if _rq_cache.exists()
        else "# Research Question & Hypothesis\n\n(Create cm1_research_question.md, or type here.)"
    )
    rq_input = mo.ui.text_area(
        value=_default,
        rows=14,
        full_width=True,
        label="Research question / hypothesis (cached in cm1_research_question.md)",
    )
    rq_input
    return (rq_input,)


@app.cell(hide_code=True)
def stage_1_load(rq_input):
    research_question = rq_input.value
    return (research_question,)


@app.cell(hide_code=True)
def stage_2_header(mo):
    mo.output.replace(
        mo.md(
            """
            ---
            ## Stage 2 — Capability-Feasibility Mapping

            Evaluates whether the hypothesis can be tested with CM1 on the
            available cluster. No chat needed — click run, review the report.
            Output: `cm1_feasibility_report.md`
            """
        )
    )
    return


@app.cell
def stage_2_button(mo):
    s2_btn = mo.ui.run_button(label="Run Stage 2 — Feasibility")
    s2_btn
    return (s2_btn,)


@app.cell(hide_code=True)
async def stage_2_run(
    CM1CapabilityFeasibilityMapperAgent,
    CM1CapabilityFeasibilityMapperConfig,
    CapabilityFeasibilityMapperInputSchema,
    Path,
    mo,
    research_question,
    s2_btn,
):
    _path = Path("cm1_feasibility_report.md")
    if not _path.exists():
        mo.stop(
            not s2_btn.value,
            mo.callout(mo.md("Click **Run Stage 2** to assess feasibility."), kind="info"),
        )
        _agent = CM1CapabilityFeasibilityMapperAgent(CM1CapabilityFeasibilityMapperConfig())
        _r = await _agent.arun(
            CapabilityFeasibilityMapperInputSchema(research_questions_md=research_question)
        )
        if hasattr(_r, "report") and _r.report:
            _path.write_text(_r.report, encoding="utf-8")
        else:
            mo.stop(True, mo.callout(mo.md(f"Stage 2 needs input: {_r.content}"), kind="warn"))
    mo.output.replace(
        mo.vstack([
            mo.callout(mo.md("**Stage 2 done** — `cm1_feasibility_report.md` (delete to re-run)."), kind="success"),
            mo.accordion({"Feasibility report": mo.md(_path.read_text(encoding="utf-8"))}),
        ])
    )
    return


@app.cell
def _(Path, mo):
    mo.md(Path("cm1_feasibility_report.md").read_text(encoding="utf-8"))
    return


@app.cell
def stage_2_load(Path):
    _p = Path("cm1_feasibility_report.md")
    feasibility_report = _p.read_text(encoding="utf-8") if _p.exists() else ""
    return (feasibility_report,)


@app.cell(hide_code=True)
def stage_3_header(mo):
    mo.output.replace(
        mo.md(
            """
            ---
            ## Stage 3 — Workflow Spec Builder

            Designs the experiment matrix (baseline + perturbations) with
            concrete namelist/sounding changes. Output: `cm1_workflow_spec.md`
            """
        )
    )
    return


@app.cell
def stage_3_button(mo):
    s3_btn = mo.ui.run_button(label="Run Stage 3 — Workflow Spec")
    s3_btn
    return (s3_btn,)


@app.cell(hide_code=True)
async def stage_3_run(
    CM1WorkflowSpecBuilderAgent,
    CM1WorkflowSpecBuilderConfig,
    Path,
    WorkflowSpecBuilderInputSchema,
    feasibility_report,
    mo,
    research_question,
    s3_btn,
):
    _path = Path("cm1_workflow_spec.md")
    if not _path.exists():
        mo.stop(
            not feasibility_report,
            mo.callout(mo.md("Waiting for Stage 2 output."), kind="warn"),
        )
        mo.stop(
            not s3_btn.value,
            mo.callout(mo.md("Click **Run Stage 3** to design the experiments."), kind="info"),
        )
        _agent = CM1WorkflowSpecBuilderAgent(CM1WorkflowSpecBuilderConfig())
        _r = await _agent.arun(
            WorkflowSpecBuilderInputSchema(
                stage_1_hypotheses=research_question,
                stage_2_feasibility=feasibility_report,
            )
        )
        if hasattr(_r, "spec") and _r.spec:
            _path.write_text(
                _r.spec + "\n\n---\n\n# Reasoning\n\n" + _r.reasoning, encoding="utf-8"
            )
        else:
            mo.stop(True, mo.callout(mo.md(f"Stage 3 needs input: {_r.content}"), kind="warn"))
    mo.output.replace(
        mo.vstack([
            mo.callout(mo.md("**Stage 3 done** — `cm1_workflow_spec.md` (delete to re-run)."), kind="success"),
            mo.accordion({"Workflow spec": mo.md(_path.read_text(encoding="utf-8"))}),
        ])
    )
    return


@app.cell
def _(Path, mo):
    mo.md(Path("cm1_workflow_spec.md").read_text(encoding="utf-8"))
    return


@app.cell
def stage_3_load(Path):
    _p = Path("cm1_workflow_spec.md")
    workflow_spec_content = _p.read_text(encoding="utf-8") if _p.exists() else ""
    return (workflow_spec_content,)


@app.cell(hide_code=True)
def stage_4_header(mo):
    mo.output.replace(
        mo.md(
            """
            ---
            ## Stage 4 — Experiment Implementation (chat, HITL)

            The agent translates the spec into FileEdit JSON and submits the
            experiment batch via the `job_submit` MCP tool. Chat with it —
            type **go** to start, answer its clarifications, approve the
            submission. Output: `cm1_stage4_report.md` with job ID + workspace.
            """
        )
    )
    return


@app.cell(hide_code=True)
def stage_4_run(
    CM1ExperimentImplementationAgent,
    CM1ExperimentImplementationConfig,
    ExperimentImplementationInputSchema,
    ExperimentImplementationOutputSchema,
    Path,
    mo,
    workflow_spec_content,
):
    mo.stop(
        not workflow_spec_content,
        mo.callout(mo.md("Waiting for Stage 3 output."), kind="warn"),
    )
    mo.stop(
        Path("cm1_stage4_report.md").exists(),
        mo.callout(mo.md("**Stage 4 cached** — `cm1_stage4_report.md`. Delete it to re-run."), kind="success"),
    )

    _agent = CM1ExperimentImplementationAgent(CM1ExperimentImplementationConfig())
    # Persist conversation context across chat turns (job state lives in the
    # tool-call history).
    _state = {"ctx": None}

    async def _model(messages):
        _new_msg = messages[-1].content if messages else ""
        if _state["ctx"] is None:
            _r = await _agent.arun(
                ExperimentImplementationInputSchema(stage_3_spec=workflow_spec_content)
            )
        else:
            _r = await _agent.arun(
                ExperimentImplementationInputSchema(stage_3_spec=_new_msg),
                run_context=_state["ctx"],
            )
        _state["ctx"] = getattr(_r, "_run_context", _state["ctx"])
        if isinstance(_r, ExperimentImplementationOutputSchema):
            # Saved file keeps the Job ID / Workspace lines the result cell
            # parses; the user-facing reply stays clean.
            _md = (
                f"- Job ID: `{_r.job_id}`\n"
                f"- Workspace: `{_r.workspace_name}`\n\n"
                f"{_r.report}"
            )
            Path("cm1_stage4_report.md").write_text(_md, encoding="utf-8")
            return f"**Experiment submitted.**\n\n{_r.report}"
        return _r.content

    mo.output.replace(
        mo.vstack([
            mo.callout(mo.md("**Stage 4 — Experiment Implementation.** Type 'go' to start, then approve or steer the submission."), kind="info"),
            mo.ui.chat(_model, show_configuration_controls=False),
        ])
    )
    return


@app.cell(hide_code=True)
def stage_4_result(Path, mo):
    """Load Stage-4 result from disk."""
    from akd_ext.agents.closed_loop.stages.experiment_implementation import (
        ExperimentImplementationOutputSchema as _EIOut,
    )

    _md_path = Path("cm1_stage4_report.md")
    impl_result = None
    if _md_path.exists():
        import re as _re

        _text = _md_path.read_text(encoding="utf-8")
        _job = _re.search(r"Job ID:\s*`([^`]+)`", _text)
        _ws = _re.search(r"Workspace:\s*`([^`]+)`", _text)
        if _job and _ws:
            impl_result = _EIOut(
                job_id=_job.group(1), workspace_name=_ws.group(1), report=_text
            )
            mo.output.replace(
                mo.callout(
                    mo.md(
                        f"**Stage 4 loaded.** Job `{impl_result.job_id}` · "
                        f"workspace `{impl_result.workspace_name}`"
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
            ## Stage 5 - Experiment Analysis Agent

            **Say anything in the chat to start** (e.g. "hi"). The agent checks
            the experiment status and proposes a figure plan to test the
            hypothesis - each figure with what it shows and why it matters.

            From there, just chat to:
            - **refine** the plan ("drop the moisture figure", "add a vorticity panel")
            - **approve** it ("looks good") to generate the figures
            - **check status** ("is it done?") any time
            - **analyze** the results once the run finishes - the agent fetches
              the figures and returns a vision-based analysis against the hypothesis.
            """
        )
    )
    return


@app.cell(hide_code=True)
def stage_5_run(
    CM1ExperimentAnalysisAgent,
    CM1ExperimentAnalysisConfig,
    ExperimentAnalysisInputSchema,
    ExperimentAnalysisOutputSchema,
    Path,
    impl_result,
    mo,
    research_question,
    workflow_spec_content,
):
    """Experiment Analysis Agent — one agent owns the whole lifecycle.

    The same single agent the frontend registers: each turn is one
    ``arun`` call; the agent routes design → approve → status → analyze
    internally and returns a chat message or the final structured analysis.
    """
    mo.stop(
        impl_result is None,
        mo.callout(mo.md("Waiting for the experiment job (Experiment Implementation)."), kind="warn"),
    )

    _agent = CM1ExperimentAnalysisAgent(CM1ExperimentAnalysisConfig())

    def _params(msg):
        return ExperimentAnalysisInputSchema(
            job_id=impl_result.job_id,
            workspace_name=impl_result.workspace_name,
            hypothesis=research_question,
            experiment_spec=workflow_spec_content,
            message=msg,
        )

    def _render(r):
        # Final structured analysis → persist for Stage 6; everything else
        # (figure plan / approval / status) is a chat-message TextOutput.
        if isinstance(r, ExperimentAnalysisOutputSchema):
            if r.markdown:
                Path("cm1_stage5_analysis.md").write_text(r.markdown, encoding="utf-8")
            return (
                f"**Analysis complete — {len(r.analyses)} figure(s) analyzed.**"
                f"\n\n{r.markdown or ''}"
            )
        return r.content

    async def _model(messages):
        # First message of a fresh chat → clear any leftover plan from a prior
        # run so the agent greets (status check + plan) instead of treating it
        # as a revision. Later turns keep the plan for cumulative edits.
        if len(messages) <= 1:
            Path(f"cm1_pending_design_{impl_result.job_id}.json").unlink(missing_ok=True)
        return _render(await _agent.arun(_params(messages[-1].content if messages else "")))

    # Chat-first: no pre-rendered output. The scientist's FIRST message
    # (whatever it is) makes the agent check the job status and propose the
    # plan. A fresh module on disk means this stage already finished — show a
    # short note so re-running the notebook doesn't re-propose.
    if Path(f"cm1_analysis_module_{impl_result.job_id}.py").exists():
        _intro = "Plan already approved & submitted. Ask me to **check status** or **analyze** the results."
    else:
        _intro = (
            "Say anything below to begin — I'll check the experiment and "
            "propose the analysis plan."
        )

    mo.output.replace(
        mo.vstack([
            mo.callout(mo.md(_intro), kind="info"),
            mo.ui.chat(_model, show_configuration_controls=False),
        ])
    )
    return


@app.cell
def stage_5_load(Path):
    _p = Path("cm1_stage5_analysis.md")
    stage5_markdown = _p.read_text(encoding="utf-8") if _p.exists() else ""
    return (stage5_markdown,)


@app.cell(hide_code=True)
def stage_6_header(mo):
    mo.output.replace(
        mo.md(
            """
            ---
            ## Stage 6 — Interpretation & Paper Assembly

            Writes the publication-style paper organized around the hypothesis
            verdict, from all upstream artifacts. Output: `cm1_stage6_paper.md`
            """
        )
    )
    return


@app.cell
def stage_6_button(mo):
    s6_btn = mo.ui.run_button(label="Run Stage 6 — Assemble Paper")
    s6_btn
    return (s6_btn,)


@app.cell(hide_code=True)
async def stage_6_run(
    CM1InterpretationPaperAssemblyAgent,
    CM1InterpretationPaperAssemblyConfig,
    InterpretationPaperAssemblyInputSchema,
    InterpretationPaperAssemblyOutputSchema,
    Path,
    impl_result,
    mo,
    research_question,
    s6_btn,
    stage5_markdown,
    workflow_spec_content,
):
    _path = Path("cm1_stage6_paper.md")
    if not _path.exists():
        mo.stop(
            not stage5_markdown,
            mo.callout(mo.md("Waiting for Stage 5c analysis."), kind="warn"),
        )
        mo.stop(
            not s6_btn.value,
            mo.callout(mo.md("Click **Run Stage 6** to assemble the paper."), kind="info"),
        )
        _agent = CM1InterpretationPaperAssemblyAgent(CM1InterpretationPaperAssemblyConfig())
        _r = await _agent.arun(
            InterpretationPaperAssemblyInputSchema(
                hypothesis=research_question,
                experiment_design=workflow_spec_content,
                implementation_report=impl_result.report if impl_result else "",
                experiment_analysis=stage5_markdown,
            )
        )
        # On success the agent returns the structured paper (has `.report`);
        # otherwise a TextOutput chat message (only that has `.content`).
        # mo.stop evaluates this arg eagerly, so use getattr to avoid an
        # AttributeError on the success path.
        mo.stop(
            not isinstance(_r, InterpretationPaperAssemblyOutputSchema),
            mo.callout(mo.md(f"Stage 6 says: {getattr(_r, 'content', '')}"), kind="warn"),
        )
        _path.write_text(_r.report, encoding="utf-8")
    mo.output.replace(
        mo.vstack([
            mo.callout(mo.md("**Stage 6 done** — `cm1_stage6_paper.md` (delete to re-run)."), kind="success"),
            mo.md(_path.read_text(encoding="utf-8")),
        ])
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
