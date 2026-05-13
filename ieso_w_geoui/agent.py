"""IESO Worldview agent — GeoUI Protocol variant.

A drop-in alternative to ``akd_ext.agents.ieso_worldview.IESOWorldviewAgent``
that emits and consumes ``GeoIntent`` instead of speaking the Worldview
permalink URL grammar directly. The Worldview-specific permalink MCP
tool is replaced with two local tools: ``geoui_render_intent`` (intent →
URL) and ``geoui_get_state`` (URL → intent). All other MCP capabilities
(CMR, layer lookup, Earthdata search, vector DB, SDE fallback) are kept
unchanged.

Public API:
    IESOWorldviewGeoUIAgent,
    IESOWorldviewGeoUIAgentInputSchema,
    IESOWorldviewGeoUIAgentOutputSchema,
    IESOWorldviewGeoUIAgentConfig
"""

from __future__ import annotations

import os
from typing import Any, Literal

from akd._base import InputSchema, OutputSchema, TextOutput
from akd.tools import BaseTool
from akd_ext.agents._base import PydanticAIBaseAgent, PydanticAIBaseAgentConfig
from akd_ext.tools.worldview import (
    EarthdataSearchLandingPageTool,
)
from pydantic import Field
from pydantic_ai.capabilities import MCP
from pydantic_ai.mcp import MCPServerStdio

from ieso_w_geoui.tools import GeoUIGetStateTool, GeoUIRenderIntentTool

# -----------------------------------------------------------------------------
# System prompt
# -----------------------------------------------------------------------------

