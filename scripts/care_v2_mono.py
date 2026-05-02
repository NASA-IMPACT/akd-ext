"""Single mono CARE v2 interviewer agent served via the pydantic-ai web chat UI.

Architecture: ONE interviewer agent for ALL CARE v2 phases. At session start,
the agent inspects the workspace artifacts to infer the current phase and
proposes the next sub-stage. No `--phase` flag — the agent figures it out from
the artifacts.

Two `LocalBackend`s per agent:
  - `artifacts` (R/W): scoped to ./tmp/care-v2/<agent_name>/. Used by
    `ConsoleCapability` for the canonical six file ops.
  - `prompts` (R/O): scoped to ALL phase prompt dirs of the cloned CARE v2
    repo (`<CARE_REPO>/phase_*/prompts/`). Read via the custom
    `read_prompt(path)` tool only. Path is repo-relative,
    e.g. `phase_2_*/prompts/phase2_2_context_workspace_prompt.md`.

Usage:
    # Fresh start — agent_name auto-generated, agent will infer empty workspace and propose Phase 1
    uv run python scripts/care_v2_mono.py --port 7932

    # Specific agent name (workspace persists across runs; agent picks up where it left off)
    uv run python scripts/care_v2_mono.py --agent-name cmr_search --port 7932

    # Resume a session — agent infers state from existing artifacts
    uv run python scripts/care_v2_mono.py --agent-name cmr_search --port 7932

CLI flags (override env vars):
    --agent-name       workspace dir name (default: auto-generated session_<timestamp>)
    --model            model id (default: openai:gpt-5.2)
    --thinking         none | low | medium (default) | high
    --trace            off | tools (default) | verbose — terminal tool-call visibility
    --host             host to bind (default: 127.0.0.1)
    --port             port to bind (default: 7932)

Env vars (used as defaults if no CLI flag):
    CARE_REPO_PATH       path to cloned CARE v2 repo
    CARE_WORKSPACE_ROOT  parent dir for per-agent workspaces
    CARE_MODEL, CARE_THINKING

Behavior:
    - Forward-jump prevention: agent refuses to start a sub-stage whose
      prerequisites (prior sub-stages' artifacts) are missing or unconfirmed.
    - Backward edits ALLOWED: user can revise a prior phase's artifact at any
      time without restarting / phase-switching.

Notes:
    - Uses `pydantic_ai.ui._web.create_web_app` directly (clai web doesn't pass
      `deps`). Both `system_prompt` (on the Agent) AND `instructions` (on
      `create_web_app`) get the same meta-prompt — belt-and-suspenders.
    - Phase prompts are NOT inlined here. They live in the cloned CARE v2 repo
      and are read at runtime via `read_prompt(<repo-relative-path>)`.
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


def discover_all_prompts(care_repo: Path) -> tuple[list[Path], str]:
    """Scan all phase dirs and return (per-phase prompts dirs, markdown listing).

    The listing groups prompts by phase; paths are repo-relative so the agent
    can pass them straight to `read_prompt`. Used once at startup to:
      - scope the prompts backend (allowed_directories = list of phase prompt dirs)
      - bake the file listing into the mono meta-prompt's `{prompt_tree}` slot
    """
    phase_dirs = sorted(care_repo.glob("phase_*"))
    if not phase_dirs:
        raise SystemExit(f"No phase_* dirs under {care_repo}. Check CARE_REPO_PATH and the `Care_version2` branch.")

    prompts_dirs: list[Path] = []
    lines: list[str] = [
        "Prompt files available across phases (read via `read_prompt('<path>')`):",
        "",
    ]
    for phase_dir in phase_dirs:
        prompts_dir = phase_dir / "prompts"
        if not prompts_dir.is_dir():
            continue
        prompts_dirs.append(prompts_dir)
        lines.append(f"### {phase_dir.name}")
        for f in sorted(prompts_dir.glob("*.md")):
            rel = f.relative_to(care_repo)
            lines.append(f"  - `{rel}`")
        lines.append("")

    if not prompts_dirs:
        raise SystemExit(f"No phase_*/prompts/ dirs under {care_repo}")

    return prompts_dirs, "\n".join(lines)


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
def read_prompt(ctx: RunContext[Deps], path: str) -> str:
    """Read a CARE v2 prompt by repo-relative path.

    The available paths are listed at the top of your instructions (the
    `prompt_tree` section). Examples:
      - phase_1_scope_and_decompose/prompts/phase1_scope_and_decompose_agent_prompt.md
      - phase_2_key_information_elicitation/prompts/phase2_2_context_workspace_prompt.md

    Returns the file content as a string (or an error string from the backend
    if the path is denied / not found).
    """
    return ctx.deps.prompts.read(path)


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
3. **Manifest at end-of-sub-stage**: each leaf directory has multiple
   per-aspect files plus a brief `index.md` manifest. The manifest contains
   a directory summary plus one entry per file (WHAT it covers, WHEN it
   applies, and the filename). Don't dump everything into one big
   `index.md`. On substage confirmation, remove `(draft)` markers and
   process metadata (status, source, SME identity, timestamp, open
   questions) from artifacts. Write `index.md` when the substage that owns
   it is confirmed (or on user request).

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
# Mono meta-prompt — single prompt covering all phases, with state inference
# ──────────────────────────────────────────────────────────────────────────

MONO_META_BODY = """\
# CARE v2 Interviewer (Single-Agent / All Phases)

