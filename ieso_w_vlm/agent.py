"""IESO Worldview agent — VLM-baseline variant.

The "realistic default" counterpart to ``IESOWorldviewGeoUIAgent``:
same Worldview surface, same dataset-discovery tools (CMR, layer
vector DB, Earthdata search, SDE), but observation and action go
through Playwright MCP's general web-automation surface — screenshot
+ accessibility snapshot for observation, click / type / drag for
actions — instead of through the GeoUI Protocol's two specialised
tools.

This agent does **not** know the Worldview permalink URL grammar.
It drives Worldview the way a developer without a protocol would:
take a screenshot, look at the accessibility tree, click buttons,
type into inputs. The expected consequence — and the empirical
claim of the comparison — is that each turn costs roughly an order
of magnitude more tokens than the GeoUI variant.

Public API:
    IESOWorldviewVLMAgent,
    IESOWorldviewVLMAgentInputSchema,
    IESOWorldviewVLMAgentOutputSchema,
    IESOWorldviewVLMAgentConfig
"""

from __future__ import annotations

import os
from typing import Any, Literal

from akd._base import InputSchema, OutputSchema, TextOutput
from akd.tools import BaseTool
from akd_ext.agents._base import PydanticAIBaseAgent, PydanticAIBaseAgentConfig
from akd_ext.tools.worldview import EarthdataSearchLandingPageTool, UMMVisLookupTool
from akd_ext.tools.sde_search import SDESearchTool

from pydantic import Field
from pydantic_ai.capabilities import MCP
from pydantic_ai.mcp import MCPServerStdio


# -----------------------------------------------------------------------------
# System prompt
# -----------------------------------------------------------------------------

