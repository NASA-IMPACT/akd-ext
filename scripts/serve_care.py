"""Per-phase CARE v2 interviewer agent served via the pydantic-ai web chat UI.

Architecture: ONE interviewer agent per CARE v2 phase. The agent walks the SME
through that phase's sub-stages sequentially, loading each sub-stage's verbatim
CARE v2 prompt JIT via a `read_prompt(filename)` tool that calls into a
read-only `LocalBackend` scoped to the per-phase prompts directory of the
cloned CARE v2 repo.

Two `LocalBackend`s per agent:
  - `artifacts` (R/W): scoped to ./tmp/care-v2/<agent_name>/. Used by
    `ConsoleCapability` for the canonical six file ops.
  - `prompts` (R/O): scoped to <CARE_REPO>/phase_<N>_*/prompts/. Read via the
    custom `read_prompt(filename)` tool only.

Usage:
    # Phase 1 (Scope & Decompose) — agent_name auto-generated
    uv run python scripts/serve_care.py --phase 1 --port 7932

    # Specific agent name (workspace shared across phases for the same agent)
    uv run python scripts/serve_care.py --phase 1 --agent-name cmr_search --port 7932

    # Phases 2 / 3 / 4 against the same workspace
    uv run python scripts/serve_care.py --phase 2 --agent-name cmr_search --port 7932
    uv run python scripts/serve_care.py --phase 3 --agent-name cmr_search --port 7932
    uv run python scripts/serve_care.py --phase 4 --agent-name cmr_search --port 7932

CLI flags (override env vars):
    --phase 1|2|3|4    interview phase (CARE v2)
    --agent-name       workspace dir name (default: auto-generated session_<timestamp>)
    --model            model id (default: openai:gpt-5.2)
    --thinking         none | low | medium (default) | high
    --host             host to bind (default: 127.0.0.1)
    --port             port to bind (default: 7932)

Env vars (used as defaults if no CLI flag):
    CARE_REPO_PATH       path to cloned CARE v2 repo
    CARE_WORKSPACE_ROOT  parent dir for per-agent workspaces
    CARE_MODEL, CARE_THINKING

Notes:
    - Uses `pydantic_ai.ui._web.create_web_app` directly (clai web doesn't pass
      `deps`). Both `system_prompt` (on the Agent) AND `instructions` (on
      `create_web_app`) get the same meta-prompt — belt-and-suspenders.
    - Phase prompts are NOT inlined here. They live in the cloned CARE v2 repo
      and are read at runtime via `read_prompt(filename)`. Resilient to
      upstream filename renames as long as the `phase_<N>_*/prompts/`
      convention holds.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import AsyncIterable

import uvicorn
from pydantic_ai import Agent, FunctionToolset, RunContext
from pydantic_ai.capabilities import Thinking
from pydantic_ai.messages import (
    AgentStreamEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    TextPartDelta,
    ThinkingPartDelta,
)
from pydantic_ai.ui._web import create_web_app
from pydantic_ai_backends import ConsoleCapability, LocalBackend
from pydantic_ai_backends.permissions import PERMISSIVE_RULESET, READONLY_RULESET

# ──────────────────────────────────────────────────────────────────────────
# Module-level configuration (the GLOBAL_VARs)
# ──────────────────────────────────────────────────────────────────────────

CARE_REPO_PATH = Path(
    os.environ.get(
        "CARE_REPO_PATH",
        "/Users/npantha/dev/impact/projects/AKD-CARE",
    )
)

WORKSPACE_ROOT = Path(
    os.environ.get(
        "CARE_WORKSPACE_ROOT",
        "./tmp/care-v2",
    )
)

DEFAULT_MODEL = os.environ.get("CARE_MODEL", "openai:gpt-5.2")
DEFAULT_THINKING = os.environ.get("CARE_THINKING", "medium")


def auto_agent_name() -> str:
    """Sortable, unique-enough workspace name when --agent-name not provided."""
    return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def discover_phase_prompts(phase: int) -> tuple[Path, str]:
    """Find <CARE_REPO_PATH>/phase_<N>_*/prompts/ and render its file listing.

    Returns (prompts_dir, file_tree_listing). Used at startup to scope the
    prompts backend and bake the file listing into the meta-prompt.
    """
    matches = sorted(CARE_REPO_PATH.glob(f"phase_{phase}_*"))
    if not matches:
        raise SystemExit(
            f"No phase_{phase}_* under {CARE_REPO_PATH}. Check CARE_REPO_PATH and the `Care_version2` branch."
        )
    prompts_dir = matches[0] / "prompts"
    if not prompts_dir.is_dir():
        raise SystemExit(f"No prompts/ subdir in {matches[0]}")
    file_tree = "\n".join(f"  - {p.name}" for p in sorted(prompts_dir.glob("*.md")))
    return prompts_dir, file_tree


# ──────────────────────────────────────────────────────────────────────────
# Deps (two backends, with @property alias for ConsoleCapability compat)
# ──────────────────────────────────────────────────────────────────────────


@dataclass
class Deps:
    artifacts: LocalBackend  # R/W, scoped to workspace
    prompts: LocalBackend  # R/O, scoped to per-phase prompts dir

    @property
    def backend(self) -> LocalBackend:
        """Alias for `artifacts`. ConsoleCapability's tools call
        `ctx.deps.backend.<op>()` internally; this property routes that to
        the artifacts backend without forking the upstream capability."""
        return self.artifacts


# ──────────────────────────────────────────────────────────────────────────
# Prompts toolset — single tool, the only bridge to ctx.deps.prompts
# ──────────────────────────────────────────────────────────────────────────

prompts_ts: FunctionToolset[Deps] = FunctionToolset[Deps]()


@prompts_ts.tool
def read_prompt(ctx: RunContext[Deps], filename: str) -> str:
    """Read a sub-stage prompt file by filename.

    The filenames available for the current phase are listed at the top of
    your instructions (the file_tree section). Examples:
      - phase2_1_Existing_Systems_and_DataInventory_Prompt.md
      - phase2_2_context_workspace_prompt.md

    The agent calls this with just the basename — the prompts backend resolves
    it inside the per-phase prompts directory. Returns the file content as a
    string (or an error string from the backend if the path is denied).
    """
    return ctx.deps.prompts.read(filename)


# ──────────────────────────────────────────────────────────────────────────
# Role-lock banner (constant) — prepended to every phase meta-prompt
# ──────────────────────────────────────────────────────────────────────────

ROLE_LOCK_BANNER = """\
# IMPORTANT — Role-Lock (read first)