IESO_WORLDVIEW_GEOUI_AGENT_SYSTEM_PROMPT = """
  ## **ROLE**

  You are a **NASA Worldview Scientific Data Assistant Agent** operating
  over the **GeoUI Protocol**.

  You act as a **non-authoritative, transparency-first guide** that helps users:

  * Discover NASA datasets
  * Understand dataset meaning, limitations, and proxies
  * Configure and emit Worldview visualizations through a structured
    application-state schema (``GeoIntent``)
  * Perform **Worldview-native exploratory analysis only**

  You **do not interpret, conclude, recommend scientifically, or make decisions for the user**.

  ## **OBJECTIVE**

  Enable users to:

  1. Translate their intent into scientifically relevant datasets
  2. Explore datasets via **GeoIntent-rendered Worldview deep links**
  3. Understand dataset caveats, uncertainty, and limitations
  4. **Support visualization-driven and all the analysis workflows aligned with Worldview capabilities**
  5. Maintain **full human control over dataset selection and interpretation**

  ## **CONTEXT & INPUTS**

  ### **Available Systems & Tools**

  * **GeoUI Protocol tools (Primary visualization interface)**
    * ``geoui_render_intent(intent)`` — render a ``GeoIntent`` as a Worldview permalink URL
    * ``geoui_get_state(url)`` — read the current application state from a Worldview URL
  * **Browser tools (Playwright MCP) — used to open the visualization and observe live state**
    * ``browser_navigate(url)`` — open a URL in the user-facing Chromium window
    * ``browser_evaluate(function)`` — run a JS snippet in the open page; primary use is
      ``() => window.location.href`` to read the current Worldview URL after the user may
      have interacted with the map
    * Other Playwright tools may be exposed; do not use them unless explicitly asked.
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
    * Semantic mapping (non-authoritative)
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
  * **All visualization changes must flow through ``geoui_render_intent``**;
    do not construct Worldview URLs by hand.

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
    * Worldview layers
    * CMR metadata (Should be parallel)
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

  ### **Step 6.5: Observe Current State (when iterating)**

  * On every turn after the first, read the **live** Worldview URL from
    the browser — do NOT trust your memory of the last URL you produced.
    The user may have panned, zoomed, toggled layers, or scrubbed the
    date directly in the map, and those changes only show up in the
    browser's address bar.
  * Procedure:
    1. Call ``browser_evaluate(function="() => window.location.href")``
       to get the current URL.
    2. Call ``geoui_get_state(url=...)`` on that URL to obtain the
       current ``GeoIntent``.
  * Treat the returned GeoIntent as your starting point for refinement.
  * Carry forward fields the user did not ask to change; modify only
    the fields implicated by the latest user request.
  * Skip discovery (steps 4–6) for fields already in the state.

  ### **Step 7: Visualization Construction (via GeoUI Protocol)**

  * Build a **``GeoIntent``** describing the desired application state.
  * Call ``geoui_render_intent(intent=...)`` to obtain the Worldview
    permalink URL.
  * **Immediately** call ``browser_navigate(url=...)`` with that URL so
    the visualization opens in the user-facing Chromium window. The
    user is watching that window — do not just hand back a URL string
    and stop. Navigation is part of finishing the turn.
  * GeoIntent core fields:
    * ``viewport``: ``{ "bbox": [west, south, east, north], "crs": "EPSG:4326" }``
      (``crs`` defaults to ``"EPSG:4326"``; use ``"EPSG:3413"`` for arctic
      or ``"EPSG:3031"`` for antarctic if Worldview supports the layer there.)
    * ``time``: ``{ "instant": "YYYY-MM-DD" }`` (sub-daily ISO datetimes also accepted).
    * ``layers``: list of LayerRef objects, each with:
      * ``id`` (required, e.g. ``"MODIS_Aqua_Aerosol"``)
      * ``visible`` (default true), ``opacity`` (0.0–1.0, optional)
  * For extensions, declare their URIs in ``geoui_extensions`` AND
    populate the namespaced fields:
    * ``https://geoui.org/ext/compare/v1.0.0`` (A/B comparison):
      * ``compare:layers`` (required: B-side layer stack)
      * ``compare:time`` (optional; defaults to root time)
      * ``compare:mode`` (``"swipe"`` / ``"spy"`` / ``"opacity"``, default ``"swipe"``)
      * ``compare:value`` (0–100, default 50)
      * ``compare:active_side`` (``"A"`` / ``"B"``, default ``"A"``)
    * ``https://geoui.org/ext/chart/v1.0.0`` (time-series statistics):
      * ``chart:layer`` (required, single layer id)
      * ``chart:area`` (optional, [x1, y1, x2, y2] AOI)
      * ``chart:time`` (optional, ``{ "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" }``)
      * ``chart:autoload`` (bool, default false)
    * ``https://geoui.org/ext/raster-styling/v1.0.0`` (per-layer styling — fields go on each LayerRef object):
      * ``raster-styling:palettes`` (list of palette ids)
      * ``raster-styling:style`` (style id)
      * ``raster-styling:min``, ``raster-styling:max``
      * ``raster-styling:squash`` (bool, squashes palette to min/max range)

  ### **Step 8: Analysis Support (Limited)**

  * Provide:
    * Time series via the chart extension
    * Regional statistics via the chart extension
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
  WORLDVIEW\\_URL: (the URL returned from ``geoui_render_intent``)

  Options [provide with more options]
  PARAMETERS\\_USED: (summary of the GeoIntent you constructed — list
  the core fields you set and any extensions you declared)
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
# MCP capabilities (Worldview permalink MCP removed; everything else kept)
# -----------------------------------------------------------------------------


def get_default_ieso_worldview_geoui_capabilities() -> list[Any]:
    """Default MCP server capabilities for the GeoUI-variant agent.

    Same as :func:`akd_ext.agents.ieso_worldview.get_default_ieso_worldview_capabilities`
    minus the ``worldview_permalink_tool`` MCP (replaced by the local
    ``geoui_render_intent`` tool) and minus the three IESO/SDE MCPs
    whose tools we now run locally to sidestep FastMCP Cloud cold-start
    DNS hiccups:

      - ``umm_vis_lookup_tool``               → ``UMMVisLookupTool`` (local)
      - ``earthdata_search_landing_page_tool``→ ``EarthdataSearchLandingPageTool`` (local)
      - ``sde_search_tool``                   → ``SDESearchTool`` (local)

    The two MCPs that remain have no local equivalent in this codebase:

      - ``CMR_MCP_Server`` (AWS-hosted; no cold-start risk).
      - ``IESO_Validation_MCP_Server`` (FastMCP-hosted; may cold-start —
        we accept that until a local version exists).

    Auth tokens are read from env at construction time:
      - IESO_MCP_KEY:        currently unused; was for the disabled MCPs
      - VECTOR_DB_TOOL_KEY:  IESO validation / layer vector-DB server
      - SDE_MCP_KEY:         currently unused; was for the disabled SDE MCP
    """
    # vector_db_tool_key = os.environ.get("VECTOR_DB_TOOL_KEY")

    return [
        # ── DISABLED: replaced by local UMMVisLookupTool ──────────────────
        # MCP(
        #     url="https://sudden-gold-carp-features-tool-cmr-uat.fastmcp.app/mcp",
        #     id="ieso-worldview-tool-umm_vis_lookup_tool",
        #     allowed_tools=["umm_vis_lookup_tool"],
        #     authorization_token=os.environ.get("IESO_MCP_KEY"),
        #     description="Layerid Visualization lookup for CMR Concept id",
        # ),
        # ── DISABLED: replaced by local EarthdataSearchLandingPageTool ────
        # MCP(
        #     url="https://sudden-gold-carp-features-tools-earthdata-search-da3be0.fastmcp.app/mcp",
        #     id="ieso-worldview-tool-earthdata_search_landing_page_tool",
        #     allowed_tools=["earthdata_search_landing_page_tool"],
        #     authorization_token=os.environ.get("IESO_MCP_KEY"),
        #     description="Earthdata search landing page for concept id",
        # ),
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
        # ── Currently authorization issue ────
        # MCP(
        #     url="https://ieso-benchmark-mcp-tools.fastmcp.app/mcp",
        #     id="IESO_Validation_MCP_Server",
        #     allowed_tools=[
        #         "search_worldview_layers",
        #         "validate_temporal_coverage",
        #     ],
        #     authorization_token=vector_db_tool_key,
        # ),
        # ── DISABLED: replaced by local SDESearchTool ─────────────────────
        # MCP(
        #     url="https://brainy-lime-pheasant.fastmcp.app/mcp",
        #     id="sde_mcp_tool",
        #     allowed_tools=["sde_search_tool"],
        #     authorization_token=os.environ.get("SDE_MCP_KEY"),
        # ),
    ]


# -----------------------------------------------------------------------------
# Playwright MCP wiring (CDP-attach: external Chromium spans turns)
# -----------------------------------------------------------------------------
#
# The browser sits behind an MCP server speaking stdio. We need Chromium
# state (URL, pan/zoom, layer toggles) to survive across ``agent.arun``
# calls so the user can interact with the map between turns. Earlier we
# tried pre-entering the stdio server in an async marimo cell so the
# subprocess would span every arun — pydantic_ai's reference-counted
# ``MCPServer.__aenter__`` made that plausible on paper, but it doesn't
# survive marimo's task model: ``MCPServerStdio`` enters an ``anyio``
# task group internally, anyio insists the cancel scope exits on the
# same asyncio task that entered it, and marimo's per-cell tasks die
# the moment their cell returns. End result was
# ``RuntimeError: Attempted to exit cancel scope in a different task
# than it was entered in`` and the chat handler disappearing from the
# marimo function registry.
#
# Fix: don't try to persist the MCP at all. Keep Chromium alive
# *externally* (the user launches it with ``--remote-debugging-port``),
# create the Playwright MCP fresh per arun, and have it attach via
# ``--cdp-endpoint``. The MCP's anyio scope is then fully contained in
# one arun task; Chromium state lives outside Python entirely.
#
# Usage from the notebook:
#
#     pw = make_playwright_mcp(cdp_endpoint="http://localhost:9222")
#     agent = IESOWorldviewGeoUIAgent(
#         IESOWorldviewGeoUIAgentConfig(
#             capabilities=[
#                 *get_default_ieso_worldview_geoui_capabilities(),
#                 playwright_capability(pw),
#             ],
#         ),
#     )
#
# Before opening the notebook the user launches Chromium with remote
# debugging enabled, for example:
#
#     /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
#         --remote-debugging-port=9222 \
#         --user-data-dir=/tmp/worldview-chromium
#
# Leaving ``cdp_endpoint=None`` falls back to vanilla per-turn
# Chromium boot (no state persistence) — useful for headless tests but
# not the demo path.


def make_playwright_mcp(cdp_endpoint: str | None = None) -> MCPServerStdio:
    """Return an unstarted Playwright MCP stdio server.

    Args:
        cdp_endpoint: If set, the MCP attaches to an already-running
            Chromium via Chrome DevTools Protocol (e.g.
            ``"http://localhost:9222"``). Required for state to survive
            across turns. If ``None``, the MCP boots its own Chromium
            on each arun (first such boot downloads ~150 MB).
    """
    args = ["@playwright/mcp@latest"]
    if cdp_endpoint:
        args += ["--cdp-endpoint", cdp_endpoint]
    return MCPServerStdio(command="npx", args=args)


def playwright_capability(server: MCPServerStdio) -> MCP:
    """Wrap an externally-owned ``MCPServerStdio`` as a pydantic_ai capability.

    ``builtin=False`` forces the local toolset path; ``local=server`` reuses
    the caller's already-instantiated (and ideally already-entered) MCP
    server instead of building a fresh one. ``allowed_tools`` restricts the
    ~20-tool Playwright surface to the two the agent should reach for —
    everything else (snapshot, click, evaluate-on-element, etc.) is filtered
    out so the model doesn't wander.
    """
    return MCP(
        url="stdio://playwright-mcp",  # placeholder; only used for the cap's id slug
        builtin=False,
        local=server,
        id="playwright_mcp",
        allowed_tools=["browser_navigate", "browser_evaluate"],
        description="Headed Chromium for opening Worldview URLs and reading back live state.",
    )


def get_default_geoui_tools() -> list[BaseTool]:
    """Default local AKD tools wired into the GeoUI-variant agent.

    Includes the two GeoUI Protocol tools plus three IESO/SDE tools that
    we previously routed through FastMCP-hosted servers. The local
    versions are functionally equivalent and avoid the cold-start DNS
    issue (see ``get_default_ieso_worldview_geoui_capabilities``).
    """
    return [
        GeoUIRenderIntentTool(),
        GeoUIGetStateTool(),
        # UMMVisLookupTool(), # currently uat server that ummvis depdends upon is broken
        EarthdataSearchLandingPageTool(),
        # SDESearchTool(), # currently uat server that ummvis depdends upon is broken
    ]


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------


class IESOWorldviewGeoUIAgentConfig(PydanticAIBaseAgentConfig):
    """Configuration for the GeoUI-variant IESO Worldview agent."""

    description: str = Field(
        default=(
            """Earth science Worldview-visualization agent operating over the
            GeoUI Protocol. Helps users translate Earth science queries into
            NASA Worldview permalinks by clarifying intent, surfacing candidate
            datasets, awaiting user confirmation, and producing a reproducible
            visualization URL through a declarative GeoIntent rendered by the
            geoui_render_intent tool. Reads the current visualization state via
            geoui_get_state to support iterative refinement. Outputs are
            delivered via a structured schema and interactive chat for
            clarification, dataset selection, approval gates, and disclaimers."""
        )
    )
    system_prompt: str = Field(default=IESO_WORLDVIEW_GEOUI_AGENT_SYSTEM_PROMPT)
    model_name: str = Field(default="openai:gpt-5.2")
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(default="medium")
    capabilities: list[Any] = Field(default_factory=get_default_ieso_worldview_geoui_capabilities)
    tools: list[BaseTool] = Field(default_factory=get_default_geoui_tools)


# -----------------------------------------------------------------------------
# Input/Output schemas
# -----------------------------------------------------------------------------


class IESOWorldviewGeoUIAgentInputSchema(InputSchema):
    """Input schema for the GeoUI-variant IESO Worldview agent."""

    query: str = Field(..., description="Earth science query to interact with worldview visualization")


class IESOWorldviewGeoUIAgentOutputSchema(OutputSchema):
    """Structured response from the GeoUI-variant agent.

    Use this on the final turn, after the user has confirmed a dataset;
    populate ``result`` with the full sectioned response and ``url`` with
    the Worldview permalink returned by ``geoui_render_intent``.
    Use ``TextOutput`` for clarification questions or when no dataset has
    been confirmed yet.
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
        description="Worldview permalink that resolves the science query, as returned by geoui_render_intent.",
    )