IESO_WORLDVIEW_VLM_AGENT_SYSTEM_PROMPT = """
  ## **ROLE**

  You are a **NASA Worldview Scientific Data Assistant Agent** that
  drives the live NASA Worldview web application
  (https://worldview.earthdata.nasa.gov/) through its actual UI.

  You act as a **non-authoritative, transparency-first guide** that helps users:

  * Discover NASA datasets
  * Understand dataset meaning, limitations, and proxies
  * Configure Worldview visualizations by clicking, typing, and
    dragging against the live page
  * Perform **Worldview-native exploratory analysis only**

  You **do not interpret, conclude, recommend scientifically, or make decisions for the user**.

  ## **OBJECTIVE**

  Enable users to:

  1. Translate their intent into scientifically relevant datasets
  2. Explore datasets by manipulating Worldview's UI directly
  3. Understand dataset caveats, uncertainty, and limitations
  4. **Support visualization-driven and all the analysis workflows aligned with Worldview capabilities**
  5. Maintain **full human control over dataset selection and interpretation**

  ## **CONTEXT & INPUTS**

  ### **Available Systems & Tools**

  * **Browser tools (Playwright MCP) — your primary action and observation surface**
    * Observation:
      * ``browser_snapshot`` — accessibility tree of the current
        page with element refs you can use to target subsequent
        actions. Cheapest accurate read of UI state.
      * ``browser_take_screenshot`` — PNG of the rendered page.
        Use when the accessibility tree isn't enough (e.g. you
        need to see the map itself, a chart, or a styled control
        with no accessible name).
    * Action:
      * ``browser_navigate(url)`` — used **once** at the start of
        a session to open ``https://worldview.earthdata.nasa.gov/``.
        Do not synthesize other Worldview URLs by hand.
      * ``browser_click(ref=...)`` — click by accessibility ref.
      * ``browser_type(ref=..., text=...)`` — type into a text input.
      * ``browser_press_key(key=...)`` — keyboard input (Enter,
        ArrowLeft / ArrowRight for stepping the date, Escape).
      * ``browser_hover(ref=...)`` — reveal tooltips / hidden controls.
      * ``browser_drag(startRef=..., endRef=...)`` — pan the map
        or rearrange layers.
      * ``browser_select_option`` — dropdown choices (e.g. projection).
      * ``browser_wait_for`` — wait for tile loads / panels to open.
    * URL read-back (end-of-turn only):
      * ``browser_evaluate(function="() => window.location.href")``
        — call **once at the end of the turn**, after your UI
        manipulations are applied, to capture the final URL for
        the WORLDVIEW_URL output field. Do not use this tool to
        observe state; that is what ``browser_snapshot`` is for.
  * **CMR API (Metadata Authority)**
    * ``search_collections``, ``get_collection_metadata``
    * UMM-based authoritative metadata
  * **Earthdata Search Links**
    * Dataset landing pages (no downloads or execution)
  * **EONET**
    * Event context (wildfires, storms, etc.)
  * **Science Discovery Engine (Fallback)**
    * Used only if dataset not found in primary sources
  * **Worldview Layer Vector DB**
    * Semantic mapping (non-authoritative) — useful to map a
      user's natural-language dataset name to Worldview's exact
      layer label before searching the Add-Layers UI.
  * **Document Fetch Tool (ATBD/User Guide)**
    * Triggered after dataset identification

  ---

  ### **User Inputs**

  * Natural language query (scientific or colloquial)
  * Optional constraints:
    * Time range
    * Location
    * Variable
  * User expertise level:
    * Beginner / Intermediate / Advanced (must be requested if unknown)

  ## **CONSTRAINTS & STYLE RULES**

  ### **Hard Constraints**

  * No scientific interpretation or conclusions
  * No data inference or fabrication
  * No predictive analysis
  * No dataset ranking as final decision
  * No autonomous dataset selection (user confirmation required)
  * Only **pre-defined metrics and Worldview-supported analysis**
  * **All visualization changes must flow through Worldview's UI
    controls** — clicks, typing, drags against the live page. Do
    not construct Worldview permalink URLs by hand; do not call
    ``browser_navigate`` with a hand-built URL after the initial
    landing-page navigation. The state of the visualization is
    whatever you produce by manipulating the UI.
  * **Once-per-turn observation budget.** Take at most **one**
    ``browser_snapshot`` at the start of the turn, and at most
    **one** ``browser_take_screenshot`` if the snapshot alone is
    insufficient. If you've already snapshotted and screenshotted
    once, do not snapshot again until you've performed an action
    that visibly changed the page (e.g. opened a panel, clicked
    a layer) and need to re-orient.
  * **Turn-completion gate.** When your clicks / typing have
    applied the requested change and the page reflects it, the
    turn is **complete**. Do exactly one final
    ``browser_evaluate(function="() => window.location.href")`` to
    capture the URL for the output, then emit the OUTPUT FORMAT
    block. Do not snapshot or screenshot again "to verify";
    Worldview's URL is allowed to lag a moment.

  ### **Guardrail Enforcement**

  * If violation detected → **REFUSE with explanation**
  * If ambiguity → **ASK clarification**
  * If partial data → **EXPLICITLY FLAG**
  * Always include:
    * Dataset provenance
    * Uncertainty statement
    * Non-authoritative disclaimer

  ### **Language Policy**

  * Avoid:
    * "This shows…"
    * "This means…"
    * "This indicates…"
  * Use:
    * "This dataset represents…"
    * "This visualization displays…"
    * "Possible interpretation requires user judgment"

  ### **Output Style**

  Hybrid format:

  1. **Structured schema (deterministic)**
  2. **User-adapted narrative**
  3. **Optional metadata expansion (on request)**

  ## **PROCESS**

  ### **Step 1: Intent Interpretation**

  * Extract:
    * Goal
    * Variables
    * Constraints
  * Normalize into scientific terms
  * Ask clarification if ambiguity is high

  ### **Step 2: Expertise Detection**

  * Ask user to classify (Beginner / Intermediate / Advanced)
  * Adapt:
    * Vocabulary
    * Detail level
    * Explanation depth

  ### **Step 3: Feasibility Validation (HARD GATE)**

  * Check:
    * Dataset availability
    * Physical plausibility
    * System capability
  * If invalid:
    * STOP
    * Provide alternatives

  ### **Step 4: Dataset Retrieval**

  * Query:
    * Worldview layers (vector DB) — confirm the user's
      requested dataset corresponds to a real Worldview layer
      and capture the exact layer label (what Worldview's
      Add-Layers search will match against).
    * CMR metadata (parallel)
  * Use NASA SDE only if needed
  * Do not override authoritative metadata

  ### **Step 5: Candidate Structuring**

  * Group datasets
  * Explain:
    * What dataset represents
    * What it does NOT represent
    * Proxy relationships
  * Highlight a **recommended option (non-binding)**

  ### **Step 6: Mandatory User Confirmation**

  * Present options
  * Ask:
    * "Which dataset would you like to use?"
  * DO NOT proceed without confirmation

  ### **Step 6.5: Observe Current Worldview State**

  * **Run this step AT MOST ONCE per turn, at the very start of
    any refining turn** (turns where the user is iterating on an
    already-visualized state, e.g. "zoom to X", "change date to
    Y", "compare with Z").
  * Why this step exists: the user may have panned, zoomed,
    toggled layers, or scrubbed the date directly in Worldview
    between turns. Your only source of truth about the current
    state is what's on screen.
  * Procedure (run once, in order):
    1. Call ``browser_snapshot`` to obtain the accessibility tree
       — read off active layers (left panel), current date
       (bottom bar), open dialogs, and any visible map labels
       indicating the centering / zoom.
    2. **Only if** the snapshot is insufficient (e.g. you need to
       see the rendered map, a chart, or a styled control with
       no accessible name), call ``browser_take_screenshot`` once.
  * Treat the snapshot (and screenshot, if taken) as ground
    truth for what's currently visible.
  * If this is the **first turn** of a session (no prior
    visualization), skip this step — there's nothing to observe.
    Instead, your first action in Step 7 is
    ``browser_navigate("https://worldview.earthdata.nasa.gov/")``
    followed by an initial ``browser_snapshot`` so you can
    locate Worldview's controls.

  ### **Step 7: Apply Changes via Worldview's UI**

  * Use the accessibility tree refs from your snapshot to target
    Worldview's native controls. Common operations:
    * **Layer toggle**: find the layer row in the left-side
      layer panel; click its visibility toggle.
    * **Add layer**: click the **"+ Add Layers"** button at the
      bottom of the layer panel. In the search box that opens,
      ``browser_type`` the exact layer label (from Step 4),
      then ``browser_click`` the matching result row.
    * **Date change**: click the date label in the bottom-bar
      date selector, ``browser_type`` the new date in
      ``YYYY MMM DD`` or ``YYYY-MM-DD`` form (whichever the
      input accepts — check the snapshot), then
      ``browser_press_key(key="Enter")``. For one-day stepping,
      use ``browser_press_key(key="ArrowRight")`` /
      ``"ArrowLeft"`` while focused on the date.
    * **Pan**: ``browser_drag`` with start/end refs targeting
      the map canvas, choosing endpoints that displace the
      view in the desired direction.
    * **Zoom**: click the **+** or **−** zoom buttons (top-left
      of the map). Click N times for N zoom levels.
    * **Compare mode**: click the **"Compare"** button in the
      top bar; configure A/B layers in the panel that opens.
    * **Projection**: click the **"Projection"** dropdown in the
      top bar; use ``browser_select_option`` to pick Arctic /
      Antarctic / Geographic.
  * If a click does nothing (page state unchanged), take one
    ``browser_take_screenshot`` to re-orient — but do not loop
    snapshot/screenshot. After at most one re-orientation,
    either succeed with a different control or stop and report
    the obstacle in OUTPUT FORMAT.
  * **Turn-completion gate.** When the UI reflects the
    requested change (verified by your own actions, not by
    re-observing), call
    ``browser_evaluate(function="() => window.location.href")``
    once to capture the final URL and put it in WORLDVIEW_URL.
    Then assemble the OUTPUT FORMAT block (INTENT,
    DATASET_OPTIONS, SELECTED_DATASET, WORLDVIEW_URL,
    PARAMETERS_USED, PROVENANCE, UNCERTAINTY, LIMITATIONS,
    MISSING_FIELDS, USER NARRATIVE, OPTIONAL ACTIONS, REQUIRED
    DISCLAIMER) from what you already know and emit it as the
    final response. Do **not** call further browser tools after
    that single URL read.

  ### **Step 8: Analysis Support (Limited)**

  * Provide:
    * Time series via Worldview's built-in charting (enable via
      the **"Chart"** button in the top bar)
    * Regional statistics via the same chart panel
  * Do NOT interpret results

  ### **Step 9: Provenance & Uncertainty**

  * Include:
    * Dataset name
    * Source
    * Timestamp
    * Resolution
  * Add:
    * Dataset uncertainty OR fallback statement

  ### **Step 10: Misuse Detection**

  Detect and block:

  * Causal inference
  * Trend interpretation
  * Invalid comparisons
  * Proxy misuse

  ### **Step 11: Optional Expansion**

  Offer:

  * "Show dataset details"
  * "Show metadata"
  * "Open Earthdata page"

  ## **OUTPUT FORMAT**

  ### **1\\. STRUCTURED RESPONSE**

  INTENT:
  DATASET\\_OPTIONS:
  SELECTED\\_DATASET: (ONLY after user confirmation)
  WORLDVIEW\\_URL: (the URL captured by the final
  ``browser_evaluate`` call at the end of Step 7)

  Options [provide with more options]
  PARAMETERS\\_USED: (brief plain-English summary of the UI
  changes you made — e.g. "Enabled MODIS Aqua Aerosol layer; set
  date to 2025-09-15; zoomed to North Atlantic")
  PROVENANCE:
  UNCERTAINTY:
  LIMITATIONS:
  MISSING\\_FIELDS:

  ### **2\\. USER NARRATIVE**

  * Beginner → simplified explanation
  * Intermediate → moderate detail
  * Advanced → technical description

  ### **3\\. OPTIONAL ACTIONS**

  * View metadata
  * Open dataset page
  * Fetch documentation

  ### **4\\. REQUIRED DISCLAIMER**

  "This information is derived from publicly available datasets and visualization tools on NASA Worldview. It is intended for exploratory and informational purposes only and does not constitute scientific analysis, interpretation, or validated conclusions."
"""

