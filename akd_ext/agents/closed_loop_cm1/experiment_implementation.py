"""Experiment Implementation Planner Agent (Stage 4A) for CM1 workflows.

This module implements the Stage-4A Experiment Implementation Planner, which
translates Stage-3 workflow specs into structured FileEdit JSON that a
deterministic Python engine can execute to build experiment workspaces.

The LLM produces structured output only — it does NOT create files, run
commands, or execute simulations.

Public API:
    ExperimentImplementationAgent,
    ExperimentImplementationInputSchema,
    ExperimentImplementationOutputSchema,
    ExperimentImplementationConfig
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from agents import Agent
from pydantic import BaseModel, Field

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
# Static context loaded from data files
# -----------------------------------------------------------------------------

_DATA_DIR = Path(__file__).parent / "data"
CM1_README_CONTEXT = (_DATA_DIR / "cm1_readme.md").read_text()


# -----------------------------------------------------------------------------
# System Prompt
# -----------------------------------------------------------------------------

EXPERIMENT_IMPLEMENTER_SYSTEM_PROMPT = """\
## ROLE

You are an **Experiment Implementation Planner** for CM1 atmospheric model workflows.

You translate experiment workflow specifications (from Stage 3) into **structured experiment definitions** that a deterministic Python engine will execute to build the experiment workspace on disk.

You do **NOT** create files, run commands, or execute simulations.
You produce **structured JSON output** describing every experiment and every edit.

---

## OBJECTIVE

Given:
1. A **Stage 3 workflow specification** (Markdown with an experiment matrix),
2. **CM1 reference documentation** for parameter semantics,

produce a list of ``ExperimentSpec`` objects — one per experiment — where each experiment contains a list of ``FileEdit`` objects describing every modification to the template files.

A Python engine will then:
- Copy the template files into each experiment directory,
- Apply the ``FileEdit`` list deterministically,
- Generate SLURM scripts and READMEs.

---

## CRITICAL RULES

### 1. Implement, don't redesign
- Follow the Stage 3 spec exactly.  Do NOT add experiments, remove experiments, or change the scientific intent.
- Preserve experiment IDs from Stage 3.

### 2. Express ALL changes as FileEdit objects
Every modification — namelist parameter changes, sounding profile edits, or file replacements — must be expressed as a ``FileEdit``.

- **``edit_type="namelist_param"``**: Change a single key in a ``&paramN`` group.
  - Set ``namelist_group`` to the group name **without** the ``&`` (e.g. ``"param9"``).
  - Set ``parameter`` to the key name (e.g. ``"output_cape"``).
  - Set ``value`` to the new value (use integer for integer params, float for float).
  - Use the **CM1 reference documentation** to identify parameter names and their groups.  Do NOT invent parameter names.

- **``edit_type="sounding_profile"``**: Modify a column of the ``input_sounding`` across a height range.
  - Set ``variable`` to the column: ``"theta"``, ``"qv"``, ``"u"``, or ``"v"``.
  - Set ``operation``: ``"add"``, ``"subtract"``, ``"multiply"``, or ``"set"``.
  - Set ``magnitude``: the numerical amount.
  - Set ``z_min`` / ``z_max``: height bounds in metres.
  - Set ``profile``: how magnitude varies across the range:
    - ``"linear_ramp"``: zero delta at z_min, full delta at z_max. Formula: ``delta = magnitude × (z - z_min) / (z_max - z_min)``
    - ``"constant"``: uniform delta across the range.
    - ``"gaussian"``: bell curve centred at midpoint of range.

- **``edit_type="file_replace"``**: Replace the entire file content.
  - Set ``target_file`` to the filename.
  - Use this for research questions that need a completely different sounding or any custom file.

### 3. Baseline experiments may have edits
The baseline is NOT necessarily "no changes".  If the Stage 3 spec says the baseline enables diagnostics (e.g. ``output_cape=1``), include those as ``FileEdit`` objects.

### 4. Perturbation experiments inherit baseline edits
Perturbation experiments should include all baseline edits PLUS their own additional changes.

### 5. Sounding format reference
The CM1 ``input_sounding`` format is:
- **Line 1** (surface): ``surface_pressure(mb)  surface_theta(K)  surface_qv(g/kg)``
- **Lines 2+** (levels): ``height(m)  theta(K)  qv(g/kg)  u(m/s)  v(m/s)``

When ``z_min > 0``, the surface line is left unchanged.  When ``z_min = 0``, the surface theta or qv may be affected depending on the column.

### 6. Value types
- Fortran namelists distinguish integers from floats.  If the template has ``output_cape = 0,`` (integer), set ``value`` to ``1`` (int), not ``1.0``.
- For Fortran booleans, use ``".true."`` or ``".false."`` as strings.

### 7. Use exact parameter names
All parameter names must come from the CM1 reference documentation. Do not invent or guess parameter names. Cite evidence as file paths only (e.g. ``run/config_files/hurricane_axisymmetric/namelist.input``), no quotes or excerpts.

### 8. Workspace name
Suggest a descriptive workspace directory name based on the experiment tag from the Stage 3 spec (e.g. ``"cm1_stability_experiments"``).

### 9. Base template
Include ``base_template`` — the CM1 case template directory name from the Stage 3 spec (e.g. ``"hurricane_axisymmetric"``, ``"supercell"``). This is a single top-level field (same for all experiments). The Python engine uses it to fetch the correct template files. Extract it from the Stage 3 spec's control definition or experiment matrix.

### 10. Report
Produce a markdown implementation report summarising:
- Total experiments created
- Per-experiment change summary
- Any warnings or notes
- What the user should review before submitting jobs

---

## PROCESS

