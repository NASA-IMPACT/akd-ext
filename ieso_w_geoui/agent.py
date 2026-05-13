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
from pydantic import Field
from pydantic_ai.capabilities import MCP

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

  * If a prior Worldview URL exists from earlier in the conversation,
    call ``geoui_get_state(url=...)`` to retrieve the current ``GeoIntent``.
  * Treat the returned GeoIntent as your starting point for refinement.
  * Carry forward fields the user did not ask to change; modify only
    the fields implicated by the latest user request.
  * Skip discovery (steps 4–6) for fields already in the state.

  ### **Step 7: Visualization Construction (via GeoUI Protocol)**

  * Build a **``GeoIntent``** describing the desired application state.
  * Call ``geoui_render_intent(intent=...)`` to obtain the Worldview
    permalink URL. The returned URL is the visualization the user opens.
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
    minus the ``worldview_permalink_tool`` MCP. Permalink construction is
    now a local tool (``geoui_render_intent``).

    Auth tokens are read from env at construction time:
      - IESO_MCP_KEY: the two remaining IESO-hosted worldview tool servers
      - VECTOR_DB_TOOL_KEY: IESO validation / layer vector-DB server
      - SDE_MCP_KEY: Science Discovery Engine fallback server
    """
    ieso_mcp_key = os.environ.get("IESO_MCP_KEY")
    vector_db_tool_key = os.environ.get("VECTOR_DB_TOOL_KEY")
    sde_mcp_key = os.environ.get("SDE_MCP_KEY")

    return [
        MCP(
            url="https://sudden-gold-carp-features-tool-cmr-uat.fastmcp.app/mcp",
            id="ieso-worldview-tool-umm_vis_lookup_tool",
            allowed_tools=["umm_vis_lookup_tool"],
            authorization_token=ieso_mcp_key,
            description="Layerid Visualization lookup for CMR Concept id",
        ),
        MCP(
            url="https://sudden-gold-carp-features-tools-earthdata-search-da3be0.fastmcp.app/mcp",
            id="ieso-worldview-tool-earthdata_search_landing_page_tool",
            allowed_tools=["earthdata_search_landing_page_tool"],
            authorization_token=ieso_mcp_key,
            description="Earthdata search landing page for concept id",
        ),
        MCP(
            url="https://w4hu71445m.execute-api.us-east-1.amazonaws.com/mcp/cmr/mcp",
            id="CMR_MCP_Server",
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
            authorization_token=vector_db_tool_key,
        ),
        MCP(
            url="https://brainy-lime-pheasant.fastmcp.app/mcp",
            id="sde_mcp_tool",
            allowed_tools=["sde_search_tool"],
            authorization_token=sde_mcp_key,
        ),
    ]


def get_default_geoui_tools() -> list[BaseTool]:
    """Default local AKD tools wired into the GeoUI-variant agent."""
    return [GeoUIRenderIntentTool(), GeoUIGetStateTool()]


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
#     OPENAI_API_KEY, IESO_MCP_KEY, VECTOR_DB_TOOL_KEY, SDE_MCP_KEY.
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

    required = ["OPENAI_API_KEY", "IESO_MCP_KEY", "VECTOR_DB_TOOL_KEY", "SDE_MCP_KEY"]
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
