"""Code Generator Agent — produces Python code from a design document.

Takes the design document (from the designer) and the original context.
On retries it also receives ``correction_feedback`` with the validation
failure reason so the model can self-correct.

Returns :class:`CodeGeneratorOutputSchema` with complete source, libraries,
output files, and an explanation.
"""

from __future__ import annotations

import ast
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
    CodeGeneratorInputSchema,
    CodeGeneratorOutputSchema,
)

__all__ = [
    "CodeGeneratorAgent",
    "CodeGeneratorConfig",
]


# ---------------------------------------------------------------------------
# Generic system prompt
# ---------------------------------------------------------------------------

_GENERIC_GENERATOR_PROMPT = """\
## ROLE

You are the **Code Generator**. You receive a design document (a detailed \
markdown spec) and produce a **complete, self-contained Python script** \
that implements it exactly.

---

## INPUTS

1. **design_document** — A comprehensive markdown spec from the Code \
   Designer. It contains: goal & success criteria, approach, workflow, \
   constraints, I/O spec, libraries, best practices, visualisation \
   specifications (if any), and edge cases. \
   Follow it closely — the designer has already made the architectural \
   decisions.
2. **context** — The original task description for additional background.
3. **correction_feedback** — If non-empty, your previous code was rejected \
   by a validator. Fix the specific issues described.

---

## YOUR JOB

Translate the design document into a single Python **plot module**. \
Follow the WORKFLOW section step-by-step and honor every CONSTRAINT. \
Respect every best practice listed in the design document.

---

## CODE QUALITY RULES

- **Single file**. Everything in one self-contained script.
- **No external dependencies** beyond the allowed library set.
- **Type hints** on all function signatures.
- **Docstrings** on every function.
- **Descriptive names** — no single-letter variables except loop indices.
- **pathlib.Path** for all file operations. NOT ``os.path``.
- **try/except** around all I/O with informative error messages.
- **Graceful degradation** — if an expected variable or series is \
  missing from the provided data, log a console WARNING and skip the \
  affected figure. Don't crash.
- **Module contract** — your output is a **plot module** executed by a \
  fixed harness. It MUST define exactly one entrypoint:
  ``def generate_figures(data, output_dir):`` where ``data`` is the \
  pre-loaded experiment data (described in the data interface reference) \
  and ``output_dir`` is a ``pathlib.Path``. The harness owns the CLI, \
  file discovery, data parsing, and unit conversion — your module does \
  NONE of that.
- **No file I/O** — do not read any files and do not use ``argparse``. \
  The only filesystem effect is saving figures under ``output_dir``.
- All parameters (thresholds, window sizes, colors, flags) must be \
  defined as named constants at the top of the module.

---

## COMPLETENESS — NON-NEGOTIABLE

Implement **every** figure, table, and output file listed in the design \
document. Do NOT silently drop any. The design document was produced by a \
domain expert; every artefact exists to support the hypothesis. If the \
design specifies 18 figures, the code must produce 18 figures. A long \
script is fine — an incomplete script is not.

If you cannot implement a specific figure (e.g., required data is not \
described), emit a clear ``WARNING`` log explaining why it was skipped \
so the intent checker can see it. Never skip silently.

The reverse also holds: do NOT produce outputs the design document does \
not specify — no manifests, run-log files, debug tables, or extra CSVs. \
Warnings go to the console (``warnings`` module or ``print``), not to \
log files.

---

## PLOT FORMATTING (when the design document specifies plots)

- ``matplotlib.use('Agg')`` BEFORE importing ``pyplot``
- ``dpi=150`` on all ``savefig()`` calls
- ``plt.tight_layout()`` before every save
- ``plt.close()`` after every save to free memory
- When comparing multiple datasets: ALL on the same axes with a legend
- Consistent color scheme across all plots (use a colour list or colormap)
- Grid on, clear labels with units
- **Never save an empty figure** — if none of a figure's data is \
  available at runtime, skip the figure entirely and log a WARNING. \
  A blank plot with axes and no curves must never be written to disk.

---

## CORRECTION FEEDBACK

If ``correction_feedback`` is non-empty, your previous code was rejected. \
Read the feedback carefully and fix the SPECIFIC issues described:
- **Forbidden import**: replace with an allowed alternative. \
  ``os.listdir()`` → ``pathlib.Path.iterdir()``, \
  ``os.path.join()`` → ``pathlib.Path / "child"``, \
  ``os.makedirs()`` → ``pathlib.Path.mkdir(parents=True, exist_ok=True)``.
- **Intent mismatch**: re-read the design document and implement what \
  it actually asks for.
- **Missing library**: add it to the ``libraries`` list.
- Do NOT rewrite from scratch — fix the specific issues.
"""