# -----------------------------------------------------------------------------
# Agent
# -----------------------------------------------------------------------------


class IESOWorldviewGeoUIAgent(
    PydanticAIBaseAgent[IESOWorldviewGeoUIAgentInputSchema, IESOWorldviewGeoUIAgentOutputSchema]
):
    """GeoUI-variant of the IESO Worldview agent.

    Resolves an Earth science query into a NASA Worldview permalink via
    a declarative GeoIntent passed through ``geoui_render_intent``. Reads
    the current visualization state via ``geoui_get_state`` to support
    iterative refinement.
    """

    input_schema = IESOWorldviewGeoUIAgentInputSchema
    output_schema = IESOWorldviewGeoUIAgentOutputSchema | TextOutput
    config_schema = IESOWorldviewGeoUIAgentConfig

    def check_output(self, output) -> str | None:
        if isinstance(output, IESOWorldviewGeoUIAgentOutputSchema):
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
#   - .env populated from .env.example (or shell env) with at minimum
#     OPENAI_API_KEY and VECTOR_DB_TOOL_KEY. IESO_MCP_KEY and SDE_MCP_KEY
#     are no longer needed by this agent (their MCPs were replaced by
#     local tool variants — see get_default_ieso_worldview_geoui_capabilities).
#   - Cost: one LLM round-trip. The query is intentionally light; the
#     agent may respond with a clarifying TextOutput rather than a
#     rendered URL — that's a successful wiring test either way.
#
# Run from the worktree root:
#   .venv/bin/python -m ieso_w_geoui.agent


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
        agent = IESOWorldviewGeoUIAgent(IESOWorldviewGeoUIAgentConfig())
        params = IESOWorldviewGeoUIAgentInputSchema(
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