You are the CARE v2 interviewer for the full design process. The user may
launch you at any point — at session start you infer where you are by
inspecting the workspace artifacts and propose the next step.

## Phases

| Phase | Sub-stages | Outputs |
|-------|------------|---------|
| 1 — Scope & Decompose             | (single)            | `scope.md` |
| 2 — Key Info Elicitation          | 2.1, 2.2, 2.3, 2.4  | `contexts/`, `tools/`, `output.md` |
| 3 — Reasoning & Guardrails        | 3.1, 3.2            | `reasoning.md`, `guardrails/` |
| 4 — Prompt Architecture           | (single)            | `agents.md` |

(Phase 5 / benchmarking is out of scope.)

## Available CARE v2 prompts

{prompt_tree}

## Sub-stage → CARE v2 prompt → output artifacts

| Sub-stage | CARE v2 prompt path (pattern)                              | Output artifacts                                  |
|-----------|------------------------------------------------------------|---------------------------------------------------|
| 1.1       | `phase_1_scope_and_decompose/prompts/phase1_*.md`          | `scope.md`                                        |
| 2.1       | `phase_2_*/prompts/phase2_1_*.md`                          | `contexts/<system>.md` (per system)               |
| 2.2       | `phase_2_*/prompts/phase2_2_*.md`                          | `contexts/<topic>.md` + `contexts/index.md`       |
| 2.3       | `phase_2_*/prompts/phase2_3_*.md`                          | `tools/<tool>/<aspect>.md` + `tools/index.md`     |
| 2.4       | `phase_2_*/prompts/Phase2_4_*.md`                          | `output.md`                                       |
| 3.1       | `phase_3_*/prompts/phase3_1_*.md`                          | `reasoning.md`                                    |
| 3.2       | `phase_3_*/prompts/phase3_2_*.md` (+ taxonomy reference)   | `guardrails/<rule>.md` + `guardrails/index.md`    |
| 4.1       | `phase_4_*/prompts/phase_4_*.md`                           | `agents.md`                                       |

Resolve the actual filename for each sub-stage from the prompt-file listing
above; pass the full repo-relative path to `read_prompt`.

## Session-start protocol

1. **Orient**: `ls` the workspace and `read_file` each existing artifact
   (skim is fine) to understand the current state.
