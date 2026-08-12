"""CM1-specialized closed-loop workflow agents.

Each agent is a subclass of the generic stage agent with CM1-specific
system prompts, context files, tools, and descriptions pre-configured.

Public API:
    CM1CapabilityFeasibilityMapperAgent, CM1CapabilityFeasibilityMapperConfig,
    CM1WorkflowSpecBuilderAgent, CM1WorkflowSpecBuilderConfig,
    CM1ExperimentImplementationAgent, CM1ExperimentImplementationConfig,
    CM1ResearchReportGeneratorAgent, CM1ResearchReportGeneratorConfig,
    CM1InterpretationPaperAssemblyAgent, CM1InterpretationPaperAssemblyConfig,
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, Literal

from loguru import logger
from pydantic import Field

from akd._base import (
    CompletedEvent,
    CompletedEventData,
    InputSchema,
    OutputSchema,
    RunContext,
    RunningEvent,
    StartingEvent,
    StartingEventData,
    StreamEvent,
    TextOutput,
)
from akd_ext.agents._base import PydanticAIBaseAgent, PydanticAIBaseAgentConfig
from akd_ext.agents.code_generator import (
    CodeDesignerAgent,
    CodeDesignerConfig,
    CodeDesignerInputSchema,
    CodeDesignerOutputSchema,
    CodeGeneratorConfig,
    CodeGeneratorPipeline,
    CodeGeneratorPipelineConfig,
    CodeGeneratorPipelineInputSchema,
    CodeGeneratorPipelineOutputSchema,
    IntentCheckerConfig,
    render_figure_plan,
)
from akd_ext.agents.closed_loop.cm1.prompts import (
    CAPABILITY_FEASIBILITY_MAPPER_SYSTEM_PROMPT,
    CM1_ANALYSIS_METHODOLOGY,
    CM1_HARNESS_INTERFACE,
    DATA_ANALYSIS_SYSTEM_PROMPT,
    EXPERIMENT_IMPLEMENTER_SYSTEM_PROMPT,
    INTERPRETATION_PAPER_ASSEMBLY_SYSTEM_PROMPT,
    RESEARCH_REPORT_GENERATOR_SYSTEM_PROMPT,
    WORKFLOW_SPEC_BUILDER_SYSTEM_PROMPT,
)
from akd_ext.agents.closed_loop.cm1.tools import (
    _mcp_auth_headers,
    get_default_impl_tools,
    get_default_report_tools,
)
from akd_ext.agents.closed_loop.stages.capability_feasibility_mapper import (
    CapabilityFeasibilityMapperAgent,
    CapabilityFeasibilityMapperConfig,
)
from akd_ext.agents.closed_loop.stages.experiment_analysis import (
    ExperimentAnalysisAgent,
    ExperimentAnalysisConfig,
    ExperimentAnalysisInputSchema,
    ExperimentAnalysisOutputSchema,
)
from akd_ext.agents.closed_loop.stages.experiment_implementation import (
    ExperimentImplementationAgent,
    ExperimentImplementationConfig,
)
from akd_ext.agents.closed_loop.stages.interpretation_paper_assembly import (
    InterpretationPaperAssemblyAgent,
    InterpretationPaperAssemblyConfig,
)
from akd_ext.agents.closed_loop.stages.research_report_generator import (
    ResearchReportGeneratorAgent,
    ResearchReportGeneratorConfig,
)
from akd_ext.agents.closed_loop.stages.workflow_spec_builder import (
    WorkflowSpecBuilderAgent,
    WorkflowSpecBuilderConfig,
)

_CONTEXT_DIR = Path(__file__).parent / "context"


def _load_cm1_and_cluster_context() -> dict[str, str]:
    """Load both CM1 README and Cluster IT context files."""
    return {
        "Cluster IT Context": (_CONTEXT_DIR / "cluster_it.md").read_text(),
        "CM1 README Context": (_CONTEXT_DIR / "cm1_readme.md").read_text(),
    }


def _load_cm1_context() -> dict[str, str]:
    """Load CM1 README context file only."""
    return {
        "CM1 README Context": (_CONTEXT_DIR / "cm1_readme.md").read_text(),
    }


# -----------------------------------------------------------------------------
# Stage 2: Capability & Feasibility Mapper
# -----------------------------------------------------------------------------


class CM1CapabilityFeasibilityMapperConfig(CapabilityFeasibilityMapperConfig):
    """CM1-specific configuration for Capability & Feasibility Mapper."""

    system_prompt: str = Field(default=CAPABILITY_FEASIBILITY_MAPPER_SYSTEM_PROMPT)
    context_files: dict[str, str] = Field(default_factory=_load_cm1_and_cluster_context)
    description: str = Field(
        default="Research-analysis agent that evaluates whether research questions and hypotheses can be "
        "realistically tested using available numerical models (CM1, WRF, HWRF, OLAM), codebases, and "
        "cluster resources. Produces structured capability-feasibility assessment reports with evidence "
        "paths and capability vs feasibility matrices. May also produce free-form text responses to "
        "chat with the user for clarification, approval gates, or status updates."
    )


class CM1CapabilityFeasibilityMapperAgent(CapabilityFeasibilityMapperAgent):
    """CM1-specialized Capability & Feasibility Mapper Agent."""

    config_schema = CM1CapabilityFeasibilityMapperConfig


# -----------------------------------------------------------------------------
# Stage 3: Workflow Spec Builder
# -----------------------------------------------------------------------------


class CM1WorkflowSpecBuilderConfig(WorkflowSpecBuilderConfig):
    """CM1-specific configuration for Workflow Spec Builder."""

    system_prompt: str = Field(default=WORKFLOW_SPEC_BUILDER_SYSTEM_PROMPT)
    context_files: dict[str, str] = Field(default_factory=_load_cm1_context)
    description: str = Field(
        default="Stage-3 experiment design agent that converts research questions into scientifically "
        "traceable, feasibility-aware simulation workflow specifications for CM1 or WRF. Proposes "
        "baseline plus perturbation experiments, parameter sweeps, and namelist changes as execution-ready "
        "Markdown documents. May also produce free-form text responses to chat with the user for "
        "clarification, approval gates, or status updates."
    )


class CM1WorkflowSpecBuilderAgent(WorkflowSpecBuilderAgent):
    """CM1-specialized Workflow Spec Builder Agent."""

    config_schema = CM1WorkflowSpecBuilderConfig


# -----------------------------------------------------------------------------
# Stage 4: Experiment Implementation
# -----------------------------------------------------------------------------


class CM1ExperimentImplementationConfig(ExperimentImplementationConfig):
    """CM1-specific configuration for Experiment Implementation."""

    system_prompt: str = Field(default=EXPERIMENT_IMPLEMENTER_SYSTEM_PROMPT)
    context_files: dict[str, str] = Field(default_factory=_load_cm1_context)
    tools: list[Any] = Field(default_factory=get_default_impl_tools)
    description: str = Field(
        default="Stage-4A implementation planner that translates Stage-3 workflow specs into structured "
        "FileEdit JSON and submits experiment batches as jobs via MCP tool calls. Produces deterministic "
        "edit definitions (namelist_param, sounding_profile, file_replace) without directly creating files "
        "or executing commands. May also produce free-form text responses to chat with the user for "
        "clarification, approval gates, or status updates."
    )


class CM1ExperimentImplementationAgent(ExperimentImplementationAgent):
    """CM1-specialized Experiment Implementation Agent."""

    config_schema = CM1ExperimentImplementationConfig


# -----------------------------------------------------------------------------
# Stage 5: Research Report Generator
# -----------------------------------------------------------------------------


class CM1ResearchReportGeneratorConfig(ResearchReportGeneratorConfig):
    """CM1-specific configuration for Research Report Generator."""

    system_prompt: str = Field(default=RESEARCH_REPORT_GENERATOR_SYSTEM_PROMPT)
    tools: list[Any] = Field(default_factory=get_default_report_tools)
    description: str = Field(
        default="Stage-5 report generator that produces publication-style scientific reports interpreting "
        "CM1 experiment results. Checks job status via MCP tools, fetches figure URLs, and generates "
        "Markdown reports with Abstract, Methodology, Results, Discussion, and Conclusion sections. "
        "May also produce free-form text responses to chat with the user for clarification, approval gates, "
        "or status updates."
    )


class CM1ResearchReportGeneratorAgent(ResearchReportGeneratorAgent):
    """CM1-specialized Research Report Generator Agent."""

    config_schema = CM1ResearchReportGeneratorConfig


# -----------------------------------------------------------------------------
# Stage 6: Interpretation & Paper Assembly
# -----------------------------------------------------------------------------


class CM1InterpretationPaperAssemblyConfig(InterpretationPaperAssemblyConfig):
    """CM1-specific configuration for Stage-6 Paper Assembly."""

    system_prompt: str = Field(default=INTERPRETATION_PAPER_ASSEMBLY_SYSTEM_PROMPT)
    description: str = Field(
        default="Stage-6 paper assembly agent for CM1 experiments. Takes Stage-1 hypothesis, "
        "Stage-3 experiment design, Stage-4 implementation report, and Stage-5 figure analysis, "
        "then produces a publication-style scientific report in Markdown with Abstract, Introduction, "
        "Methodology, Results, Discussion, and Conclusion sections."
    )


class CM1InterpretationPaperAssemblyAgent(InterpretationPaperAssemblyAgent):
    """CM1-specialized Stage-6 Paper Assembly Agent."""

    config_schema = CM1InterpretationPaperAssemblyConfig


# -----------------------------------------------------------------------------
# Stage 5: Experiment Analysis Agent
# -----------------------------------------------------------------------------


class CM1ExperimentAnalysisConfig(ExperimentAnalysisConfig):
    """CM1-specific configuration for the Experiment Analysis Agent."""

    system_prompt: str = Field(default=DATA_ANALYSIS_SYSTEM_PROMPT)
    # gpt-5.2 (reasoning) instead of the nano default so the conversational
    # turns are higher quality AND surface a live "thinking" trace. summary
    # "detailed" is required — "auto" skips the summary for short reasoning,
    # which left the chat looking frozen/dead while the model worked.
    model_name: str = Field(default="gpt-5.2")
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(default="low")
    reasoning_summary: Literal["auto", "detailed", "concise"] | None = Field(default="detailed")
    description: str = Field(
        default="Experiment Analysis Agent for CM1 experiments. A conversational "
        "orchestrator covering the full post-experiment analysis lifecycle: it "
        "designs the figure plan for human review, generates and validates a "
        "vetted analysis module on approval (via the code-generation pipeline), "
        "then — once the job completes — fetches figures via job_plot and runs "
        "vision-based figure analysis. Returns chat messages (TextOutput) for "
        "the design/approval/status turns and a structured analysis report when "
        "complete."
    )


# ---------------------------------------------------------------------------
# Intent classification — a small LLM decides design vs approve vs analyze.
# Free-form chat can't be routed by keywords; an LLM reads the turn (plus
# whether a plan/module exists) and returns the intent. On a vague/ambiguous
# turn it returns "clarify" so the agent asks rather than guessing an action.
# ---------------------------------------------------------------------------

# Shown when the turn is too vague to act on — ask instead of guessing.
_CLARIFY_MSG = (
    "I'm not sure what you'd like to do. You can ask me to **analyze** the "
    "result figures, **check the experiment status**, or **change the figure "
    "plan** (add/drop/alter figures). Which one?"
)

_INTENT_PROMPT = """\
You are the intent router for a chat where a scientist reviews a proposed
plot/figure plan for a tropical-cyclone experiment, then has the figures
plotted and the results analyzed.

