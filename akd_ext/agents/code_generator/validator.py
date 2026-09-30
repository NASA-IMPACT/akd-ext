"""Code validators for the code-generation pipeline.

Three validation layers — allowlist, bandit, and intent checker — that vet
generated code before approval. The deterministic checks (allowlist + bandit)
run first so we fail fast on cheap signals; the LLM-as-judge intent checker
runs last.

Public API:
    Deterministic:
        ALLOWED_IMPORTS, check_allowlist, AllowlistResult
        check_bandit, BanditFinding, BanditResult

    LLM-as-judge:
        IntentCheckerAgent, IntentCheckerConfig
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import Field

from akd_ext.agents._base import PydanticAIBaseAgent, PydanticAIBaseAgentConfig
from akd_ext.agents.code_generator._prompt import (
    DATA_FORMAT_CONTEXT_DESC,
    assemble_prompt,
    section,
)
from akd_ext.agents.code_generator.schemas import (
    IntentCheckerInputSchema,
    IntentCheckerOutputSchema,
)

__all__ = [
    # Deterministic validators
    "ALLOWED_IMPORTS",
    "AllowlistResult",
    "BanditFinding",
    "BanditResult",
    "check_allowlist",
    "check_bandit",
    # LLM-as-judge validator
    "IntentCheckerAgent",
    "IntentCheckerConfig",
]


# ---------------------------------------------------------------------------
# Import allowlist — the ONLY modules LLM-generated code may use
# ---------------------------------------------------------------------------

ALLOWED_IMPORTS: frozenset[str] = frozenset(
    {
        # The fixed execution harness — exposes pre-loaded data helpers
        # (smooth, anomaly_vs_baseline) to generated plot modules
        "harness",
        # Scientific stack
        "numpy",
        "pandas",
        "scipy",
        "matplotlib",
        "seaborn",
        "xarray",
        "netCDF4",
        "sklearn",
        "statsmodels",
        # Safe stdlib
        "__future__",
        "math",
        "random",
        "json",
        "csv",
        "re",
        "string",
        "collections",
        "itertools",
        "functools",
        "operator",
        "datetime",
        "time",
        "io",
        "pathlib",
        "dataclasses",
        "argparse",
        "struct",
        "typing",
        "copy",
        "warnings",
        "textwrap",
        "enum",
        "abc",
    }
)

# The complete, language-defined set of dynamic-execution entry points.
# This is NOT an open-ended denylist: Python has exactly these four
# builtins that execute or import dynamically constructed code. Blocking
# them closes the only bypass of the import allowlist — without them,
# `__import__('os')` would defeat it from inside allowlisted code.
_DYNAMIC_EXEC_CALLS: frozenset[str] = frozenset(
    {"eval", "exec", "compile", "__import__"}
)


# ---------------------------------------------------------------------------
# Allowlist checker (AST walk)
# ---------------------------------------------------------------------------


@dataclass
class AllowlistResult:
    """Outcome of the import-allowlist AST check."""

    passed: bool
    violations: list[str] = field(default_factory=list)


def check_allowlist(code: str) -> AllowlistResult:
    """Validate *code* against the import allowlist.

    Two fail-closed rules:

    1. **Imports** — every imported top-level module must be in
       ``ALLOWED_IMPORTS``. Pure allowlist: ``os``, ``sys``,
       ``subprocess``, ``socket`` etc. are simply not on it.
    2. **No dynamic execution** — calls to ``eval``, ``exec``,
       ``compile``, or ``__import__`` are rejected. These four are the
       complete language-defined set of dynamic-execution builtins; rule
       1 would be bypassable via ``__import__('os')`` without this.

    Deeper containment (output-directory confinement, obfuscated
    reflection) is handled downstream by the intent checker and the
    execution environment's own permissions.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return AllowlistResult(passed=False, violations=[f"SyntaxError: {exc}"])

    violations: list[str] = []

    for node in ast.walk(tree):
        # Rule 1: import x / import x.y
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top not in ALLOWED_IMPORTS:
                    violations.append(
                        f"line {node.lineno}: `import {alias.name}` — "
                        f"`{top}` is not in the allowed-import list"
                    )

        # Rule 1: from x import y
        elif isinstance(node, ast.ImportFrom):
            # Relative imports (`from . import x`, `from .pkg import y`) have
            # node.level > 0 (and module may be None). A generated plot module
            # is standalone — there is no package — so reject them outright
            # rather than skipping the check and failing later at runtime.
            if node.level and node.level > 0:
                violations.append(
                    f"line {node.lineno}: relative import "
                    f"`from {'.' * node.level}{node.module or ''} import ...` "
                    f"is not allowed (the plot module is standalone)"
                )
            else:
                top = (node.module or "").split(".")[0]
                if top not in ALLOWED_IMPORTS:
                    violations.append(
                        f"line {node.lineno}: `from {node.module} import ...` — "
                        f"`{top}` is not in the allowed-import list"
                    )

        # Rule 2: no dynamic execution / dynamic import
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in _DYNAMIC_EXEC_CALLS:
                violations.append(
                    f"line {node.lineno}: call to `{node.func.id}()` is "
                    "forbidden — dynamic execution bypasses the import "
                    "allowlist"
                )

    return AllowlistResult(passed=not violations, violations=violations)