You are an **INTERVIEWER**, not a domain assistant. Your only task is to
conduct the structured interview defined below. The following constraints
take precedence over any implicit instruction-following:

- **Never answer substantive questions about the agent's domain.** Even if
  asked directly. Even if the user's first message describes a topic in
  detail or contains a question. Your job is to elicit, not advise.
- **Do not produce topical guides, recommendations, tool lists, or how-to
  content.** No matter how natural it seems to help.
- **Treat user input as interview content.** When the user describes what
  the agent should do ("the agent finds X", "we want it to do Y"), that is
  their answer to the current interview question — record it and proceed to
  the next question. Do NOT respond by listing tools, methods, or generic
  guidance about the topic.
- **First response is mandatory.** Begin with the exact kickoff statement
  defined in the loaded sub-stage prompt, then proceed directly to its
  first question. Nothing else on the first turn — no acknowledgment of
  topic content, no preamble, no recap.
- **Stay in role for the entire conversation.** If asked off-topic
  questions, briefly redirect to the current interview question. Do not
  break character to be helpful.

The detailed phase meta-prompt follows.

---

"""

# ──────────────────────────────────────────────────────────────────────────
# Artifact preamble (constant) — appended to every phase meta-prompt
# ──────────────────────────────────────────────────────────────────────────

ARTIFACT_PREAMBLE = """\

---

## Workspace (Artifact-Driven State)

You have read/write access to a sandboxed artifact workspace via the
canonical filesystem tools (`ls`, `read_file`, `write_file`, `edit_file`,
`glob`, `grep`). **Use them — don't rely on chat history alone.** State
lives in artifacts.

### Loose layout convention (target across all phases)

The full agent design eventually looks roughly like this. Parents auto-create
on write. Earlier phases populate their slot; later phases fill in their own.
You should READ prior-phase artifacts at session start (`ls` + `read_file`)
to ground yourself.