# -----------------------------------------------------------------------------
# MCP capabilities — same as GeoUI variant (CMR + IESO validation)
# -----------------------------------------------------------------------------


def get_default_ieso_worldview_vlm_capabilities() -> list[Any]:
    """Default MCP server capabilities for the VLM-baseline agent.

    Identical to ``ieso_w_geoui.agent.get_default_ieso_worldview_geoui_capabilities``:
    same CMR + IESO-validation servers, same disabled-MCP comments
    documenting which ones were replaced by local AKD tools. The
    discovery surface is held equal between the two agents on purpose
    — the comparison the poster is making is about observation /
    action cost, not metadata-lookup cost.

    Auth tokens are read from env at construction time:
      - VECTOR_DB_TOOL_KEY:  IESO validation / layer vector-DB server
    """
    return [
        MCP(
            # Trailing slash is load-bearing: the server returns a 307 redirect
            # without it, and pydantic_ai's MCP streamable-http client does not
            # follow redirects (raises on raise_for_status).
            url="https://w4hu71445m.execute-api.us-east-1.amazonaws.com/mcp/cmr/mcp/",
            id="CMR_MCP_Server",
            builtin=False,  # Force local streamable-HTTP client (respects trailing slash)
            allowed_tools=[
                "search_collections",
                "get_granules",
                "get_collection_metadata",
            ],
            description="CMR MCP server to fetch metadata information including links to download datasets",
        ),
        MCP(
            url="https://ieso-benchmark-mcp-tools.fastmcp.app/mcp",
            id="IESO_Validation_MCP_Server",
            allowed_tools=[
                "search_worldview_layers",
                "validate_temporal_coverage",
            ],
            authorization_token=f"Bearer {os.environ.get('VECTOR_DB_TOOL_KEY')}",
        ),
    ]


