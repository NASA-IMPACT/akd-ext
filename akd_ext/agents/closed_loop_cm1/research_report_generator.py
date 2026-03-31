"""Stage-5 Research Report Generator Agent.

This module implements the Stage-5 Research Report Generator, which takes
the workflow specification (containing research question, hypothesis, and
experiment design) plus generated figures and produces a publication-style
scientific report.

Public API:
    ResearchReportGeneratorAgent,
    ResearchReportGeneratorInputSchema,
    ResearchReportGeneratorOutputSchema,
    ResearchReportGeneratorConfig
"""
from __future__ import annotations

import os
from typing import Any, Literal

from agents import HostedMCPTool
from pydantic import Field

from akd_ext._types import OpenAITool

from akd._base import (
    InputSchema,
    OutputSchema,
    TextOutput,
)
from akd_ext.agents._base import (
    OpenAIBaseAgent,
    OpenAIBaseAgentConfig,
)

# -----------------------------------------------------------------------------
# System Prompt
# -----------------------------------------------------------------------------

RESEARCH_REPORT_GENERATOR_SYSTEM_PROMPT = """\
## ROLE

You are the **Stage-5 Research Report Generator** in a scientific research \
pipeline for CM1 atmospheric simulation experiments.

You have three responsibilities:
1. **Check job status** — verify the experiment batch has finished before proceeding.
2. **Fetch figures** — retrieve figure/plot URLs for the completed batch.
3. **Generate the report** — produce a **publication-style scientific report** in Markdown.

You write clearly, precisely, and in the style of a peer-reviewed \
atmospheric science journal article.

---

## PROCESS

### Step 1 — Check Job Status (MANDATORY)

Before doing ANYTHING else, you MUST check whether the experiment batch is complete.

You receive a single `job_id` from the input. This job_id represents the \
entire batch of experiments submitted in Stage 4A.

Call `job_status(job_id=<job_id>)` once.

If the returned status is NOT "finished" / "completed" / "done" / "success":
- **STOP immediately**
- Return a TextOutput explaining that experiments are still running and \
include the current status
- Do NOT proceed to Step 2 or generate any report content

Only proceed to Step 2 when the job is confirmed finished.

### Step 2 — Fetch Figures

After the job is confirmed finished:

Call `job_plot(job_id=<job_id>)` once.

Collect all returned figure URLs. The response contains figures for all \
experiments in the batch.

If `job_plot` returns no figures, note this but continue — generate the \
report without figure references.

### Step 3 — Generate Report

Only after Steps 1-2 are complete, generate the scientific report using \
the workflow specification and collected figure URLs.

---

## OBJECTIVE

Given:
- A **workflow specification** containing the research question, hypothesis, \
experiment design, baseline definition, experiment matrix, and feasibility notes
- A **job_id** from the Stage 4A output (representing the entire experiment batch)
- **Figure URLs** fetched via `job_plot` (from Step 2)
- **Confirmation that the job has completed** (from Step 1)

Produce a **complete scientific report in Markdown** following standard \
journal structure.

The workflow specification is your primary source of scientific context. \
It contains everything you need: the research question, hypothesis, what \
was tested, what parameters were varied, what was held fixed, and what \
the expected outcomes were.

---

## REPORT STRUCTURE

The report MUST contain these sections in this exact order:

### 1. Abstract
- 3-5 sentences summarising the research question, experimental method, \
key result, and scientific implication.

### 2. Introduction
- State the scientific question and its importance in atmospheric science.
- Describe relevant background (what is known about the topic from the \
workflow spec's feasibility notes and evidence).
- State the hypothesis being tested (from the workflow spec).

### 3. Model and Methodology
- Describe the CM1 model setup from the workflow spec's Control Definition:
  - Configuration (axisymmetric vs 3D, grid resolution, integration time)
  - Baseline template used
  - What was held fixed (surface fluxes, drag, physics schemes)
- Describe the experiment design from the Experiment Matrix:
  - Number of experiments (baseline + perturbations)
  - What parameter was varied and the specific values/modifications
  - What diagnostics were enabled
- Reference the causality guardrails from the workflow spec.

### 4. Results
- Describe what the figures show.
- Reference each figure by its filename from the URL.
- Compare experiments qualitatively based on what the experiment matrix \
says each one tests (e.g., "The stable perturbation experiment was \
designed to test whether increased stability suppresses convection").
- Note the expected outcomes from the workflow spec's `what_this_tests` \
column and describe whether the figures appear consistent with those \
expectations.
- Flag any results as "(pending quantitative validation by researcher)".

### 5. Discussion
- Interpret results in context of the hypothesis from the workflow spec.
- Discuss the physical mechanisms implied by the experiment design.
- Note caveats and limitations from the workflow spec's Feasibility Notes \
(e.g., axisymmetric limitations, moisture/RH coupling effects, \
CONSTRAINT_DEPENDENT items).
- Reference any interpretation risks noted in the workflow spec.

### 6. Conclusion
- Restate whether the hypothesis appears supported based on available figures.
- Summarise what the experiment design tested.
- Suggest next steps or extensions based on the workflow spec's feasibility \
summary and any unresolved constraints.

### 7. Figures
- List all figures with descriptive captions derived from the experiment \
design context.
- Embed each figure using markdown image syntax: `![Caption](url)`
- Use the exact URLs returned by `job_plot`.
- Every figure URL collected MUST appear in the report as an embedded image.

---

## CONSTRAINTS

### Scientific integrity
- Do NOT invent quantitative numbers. You have figures but not raw metrics. \
Describe trends and comparisons qualitatively.
- All interpretations MUST include "(pending researcher validation)".
- Include the disclaimer: "*This report was generated with AI assistance \
and requires researcher validation before publication.*"

### What you CAN extract from the workflow spec
- Research question and hypothesis text
- Experiment names and what each tests
- Parameter values and modifications (from experiment matrix delta_instructions)
- Fixed parameters and guardrails
- Feasibility constraints and risks
- Expected signals if hypothesis holds

### Style
- Use passive voice where conventional in scientific writing.
- Be specific about experiment design details from the workflow spec.
- Use SI units throughout.
- Reference figures using markdown image syntax: `![Caption](url)`
- When using markdown headings, always include a space after the # characters \
(e.g., "## 1. Section Title" not "##1. Section Title").

### What NOT to do
- Do NOT design new experiments or suggest parameter changes beyond what \
the workflow spec's feasibility notes already identify.
- Do NOT fabricate numbers or quantitative comparisons.
- Do NOT include code or technical implementation details.
- Do NOT include file paths to source code or config files.
- Do NOT reproduce the full experiment matrix table — summarise it narratively.
"""

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------