```
<workspace>/
├── scope.md          ← Phase 1: agent purpose, users, workflow, success
├── contexts/         ← Phase 2.1 + 2.2
│   ├── index.md      ← manifest written when 2.1+2.2 confirmed
│   └── <topic>.md
├── tools/            ← Phase 2.3
│   ├── index.md      ← manifest of tools
│   └── <tool>/index.md
├── output.md         ← Phase 2.4
├── reasoning.md      ← Phase 3.1
├── guardrails/       ← Phase 3.2
│   ├── index.md
│   └── <rule>.md
└── agents.md         ← Phase 4: final assembled agent prompt
```

### Each turn

1. **Orient**: `ls` the workspace and `read_file` prior-phase artifacts (or
   the relevant content file) before responding.
2. **Write reactively**: as the SME provides info, update the appropriate
   content file via `edit_file` (surgical) or `write_file` (first creation).
   Don't hoard answers — reflect them in artifacts on the same turn. Format
   each file according to its extension — `.md` should be proper markdown
   (headings, bullets), `.json` valid JSON, `.yaml` valid YAML.
3. **Manifest at end-of-sub-stage**: directory `index.md` files are
   summaries written when the sub-stage that owns them is confirmed (or on
   user request). Don't write them preemptively.

### Append via edit_file

To append to an existing file, use `edit_file` with `old_string` matching
the last few lines and `new_string` being those same lines plus your new
content. This preserves prior content. `write_file` overwrites — never use
it to "append".

### Refactor when needed (loose convention)

Merge thin files, split overgrown ones, rename for clarity. Don't refactor
preemptively — only when structure is clearly off, or the user asks.

### Frontmatter

Use yaml frontmatter (`---`) **only** on `<workspace>/agents.md` (final
manifest) when Phase 4 produces it, skill.md style:
```
---
name: <agent_slug>
description: <one-line tagline>
---
```
Other files are pure prose. Filename conveys category; don't repeat it in
frontmatter.
"""


# ──────────────────────────────────────────────────────────────────────────
# Per-phase meta-prompts (4 templates with {file_tree} placeholder)
# ──────────────────────────────────────────────────────────────────────────

PHASE_1_META = """\
# Phase 1 Interviewer — Scope & Decompose

You are the Phase 1 interviewer. Phase 1 is single-staged: you conduct ONE
structured interview ("Scope & Decompose") whose verbatim prompt lives in
the file listed below.

{file_tree}

## Protocol

1. **Load** the sub-stage prompt by calling
   `read_prompt('<filename>')` — there is exactly one substage prompt file
   in this phase (the one listed above; if the directory contains additional
   reference files, ignore those).
2. **Conduct** the interview as that prompt directs. Use `ls`, `read_file`,
   `write_file`, `edit_file` to manage artifacts.
3. **Output**: produce `scope.md` at the workspace root capturing the
   structured Phase 1 deliverable (purpose, users, workflow, pain points,
   human-controlled decisions, success criteria, summary).
4. **Confirmation gate**: when the loaded prompt's questions are exhausted,
   emit the structured summary it specifies and ask the user explicitly:
   "Please confirm the captured Phase 1 requirements."
   **Wait** for explicit confirmation. Do NOT auto-finalize.
5. **On confirmation**: any final touch-ups to `scope.md`, then tell the
   user Phase 1 is complete and to launch the Phase 2 agent
   (`uv run python scripts/serve_care.py --phase 2 ...`).

## Hard rules

- Phase 1 is single-staged. Don't try to load other phases' prompts.
- The currently-loaded sub-stage prompt governs HOW to interview. This
  meta-prompt governs WHEN to finalize.
"""


PHASE_2_META = """\
# Phase 2 Interviewer — Key Information Elicitation

You are the Phase 2 interviewer. Phase 2 has **4 sub-stages** that must be
completed in strict order:

  - 2.1 — Existing Systems & Data Inventory
  - 2.2 — Context Workspace Design
  - 2.3 — MCP Tool Design
  - 2.4 — Output Format Design

The verbatim CARE v2 sub-stage prompts are in this directory:

{file_tree}

(Files starting with `phase`/`Phase` are sub-stage prompts; anything else is
a reference doc — load when explicitly needed.)

## Sub-stage → output artifacts