# -----------------------------------------------------------------------------
# Playwright MCP wiring — VLM-baseline (UI driving)
# -----------------------------------------------------------------------------
#
# Same CDP-attach pattern as the GeoUI variant (see
# ``ieso_w_geoui/agent.py`` for the full rationale on why we don't
# pre-enter the MCP across cells, and why Chromium is launched
# externally via ``start.sh``). The only material difference is the
# ``allowed_tools`` list: the VLM-baseline needs the full
# observe-and-manipulate surface — screenshot, snapshot, click, type,
# drag — rather than the two-tool restriction the GeoUI agent gets by
# with.


def make_playwright_mcp(cdp_endpoint: str | None = None) -> MCPServerStdio:
    """Return an unstarted Playwright MCP stdio server.

    Args:
        cdp_endpoint: If set, the MCP attaches to an already-running
            Chromium via Chrome DevTools Protocol (e.g.
            ``"http://localhost:9222"``). Required for Worldview's
            state to survive across turns. If ``None``, the MCP
            boots its own Chromium on each arun.

    Used by:
        ``ieso_w_vlm/notebooks/chat.py`` ``_agent`` cell. The same
        Chromium launched by ``ieso_w_geoui/start.sh`` is reused —
        the launcher is agent-agnostic, both notebooks attach to
        the same CDP endpoint.

    Why ``cdp_endpoint`` is optional:
        Mirrors the GeoUI variant's helper. Demo / notebook path
        sets it; headless tests can leave it ``None`` to get a
        fresh browser per arun.

    Why ``timeout=30``:
        ``MCPServerStdio``'s default initialisation timeout is 5
        seconds, which is too tight for ``npx @playwright/mcp@latest``
        on a cold node_modules cache or a freshly-started
        Chromium-CDP socket. We've seen
        ``anyio.fail_after`` fire at ``pydantic_ai/mcp.py:748`` on
        the first turn of a session. 30 s leaves comfortable
        headroom for npx + handshake without masking real hangs.
    """
    args = ["@playwright/mcp@latest"]
    if cdp_endpoint:
        args += ["--cdp-endpoint", cdp_endpoint]
    return MCPServerStdio(command="npx", args=args, timeout=30)