Classify the user's latest message into EXACTLY one intent:

- "status" — the user wants to know whether the experiment job has finished.
  Choose this for any progress/timing question (e.g. "is it done?", "check
  status", "is the experiment still running?", "how's the job?"). This is
  valid AT ANY TIME, including before any plan is designed.
- "approve" — the user accepts the CURRENT plan as-is and wants the figures
  plotted. Only choose this for a CLEAR affirmation of the plan with NO
  requested change (e.g. "yes", "looks good", "perfect", "go ahead",
  "approve", "ship it"). Bare procedural words alone — "go", "proceed",
  "next", "continue", "ok" — are NOT approval; treat those as "design".
- "design" — the user wants to create or change the plan: an initial design
  request, OR any add/drop/replace/adjust request, OR a question about the
  figures.
- "analyze" — the user wants to fetch and interpret the RESULT figures
  (e.g. "analyze the results", "show me the figures", "what do the plots
  say?"). This is about reading outputs, not just checking if the job is done.
- "clarify" — a contentless acknowledgement or vague reply that does NOT
  clearly affirm the plan or name an action ("cool", "ok", "sure", "ya sure",
  "alright", "hmm", "thanks", "nice", "great", "got it"). Choose this so the
  agent can ASK the user what they want, rather than guessing.

RULES (apply in order):
- A clear yes to the CURRENT plan is ALWAYS "approve": "yes", "looks good",
  "sounds good", "perfect", "lgtm", "approve", "ship it", "plot it",
  "make the plots". These are NOT clarify.
- A contentless acknowledgement or vague reply ("cool", "ok", "sure",
  "ya sure", "go", "proceed", "thanks", "hmm") is "clarify" — it neither
  affirms the plan nor names an action. NEVER map these to "approve" or
  "design".
- If a message names MORE THAN ONE intent ("check status and analyze"), pick
  the MOST ACTIONABLE one: prefer "analyze", otherwise "status".
- When still in doubt, choose "clarify" — NEVER default to "design".

Context flags (has_plan / has_module) describe the current state."""


class _IntentInput(InputSchema):
    """Input for the intent router."""

    message: str = Field(..., description="The user's latest chat message.")
    has_plan: bool = Field(default=False, description="A figure plan has been proposed.")
    has_module: bool = Field(default=False, description="An analysis module has been generated.")


class _IntentOutput(OutputSchema):
    """Routed intent."""

    __response_field__ = "intent"
    intent: Literal["design", "approve", "analyze", "status", "clarify"] = Field(
        ..., description="The single routed intent."
    )


class _IntentClassifierConfig(PydanticAIBaseAgentConfig):
    """Small, fast model for one-shot intent routing."""

    system_prompt: str = Field(default=_INTENT_PROMPT)
    model_name: str = Field(default="openai:gpt-5-nano")


class _IntentClassifierAgent(
    PydanticAIBaseAgent[_IntentInput, _IntentOutput],
):
    """One cheap LLM call → design | approve | analyze."""

    input_schema = _IntentInput
    output_schema = _IntentOutput
    config_schema = _IntentClassifierConfig


# ---------------------------------------------------------------------------
# Status replies — a small LLM answers progress questions in plain language.
# The user phrases the same question many ways ("is it done?", "are the plots
# ready?", "did the figures come out?") and means different things — whether
# the EXPERIMENT (HPC run) finished vs whether the FIGURES are available. A
# canned sentence can't tell those apart; this agent answers the actual ask
# from the real state.
# ---------------------------------------------------------------------------

_STATUS_REPLY_PROMPT = """\
You answer a scientist's progress question about a tropical-cyclone experiment
and its analysis figures. Reply in 1-3 short sentences, plain and specific to
what they asked. No emojis. No markdown headers.

Two distinct things can be "ready", do NOT conflate them:
1. The EXPERIMENT — the HPC simulation run (experiment_status).
2. The FIGURES — the analysis plots produced from the run (figures_count > 0
   means plots are available to view; plan_approved means a figure plan was
   approved and queued for plotting).

Use the provided facts to answer the SPECIFIC question:
- If they asked about the experiment/run/job → answer from experiment_status.
- If they asked about the plots/figures/charts → answer from figures_count
  and plan_approved. If no plan is approved yet, say no plots are queued. If a
  plan is approved but figures_count is 0, say the plots aren't ready yet. If
  figures_count > 0, say N figures are ready and they can say "analyze" to
  view and interpret them.
- If ambiguous, briefly cover both.
Refer to the job by its id. Never invent a status not implied by the facts."""


class _StatusReplyInput(InputSchema):
    """Facts + question for the status responder."""

    question: str = Field(..., description="The user's latest progress question.")
    job_id: str = Field(..., description="The experiment job id.")
    experiment_status: str = Field(
        ..., description="running | complete | failed | unknown."
    )
    plan_approved: bool = Field(
        default=False, description="A figure plan was approved and queued for plotting."
    )
    figures_count: int = Field(
        default=0, description="Number of result figures available via job_plot."
    )


class _StatusReplyOutput(OutputSchema):
    """Natural-language status reply."""

    __response_field__ = "reply"
    reply: str = Field(..., description="The plain-language answer to the user.")


class _StatusReplyConfig(PydanticAIBaseAgentConfig):
    """Small, fast model for one-shot status replies."""

    system_prompt: str = Field(default=_STATUS_REPLY_PROMPT)
    model_name: str = Field(default="openai:gpt-5-nano")


class _StatusReplyAgent(
    PydanticAIBaseAgent[_StatusReplyInput, _StatusReplyOutput],
):
    """One cheap LLM call → a state-aware progress answer."""

    input_schema = _StatusReplyInput
    output_schema = _StatusReplyOutput
    config_schema = _StatusReplyConfig


def _plan_change_summary(prev_figs: list[dict[str, Any]], new_figs: list[Any]) -> str:
    """A short 'what changed' header diffing two figure plans by filename.

    Prepended to a revised plan so the scientist sees the delta (added /
    removed figures) up front instead of eyeballing the whole table.
    """
    prev_names = [f.get("filename", "") for f in prev_figs]
    new_names = [f.filename for f in new_figs]
    added = [f for f in new_figs if f.filename not in prev_names]
    removed = [n for n in prev_names if n and n not in new_names]
    lines: list[str] = []
    for f in added:
        lines.append(f"- **Added** `{f.filename}` — {f.shows}")
    for n in removed:
        lines.append(f"- **Removed** `{n}`")
    if not lines:
        return "**Plan updated** — existing figures refined (none added or removed).\n\n"
    return "**Plan updated.** Changes in this revision:\n" + "\n".join(lines) + "\n\n"


class CM1ExperimentAnalysisAgent(ExperimentAnalysisAgent):
    """CM1 Experiment Analysis Agent — single conversational orchestrator.

    The frontend registers and calls ONE agent. Internally it owns three
    components and routes each chat turn to the right one:

    1. **Design** — ``CM1PlotDesignerAgent`` proposes / revises the figure
       plan (returned as a chat message via ``render_figure_plan``).
    2. **Generate** — on 'approve', ``CodeGeneratorPipeline`` produces and
       validates the analysis module; the approved design and module are
       persisted, keyed by ``job_id``.
    3. **Analyze** — once the module is submitted and the job completes,
       the inherited base behaviour (``job_status`` → ``job_plot`` →
       ``ImageAnalyzer``) runs and returns the structured analysis.

    ``run_context`` threads through the analyze branch unchanged so the
    downstream paper-assembly stage receives the same context.
    """

    config_schema = CM1ExperimentAnalysisConfig

    @property
    def _auth_headers(self) -> dict[str, str]:
        """Auth header for the CM1 MCP server.

        Delegates to ``cm1/tools._mcp_auth_headers`` — the single source of
        scheme resolution — so job_submit (tools.py) and job_status / job_plot
        (here) can never desync on a future auth change.
        """
        return _mcp_auth_headers(self._api_key, self.config.mcp_url or "")

    # -- per-job state files (job_id namespaces design/module state) --------

    @staticmethod
    def _pending_path(job_id: str) -> Path:
        return Path(f"cm1_pending_design_{job_id}.json")

    @staticmethod
    def _module_path(job_id: str) -> Path:
        return Path(f"cm1_analysis_module_{job_id}.py")

    def _read_pending(self, job_id: str) -> dict[str, Any] | None:
        """Load the persisted figure plan, or None if absent or unreadable.

        A truncated/corrupt state file (interrupted or interleaved write)
        returns None — the caller falls back to a fresh plan — instead of
        raising JSONDecodeError out of the turn.
        """
        p = self._pending_path(job_id)
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning(f"[Stage5] pending plan for {job_id} unreadable ({exc!r}); treating as no plan")
            return None
        return data if isinstance(data, dict) else None

    def _write_pending(self, job_id: str, data: dict[str, Any]) -> None:
        """Persist the figure plan atomically (write temp + replace).

        os.replace is atomic, so an interrupted write can never leave a
        half-written file that the next read would choke on.
        """
        p = self._pending_path(job_id)
        tmp = p.with_name(p.name + ".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(p)

    def _module_is_current(self, job_id: str) -> bool:
        """True if the analysis module is already built from the CURRENT plan.

        Compares file mtimes: a module at least as new as the pending plan was
        generated from it, so re-approving would just redo identical work. If
        the plan was revised after the module (plan newer), it is stale and a
        re-approve should regenerate.
        """
        mod = self._module_path(job_id)
        if not mod.exists():
            return False
        pend = self._pending_path(job_id)
        if not pend.exists():
            return True
        return mod.stat().st_mtime >= pend.stat().st_mtime

    def _design_context(self, params: ExperimentAnalysisInputSchema) -> str:
        return (
            f"# Research Question & Hypothesis\n\n{params.hypothesis}\n\n"
            f"---\n\n# Experiment Specification\n\n{params.experiment_spec}\n"
        )

    async def _job_status(self, job_id: str) -> str:
        """Raw job status via the job_status MCP tool: complete | running |
        failed | unknown. Never raises."""
        from akd_ext.agents.closed_loop.stages.experiment_analysis import _mcp_call

        try:
            payload = await _mcp_call(
                url=self.config.mcp_url, headers=self._auth_headers,
                tool="job_status", args={"job_id": job_id}, read_timeout=60.0,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[Stage5] job_status failed: {exc!r}")
            return "unknown"
        status = self._extract_status(payload)
        if status in {"complete", "completed", "success", "succeeded", "done"}:
            return "complete"
        if status in {"failed", "error", "cancelled", "canceled"}:
            return "failed"
        if status == "unknown":
            return "unknown"
        return "running"

    def _status_sentence(self, job_id: str, status: str) -> str:
        """One plain-language line describing the experiment job status."""
        return {
            "complete": f"Your experiment (job `{job_id}`) has finished.",
            "running": f"Your experiment (job `{job_id}`) is still running in the background — this can take a while.",
            "failed": f"Your experiment (job `{job_id}`) reports a failed status.",
            "unknown": f"I couldn't read the status for job `{job_id}` right now.",
        }[status]

    async def _figures_count(self, job_id: str, workspace: str) -> int:
        """How many result figures job_plot exposes right now (0 on any error)."""
        from akd_ext.agents.closed_loop.stages.experiment_analysis import _mcp_call

        try:
            payload = await _mcp_call(
                url=self.config.mcp_url, headers=self._auth_headers,
                tool="job_plot",
                args={"job_id": job_id, "workspace_name": workspace, "user_name": ""},
                read_timeout=60.0,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[Stage5] job_plot (count) failed: {exc!r}")
            return 0
        n = 0
        for k, v in payload.items():
            if k.startswith("_") or k in ("payload", "job_id"):
                continue
            if isinstance(v, list):
                n += sum(1 for u in v if isinstance(u, str) and u.startswith("http"))
            elif isinstance(v, str) and v.startswith("http"):
                n += 1
        return n

    async def _check_status(self, job_id: str, question: str = "", workspace: str = "") -> TextOutput:
        """Answer a progress question from REAL state (job_status + job_plot).

        An LLM phrases the reply so "is the experiment done?" and "are the
        plots ready?" get distinct, accurate answers; a canned line is the
        fallback if the LLM call fails.
        """
        status = await self._job_status(job_id)
        plan_approved = self._module_path(job_id).exists()
        # Only probe figures once it's plausible they exist — a plan was
        # approved and the run has finished — to avoid a needless job_plot call.
        figs = (
            await self._figures_count(job_id, workspace)
            if (plan_approved and status == "complete")
            else 0
        )
        try:
            result = await _StatusReplyAgent().arun(_StatusReplyInput(
                question=question or "What's the status?",
                job_id=job_id,
                experiment_status=status,
                plan_approved=plan_approved,
                figures_count=figs,
            ))
            if isinstance(result, _StatusReplyOutput) and result.reply.strip():
                return TextOutput(content=result.reply.strip())
            raise ValueError("status responder returned no reply")
        except Exception as exc:  # noqa: BLE001 — never crash on a status check
            logger.warning(f"[Stage5] status LLM failed ({exc!r}); using canned line")
            line = self._status_sentence(job_id, status)
            if status == "complete" and figs:
                line += f" {figs} figure(s) are ready — say 'analyze' to view and interpret them."
            elif status == "complete":
                line += " Say 'analyze' once a figure plan is approved to fetch the results."
            elif status == "running":
                line += " Ask me to check again in a bit."
            return TextOutput(content=line)

    # -- orchestration ------------------------------------------------------
    #
    # The routing lives once in _astream; _arun drains it and returns the
    # final output. The analyze branch delegates to the inherited base
    # streaming pipeline, so run_context flows to the downstream stage
    # unchanged. (Same single-source-of-truth pattern as CodeGeneratorPipeline.)

    async def _generate_module(
        self, params: ExperimentAnalysisInputSchema, meta: dict[str, Any]
    ) -> TextOutput:
        """Run the code-generation pipeline on an approved design."""
        pipeline = CodeGeneratorPipeline(CodeGeneratorPipelineConfig(
            designer_config=CodeDesignerConfig(
                data_format_context=CM1_HARNESS_INTERFACE,
                analysis_methodology=CM1_ANALYSIS_METHODOLOGY,
            ),
            generator_config=CodeGeneratorConfig(data_format_context=CM1_HARNESS_INTERFACE),
            intent_checker_config=IntentCheckerConfig(data_format_context=CM1_HARNESS_INTERFACE),
        ))
        gen = await pipeline.arun(CodeGeneratorPipelineInputSchema(
            context=self._design_context(params),
            design_document=meta["design_document"],
            success_criteria=meta.get("success_criteria", []),
        ))
        if isinstance(gen, CodeGeneratorPipelineOutputSchema) and gen.vetted_code:
            # Persist the vetted plot module locally (artifact / fallback)...
            code = gen.vetted_code.code
            self._module_path(params.job_id).write_text(code, encoding="utf-8")
            module_file = self._module_path(params.job_id).name
            # ...then SHIP it to the harness via the code_submit MCP tool, which
            # runs cm1_harness.py on the experiment data and produces the
            # figures that job_plot will return. If the endpoint isn't
            # reachable, fall back to an honest "generated, not submitted".
            from akd_ext.agents.closed_loop.stages.experiment_analysis import _mcp_call

            try:
                payload = await _mcp_call(
                    url=self.config.mcp_url, headers=self._auth_headers,
                    tool="code_submit",
                    args={"code": code, "job_id": params.job_id},
                    read_timeout=600.0,  # the harness run is synchronous
                )
            except Exception as exc:  # noqa: BLE001 — endpoint may be absent
                logger.warning(f"[Stage5] code_submit unavailable: {exc!r}")
                return TextOutput(content=(
                    f"**Plan approved — analysis module generated** "
                    f"(`{module_file}`). I couldn't reach the harness submit "
                    f"endpoint ({exc}), so it hasn't run yet. Once it's run "
                    f"through the harness, ask me to 'analyze' to fetch the figures."
                ))
            if payload.get("status") == "completed":
                n = payload.get("figures_produced", 0)
                return TextOutput(content=(
                    f"**Plan approved and submitted.** The harness ran the "
                    f"analysis module and produced {n} figure(s). Ask me to "
                    f"'analyze' to fetch and interpret them."
                ))
            err = payload.get("error") or (payload.get("log_tail", "")[-400:]) or "unknown error"
            return TextOutput(content=(
                f"**Plan approved**, but the harness run failed:\n{err}\n\n"
                f"Revise the plan (e.g. 'drop figure 6') and approve again."
            ))
        attempts = getattr(gen, "attempt_history", []) or []
        trail = "\n".join(
            f"  - attempt {a.attempt}: {a.stage_failed or 'ok'} — {a.failure_reason}"
            for a in attempts if not a.passed
        )
        reason = getattr(gen, "rejection_reason", str(gen))
        return TextOutput(content=(
            f"Code generation failed after {len(attempts)} attempts — no module generated.\n"
            f"Most recent reason: {reason}\n"
            + (f"{trail}\n" if trail else "")
            + "Reply with a change (e.g. 'drop figure 6') and I'll revise the plan, then approve again."
        ))

    async def _design(
        self, params: ExperimentAnalysisInputSchema
    ) -> ExperimentAnalysisOutputSchema | TextOutput:  # type: ignore[name-defined]
        """Propose or revise the figure plan; persist it keyed by job_id.

        Revisions are CUMULATIVE: the current plan is fed back to the
        designer with an instruction to apply only the requested change and
        preserve everything else, so edits accumulate across turns instead
        of regenerating from scratch.
        """
        msg = (params.message or "").strip()
        low = msg.lower()
        base_ctx = self._design_context(params)
        # The FIRST turn is the greeting. "Fresh" = no readable plan on disk —
        # so a missing OR corrupt state file both fall back to a fresh plan
        # (never crash on a truncated file).
        prev = self._read_pending(params.job_id)
        is_fresh = prev is None

        if not is_fresh:
            # Cumulative revision — give the designer the EXACT current plan
            # and ask it to apply only this delta, keeping all else unchanged.
            ctx = (
                base_ctx
                + "\n\n---\n# CURRENT FIGURE PLAN (revise THIS document)\n\n"
                + prev["design_document"]
                + "\n\n---\nREVISION REQUESTED by the reviewing scientist:\n"
                + msg
                + "\nApply ONLY this change. Keep every other figure exactly as "
                "it is above — do not re-add figures previously removed, and do "
                "not drop figures not mentioned."
            )
        elif low:
            # First turn — pass whatever the scientist typed as soft guidance
            # for the initial plan, then still greet. A bare "hi" is harmless
            # here: the designer simply ignores it and proposes the default plan.
            ctx = base_ctx + f"\n\n---\nInitial focus requested by the scientist:\n{msg}"
        else:
            ctx = base_ctx
        design = await CM1PlotDesignerAgent().arun(CodeDesignerInputSchema(context=ctx))
        if isinstance(design, CodeDesignerOutputSchema):
            self._write_pending(params.job_id, {
                "design_document": design.design_document,
                "success_criteria": design.success_criteria,
                "figures": [f.model_dump() for f in design.figures],
            })
            if is_fresh:
                # First entry into the stage — introduce ourselves, check the
                # real job status, then present the plan proactively (no
                # "design" command needed).
                intro = (
                    "Hi — I'm the **Stage 5 Data Analysis agent**. I help you turn "
                    "your CM1 experiment into figures that test your hypothesis. "
                    "You can ask me to **check the experiment status** any time, "
                    "and we'll **design the plots together** — review each figure "
                    "and why it matters, refine the set, then approve to plot."
                )
                status = await self._job_status(params.job_id)
                line = self._status_sentence(params.job_id, status)
                if status == "complete":
                    lead = f"{intro}\n\n{line} Here's the analysis plan I propose:"
                    tail = (
                        "Refine the plan (e.g. \"drop the CAPE figures\") or say "
                        "\"looks good\" to plot the figures; then ask me to "
                        "\"analyze\" the results."
                    )
                else:
                    lead = (
                        f"{intro}\n\n{line} Meanwhile, here's the analysis plan I "
                        "propose, so it's ready the moment the run finishes:"
                    )
                    tail = (
                        "Refine it (e.g. \"drop the CAPE figures\", \"add a "
                        "vorticity panel\") or say \"looks good\" to queue the "
                        "plots. When you're ready, ask me to check whether the "
                        "experiment has finished."
                    )
                return TextOutput(content=f"{lead}\n\n{render_figure_plan(design)}\n\n{tail}")
            # Revision: lead with what changed (added/removed figures), since
            # `prev` is in scope here (this branch only runs when not is_fresh).
            return TextOutput(content=(
                _plan_change_summary(prev.get("figures", []), design.figures)
                + render_figure_plan(design)
                + "\n\n*(reply with feedback to revise, or 'approve' to plot the figures)*"
            ))
        return design  # TextOutput passthrough

    def _resolve_turn(
        self, params: ExperimentAnalysisInputSchema, run_context: RunContext
    ) -> str:
        """The user's latest chat turn.

        Works under both drivers:
        - **Notebook**: the turn is passed in ``params.message``.
        - **LangGraph / HITL**: the message field is empty; the turn lives in
          ``run_context`` — either ``human_response.content`` (on resume) or
          the last ``role='user'`` entry in the carried ``messages`` history.
        """
        if (params.message or "").strip():
            return params.message.strip()

        # LangGraph/UI driver delivers the reply as 'query' (inputs.<node>.query
        # on resume) instead of 'message'. Treat it as the same chat turn.
        if (getattr(params, "query", None) or "").strip():
            return params.query.strip()

        hr = getattr(run_context, "human_response", None)
        content = getattr(hr, "content", None)
        if content:
            return content if isinstance(content, str) else str(content)

        for m in reversed(getattr(run_context, "messages", None) or []):
            role = m.get("role") if isinstance(m, dict) else getattr(m, "role", None)
            if role == "user":
                c = m.get("content") if isinstance(m, dict) else getattr(m, "content", "")
                if c:
                    return c if isinstance(c, str) else str(c)
        return ""

    async def _route(self, turn: str, job_id: str) -> str:
        """Classify the chat turn into 'analyze' | 'approve' | 'design'.

        A small LLM (``_IntentClassifierAgent``) reads the turn plus the
        current state and returns the intent. If that call fails we fall back
        to a safe, non-destructive default for the current state (no keyword
        guessing). State gates are applied last: 'analyze' is only actionable
        once a module exists.
        """
        has_module = self._module_path(job_id).exists()
        has_plan = self._pending_path(job_id).exists()

        # First turn of the chat (no plan and nothing generated yet): whatever
        # the scientist typed, greet them — the greeting already checks the
        # live job status AND shows the proposed plan. They never need a magic
        # word; "hi", "is it done?", or "make intensity plots" all land here.
        if not has_plan and not has_module:
            return "design"

        intent = "design"
        try:
            result = await _IntentClassifierAgent().arun(
                _IntentInput(message=turn, has_plan=has_plan, has_module=has_module),
            )
            if isinstance(result, _IntentOutput):
                intent = result.intent
            else:
                raise ValueError("classifier returned non-structured output")
        except Exception as exc:  # noqa: BLE001 — fall back, never crash routing
            logger.warning(f"[Stage5] intent LLM failed ({exc!r}); using safe default")
            # No keyword guessing: pick the safe, non-destructive intent for the
            # current state — poll status when there are results to look at,
            # otherwise (re)show the plan. Never auto-approve/analyze on a guess.
            intent = "status" if has_module else "design"

        # State gate: 'analyze' (reading result figures) needs a module; a bare
        # status check works any time. Downgrade analyze→status before a module
        # exists so "show me results" early still gives a useful answer.
        if intent == "analyze" and not has_module:
            intent = "status"
        # Nothing to approve/analyze before a plan exists — the very first turn
        # (whatever the scientist typed) goes to design, which greets + shows
        # the plan. Pure status questions are still allowed through.
        if not has_plan and intent in {"approve", "analyze"}:
            intent = "design"
        return intent

    async def _astream(  # type: ignore[override]
        self,
        params: ExperimentAnalysisInputSchema,
        run_context: RunContext,
        **kwargs: Any,
    ) -> AsyncIterator[StreamEvent]:
        cn = self.__class__.__name__
        # Immediate feedback so the chat doesn't look dead while we route. The
        # intent-classification LLM call below takes a beat before the
        # phase-specific "Designing…/Checking…/Analyzing…" line appears, so emit
        # a generic progress line the instant the turn arrives.
        yield RunningEvent(source=cn, message="Thinking…", run_context=run_context)
        # Resolve the user's turn from run_context (LangGraph) or message
        # (notebook), then make it visible to the downstream helpers.
        params = params.model_copy(update={"message": self._resolve_turn(params, run_context)})
        phase = await self._route(params.message, params.job_id)

        # --- analyze: delegate to the inherited streaming pipeline
        #     (job_status → job_plot → ImageAnalyzer). run_context threads
        #     through untouched for the downstream stage.
        if phase == "analyze":
            async for event in super()._astream(params, run_context, **kwargs):
                yield event
            return

        yield StartingEvent(
            source=cn, message=f"Starting {cn}",
            data=StartingEventData[ExperimentAnalysisInputSchema](params=params),
            run_context=run_context,
        )

        # --- status: poll the experiment job (works any time)
        if phase == "status":
            yield RunningEvent(source=cn, message="Checking experiment job status…", run_context=run_context)
            out: ExperimentAnalysisOutputSchema | TextOutput = await self._check_status(
                params.job_id, question=params.message, workspace=params.workspace_name)
            yield CompletedEvent(source=cn, message=f"Completed {cn}", data=CompletedEventData(output=out), run_context=run_context)
            return

        # --- approve: generate the analysis module
        if phase == "approve":
            meta = self._read_pending(params.job_id)
            if meta is None:
                out: ExperimentAnalysisOutputSchema | TextOutput = TextOutput(
                    content="Nothing to approve yet — send 'design' to get a figure plan first."
                )
            elif self._module_is_current(params.job_id):
                out = TextOutput(content=(
                    "The plan is already approved and the analysis module is generated — "
                    "nothing to re-generate. Ask me to 'check status' or 'analyze' the results "
                    "(revise the plan first if you want different figures)."
                ))
            else:
                yield RunningEvent(source=cn, message="Plotting the approved figures…", run_context=run_context)
                out = await self._generate_module(params, meta)
            yield CompletedEvent(source=cn, message=f"Completed {cn}", data=CompletedEventData(output=out), run_context=run_context)
            return

        # --- clarify: the turn was too vague to act on — ask, don't guess
        if phase == "clarify":
            yield CompletedEvent(
                source=cn, message=f"Completed {cn}",
                data=CompletedEventData(output=TextOutput(content=_CLARIFY_MSG)),
                run_context=run_context,
            )
            return

        # --- design / revise the figure plan
        yield RunningEvent(source=cn, message="Designing the figure plan…", run_context=run_context)
        out = await self._design(params)
        yield CompletedEvent(source=cn, message=f"Completed {cn}", data=CompletedEventData(output=out), run_context=run_context)

    async def _arun(  # type: ignore[override]
        self,
        params: ExperimentAnalysisInputSchema,
        run_context: RunContext,
        **kwargs: Any,
    ) -> ExperimentAnalysisOutputSchema | TextOutput:  # type: ignore[name-defined]
        params = params.model_copy(update={"message": self._resolve_turn(params, run_context)})
        phase = await self._route(params.message, params.job_id)

        if phase == "analyze":
            return await super()._arun(params, run_context, **kwargs)

        if phase == "status":
            return await self._check_status(
                params.job_id, question=params.message, workspace=params.workspace_name)

        if phase == "approve":
            meta = self._read_pending(params.job_id)
            if meta is None:
                return TextOutput(content="Nothing to approve yet — send 'design' to get a figure plan first.")
            if self._module_is_current(params.job_id):
                return TextOutput(content=(
                    "The plan is already approved and the analysis module is generated — "
                    "nothing to re-generate. Ask me to 'check status' or 'analyze' the results "
                    "(revise the plan first if you want different figures)."
                ))
            return await self._generate_module(params, meta)

        if phase == "clarify":
            return TextOutput(content=_CLARIFY_MSG)

        return await self._design(params)


# -----------------------------------------------------------------------------
# Stage 5b: Post-Experiment Plot Designer (human approval gate)
# -----------------------------------------------------------------------------


class CM1PlotDesignerConfig(CodeDesignerConfig):
    """CM1-specific configuration for the post-experiment Plot Designer."""

    data_format_context: str = Field(default=CM1_HARNESS_INTERFACE)
    analysis_methodology: str = Field(default=CM1_ANALYSIS_METHODOLOGY)
    description: str = Field(
        default=(
            "Stage-5 (CM1 closed loop): designs the post-experiment analysis "
            "figure plan for HUMAN REVIEW. Present the structured `figures` "
            "field to the user — each entry states the figure, what it "
            "shows, and WHY it is generated (its link to the hypothesis); "
            "use render_figure_plan() for the review table. Iterate on the "
            "user's feedback (re-run with the feedback appended to the "
            "context). Code generation is gated on approval: ONLY after the "
            "user explicitly confirms the plan, run the CodeGeneratorPipeline "
            "with the approved design_document and success_criteria to "
            "produce and submit the analysis module. Do not use this agent "
            "for any other purpose."
        )
    )


class CM1PlotDesignerAgent(CodeDesignerAgent):
    """CM1-specialized Plot Designer — the human approval gate before generation.

    Produces the figure-plan design document for the user to review in
    chat. The CodeGeneratorPipeline runs only after explicit confirmation,
    receiving the approved design via ``design_document`` /
    ``success_criteria`` on its input schema (which skips the internal
    designer).
    """

    config_schema = CM1PlotDesignerConfig