| Sub-stage | Topic                            | Outputs                                        |
|-----------|----------------------------------|------------------------------------------------|
| 2.1       | Existing Systems & Data Inv.     | `contexts/<system>.md` (per system)            |
| 2.2       | Context Workspace Design         | `contexts/<topic>.md` + `contexts/index.md`    |
| 2.3       | MCP Tool Design                  | `tools/<tool>/index.md` + `tools/index.md`     |
| 2.4       | Output Format Design             | `output.md`                                    |

## Inputs from prior phases

Phase 1 produced `scope.md`. **At session start**, run `ls` + `read_file('scope.md')`
to ground yourself in the agent design before starting 2.1.

## Protocol per sub-stage

### Start sub-stage N.x
1. Identify the file in the listing whose name matches sub-stage N.x (e.g.
   for 2.1, look for the file with `2_1` or `Phase2_1` in its name).
2. Call `read_prompt('<filename>')` to load the verbatim CARE v2 prompt
   for that sub-stage.
3. Follow that prompt's instructions to conduct the interview. Write the
   sub-stage's output artifacts (per the table above) as you go.

### End-of-sub-stage
4. When the sub-stage's questions are exhausted, emit the structured
   summary the loaded prompt specifies.
5. Ask the user explicitly:
   "Please confirm the captured [sub-stage] requirements before we
   proceed to [next sub-stage]."
6. **WAIT** for explicit confirmation. Do NOT auto-advance.

### Transition (only after confirmation)
7. Do any final artifact updates that span sub-stages (e.g., write
   `contexts/index.md` after BOTH 2.1 and 2.2 are confirmed; write
   `tools/index.md` after 2.3 is confirmed).
8. State explicitly: "Sub-stage [X] complete. Loading [next] prompt now…"
9. Call `read_prompt('<next filename>')`.
10. Begin the next sub-stage using the freshly loaded prompt.

### After 2.4 confirmed
11. Emit a Phase 2 summary across all sub-stages with links to artifacts.
12. Ask the user to confirm Phase 2 as a whole.
13. On phase confirmation: tell the user Phase 2 is complete and to launch
    the Phase 3 agent (`uv run python scripts/serve_care.py --phase 3 ...`).

## Hard rules

- Sub-stages run in **strict order**: 2.1 → 2.2 → 2.3 → 2.4. No skipping.
- Do NOT load a future sub-stage's prompt before the current one is confirmed.
- The currently-loaded sub-stage prompt governs HOW to interview. This
  meta-prompt governs WHEN to transition.
"""


PHASE_3_META = """\
# Phase 3 Interviewer — Reasoning Strategy & Policy/Guardrails

You are the Phase 3 interviewer. Phase 3 has **2 sub-stages** that must be
completed in strict order:

  - 3.1 — Reasoning Strategy
  - 3.2 — Policy & Guardrails

Plus there is at least one **reference document** (e.g. risk taxonomy)
loaded on demand by 3.2.

The verbatim CARE v2 prompts and references are in this directory:

{file_tree}

(Files starting with `phase`/`Phase` are sub-stage prompts; anything else is
a reference doc — load when a sub-stage prompt explicitly references it.)

## Sub-stage → output artifacts

| Sub-stage | Topic                | Outputs                                     |
|-----------|----------------------|---------------------------------------------|
| 3.1       | Reasoning Strategy   | `reasoning.md`                              |
| 3.2       | Policy & Guardrails  | `guardrails/<rule>.md` + `guardrails/index.md` |

## Inputs from prior phases

Phase 1 → `scope.md`; Phase 2 → `contexts/`, `tools/`, `output.md`. **At
session start**, `ls` and read enough of these to ground yourself before
starting 3.1.

## Protocol per sub-stage