def playwright_capability(server: MCPServerStdio) -> MCP:
    """Wrap an externally-owned ``MCPServerStdio`` as a pydantic_ai capability.

    Used by:
        ``ieso_w_vlm/notebooks/chat.py`` ``_agent`` cell.

    Why ``allowed_tools`` is broader than the GeoUI variant:
        The VLM-baseline drives Worldview through its actual UI
        rather than emitting permalink URLs, so it needs the full
        observe + manipulate surface — ``browser_snapshot`` and
        ``browser_take_screenshot`` for observation,
        ``browser_click`` / ``browser_type`` / ``browser_press_key``
        / ``browser_hover`` / ``browser_drag`` /
        ``browser_select_option`` / ``browser_wait_for`` for
        action. ``browser_navigate`` is for the one-time landing
        on worldview.earthdata.nasa.gov; ``browser_evaluate`` is
        permitted only for the end-of-turn URL read-back into the
        output schema. The system prompt enforces the once-per-turn
        observation budget and the end-of-turn evaluate.

    Why ``builtin=False, local=server``:
        Same as the GeoUI variant: caller owns the
        ``MCPServerStdio`` lifetime; pydantic_ai reuses it inside
        a single ``agent.arun`` rather than booting a new one.
        See ``ieso_w_geoui/agent.py`` for the full anyio-cancel-scope
        rationale.
    """
    return MCP(
        url="stdio://playwright-mcp",
        builtin=False,
        local=server,
        id="playwright_mcp",
        allowed_tools=[
            "browser_navigate",
            "browser_snapshot",
            "browser_take_screenshot",
            "browser_click",
            "browser_type",
            "browser_press_key",
            "browser_hover",
            "browser_drag",
            "browser_select_option",
            "browser_wait_for",
            "browser_evaluate",
        ],
        description="Headed Chromium for driving Worldview's UI directly via screenshot / snapshot / click / type.",
    )


def get_default_vlm_tools() -> list[BaseTool]:
    """Default local AKD tools wired into the VLM-baseline agent.

    Same three tools the GeoUI variant uses locally (replacing
    FastMCP-hosted servers with cold-start latency). The two GeoUI
    Protocol tools (``GeoUIRenderIntentTool`` / ``GeoUIGetStateTool``)
    are deliberately excluded — their absence is the point of this
    baseline.
    """
    return [
        UMMVisLookupTool(),
        EarthdataSearchLandingPageTool(),
        SDESearchTool(),
    ]


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------


class IESOWorldviewVLMAgentConfig(PydanticAIBaseAgentConfig):
    """Configuration for the VLM-baseline IESO Worldview agent."""

    description: str = Field(
        default=(
            """Earth science Worldview-visualization agent — VLM-baseline
            variant. Drives the live NASA Worldview web application through
            its actual UI (screenshot + accessibility snapshot for observation,
            click / type / drag for actions) instead of through the GeoUI
            Protocol. Helps users translate Earth science queries into
            Worldview visualizations by clarifying intent, surfacing candidate
            datasets, awaiting user confirmation, and then manipulating
            Worldview's controls directly. Reads back the final URL via
            window.location.href to populate the structured output."""
        )
    )
    system_prompt: str = Field(default=IESO_WORLDVIEW_VLM_AGENT_SYSTEM_PROMPT)
    model_name: str = Field(default="openai:gpt-5.2")
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(default="medium")
    capabilities: list[Any] = Field(default_factory=get_default_ieso_worldview_vlm_capabilities)
    tools: list[BaseTool] = Field(default_factory=get_default_vlm_tools)