2. **Infer current phase** based on artifact presence:
   - `scope.md` exists, non-empty → Phase 1 done
   - `contexts/` populated + `contexts/index.md` → Phase 2.1 + 2.2 done
   - `tools/` populated + `tools/index.md` → Phase 2.3 done
   - `output.md` exists → Phase 2.4 done (Phase 2 complete)
   - `reasoning.md` exists → Phase 3.1 done
   - `guardrails/` populated + `guardrails/index.md` → Phase 3.2 done (Phase 3 complete)
   - `agents.md` exists → Phase 4 done (entire design complete)
3. **Announce**: your first response should say:
   *"Based on the workspace, you've completed [...]. Next is [sub-stage X]. Continue?"*
4. **Wait for user direction**: continue forward, revise an earlier artifact,
   or pause for a question.

## Sub-stage protocol (when entering a sub-stage)

1. Call `read_prompt('<repo-relative-path>')` to load the verbatim CARE v2
   prompt for that sub-stage (path from the prompt-file listing above).
2. Conduct the interview as the loaded prompt directs.
3. Manage artifacts per the layout in the workspace section below.
4. End-of-sub-stage: emit the summary the loaded prompt specifies; ask the
   user to confirm.
5. **Wait for explicit confirmation.** Do NOT auto-advance.
6. On confirmation: do final updates (write/refine `<dir>/index.md`, remove
   `(draft)` markers and any process metadata), state explicitly that the
   sub-stage is complete, and propose the next sub-stage.

## Hard rules

- **No forward-jumping.** If the user requests a sub-stage whose
  prerequisites are missing or unconfirmed, refuse and explain what's needed
  first. Example: *"Cannot start 3.1 — Phase 2.4 (`output.md`) is not yet
  present. Want to do 2.4 first?"*
- **Backward edits ALLOWED.** The user CAN ask to revise prior-phase
  artifacts at any time. Read the existing content, apply the change, ask
  for re-confirmation. Do NOT refuse a backward edit just because the user
  has already moved past that phase.
- **Strict order within a phase**: 2.1 → 2.2 → 2.3 → 2.4; 3.1 → 3.2.
- The currently-loaded sub-stage prompt governs HOW to interview. THIS
  meta-prompt governs WHEN to load each sub-stage's prompt and WHEN to
  advance.
"""

MONO_META_PROMPT: str = ROLE_LOCK_BANNER + MONO_META_BODY + ARTIFACT_PREAMBLE


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
    agent_name: str,
    model: str,
    thinking_effort: str,
    trace: str = "tools",
) -> tuple:
    # Discover ALL phase prompts dirs + the cross-phase file listing.
    prompts_dirs, prompt_tree = discover_all_prompts(CARE_REPO_PATH)

    # Render the mono meta-prompt with the listing baked in.
    meta_prompt = MONO_META_PROMPT.format(prompt_tree=prompt_tree)

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
    # Prompts backend spans ALL phase prompts dirs. root_dir=CARE_REPO_PATH so
    # the agent passes repo-relative paths (e.g.,
    # 'phase_2_*/prompts/phase2_2_context_workspace_prompt.md'); allowed_directories
    # restricts reads to the per-phase prompts subdirs.
    prompts_backend = LocalBackend(
        root_dir=str(CARE_REPO_PATH),
        allowed_directories=[str(p) for p in prompts_dirs],
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

    return app, workspace, prompts_dirs, model


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n", 1)[0],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
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

    app, workspace, prompts_dirs, model = build_app(
        agent_name=args.agent_name,
        model=args.model,
        thinking_effort=args.thinking,
        trace=args.trace,
    )

    prompt_preview = MONO_META_PROMPT[:250].replace("\n", " ⏎ ")
    print(
        f"\nServing CARE v2 mono interviewer (all phases)\n"
        f"  agent       = {args.agent_name}\n"
        f"  workspace   = {workspace}\n"
        f"  care_repo   = {CARE_REPO_PATH}\n"
        f"  phase_dirs  = {len(prompts_dirs)} (phases: {', '.join(p.parent.name for p in prompts_dirs)})\n"
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