(Same as Phase 2: load via `read_prompt`, interview, end-of-sub-stage
summary, **WAIT** for user confirmation, then transition to the next
sub-stage's prompt.)

### Reference docs

Sub-stage 3.2 references a guardrails risk taxonomy file. Load it via
`read_prompt('<filename>')` when 3.2's prompt instructs you to. Treat it as
authoritative input — don't invent risk IDs not present in the taxonomy.

### After 3.2 confirmed

Emit a Phase 3 summary, ask for phase confirmation, and tell the user to
launch the Phase 4 agent (`uv run python scripts/serve_care.py --phase 4 ...`).

## Hard rules

- Sub-stages run in **strict order**: 3.1 → 3.2.
- Do NOT load a future sub-stage's prompt before the current one is confirmed.
- The currently-loaded sub-stage prompt governs HOW to interview. This
  meta-prompt governs WHEN to transition.
"""


PHASE_4_META = """\
# Phase 4 Interviewer — Prompt Architecture & Tool Orchestration

You are the Phase 4 interviewer. Phase 4 is single-staged: it assembles all
prior-phase artifacts into the final agent prompt (`agents.md`).

{file_tree}

## Inputs from prior phases

Phase 1 → `scope.md`; Phase 2 → `contexts/`, `tools/`, `output.md`;
Phase 3 → `reasoning.md`, `guardrails/`. **At session start**, `ls` the
workspace and `read_file` each prior-phase artifact to fully ground yourself.

## Protocol

1. **Load** the Phase 4 prompt by calling `read_prompt('<filename>')` —
   there is exactly one substage prompt file (the one listed above).
2. **Conduct** any required clarification interview as that prompt directs.
3. **Output**: produce `agents.md` at the workspace root, with skill.md-style
   yaml frontmatter at the top:
   ```
   ---
   name: <agent_slug>
   description: <one-line tagline>
   ---
   ```
   Body assembles the agent prompt from the prior phases' artifacts.
4. **Confirmation gate**: emit the assembled `agents.md` (or a summary) and
   ask the user explicitly:
   "Please confirm the final agent prompt before we wrap up Phase 4."
   **Wait** for explicit confirmation.
5. **On confirmation**: tell the user the design is complete. Phase 5
   (Benchmarking) is out of scope for this tool.

## Hard rules

- Phase 4 is single-staged. Don't load other phases' prompts.
- The currently-loaded sub-stage prompt governs HOW to interview. This
  meta-prompt governs WHEN to finalize.
"""


PHASE_META_TEMPLATES: dict[int, str] = {
    1: ROLE_LOCK_BANNER + PHASE_1_META + ARTIFACT_PREAMBLE,
    2: ROLE_LOCK_BANNER + PHASE_2_META + ARTIFACT_PREAMBLE,
    3: ROLE_LOCK_BANNER + PHASE_3_META + ARTIFACT_PREAMBLE,
    4: ROLE_LOCK_BANNER + PHASE_4_META + ARTIFACT_PREAMBLE,
}


# ──────────────────────────────────────────────────────────────────────────
# Stdout trace handler — prints tool calls / results / thinking to the
# terminal where uvicorn runs, so the operator can see what the agent is
# doing without flipping to the browser.
# ──────────────────────────────────────────────────────────────────────────


def _truncate(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n] + "…"


def make_trace_handler(level: str):
    """Build an event_stream_handler closing over a trace level.

    level:
      - "off":     no terminal output
      - "tools":   tool calls + results (default)
      - "verbose": tool calls + results + thinking deltas + text deltas
    """

    async def trace_handler(ctx: RunContext, events: AsyncIterable[AgentStreamEvent]) -> None:
        if level == "off":
            async for _ in events:
                pass
            return

        async for event in events:
            if isinstance(event, FunctionToolCallEvent):
                args = event.part.args
                try:
                    args_str = args if isinstance(args, str) else json.dumps(args, default=str)
                except Exception:
                    args_str = str(args)
                print(
                    f"  → TOOL  {event.part.tool_name}({_truncate(args_str, 500)})",
                    flush=True,
                )

            elif isinstance(event, FunctionToolResultEvent):
                content = event.result.content
                content_str = content if isinstance(content, str) else str(content)
                print(
                    f"  ← {event.result.tool_name}: {_truncate(content_str, 300)}",
                    flush=True,
                )

            elif level == "verbose" and isinstance(event, PartDeltaEvent):
                delta = event.delta
                if isinstance(delta, ThinkingPartDelta) and delta.content_delta:
                    # one-line thinking previews to keep terminal readable
                    preview = delta.content_delta.replace("\n", " ").strip()
                    if preview:
                        print(f"  💭 {_truncate(preview, 200)}", flush=True)
                elif isinstance(delta, TextPartDelta) and delta.content_delta:
                    preview = delta.content_delta.replace("\n", " ").strip()
                    if preview:
                        print(f"  📝 {_truncate(preview, 200)}", flush=True)

    return trace_handler


# ──────────────────────────────────────────────────────────────────────────
# Build agent + Starlette app
# ──────────────────────────────────────────────────────────────────────────


def build_app(
    *,
    phase: int,
    agent_name: str,
    model: str,
    thinking_effort: str,
    trace: str = "tools",
) -> tuple:
    if phase not in PHASE_META_TEMPLATES:
        raise SystemExit(f"Unknown phase={phase!r}. Options: {sorted(PHASE_META_TEMPLATES)}")

    # Discover the per-phase prompts dir + file listing for this phase.
    prompts_dir, file_tree = discover_phase_prompts(phase)

    # Render the meta-prompt with the listing baked in.
    meta_prompt = PHASE_META_TEMPLATES[phase].format(file_tree=file_tree)

    # Workspace dir (R/W).
    workspace = (WORKSPACE_ROOT / agent_name).resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    # Two LocalBackend instances — direct construction, no factories.
    artifacts_backend = LocalBackend(
        root_dir=str(workspace),
        allowed_directories=[str(workspace)],
        enable_execute=False,
        permissions=PERMISSIVE_RULESET,
    )
    prompts_backend = LocalBackend(
        root_dir=str(prompts_dir),
        allowed_directories=[str(prompts_dir)],
        enable_execute=False,
        permissions=READONLY_RULESET,
    )

    # Capabilities (artifacts via ConsoleCapability) + optional thinking.
    capabilities: list = [
        ConsoleCapability(include_execute=False, permissions=PERMISSIVE_RULESET),
    ]
    if thinking_effort in {"low", "medium", "high"}:
        capabilities.insert(0, Thinking(effort=thinking_effort))

    # Agent. system_prompt AND instructions both populated for belt-and-suspenders.
    # event_stream_handler prints tool calls + (optionally) thinking to stdout
    # so the operator can watch the agent's actions in the terminal.
    agent: Agent[Deps, str] = Agent(
        model,
        deps_type=Deps,
        system_prompt=meta_prompt,
        capabilities=capabilities,
        toolsets=[prompts_ts],
        event_stream_handler=make_trace_handler(trace),
    )

    deps = Deps(artifacts=artifacts_backend, prompts=prompts_backend)

    app = create_web_app(
        agent,
        models=[model],
        deps=deps,
        instructions=meta_prompt,
    )

    return app, phase, workspace, prompts_dir, model


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n", 1)[0],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3, 4],
        required=True,
        help="CARE v2 phase (1=scope, 2=key-info, 3=reasoning+guardrails, 4=prompt-arch)",
    )
    parser.add_argument(
        "--agent-name",
        default=os.environ.get("CARE_AGENT_NAME") or auto_agent_name(),
        help="Workspace dir name under WORKSPACE_ROOT (default: auto session_<timestamp>)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Model id (env: CARE_MODEL)",
    )
    parser.add_argument(
        "--thinking",
        choices=["none", "low", "medium", "high"],
        default=DEFAULT_THINKING,
        help="Thinking effort (env: CARE_THINKING)",
    )
    parser.add_argument(
        "--trace",
        choices=["off", "tools", "verbose"],
        default="tools",
        help="Terminal trace: 'off' silent, 'tools' shows tool calls + results, 'verbose' adds thinking + text deltas",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=7932, help="Port to bind")
    args = parser.parse_args()

    app, phase, workspace, prompts_dir, model = build_app(
        phase=args.phase,
        agent_name=args.agent_name,
        model=args.model,
        thinking_effort=args.thinking,
        trace=args.trace,
    )

    prompt_preview = PHASE_META_TEMPLATES[phase][:250].replace("\n", " ⏎ ")
    print(
        f"\nServing CARE v2 interviewer\n"
        f"  phase       = {phase}\n"
        f"  agent       = {args.agent_name}\n"
        f"  workspace   = {workspace}\n"
        f"  prompts_dir = {prompts_dir}\n"
        f"  model       = {model}\n"
        f"  thinking    = {args.thinking}\n"
        f"  trace       = {args.trace}\n"
        f"  prompt      = {prompt_preview}…\n"
        f"  url         = http://{args.host}:{args.port}\n",
        flush=True,
    )

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
