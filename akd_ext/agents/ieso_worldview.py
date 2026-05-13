"""IESO CARE Agent for NASA Worldview visualization.

This module implements the IESO Agent for guided,
reproducible discovery of NASA Worldview visualizations.

Public API:
    IESOWorldviewAgent, IESOWorldviewAgentInputSchema, IESOWorldviewAgentOutputSchema, IESOWorldviewAgentConfig
"""

from __future__ import annotations

import os
from typing import Any, Literal

from pydantic import Field
from pydantic_ai.capabilities import MCP

from akd._base import (
    InputSchema,
    OutputSchema,
    TextOutput,
)
from akd_ext.agents._base import (
    PydanticAIBaseAgent,
    PydanticAIBaseAgentConfig,
)


# -----------------------------------------------------------------------------
# System Prompts
# -----------------------------------------------------------------------------

IESO_WORLDVIEW_AGENT_SYSTEM_PROMPT = """
  ## **ROLE**

  You are a **NASA Worldview Scientific Data Assistant Agent**.

  You act as a **non-authoritative, transparency-first guide** that helps users:

  * Discover NASA datasets
  * Understand dataset meaning, limitations, and proxies
  * Configure and generate Worldview visualizations
  * Perform **Worldview-native exploratory analysis only**

  You **do not interpret, conclude, recommend scientifically, or make decisions for the user**.

  ## **OBJECTIVE**

  Enable users to:

  1. Translate their intent into scientifically relevant datasets
  2. Explore datasets via **NASA Worldview deep links**
  3. Understand dataset caveats, uncertainty, and limitations
  4. **Support visualization-driven and all the analysis workflows aligned with Worldview capabilities**
  5. Maintain **full human control over dataset selection and interpretation**

  ## **CONTEXT & INPUTS**

  ### **Available Systems & Tools**

  * **NASA Worldview (Primary Interface)**
    * Generate deep links using URL parameters
    * Support layers, time, comparison modes, charting
  * **CMR API (Metadata Authority)**
    * `search_collections`, `get_collection_metadata`
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
    * “This shows…”
    * “This means…”
    * “This indicates…”
  * Use:
    * “This dataset represents…”
    * “This visualization displays…”
    * “Possible interpretation requires user judgment”

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
    * “Which dataset would you like to use?”
  * DO NOT proceed without confirmation

  ### **Step 7: Visualization Construction**

  * Generate **Worldview deep link**
  * Configure:
    * Layers
    * Time
    * Viewport
    * Comparison (if relevant)
  * Ensure only valid parameters used

  ### **Step 8: Analysis Support (Limited)**

  * Provide:
    * Time series (if supported)
    * Regional statistics (if supported)
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

  * “Show dataset details”
  * “Show metadata”
  * “Open Earthdata page”

  ## **OUTPUT FORMAT**

  ### **1\. STRUCTURED RESPONSE**

  INTENT:
  DATASET\_OPTIONS:
  SELECTED\_DATASET: (ONLY after user confirmation)
  WORLDVIEW\_URL:

  Options \[provide with more options\]
  PARAMETERS\_USED:
  PROVENANCE:
  UNCERTAINTY:
  LIMITATIONS:
  MISSING\_FIELDS:

  ### **2\. USER NARRATIVE**

  * Beginner → simplified explanation
  * Intermediate → moderate detail
  * Advanced → technical description

  ### **3\. OPTIONAL ACTIONS**

  * View metadata
  * Open dataset page
  * Fetch documentation

  ### **4\. REQUIRED DISCLAIMER**

  “This information is derived from publicly available datasets and visualization tools on NASA Worldview . It is intended for exploratory and informational purposes only and does not constitute scientific analysis, interpretation, or validated conclusions.”
"""

# -----------------------------------------------------------------------------
# MCP capabilities
# -----------------------------------------------------------------------------


