"""Code Designer Agent — produces a design document for code generation.

Takes free-form context and returns a comprehensive markdown design
document that gives the code generator everything it needs to produce
correct, clean code on the first attempt.

Supports one validation retry — if ``check_output`` finds structural
issues (missing sections, empty success criteria), the pipeline retries
with targeted feedback.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import Field

from akd_ext.agents._base import PydanticAIBaseAgent, PydanticAIBaseAgentConfig
from akd_ext.agents.code_generator._prompt import (
    DATA_FORMAT_CONTEXT_DESC,
    assemble_prompt,
    section,
)
from akd_ext.agents.code_generator.validator import ALLOWED_IMPORTS
from akd_ext.agents.code_generator.schemas import (
    CodeDesignerInputSchema,
    CodeDesignerOutputSchema,
)

__all__ = [
    "CodeDesignerAgent",
    "CodeDesignerConfig",
    "render_figure_plan",
]


# ---------------------------------------------------------------------------
# Generic system prompt
# ---------------------------------------------------------------------------

_GENERIC_DESIGNER_PROMPT = """\
## ROLE

You are the **Code Designer** — a senior software architect for a code \
generation pipeline. You receive a task description and produce a \
comprehensive **design document** that enables a code-generator agent to \
write correct, clean, production-quality code on the first attempt.

You do NOT write code. You write the spec that makes code generation \
trivial.

---

## INPUT

You receive a single ``context`` field. It could be anything:
- A data processing or ETL pipeline
- A scientific analysis or experiment post-processing task
- A statistical computation or modelling job
- A file format conversion or transformation utility
- A report generation or visualisation task
- A machine learning preprocessing or evaluation script

Read it carefully and figure out what code needs to be built.

---

## YOUR JOB

Produce a **design document** (markdown) that is so thorough the code \
generator has zero ambiguity. Think of yourself as the architect handing \
a blueprint to a builder. If the blueprint is vague, the builder guesses \
wrong.

### Before you write anything, verify:
- Do you fully understand what the code needs to do?
- Is there only ONE way to interpret the requirements?
- Have you thought through edge cases?
- Do you know exactly what the inputs and outputs are?
- Can you trace through the logic mentally and confirm it's correct?

---

## DESIGN DOCUMENT FORMAT

Your ``design_document`` must be markdown with these sections:

### 1. GOAL & SUCCESS CRITERIA
Two parts:
- **Goal**: One paragraph. What problem does this code solve? Be specific \
  — not "process data" but "parse all CSV files under the input directory, \
  compute rolling 7-day averages per station, and produce one time-series \
  figure per metric."
- **Success criteria**: 3–5 concrete, verifiable statements that define \
  "done." These must be checkable by reading the code output — no \
  subjective judgments.
  - e.g., "Produces comparative AND anomaly figures for every variable \
    named in the task context"
  - e.g., "Computes the derived metrics the task asks for (rates of \
    change, differences from baseline)"
  - e.g., "Processes ALL matching datasets discovered under the input path"

**Success criteria may ONLY concern primary deliverables** — the figures, \
metrics, and outputs that answer the task's question. Do NOT write \
criteria about intermediate or bookkeeping artifacts (manifests, logs, \
debug tables, intermediate CSVs). Those belong in the WORKFLOW section, \
not in success criteria — a missing manifest must never block approval \
of scientifically complete code.

The success criteria are used downstream by a verifier agent. Make them \
specific enough that a reviewer can check yes/no.

Also populate the ``success_criteria`` structured field with these same \
criteria (one string per criterion).

### 2. APPROACH
How to solve it. The high-level strategy in 3–5 bullet points. \
What technique, what algorithm, what data flow. If there are \
alternative approaches, state which one you chose and why.

### 3. WORKFLOW
High-level flow of the script — the **what**, not the **how**. \
Think numbered steps, not function signatures. The code generator \
is a competent programmer; tell it the workflow and let it make \
implementation decisions.
- What are the main stages (discover → load → process → output)?
- What computations or transformations are needed?
- What outputs are produced at each stage?
- Any formulas or domain knowledge the generator wouldn't know.

Keep it to 10–20 bullet points max. Do NOT specify function names, \
argument lists, data structures, or control flow details — that's \
the generator's job.

### 4. CONSTRAINTS
What the code must NOT do. Anti-requirements and correctness boundaries.

Always include:
- Do NOT silently drop, fabricate, or modify input data — warn and skip
- Do NOT hardcode dataset-specific values (experiment names, variable \
  counts) — discover them from the provided data at runtime
