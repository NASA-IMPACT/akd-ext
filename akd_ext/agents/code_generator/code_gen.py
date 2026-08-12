"""Code Generator Pipeline — orchestrates design → generate → validate.

Flow:
    1. **Designer** produces a design document → ``CodeDesignerOutputSchema``.
       Structural validation (missing sections, empty success criteria)
       happens inside the agent itself: ``check_output`` is wired into
       pydantic_ai's retry loop, so ``designer.arun()`` only returns
       validated output.
    2. **Generator** produces code from the design document.
    3. **Validators** (allowlist → bandit → intent checker) vet the code.
    4. On failure → feed the failure reason back as ``correction_feedback``
       and retry from step 2 (up to ``max_retries`` times).
    5. On success → return ``CodeGeneratorPipelineOutputSchema`` with
       :class:`VettedCode`.

The pipeline itself never calls an LLM directly — it delegates to the
three sub-agents and the two pure-function validators. The orchestration
logic lives in ``_astream``; ``_arun`` drains the stream and returns the
final output, so there is exactly one copy of the loop.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any, Literal

from loguru import logger
from pydantic import Field

from akd._base import (
    CompletedEvent,
    CompletedEventData,
    RunContext,
    RunningEvent,
    StartingEvent,
    StartingEventData,
    StreamEvent,
    TextOutput,
)
from akd_ext.agents._base import OpenAIBaseAgent, OpenAIBaseAgentConfig
from akd_ext.agents.code_generator.designer import (
    CodeDesignerAgent,
    CodeDesignerConfig,
)
from akd_ext.agents.code_generator.generator import (
    CodeGeneratorAgent,
    CodeGeneratorConfig,
)
from akd_ext.agents.code_generator.schemas import (
    AttemptRecord,
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
from akd_ext.agents.code_generator.validator import (
    IntentCheckerAgent,
    IntentCheckerConfig,
    check_allowlist,
    check_bandit,
    severity_rank,
)

__all__ = [
    "CodeGeneratorPipeline",
    "CodeGeneratorPipelineConfig",
]


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


class CodeGeneratorPipelineConfig(OpenAIBaseAgentConfig):
    """Configuration for the code-generation pipeline."""

    max_retries: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Max generator attempts before giving up.",
    )
    bandit_fail_on: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        default="HIGH",
        description="Minimum bandit severity that causes a failure.",
    )
    designer_config: CodeDesignerConfig = Field(
        default_factory=CodeDesignerConfig,
        description="Forwarded to the Code Designer.",
    )
    generator_config: CodeGeneratorConfig = Field(
        default_factory=CodeGeneratorConfig,
        description="Forwarded to the Code Generator.",
    )
    intent_checker_config: IntentCheckerConfig = Field(
        default_factory=IntentCheckerConfig,
        description="Forwarded to the Intent Checker.",
    )


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class CodeGeneratorPipeline(
    OpenAIBaseAgent[CodeGeneratorPipelineInputSchema, CodeGeneratorPipelineOutputSchema],
):
    """Orchestrator: designer → generator → validators → retry loop.

    This agent never calls an LLM directly. All intelligence lives in the
    three sub-agents (designer, generator, intent checker). The pipeline's
    job is deterministic orchestration: sequencing, validation,
    retry routing, and report assembly.
    """

    input_schema = CodeGeneratorPipelineInputSchema
    output_schema = CodeGeneratorPipelineOutputSchema | TextOutput
    config_schema = CodeGeneratorPipelineConfig

    # -- Sub-agent factories -----------------------------------------------

    def _make_designer(self) -> CodeDesignerAgent:
        return CodeDesignerAgent(self.config.designer_config)

    def _make_generator(self) -> CodeGeneratorAgent:
        return CodeGeneratorAgent(self.config.generator_config)

    def _make_intent_checker(self) -> IntentCheckerAgent:
        return IntentCheckerAgent(self.config.intent_checker_config)

    # -- Validator runner --------------------------------------------------

    def _run_deterministic_validators(
        self, code: str,
    ) -> ValidationResult:
        """Run allowlist + bandit (cheap, no LLM). Returns aggregated result."""
        reasons: list[str] = []

        al = check_allowlist(code)
        if not al.passed:
            reasons.extend(al.violations)

        bd = check_bandit(code, fail_on=self.config.bandit_fail_on)
        if not bd.passed:
            if bd.error:
                reasons.append(f"bandit error: {bd.error}")
            else:
                reasons.extend(
                    f"bandit {f.severity}/{f.confidence} line {f.line}: {f.issue}"
                    for f in bd.findings
                    if severity_rank(f.severity) >= severity_rank(self.config.bandit_fail_on)
                )

        return ValidationResult(
            passed=al.passed and bd.passed,
            allowlist_passed=al.passed,
            bandit_passed=bd.passed,
            failure_reasons=reasons,
        )

    # -- Report builder ----------------------------------------------------

    @staticmethod
    def _build_report(
        *,
        attempt: int,
        max_retries: int,
        vetted: VettedCode | None,
        rejected: bool,
        rejection_reason: str,
    ) -> str:
        """Build a short markdown report summarising the pipeline run."""
        lines: list[str] = ["# Code Generator Pipeline Report", ""]
        if vetted:
            lines.append(f"**Status:** ✅ Approved on attempt {attempt}/{max_retries}")
            lines.append(f"**Libraries:** {', '.join(vetted.libraries) or 'none'}")
            lines.append(f"**Output files:** {', '.join(vetted.output_files) or 'none'}")
            lines.append(f"\n{vetted.explanation}")
        else:
            lines.append(f"**Status:** ❌ Rejected after {attempt}/{max_retries} attempts")
            lines.append(f"**Reason:** {rejection_reason}")
        return "\n".join(lines)

    # -- _arun: batch mode drains the stream --------------------------------

    async def _arun(
        self,
        params: CodeGeneratorPipelineInputSchema,
        run_context: RunContext,
        **kwargs: Any,
    ) -> CodeGeneratorPipelineOutputSchema | TextOutput:
        """Drain :meth:`_astream` and return the final output.

        The orchestration loop is implemented exactly once, in
        ``_astream``. Batch mode consumes the events and keeps only the
        ``CompletedEvent`` payload; progress is carried by the
        ``RunningEvent`` stream (internal diagnostics log at DEBUG).
        """
        final: CodeGeneratorPipelineOutputSchema | TextOutput | None = None
        async for event in self._astream(params, run_context, **kwargs):
            if isinstance(event, CompletedEvent):
                final = event.data.output
        if final is None:
            return TextOutput(content="Pipeline completed without producing output.")
        return final

    # -- _astream: the single copy of the orchestration loop ----------------

    async def _astream(
        self,
        params: CodeGeneratorPipelineInputSchema,
        run_context: RunContext,
        **kwargs: Any,
    ) -> AsyncIterator[StreamEvent]:
        cn = self.__class__.__name__

        yield StartingEvent(
            source=cn,
            message=f"Starting {cn}",
            data=StartingEventData[CodeGeneratorPipelineInputSchema](params=params),
            run_context=run_context,
        )

        # 1. Design. When the caller supplies a pre-approved design
        #    (human-in-the-loop flows), the internal designer is skipped.
        #    Otherwise structural validation + retry happen inside arun():
        #    the agent's check_output is registered as a pydantic_ai output
        #    validator, so invalid designs are retried before this returns.
        if params.design_document.strip():
            design_doc = params.design_document
            success_criteria = params.success_criteria
            logger.debug("[CodeGenPipeline] using pre-approved design document — designer skipped")
            yield RunningEvent(
                source=cn,
                message=f"Using pre-approved design document ({len(success_criteria)} success criteria) — designer skipped",
                run_context=run_context,
            )
        else:
            yield RunningEvent(source=cn, message="Producing design document…", run_context=run_context)

            designer = self._make_designer()
            try:
                plan_output = await designer.arun(params.to_designer_input())
            except Exception as exc:  # noqa: BLE001 — never let the stream die without a final event
                logger.exception("[CodeGenPipeline] designer raised")
                plan_output = None
                designer_error: str | None = f"Designer raised an error: {exc}"
            else:
                designer_error = None

            if designer_error is not None or not isinstance(plan_output, CodeDesignerOutputSchema):
                final = TextOutput(content=designer_error or f"Designer failed: {plan_output}")
                yield CompletedEvent(
                    source=cn, message=f"Completed {cn}",
                    data=CompletedEventData(output=final), run_context=run_context,
                )
                return

            design_doc = plan_output.design_document
            success_criteria = plan_output.success_criteria
            yield RunningEvent(
                source=cn,
                message=f"Design document ready ({len(plan_output.libraries)} libraries, {len(plan_output.output_files)} outputs, {len(success_criteria)} success criteria)",
                run_context=run_context,
            )

        # 2. Generate + validation loop. The agents are stateless — build
        #    them once, not per attempt.
        generator = self._make_generator()
        intent_checker = self._make_intent_checker()

        correction_feedback = ""
        last_reason = ""
        attempt_history: list[AttemptRecord] = []

        for attempt in range(1, self.config.max_retries + 1):
            logger.debug(f"[CodeGenPipeline] attempt {attempt}/{self.config.max_retries}")
            yield RunningEvent(
                source=cn,
                message=f"Generating code (attempt {attempt}/{self.config.max_retries})…",
                run_context=run_context,
            )

            try:
                gen_output = await generator.arun(
                    CodeGeneratorInputSchema(
                        design_document=design_doc,
                        context=params.context,
                        correction_feedback=correction_feedback,
                    ),
                )
            except Exception as exc:  # noqa: BLE001 — feed the error into the retry loop
                last_reason = f"generator raised: {exc}"
                correction_feedback = (
                    "The previous attempt errored before producing code: "
                    f"{exc}. Regenerate complete, valid output."
                )
                attempt_history.append(AttemptRecord(
                    attempt=attempt, stage_failed="generator",
                    failure_reason=last_reason[:200],
                ))
                logger.warning(f"[CodeGenPipeline] attempt {attempt} generator raised: {exc}")
                yield RunningEvent(
                    source=cn,
                    message=f"Attempt {attempt}: generator error — {str(exc)[:120]}",
                    run_context=run_context,
                )
                continue
            if not isinstance(gen_output, CodeGeneratorOutputSchema):
                correction_feedback = f"Generator returned unexpected output: {gen_output}"
                last_reason = correction_feedback
                attempt_history.append(AttemptRecord(
                    attempt=attempt, stage_failed="generator",
                    failure_reason=last_reason[:200],
                ))
                logger.warning(f"[CodeGenPipeline] attempt {attempt} generator error")
                yield RunningEvent(source=cn, message=f"Attempt {attempt}: generator error", run_context=run_context)
                continue

            # 3a. Deterministic validators
            yield RunningEvent(source=cn, message=f"Running validators (attempt {attempt})…", run_context=run_context)

            # bandit shells out via blocking subprocess.run (up to 30s); run it
            # off the event loop so concurrent coroutines/clients aren't frozen
            # — critical in the async FastMCP-served environment.
            det = await asyncio.to_thread(self._run_deterministic_validators, gen_output.code)
            if not det.passed:
                correction_feedback = (
                    "The previous code failed validation. Fix these issues:\n"
                    + "\n".join(f"- {r}" for r in det.failure_reasons)
                )
                last_reason = "; ".join(det.failure_reasons)
                stage = "allowlist" if not det.allowlist_passed else "bandit"
                attempt_history.append(AttemptRecord(
                    attempt=attempt, stage_failed=stage,
                    failure_reason=last_reason[:200],
                ))
                logger.warning(f"[CodeGenPipeline] attempt {attempt} det validation fail: {last_reason}")
                yield RunningEvent(
                    source=cn,
                    message=f"Attempt {attempt}: deterministic validators failed — {last_reason[:120]}",
                    run_context=run_context,
                )
                continue

            # 3b. LLM intent checker (with structured success criteria)
            yield RunningEvent(source=cn, message=f"Intent check (attempt {attempt})…", run_context=run_context)

            try:
                verdict = await intent_checker.arun(
                    IntentCheckerInputSchema(
                        context=params.context,
                        design_document=design_doc,
                        code=gen_output.code,
                        success_criteria=success_criteria,
                    ),
                )
            except Exception as exc:  # noqa: BLE001 — feed the error into the retry loop
                last_reason = f"intent checker raised: {exc}"
                correction_feedback = (
                    f"The intent check errored: {exc}. Regenerate the code."
                )
                attempt_history.append(AttemptRecord(
                    attempt=attempt, stage_failed="intent",
                    failure_reason=last_reason[:200],
                ))
                logger.warning(f"[CodeGenPipeline] attempt {attempt} intent checker raised: {exc}")
                yield RunningEvent(
                    source=cn,
                    message=f"Attempt {attempt}: intent check error — {str(exc)[:120]}",
                    run_context=run_context,
                )
                continue
            if not isinstance(verdict, IntentCheckerOutputSchema):
                correction_feedback = f"Intent checker returned unexpected output: {verdict}"
                last_reason = correction_feedback
                attempt_history.append(AttemptRecord(
                    attempt=attempt, stage_failed="intent",
                    failure_reason=last_reason[:200],
                ))
                logger.warning(f"[CodeGenPipeline] attempt {attempt} intent checker error")
                continue

            if not verdict.approved:
                fixes = "\n".join(f"- {f}" for f in verdict.suggested_fixes) if verdict.suggested_fixes else ""
                correction_feedback = (
                    f"The intent checker rejected the code (confidence={verdict.confidence:.2f}).\n"
                    f"Reasoning: {verdict.reasoning}\n"
                    f"{fixes}"
                )
                last_reason = verdict.reasoning
                attempt_history.append(AttemptRecord(
                    attempt=attempt, stage_failed="intent",
                    failure_reason=last_reason[:200],
                ))
                logger.warning(f"[CodeGenPipeline] attempt {attempt} intent fail: {verdict.reasoning}")
                yield RunningEvent(
                    source=cn,
                    message=f"Attempt {attempt}: intent check failed — {verdict.reasoning[:120]}",
                    run_context=run_context,
                )
                continue

            # Final guard before approving: never return an "approved" result
            # with empty code. This runs inline (the pipeline overrides
            # _arun/_astream, so the base's check_output machinery never fires)
            # and routes an empty result back through the retry loop.
            if not gen_output.code.strip():
                correction_feedback = (
                    "All checks passed but the code field is empty. Regenerate "
                    "complete, self-contained source."
                )
                last_reason = "approved output had empty code"
                attempt_history.append(AttemptRecord(
                    attempt=attempt, stage_failed="generator",
                    failure_reason=last_reason,
                ))
                logger.warning(f"[CodeGenPipeline] attempt {attempt} empty code after validation")
                yield RunningEvent(
                    source=cn,
                    message=f"Attempt {attempt}: approved output had empty code — retrying",
                    run_context=run_context,
                )
                continue

            # All validators passed
            attempt_history.append(AttemptRecord(
                attempt=attempt, passed=True,
            ))
            vetted = VettedCode(
                code=gen_output.code,
                libraries=gen_output.libraries,
                output_files=gen_output.output_files,
                explanation=gen_output.explanation,
            )
            final_output = CodeGeneratorPipelineOutputSchema(
                vetted_code=vetted,
                rejected=False,
                report=self._build_report(
                    attempt=attempt,
                    max_retries=self.config.max_retries,
                    vetted=vetted,
                    rejected=False,
                    rejection_reason="",
                ),
                design_document=design_doc,
                attempt_history=attempt_history,
            )
            yield CompletedEvent(
                source=cn, message=f"Completed {cn}",
                data=CompletedEventData(output=final_output), run_context=run_context,
            )
            return

        # Exhausted retries
        final_output = CodeGeneratorPipelineOutputSchema(
            vetted_code=None,
            rejected=True,
            rejection_reason=last_reason,
            report=self._build_report(
                attempt=self.config.max_retries,
                max_retries=self.config.max_retries,
                vetted=None,
                rejected=True,
                rejection_reason=last_reason,
            ),
            design_document=design_doc,
            attempt_history=attempt_history,
        )
        yield CompletedEvent(
            source=cn, message=f"Completed {cn}",
            data=CompletedEventData(output=final_output), run_context=run_context,
        )