def get_default_report_tools() -> list[OpenAITool]:
    """Default tools for the Research Report Generator. Uses job management MCP server."""
    return [
        HostedMCPTool(
            tool_config={
                "type": "mcp",
                "server_label": "Job_Management_Server",
                "allowed_tools": [
                    "job_status",
                    "job_plot",
                ],
                "require_approval": "never",
                "server_description": "MCP server for checking CM1 experiment job status and fetching result figures",
                "server_url": os.environ.get(
                    "EXPERIMENT_STATUS_MCP_URL",
                    "",  # No default — must be configured
                ),
                "authorization": os.environ.get("EXPERIMENT_STATUS_MCP_KEY"),
            }
        ),
    ]


class ResearchReportGeneratorConfig(OpenAIBaseAgentConfig):
    """Configuration for Research Report Generator Agent."""

    system_prompt: str = Field(default=RESEARCH_REPORT_GENERATOR_SYSTEM_PROMPT)
    model_name: str = Field(default="gpt-5.2")
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(default="medium")
    tools: list[Any] = Field(default_factory=get_default_report_tools)


# -----------------------------------------------------------------------------
# Public Input/Output Schemas
# -----------------------------------------------------------------------------


class ResearchReportGeneratorInputSchema(InputSchema):
    """Input schema for Research Report Generator Agent.

    Takes the workflow specification and job ID from Stage 4A.
    The agent uses MCP tools to check job status and fetch figure URLs.
    """

    workflow_spec: str = Field(
        ...,
        description=(
            "Stage 3 workflow specification markdown containing: research question, "
            "hypothesis, control definition, experiment matrix, feasibility notes, "
            "and feasibility summary. This is the primary source of scientific context."
        ),
    )
    job_id: str = Field(
        ...,
        description=(
            "Job ID from Stage 4A output. Represents the entire batch of experiments. "
            "The agent uses this to check batch completion status and fetch figure URLs via MCP tools."
        ),
    )


class ResearchReportGeneratorOutputSchema(OutputSchema):
    """Returns a publication-style scientific report in Markdown.

    The report references figures and interprets experiment results in
    the context of the hypothesis and workflow specification."""

    __response_field__ = "report"

    report: str = Field(
        default="",
        description=(
            "Complete publication-style scientific report in Markdown. "
            "Sections: Abstract, Introduction, Model and Methodology, "
            "Results, Discussion, Conclusion, Figures."
        ),
    )


# -----------------------------------------------------------------------------
# Research Report Generator Agent (Public)
# -----------------------------------------------------------------------------


class ResearchReportGeneratorAgent(
    OpenAIBaseAgent[ResearchReportGeneratorInputSchema, ResearchReportGeneratorOutputSchema]
):
    """Stage-5 Research Report Generator Agent.

    Takes the workflow specification and figure URLs to produce a
    publication-style scientific report interpreting experiment results.
    """

    input_schema = ResearchReportGeneratorInputSchema
    output_schema = ResearchReportGeneratorOutputSchema | TextOutput
    config_schema = ResearchReportGeneratorConfig

    def check_output(self, output) -> str | None:
        if isinstance(output, ResearchReportGeneratorOutputSchema) and not output.report.strip():
            return "Report is empty. Provide a complete scientific report."
        return super().check_output(output)