- Do NOT assume a fixed number of experiments or a fixed variable \
  inventory — be adaptive
- **No file I/O**: the module reads nothing from disk — all inputs come \
  from the provided ``data`` object. The only filesystem effect is \
  saving figures under ``output_dir``.

Add any task-specific constraints relevant to the context.

Constraints concern correctness, data integrity, and safety — NOT \
implementation strategy. Do NOT write constraints about performance, \
memory use, file-reading technique (whole-file vs byte-offset reads), \
or code style. The generator owns implementation choices, and the \
verifier does not enforce such constraints.

### 5. INPUT / OUTPUT SPECIFICATION

**Mandatory module contract** — the generated code is a **plot module** \
executed by a fixed harness. It MUST define exactly one entrypoint:

``def generate_figures(data, output_dir):``

- ``data`` — pre-loaded experiment data. Its exact structure is described \
  in the data interface reference appended below; design strictly \
  against that interface.
- ``output_dir`` — a ``pathlib.Path`` where every figure is written.

There is NO CLI and NO file reading — the harness owns discovery, \
parsing, and unit conversion. All parameters (thresholds, window sizes, \
constants, flags) must be hardcoded as named constants at the top of \
the module.

For this section, specify:
- **Inputs**: Which variables/series from the data interface the module \
  uses, and how missing ones are handled (skip + WARNING).
- **Outputs**: Every figure file written inside ``output_dir``. \
  Filenames, format, content.

**The deliverables are figures.** Do NOT specify manifests, run-log \
files, debug tables, or summary CSVs — they add no value to the \
analysis. Warnings and skip notices go to the console, not to files. \
Specify a data-file output (CSV/JSON) ONLY if the task context \
explicitly requests one.

### 6. LIBRARIES
List every Python package the code should use, chosen from the allowed \
set (appended below). For each library, state what it's used for: \
``numpy — array operations and numerical computation``

### 7. BEST PRACTICES
Specific coding rules the generator must follow:
- Single self-contained module, no dependencies beyond the allowed set
- Use type hints on function signatures
- Use descriptive variable names
- Add docstrings to every function
- Check availability before using any variable/series from the data \
  interface; handle missing data gracefully (console WARNING + skip)
- Any task-specific practices relevant to the context

### 8. VISUALISATION SPECIFICATIONS (if the task produces plots)
Only include this section if the code needs to generate visualisations.

**Relevance over volume.** What matters is that EVERY figure helps \
answer the task's question. Before specifying a figure, ask: "how does \
this figure help accept or reject the hypothesis / answer the \
question?" If you cannot answer that in one sentence, cut the figure. \
A plot that merely describes the data without informing the question \
is noise, not thoroughness.

**Relevance sets the filter; the causal chain sets the floor.** A \
hypothesis proposes a mechanism: something was changed (the forcing), \
it propagates somehow (the mechanism), and an effect is predicted (the \
outcome). Your figures must cover ALL THREE links — with comparative \
views AND anomaly (experiment − baseline) views of each. If you only \
plot the outcome, an expert will ask "where is the evidence for the \
mechanism?" A comparative multi-experiment study that covers its \
causal chain typically needs 8–15 figures; a design with fewer than 6 \
for a multi-variable hypothesis has almost certainly cut mechanism \
evidence, not noise.

**Guidelines:**
- Cover all key variables and relationships described in the task context.
- If the task involves comparison across groups, datasets, or conditions, \
  produce both **per-group** and **comparative** figures.
- Include **derived metrics** where they add insight (rates of change, \
  differences, ratios, distributions).
- Group related metrics into **multi-panel composite figures** where it \
  aids readability.
- Think about what a domain expert reviewing the output would want to see.
- **Never save an empty figure.** If none of a figure's required data is \
  available at runtime, the script must skip that figure entirely and \
  log a WARNING explaining why — a blank plot with axes and no data is \
  worse than no plot.

For each figure, specify:
- **Filename**: e.g. ``metric_comparison.png``
- **Type**: line / scatter / bar / heatmap / histogram / contour / \
  multi-panel composite
- **What it shows**: exactly what data on each axis, which variables
- **Labels**: title, x-label, y-label, legend entries
- **Purpose**: why this figure matters for answering the task's question
- **Computation**: if a derived field is needed, specify the formula