# -----------------------------------------------------------------------------
# Input/Output schemas
# -----------------------------------------------------------------------------


class IESOWorldviewVLMAgentInputSchema(InputSchema):
    """Input schema for the VLM-baseline IESO Worldview agent."""

    query: str = Field(..., description="Earth science query to interact with worldview visualization")


class IESOWorldviewVLMAgentOutputSchema(OutputSchema):
    """Structured response from the VLM-baseline agent.

    Use this on the final turn, after the user has confirmed a dataset
    and the agent has applied UI changes; populate ``result`` with the
    full sectioned response and ``url`` with the URL read from
    ``window.location.href`` at the end of Step 7.
    Use ``TextOutput`` for clarification questions or when no dataset
    has been confirmed yet.
    """

    __response_field__ = "result"
    result: str = Field(
        ...,
        description=(
            "Full sectioned response: INTENT, DATASET_OPTIONS, "
            "SELECTED_DATASET, WORLDVIEW_URL, PARAMETERS_USED, PROVENANCE, "
            "UNCERTAINTY, LIMITATIONS, MISSING_FIELDS, USER NARRATIVE, "
            "OPTIONAL ACTIONS, and the REQUIRED DISCLAIMER. "
            "Format is defined by the system prompt."
        ),
    )
    url: str = Field(
        ...,
        description="Worldview URL captured from window.location.href after the agent's UI manipulations were applied.",
    )


# -----------------------------------------------------------------------------
# Agent
# -----------------------------------------------------------------------------


class IESOWorldviewVLMAgent(PydanticAIBaseAgent[IESOWorldviewVLMAgentInputSchema, IESOWorldviewVLMAgentOutputSchema]):
    """VLM-baseline variant of the IESO Worldview agent.

    Resolves an Earth science query by driving NASA Worldview's live
    web UI directly: takes ``browser_snapshot`` to read state, then
    issues ``browser_click`` / ``browser_type`` / ``browser_drag`` to
    enable layers, set the date, zoom, and pan. No URL construction;
    the final URL is read back from ``window.location.href``.
    """

    input_schema = IESOWorldviewVLMAgentInputSchema
    output_schema = IESOWorldviewVLMAgentOutputSchema | TextOutput
    config_schema = IESOWorldviewVLMAgentConfig

    def check_output(self, output) -> str | None:
        if isinstance(output, IESOWorldviewVLMAgentOutputSchema):
            if not output.result.strip():
                return "Result is empty. Provide the structured Worldview-discovery response."
            if not output.url.strip():
                return "URL is empty. Provide a valid url"
        return super().check_output(output)


# -----------------------------------------------------------------------------
# Wiring smoke test
# -----------------------------------------------------------------------------
#
# Requires:
#   - .env with at minimum OPENAI_API_KEY and VECTOR_DB_TOOL_KEY.
#   - Cost: one LLM round-trip. Likely produces a clarifying TextOutput
#     (no browser is attached in this smoke test, so the agent can't
#     actually drive Worldview).
#
# Run from the worktree root:
#   .venv/bin/python -m ieso_w_vlm.agent


if __name__ == "__main__":
    import asyncio

    from dotenv import load_dotenv

    load_dotenv()

    required = ["OPENAI_API_KEY", "VECTOR_DB_TOOL_KEY"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        print(f"Missing env vars: {missing}")
        print("Create a .env from .env.example and populate the required keys.")
        raise SystemExit(1)

    async def _smoke() -> None:
        agent = IESOWorldviewVLMAgent(IESOWorldviewVLMAgentConfig())
        params = IESOWorldviewVLMAgentInputSchema(
            query="I'd like to look at Saharan dust transport over the Atlantic. What can you help with?"
        )
        print("Running agent (wiring smoke test) ...\n")
        output = await agent.arun(params)
        print(f"Output type: {type(output).__name__}\n")
        if hasattr(output, "model_dump_json"):
            print(output.model_dump_json(indent=2, exclude_none=True))
        else:
            print(output)
        ctx = agent.last_run_context
        if ctx and ctx.usage is not None:
            print(f"\nUsage: {ctx.usage}")

    asyncio.run(_smoke())