def get_default_ieso_worldview_capabilities() -> list[Any]:
    """Default MCP server capabilities wired into the IESO Worldview agent.

    Auth tokens are read from env at construction time:
      - IESO_MCP_KEY: the three IESO-hosted worldview tool servers
      - VECTOR_DB_TOOL_KEY: IESO validation / layer vector-DB server
      - SDE_MCP_KEY: Science Discovery Engine fallback server
    """
    ieso_mcp_key = os.environ.get("IESO_MCP_KEY")
    vector_db_tool_key = os.environ.get("VECTOR_DB_TOOL_KEY")
    sde_mcp_key = os.environ.get("SDE_MCP_KEY")

    return [
        MCP(
            url="https://sudden-gold-carp-features-tool-worldview-permalink-82de.fastmcp.app/mcp",
            id="ieso-worldview-tool-worldview_permalink_tool",
            allowed_tools=["worldview_permalink_tool"],
            authorization_token=ieso_mcp_key,
            description="Permalink generation for NASA worldview.",
        ),
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
            description=("CMR MCP server to fetch metadata information including links to download datasets"),
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


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------


class IESOWorldviewAgentConfig(PydanticAIBaseAgentConfig):
    """Configuration for IESO CARE Agent."""

    description: str = Field(
        default=(
            """Earth science Worldview-visualization agent. Helps users translate
            Earth science queries into NASA Worldview permalinks by clarifying intent,
            surfacing candidate datasets, awaiting user confirmation, and producing a
            reproducible visualization URL with provenance and uncertainty annotations.
            Outputs are delivered via a structured schema and interactive chat with the
            user for clarification, dataset selection, approval gates, and disclaimers."""
        )
    )
    system_prompt: str = Field(default=IESO_WORLDVIEW_AGENT_SYSTEM_PROMPT)
    model_name: str = Field(default="openai:gpt-5.2")
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(default="medium")
    capabilities: list[Any] = Field(default_factory=get_default_ieso_worldview_capabilities)


# -----------------------------------------------------------------------------
# Input/Output Schemas
# -----------------------------------------------------------------------------


class IESOWorldviewAgentInputSchema(InputSchema):
    """Input schema for the IESO Worldview-discovery agent."""

    query: str = Field(..., description="Earth science query to interact with worldview visualization")


class IESOWorldviewAgentOutputSchema(OutputSchema):
    """Structured Worldview-discovery response. Use this on the final turn,
    after the user has confirmed a dataset; populate `result` with the full
    sectioned response and `url` with the Worldview permalink.
    Use TextOutput for clarification questions or when no dataset has been
    confirmed yet."""

    __response_field__ = "result"
    result: str = Field(
        ...,
        description=(
            "Full sectioned response: INTENT, DATASET_OPTIONS, "
            "SELECTED_DATASET, WORLDVIEW_URL, PARAMETERS_USED, PROVENANCE, "
            "UNCERTAINTY, LIMITATIONS, MISSING_FIELDS, USER NARRATIVE "
            "OPTIONAL ACTIONS, and the REQUIRED DISCLAIMER"
            "Format is defined by the system prompt."
        ),
    )
    url: str = Field(
        ...,
        description="Worldview permalink that resolves the science query.",
    )


# -----------------------------------------------------------------------------
# IESO Agent
# -----------------------------------------------------------------------------


class IESOWorldviewAgent(PydanticAIBaseAgent[IESOWorldviewAgentInputSchema, IESOWorldviewAgentOutputSchema]):
    """Earth science Worldview-visualization agent.

    Resolves an Earth science query into a NASA Worldview permalink.
    """

    input_schema = IESOWorldviewAgentInputSchema
    output_schema = IESOWorldviewAgentOutputSchema | TextOutput
    config_schema = IESOWorldviewAgentConfig

    def check_output(self, output) -> str | None:
        if isinstance(output, IESOWorldviewAgentOutputSchema):
            if not output.result.strip():
                return "Result is empty. Provide the structured Worldview-discovery response."
            if not output.url.strip():
                return "URL is empty. Provide a valid url"
        return super().check_output(output)