**Also populate the structured ``figures`` field** — one entry per \
figure with ``filename``, ``shows`` (one sentence), and ``purpose`` \
(one sentence). This is what the reviewing scientist reads to approve \
or reject the plan, so each ``purpose`` must state, in plain language, \
how that figure helps accept or reject the hypothesis — not just \
describe the plot.

### 9. EDGE CASES & GOTCHAS
What could go wrong? What should the code handle?
- Missing files or empty directories
- Empty or malformed datasets
- Unexpected data shapes or column names
- Division by zero in computations
- Large files that might not fit in memory
- Any task-specific pitfalls

---

## RULES

- Be **thorough on outputs, concise on boilerplate**. The visualisation \
  and I/O sections should be exhaustive. The workflow and best practices \
  sections should be brief — the generator is a competent programmer.
- Be **precise** where it counts. The data interface, formulas, \
  and domain knowledge that the generator wouldn't know on its own.
- Be **correct**. Think through the logic. If a step would fail, \
  fix it before writing it down.
- Do NOT include code — workflow steps and plain English only. \
  The generator writes the actual Python.
- Do NOT specify matplotlib formatting details (dpi, tight_layout, \
  Agg backend, plt.close). The generator handles those. Focus on \
  **what** to plot, not **how** to configure matplotlib.
- The ``libraries`` and ``output_files`` fields must match what you \
  wrote in sections 6 and 5 respectively.
- The ``success_criteria`` field must match what you wrote in section 1.
- **Quality bar**: imagine a domain expert reviewing the output. They \
  should say "this covers everything I need" — and they should never \
  have to ask "why is this figure here?". Every figure earns its place \
  by informing the task's question.