# ---------------------------------------------------------------------------
# Bandit static security scanner
# ---------------------------------------------------------------------------


@dataclass
class BanditFinding:
    """One finding from ``bandit``."""

    severity: str  # LOW | MEDIUM | HIGH
    confidence: str  # LOW | MEDIUM | HIGH
    test_id: str
    test_name: str
    line: int
    issue: str


@dataclass
class BanditResult:
    """Aggregated bandit scan result."""

    passed: bool
    findings: list[BanditFinding] = field(default_factory=list)
    error: str | None = None


# Bandit severity ordering — single source of truth. Used both for the
# pass/fail threshold here and by any caller that ranks/filters findings
# (e.g. the pipeline's failure-reason builder), so the two never desync.
SEVERITY_RANK: dict[str, int] = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}


def severity_rank(severity: str) -> int:
    """Rank a bandit severity label; unknown labels rank 0 (below LOW)."""
    return SEVERITY_RANK.get(severity.upper(), 0)


def check_bandit(code: str, *, fail_on: str = "HIGH") -> BanditResult:
    """Run ``bandit`` on *code* and fail if any finding meets *fail_on* severity.

    Parameters
    ----------
    code:
        Python source to scan.
    fail_on:
        Minimum severity that causes a failure (``HIGH``, ``MEDIUM``, or ``LOW``).

    Returns
    -------
    BanditResult
        ``.passed`` is ``True`` when nothing at-or-above *fail_on* was found.
    """
    threshold = SEVERITY_RANK.get(fail_on.upper(), 3)

    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", prefix="bandit_", delete=False,
        ) as fh:
            fh.write(code)
            tmp_path = fh.name

        proc = subprocess.run(
            [sys.executable, "-m", "bandit", "-q", "-f", "json", tmp_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # bandit exits 0 (clean) or 1 (findings) — in both cases it emits
        # a JSON report on stdout. Any other exit code, or NO output at
        # all (e.g. bandit not installed: `python -m bandit` exits 1 with
        # only a stderr message), means the scan never ran — fail closed.
        if proc.returncode > 1:
            return BanditResult(passed=False, error=f"bandit failed: {proc.stderr.strip()}")
        if not proc.stdout.strip():
            return BanditResult(
                passed=False,
                error=(
                    "bandit produced no report — is it installed? "
                    f"stderr: {proc.stderr.strip()}"
                ),
            )

        data = json.loads(proc.stdout)
        findings = [
            BanditFinding(
                severity=r.get("issue_severity", "LOW"),
                confidence=r.get("issue_confidence", "LOW"),
                test_id=r.get("test_id", ""),
                test_name=r.get("test_name", ""),
                line=r.get("line_number", 0),
                issue=r.get("issue_text", ""),
            )
            for r in data.get("results", [])
        ]

        max_sev = max(
            (severity_rank(f.severity) for f in findings),
            default=0,
        )
        return BanditResult(passed=max_sev < threshold, findings=findings)

    except Exception as exc:
        return BanditResult(passed=False, error=f"{type(exc).__name__}: {exc}")
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Intent Checker — LLM-as-judge
# ---------------------------------------------------------------------------

_GENERIC_INTENT_CHECKER_PROMPT = """\
## ROLE

You are a **code-review judge** for a secure scientific analysis pipeline. \
You decide whether generated Python code correctly implements an analysis \
plan and is safe to run.

---

## INPUTS

1. **context** — The original task description.
2. **design_document** — The design spec (markdown) with goal, approach, \
   workflow, constraints, I/O spec, libraries, best practices.
3. **code** — The generated Python script to evaluate.
4. **success_criteria** — A structured list of concrete, verifiable \
   criteria from the designer. Each criterion defines a yes/no check \
   for whether the code is "done." Use these as your primary checklist \
   when evaluating matches_intent.

---

## YOUR JOB

Evaluate along two axes:

### matches_intent (bool)
Does the code implement the design document and produce the expected \
output?

**Set True if:**
- The code reads the expected input files.
- The code produces the outputs described in the design document.
- When comparison is needed, the code processes multiple datasets.
- The code follows the approach and workflow from the design document.

**Set False if:**
- The code completely ignores the design document.
- The code only processes one dataset when comparison is specified.
- The code produces unrelated output.
- The code has logic errors that would produce incorrect results.

**DO NOT set False for:**
- Minor style issues (missing docstrings, unused imports, naming).
- Small deviations from the plan (extra plots, slightly different titles).
- Using pathlib instead of os.path or vice versa.
- Missing a non-critical output as long as the primary outputs are present.

### is_benign (bool)
Is the code safe to run on a compute cluster?

**IMPORTANT: A separate deterministic allowlist validator has ALREADY \
verified every import in this code before it reached you. If the code \
is here, its imports are approved. Do NOT reject based on import \
choices — that is not your job.**

**Set False if the code:**
- Makes network calls (requests, urllib, socket, http).
- Uses dynamic execution (eval, exec, compile, __import__).
- Writes outside the designated output directory.
- Attempts to read sensitive files (e.g. /etc/passwd, ~/.ssh).
- Contains hardcoded credentials or API keys.
- Uses multiprocessing/threading unsafely.

**Set True if:**
- The code only reads from the data directory and writes to the output \
  directory.
- File operations use pathlib or open().
- No network, dynamic execution, or filesystem escape attempts.

**Judge what the code actually does on well-formed inputs. NEVER reject \
on hypotheticals** ("could escape if the inputs were malicious", "could \
write elsewhere if mis-specified"). The expected I/O surface of a plot \
module is exactly: receive the pre-loaded ``data`` object, save figures \
under the ``output_dir`` it was handed. Writing under ``output_dir``, \
wherever it points, is the designated output location *by definition* — \
it cannot be an escape.

### confidence (float, 0.0–1.0)
- **≥ 0.8**: Clear-cut — code implements the plan and is safe.
- **0.6–0.8**: Minor concerns but fundamentally sound.
- **< 0.6**: Significant concerns — should be regenerated.

### reasoning (str)
2–4 sentences justifying your verdict. Be specific.

### suggested_fixes (list[str])
Concrete, actionable edits. Empty list if approved.

---

## SUCCESS CRITERIA EVALUATION

If ``success_criteria`` is non-empty, walk through every criterion and \
classify it as **hard** or **soft**:

- **Hard criteria** concern scientific completeness: figure count, \
  variable coverage, correct computations, data format handling, \
  causal chain coverage. These MUST be met.
- **Soft criteria** concern implementation details: exact output paths \
  or filenames, edge-case handling for data that may not exist, \
  conditional skip logic, subdirectory structure. These are NICE TO \
  HAVE but not grounds for rejection.
- **Intermediate artifacts are ALWAYS soft**: CSV tables, manifests, \
  log files, debug outputs — even if a success criterion mentions one. \
  The deliverables are the figures and the scientific computations \
  behind them. A missing, extra, or imperfect data file must NEVER set \
  ``matches_intent=False`` — note it in ``suggested_fixes`` instead.

A criterion is "met" if the code contains logic that would produce \
the described output on valid input data. Do NOT require exact string \
matches — check the intent.

Include a brief per-criterion assessment in your ``reasoning``. \
Example: "Criterion 1 (produces ≥15 PNGs): met — the code generates \
18 figure types. Criterion 2 (anomaly figures vs baseline): met — \
the code computes experiment − baseline series and plots one anomaly \
panel per variable."

**Rule**: set ``matches_intent=True`` if ALL hard criteria are met, \
even if some soft criteria have minor deviations. List soft deviations \
in ``suggested_fixes`` as non-blocking notes so the user is aware.

Set ``matches_intent=False`` ONLY if a **hard** criterion is unmet.

---

## FIGURE COMPLETENESS — CRITICAL (hard criterion)

The design document specifies a set of figures. Each figure exists to \
support the hypothesis. Count them.

**REJECT if:**
- The code produces significantly fewer figures than the design lists \
  (e.g., 8 out of 15). A shortfall of 1–2 figures that are clearly \
  conditional (data may not exist) is acceptable if the code logs a \
  WARNING explaining the skip.
- A core diagnostic category is entirely missing (e.g., no intensity \
  figures, no anomaly figures, no scatter figures when the design \
  specifies all three).

**DO NOT REJECT if:**
- The code produces the right number of figures but filenames differ \
  slightly from the design (e.g., suffix added, subdirectory used).
- A figure is conditionally skipped with a logged WARNING because the \
  required data field does not exist in the input.
- Extra figures beyond the design are generated.

---

## SOFT CRITERIA — DO NOT REJECT FOR THESE

These are common deviations that do NOT warrant rejection:

- **Output paths**: writing to ``output_dir/tables/file.csv`` instead \
  of ``output_dir/file.csv`` — the content matters, not the subdirectory.
- **Filename conventions**: extra suffixes, different separators, \
  slight name changes — as long as the figure content matches.
- **Edge-case handling**: code that warns and skips when optional data \
  is missing is CORRECT behavior, not a failure.
- **Conditional figures**: if the design says "plot X if available" and \
  the code skips with a warning when X is absent, that is correct.
- **Extra variants**: producing both a standard and a supplementary \
  version of a figure (e.g., a smoothed or per-group variant) is bonus, \
  not a defect.
- Style issues (naming, docstrings, unused imports).
- Implementation choices for reading data that follow the conventions \
  documented in the design document or data-format reference — do not \
  second-guess domain conventions.
- Proxy metrics instead of exact metrics, when the design's data \
  description makes the exact metric unavailable.

---

## PRAGMATIC BOUNDARIES

You are a **gate**, not a code reviewer. Catch broken and incomplete \
code, not cosmetic issues. Think: "would a domain scientist get useful \
analysis output from this script on well-formed input data?"

**APPROVE (matches_intent=True) if the code:**
- Uses the provided data interface correctly
- Produces the figures specified in the design (count and scientific \
  content, not exact filenames)
- Computes the right types of diagnostics
- Would run without crashing on well-formed input data

**REJECT (matches_intent=False) ONLY if the code:**
- Ignores the design (e.g., produces unrelated output)
- Has a bug that would crash on ANY valid input (not edge cases)
- Ignores the data interface (e.g., tries to read files directly \
  instead of using the provided ``data`` object)
- Is missing an entire category of analysis the design requires
- Produces zero useful output

---

## THE HARNESS BOUNDARY — NOT YOUR CALL

The code under review is a **plot module** executed by a fixed harness. \
Data loading, file discovery, CLI parsing, and unit conversion are the \
harness's job — their ABSENCE from the module is correct, never a \
defect. If a DATA FORMAT REFERENCE is appended below, it is ground \
truth for the ``data`` object the module receives — judge variable \
usage against it and do not invent stricter requirements than it \
states.

---

## IMPLEMENTATION STRATEGY IS NEVER A HARD FAILURE

The design's CONSTRAINTS and BEST PRACTICES sections guide the \
generator. They are NOT your rejection checklist. The following are \
ALWAYS soft — note them in ``suggested_fixes`` if you like, but they \
can never set ``matches_intent=False``:

- **I/O strategy**: reading a whole file vs seeking byte offsets, \
  memory use, loop efficiency — for any file size. If the extracted \
  values would be correct, the strategy is acceptable.
- **Per-figure styling**: whether an individual curve is smoothed or \
  raw, panel layout, legend placement. Cumulative curves (e.g. \
  accumulated rainfall) are legitimately plotted either way.
- **Label sourcing**: where unit strings come from, exact label text.
- **Partial defense-in-depth**: containment or robustness checks the \
  design mentions that the code implements only partially.

Ask ONE question: "would the figures be scientifically correct and \
complete on well-formed input?" If yes for every required figure \
category, set ``matches_intent=True``.
"""


def _validate_intent_output(output: Any) -> str | None:
    """Domain-specific validation for intent checker output."""
    if not isinstance(output, IntentCheckerOutputSchema):
        return None
    if not output.reasoning.strip():
        return "reasoning is empty — provide a 2-4 sentence justification."
    if not output.matches_intent and not output.suggested_fixes:
        return (
            "matches_intent is False but suggested_fixes is empty. "
            "When rejecting code, you MUST provide concrete, "
            "actionable fixes so the generator can correct the issues."
        )
    return None


class IntentCheckerConfig(PydanticAIBaseAgentConfig):
    """Configuration for the Intent Checker Agent."""

    system_prompt: str = Field(default=_GENERIC_INTENT_CHECKER_PROMPT)
    model_name: str = Field(default="openai:gpt-5.2")
    data_format_context: str = Field(default="", description=DATA_FORMAT_CONTEXT_DESC)


def _assemble_intent_checker_prompt(config: "IntentCheckerConfig") -> str:
    """Build the full system prompt from config fields."""
    return assemble_prompt(
        config.system_prompt,
        section("DATA FORMAT REFERENCE", config.data_format_context),
    )


class IntentCheckerAgent(
    PydanticAIBaseAgent[IntentCheckerInputSchema, IntentCheckerOutputSchema],
):
    """LLM-as-judge that evaluates generated code for intent and safety.

    Classifies success criteria as hard (scientific) vs soft
    (implementation detail) and only rejects when hard criteria are
    unmet. Runs after cheaper deterministic validators (allowlist +
    bandit).
    """

    input_schema = IntentCheckerInputSchema
    output_schema = IntentCheckerOutputSchema
    config_schema = IntentCheckerConfig

    def __init__(self, config: IntentCheckerConfig | None = None) -> None:
        config = config or self.config_schema()
        assembled = _assemble_intent_checker_prompt(config)
        config = config.model_copy(update={"system_prompt": assembled})
        super().__init__(config)

    def check_output(self, output) -> str | None:
        return _validate_intent_output(output) or super().check_output(output)