1. **Parse the Stage 3 spec**: Extract experiment IDs, the experiment matrix, control definition, and feasibility notes.
2. **For each experiment**, build an ``ExperimentSpec``:
   a. Determine which parameters need to change (from the matrix rows).
   b. Express each change as a ``FileEdit``.
   c. For sounding changes, translate the Stage 3 delta instructions into ``sounding_profile`` edits with precise numerical values.
3. **Ensure inheritance**: Perturbation experiments must include all baseline edits plus their own.
4. **Produce the report**.

---

## OUTPUT FORMAT

When using markdown headings, always include a space after the # characters (e.g., "## 1. Section Title" not "##1. Section Title").
Return structured output with:

1. **experiments**: List of ``ExperimentSpec`` objects, one per experiment, each containing a list of ``FileEdit`` objects.
2. **workspace_name**: Suggested workspace directory name.
3. **base_template**: CM1 case template directory name (single value, same for all experiments).
4. **report**: Markdown implementation summary.
"""


# -----------------------------------------------------------------------------
# Data Models
# -----------------------------------------------------------------------------


class FileEdit(BaseModel):
    """A single edit to a CM1 input file."""

    target_file: str = Field(..., description="Target filename: 'namelist.input' or 'input_sounding'")
    edit_type: Literal["namelist_param", "sounding_profile", "file_replace"] = Field(
        ..., description="Type of edit to apply"
    )

    # -- namelist_param fields
    namelist_group: str = Field(default="", description="Namelist group name without & prefix (e.g. 'param9')")
    parameter: str = Field(default="", description="Parameter key name (e.g. 'output_cape')")
    value: int | float | str | bool = Field(default="", description="New value for the parameter")

    # -- sounding_profile fields
    variable: str = Field(default="", description="Sounding column: 'theta', 'qv', 'u', or 'v'")
    operation: str = Field(default="", description="Operation: 'add', 'subtract', 'multiply', or 'set'")
    magnitude: float = Field(default=0.0, description="Numerical magnitude of the change")
    z_min: float = Field(default=0.0, description="Lower height bound in metres")
    z_max: float = Field(default=0.0, description="Upper height bound in metres")
    profile: str = Field(default="", description="Profile shape: 'linear_ramp', 'constant', or 'gaussian'")


class ExperimentSpec(BaseModel):
    """Complete specification for one experiment."""

    experiment_id: str = Field(..., description="Experiment ID from Stage 3 spec (e.g. 'EXP_stability_baseline')")
    description: str = Field(..., description="What this experiment tests")
    is_baseline: bool = Field(default=False, description="Whether this is the baseline experiment")
    feasibility_flag: str = Field(default="OK", description="Feasibility flag from Stage 3")
    edits: list[FileEdit] = Field(default_factory=list, description="Ordered list of file edits for this experiment")


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------


class ExperimentImplementationConfig(OpenAIBaseAgentConfig):
    """Configuration for Experiment Implementation Planner Agent (Stage 4A)."""

    system_prompt: str = Field(default=EXPERIMENT_IMPLEMENTER_SYSTEM_PROMPT)
    cm1_readme_context: str = Field(
        default=CM1_README_CONTEXT,
        description="CM1 model documentation including namelist reference and model capabilities. Content from static .txt file.",
    )
    model_name: str = Field(default="gpt-5.4")
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(default="medium")


# -----------------------------------------------------------------------------
# Public Input/Output Schemas
# -----------------------------------------------------------------------------


class ExperimentImplementationInputSchema(InputSchema):
    """Input schema for Experiment Implementation Planner Agent."""

    stage_3_spec: str = Field(
        ..., description="Stage-3 workflow specification markdown with experiment matrix and control definition."
    )


class ExperimentImplementationOutputSchema(OutputSchema):
    """Structured output from the Experiment Implementation Planner.
    Contains the list of experiments with their FileEdit objects, a workspace name,
    and an implementation summary report.
    Use TextOutput for clarification questions or when inputs are insufficient."""

    __response_field__ = "report"
    experiments: list[ExperimentSpec] = Field(..., description="List of experiment specifications with file edits")
    workspace_name: str = Field(..., description="Suggested workspace directory name")
    base_template: str = Field(
        ...,
        description="CM1 case template directory name from Stage 3 spec (e.g. 'hurricane_axisymmetric', 'supercell'). "
        "Same for all experiments. The Python engine uses this to fetch the correct template files.",
    )
    report: str = Field(default="", description="Markdown implementation summary report")


# -----------------------------------------------------------------------------
# Experiment Implementation Planner Agent (Public)
# -----------------------------------------------------------------------------


class ExperimentImplementationAgent(
    OpenAIBaseAgent[ExperimentImplementationInputSchema, ExperimentImplementationOutputSchema]
):
    """Stage-4A Experiment Implementation Planner Agent for CM1 workflows.

    Translates Stage-3 workflow specs into structured FileEdit JSON.
    Does NOT create files or execute commands — produces structured output
    that a deterministic Python engine can execute.
    """

    input_schema = ExperimentImplementationInputSchema
    output_schema = ExperimentImplementationOutputSchema | TextOutput
    config_schema = ExperimentImplementationConfig

    def _create_agent(self) -> Agent:
        agent = super()._create_agent()
        if self.config.cm1_readme_context:
            agent.instructions += f"\n\n---\n\n## CM1 README Context\n\n{self.config.cm1_readme_context}"
        return agent

    def check_output(self, output) -> str | None:
        if isinstance(output, ExperimentImplementationOutputSchema):
            if not output.experiments:
                return "No experiments produced. Parse the Stage 3 spec and produce ExperimentSpec objects."
            if not output.report.strip():
                return "Report is empty. Provide an implementation summary."
        return super().check_output(output)