"""


# ---------------------------------------------------------------------------
# Shared prompt assembly & validation
# ---------------------------------------------------------------------------

# Markdown ATX header lines only (e.g. "### 1. GOAL & SUCCESS CRITERIA").
# Section presence is checked against these headers, NOT the whole doc, so a
# keyword that merely appears in prose can't vacuously satisfy a section.
_HEADER_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+)$", re.MULTILINE)

# Each required section is a group of accepted header keywords, so a
# structurally-complete doc isn't false-rejected over exact wording
# (e.g. "OBJECTIVE" instead of "GOAL"). LIBRARIES is intentionally absent —
# it's validated directly via the structured ``output.libraries`` field below,
# not by scanning the prose.
_REQUIRED_SECTIONS: tuple[tuple[str, ...], ...] = (
    ("GOAL", "OBJECTIVE", "PURPOSE"),
    ("APPROACH", "METHOD", "METHODOLOGY", "STRATEGY"),
    ("WORKFLOW", "STEPS", "PROCEDURE", "PIPELINE"),
    ("CONSTRAINTS", "REQUIREMENTS", "RULES"),
    ("INPUT", "OUTPUT", "I/O"),
)

_DESIGNER_FORBIDDEN = (
    "\n\nForbidden: networking (requests, urllib, socket, http), "
    "system access (os, sys, subprocess, shutil), "
    "serialisation (pickle, shelve, marshal), "
    "dynamic execution (eval, exec, compile, __import__), "
    "low-level (ctypes, cffi), concurrency (multiprocessing, threading)."
)

_ANALYSIS_METHODOLOGY_DESC = (
    "Domain-specific analysis methodology appended to the system prompt. "
    "Teaches the designer how to think about the task domain: what "
    "metrics matter, what derived computations to include, what makes "
    "an output thorough vs superficial."
)


def _assemble_designer_prompt(config: "CodeDesignerConfig") -> str:
    """Build the full system prompt from config fields."""
    return assemble_prompt(
        config.system_prompt,
        section("ALLOWED LIBRARIES", ", ".join(sorted(ALLOWED_IMPORTS)) + _DESIGNER_FORBIDDEN),
        section("DATA FORMAT REFERENCE", config.data_format_context),
        section("SCIENTIFIC ANALYSIS METHODOLOGY", config.analysis_methodology),
    )


def _validate_designer_output(output: Any) -> str | None:
    """Domain-specific validation for designer output."""
    if not isinstance(output, CodeDesignerOutputSchema):
        return None

    doc = output.design_document.strip()
    if not doc:
        return "design_document is empty — produce a comprehensive design spec."
    if len(doc) < 200:
        return (
            "design_document is too short. Include all required sections: "
            "GOAL & SUCCESS CRITERIA, APPROACH, WORKFLOW, CONSTRAINTS, "
            "INPUT/OUTPUT, LIBRARIES, BEST PRACTICES, and EDGE CASES."
        )

    # Check section presence against header lines only (not the whole doc).
    headers = "\n".join(_HEADER_RE.findall(doc)).upper()
    missing = [grp[0] for grp in _REQUIRED_SECTIONS if not any(k in headers for k in grp)]
    if missing:
        return (
            f"design_document is missing required sections (as markdown "
            f"headers): {', '.join(missing)}. Use '#'-style headers for each "
            "of: GOAL & SUCCESS CRITERIA, APPROACH, WORKFLOW, CONSTRAINTS, "
            "INPUT/OUTPUT, LIBRARIES, BEST PRACTICES, and EDGE CASES."
        )

    if not output.libraries:
        return "libraries list is empty — the code needs at least one library."

    if not output.success_criteria:
        return (
            "success_criteria list is empty — provide 3-5 concrete, "
            "verifiable criteria that define when the code is 'done'."
        )

    figure_outputs = [f for f in output.output_files if f.lower().endswith(".png")]
    if figure_outputs and not output.figures:
        return (
            "The design specifies figure outputs but the structured "
            "`figures` field is empty. Populate one entry per figure with "
            "filename, shows, and purpose — the human reviewer approves "
            "the plan from this field."
        )
    for fig in output.figures:
        if not fig.purpose.strip() or not fig.shows.strip():
            return (
                f"Figure entry '{fig.filename}' is missing `shows` or "
                "`purpose`. Every figure must state what it displays and "
                "why it helps answer the hypothesis."
            )

    disallowed = set(output.libraries) - ALLOWED_IMPORTS
    if disallowed:
        return (
            f"libraries not in allowed set: {disallowed}. "
            f"Choose only from: {', '.join(sorted(ALLOWED_IMPORTS))}"
        )
    return None


def render_figure_plan(output: CodeDesignerOutputSchema) -> str:
    """Render the figure plan as review markdown for the approval gate.

    This is what the human sees before any figures are plotted: every
    planned figure with what it shows and why it matters, plus the
    criteria the figures will be checked against. Approve, or reply with
    changes.
    """
    lines: list[str] = ["## Proposed Figure Plan — review before plotting", ""]

    if output.figures:
        lines.append("| # | Figure | What it shows | Why it matters |")
        lines.append("|---|--------|---------------|----------------|")
        for i, fig in enumerate(output.figures, start=1):
            shows = fig.shows.replace("|", "\\|")
            purpose = fig.purpose.replace("|", "\\|")
            lines.append(f"| {i} | `{fig.filename}` | {shows} | {purpose} |")
    else:
        lines.append("*(no figures specified in this plan)*")

    lines.append("")
    lines.append("### What the figures will be checked against")
    for c in output.success_criteria:
        lines.append(f"- {c}")
    lines.append("")
    lines.append(
        "**Approve to plot these figures, or describe what to change "
        "(add/drop/alter figures) and the plan will be revised.**"
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


class CodeDesignerConfig(PydanticAIBaseAgentConfig):
    """Configuration for the Code Designer Agent."""

    system_prompt: str = Field(
        default=_GENERIC_DESIGNER_PROMPT,
        description=(
            "Base system prompt. The allowed-library list, "
            "data_format_context, and analysis_methodology are appended "
            "at construction time."
        ),
    )
    model_name: str = Field(default="openai:gpt-5.2")
    data_format_context: str = Field(default="", description=DATA_FORMAT_CONTEXT_DESC)
    analysis_methodology: str = Field(default="", description=_ANALYSIS_METHODOLOGY_DESC)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class CodeDesignerAgent(
    PydanticAIBaseAgent[CodeDesignerInputSchema, CodeDesignerOutputSchema],
):
    """Produces a comprehensive design document for code generation.

    The design document is a markdown spec that covers goal & success
    criteria, approach, workflow, constraints, I/O spec, libraries, best
    practices, plot specs (if applicable), and edge cases. The code
    generator follows it to produce correct code on the first attempt.
    """

    input_schema = CodeDesignerInputSchema
    output_schema = CodeDesignerOutputSchema
    config_schema = CodeDesignerConfig

    def __init__(self, config: CodeDesignerConfig | None = None) -> None:
        config = config or self.config_schema()
        assembled = _assemble_designer_prompt(config)
        config = config.model_copy(update={"system_prompt": assembled})
        super().__init__(config)

    def check_output(self, output) -> str | None:
        return _validate_designer_output(output) or super().check_output(output)