# ---------------------------------------------------------------------------
# Prompt assembly & validation
# ---------------------------------------------------------------------------

_FORBIDDEN_EXAMPLES = [
    "os", "sys", "subprocess", "shutil", "socket", "ssl",
    "urllib", "requests", "httpx", "http", "ftplib", "smtplib",
    "pickle", "shelve", "marshal", "ctypes", "cffi",
    "multiprocessing", "threading", "importlib",
]

_GENERATOR_FORBIDDEN = (
    "\n\n**FORBIDDEN** (the validator will reject your code):\n"
    + ", ".join(_FORBIDDEN_EXAMPLES)
    + "\n\nAlso forbidden: eval(), exec(), compile(), __import__()."
)


def _assemble_generator_prompt(config: Any) -> str:
    """Build the full system prompt from config fields."""
    return assemble_prompt(
        config.system_prompt,
        section("ALLOWED LIBRARIES", ", ".join(sorted(ALLOWED_IMPORTS)) + _GENERATOR_FORBIDDEN),
        section("DATA FORMAT REFERENCE", getattr(config, "data_format_context", "")),
    )


def _validate_generator_output(output: Any) -> str | None:
    """Domain-specific validation for generator output."""
    if not isinstance(output, CodeGeneratorOutputSchema):
        return None

    code = output.code.strip()
    if not code:
        return "code field is empty — generate complete Python source."
    if len(code.splitlines()) < 10:
        return (
            "code is too short (< 10 lines). Generate a complete, "
            "self-contained script."
        )

    disallowed = set(output.libraries) - ALLOWED_IMPORTS
    if disallowed:
        return (
            f"libraries not in allowed set: {disallowed}. "
            f"Choose only from: {', '.join(sorted(ALLOWED_IMPORTS))}"
        )

    # Structural checks use the AST, not substring matching: a docstring or
    # comment that merely mentions "generate_figures" or "argparse" must not
    # false-pass or false-reject (raw `in`/`.count()` heuristics did both).
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return (
            f"code has a syntax error: {exc.msg} (line {exc.lineno}). "
            "Fix it and regenerate complete, parseable source."
        )

    has_entrypoint = any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "generate_figures"
        for node in tree.body
    )
    if not has_entrypoint:
        return (
            "code is missing the mandatory entrypoint "
            "`def generate_figures(data, output_dir):`. The plot module "
            "is executed by a fixed harness that calls exactly this "
            "function (it must be defined at module level)."
        )

    if _imports_argparse(tree):
        return (
            "code imports argparse, but plot modules have no CLI — the "
            "fixed harness owns argument parsing. Remove the argparse "
            "import; parameters belong in named constants at the top of "
            "the module."
        )
    return None


def _imports_argparse(tree: ast.AST) -> bool:
    """True only if the module actually imports argparse (AST, not substring).

    A comment or docstring mentioning argparse won't trip this; only a real
    ``import argparse`` / ``from argparse import ...`` does.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == "argparse" for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] == "argparse":
                return True
    return False


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


class CodeGeneratorConfig(PydanticAIBaseAgentConfig):
    """Configuration for the Code Generator Agent."""

    system_prompt: str = Field(
        default=_GENERIC_GENERATOR_PROMPT,
        description="Base system prompt. data_format_context is appended at runtime.",
    )
    model_name: str = Field(default="openai:gpt-5.2")
    data_format_context: str = Field(default="", description=DATA_FORMAT_CONTEXT_DESC)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class CodeGeneratorAgent(
    PydanticAIBaseAgent[CodeGeneratorInputSchema, CodeGeneratorOutputSchema],
):
    """Produces Python code from a design document.

    Takes the design document (from the designer) plus the original
    context, and returns a complete, self-contained Python script with
    CLI interface, type hints, and graceful error handling.
    """

    input_schema = CodeGeneratorInputSchema
    output_schema = CodeGeneratorOutputSchema
    config_schema = CodeGeneratorConfig

    def __init__(self, config: CodeGeneratorConfig | None = None) -> None:
        config = config or self.config_schema()
        assembled = _assemble_generator_prompt(config)
        config = config.model_copy(update={"system_prompt": assembled})
        super().__init__(config)

    def check_output(self, output) -> str | None:
        return _validate_generator_output(output) or super().check_output(output)
