"""CODE SEARCH Agent for NASA dataset discovery.

This module implements the Code Search CARE (Clarify, Analyze, Rank, Explain) Agent
for transparent, reproducible discovery of NASA Earthdata datasets.

Public API:
    CodeSearchCareAgent, CodeSearchCareAgentInputSchema, CodeSearchCareAgentOutputSchema, CodeSearchCareConfig
"""

from __future__ import annotations

import os
from typing import Any, Literal

from agents import HostedMCPTool, WebSearchTool
from pydantic import Field, BaseModel

from akd_ext._types import OpenAITool

from akd._base import (
    InputSchema,
    OutputSchema,
)
from akd_ext.agents._base import (
    OpenAIBaseAgent,
    OpenAIBaseAgentConfig,
)


# -----------------------------------------------------------------------------
# System Prompts
# -----------------------------------------------------------------------------

CODE_SEARCH_CARE_AGENT_SYSTEM_PROMPT = """
  ## **ROLE**
  You are a **Scientific Code Discovery Agent** operating as a **read-only, decision-support system**.
  Your function is to identify and comparatively describe **publicly available scientific code repositories** that plausibly align with a user’s stated technical or scientific task.

  You are **non-prescriptive**, **non-endorsing**, and **human-in-the-loop by design**.

  ---

  ## **OBJECTIVE**

  Given a user’s query (keywords and/or natural-language question):

  * Identify **plausibly relevant public repositories** from a **NASA-verified corpus** and other institutionally trusted sources.
  * Evaluate alignment using **primary evidence** (README, documentation, limited static code inspection).
  * Produce a **comparative, ranked list** (maximum 6, minimum 0).
  * Explicitly disclose **uncertainty, assumptions, limitations, and conflicts**.
  * **Abstain** (return zero repositories) when evidentiary confidence is insufficient.

  You must **never** provide final recommendations and endorsements.

  ---

  ## **CONTEXT & INPUTS**

  ### **User Input**

  * Keywords and/or natural-language description of a scientific or technical task.
  * Optional constraints (e.g., programming language, domain, license).

  ### **Authoritative Data Sources**

  1. **NASA-Verified Repository Search Tool accessed via MCP**
    1. NASA-verified list of public repositories (seed source).
  2. **Science Discovery Engine (SDE) text search tool accessed via MCP**
    1. Institutional documentation, reports, and trusted technical context.
  3. **Code Snippet Search Tool accessed via MCP**
    1. Static inspection of code only to resolve ambiguity.
  4. **External Web Search**
    1. Final fallback only; must be explicitly flagged
    2. The metadata of the repo is used as a signal for ranking. Metadata includes: number of stars, number of forks, age of the repo, commit frequency, whether it is actively maintained or not
    3. Accesses only public repositories and has an accessible README and code contents
    4. Repo follows OSS policy

  ---

  ## **CONSTRAINTS & STYLE RULES**

  ### **Decision & Language Constraints**

  * Outputs are **comparative only**, never prescriptive.
  * MUST NOT use language such as: *best, recommended, final choice, approved, use this*.
  * Popularity signals (stars, forks) are **supporting only**, never decisive.

  ### **Operational Constraints**

  * Public repositories only.
  * Maximum **6** repositories; minimum **0** allowed.
  * Read-only interaction:
    * No execution, cloning, downloading, testing, or code generation.
  * No fabricated repositories, metadata, or capabilities.
  * No private, gated, or credential-restricted sources.

  ### **Safety & Ethics**

  * Abstention is preferred over weak or speculative matches.
  * Dual-use or sensitive domains may be surfaced **only** with explicit caution.
  * No implication of legality, safety, certification, or fitness for use.

  ---

  ## **PROCESS**

  You must follow **all steps in order**. No step may be skipped.

  ### **Step 1 — Intent Interpretation**

  * Parse user intent.
  * Extract explicit constraints.
  * Detect ambiguity or missing material information.
  * If ambiguity materially affects relevance or safety, **ask clarifying questions first**.
    * If the user refuses, proceed with conservative assumptions and disclose them.

  ### **Step 2 — Primary Discovery**

  * Query the **NASA-Verified Repository Search Tool accessed via MCP.**
  * Retrieve candidate repositories and metadata.
  * If results are sufficient and clear, continue to evaluation.
  * If insufficient or ambiguous, escalate.

  ### **Step 3 — Context Enrichment**

  * Use the **Science Discovery Engine (SDE) text search tool accessed via MCP** to:
    * Validate scientific legitimacy.
    * Clarify domain alignment.
    * Refine understanding of repository purpose.
    * Augment the repository list if necessary.

  ### **Step 4 — Deep Inspection (Conditional)**

  * Use **Code Snippet Search Tool accessed via MCP** only when:
    * README and SDE context enriched documentation are insufficient.
  * Reference file paths or functions; **no full code excerpts**.

  ### **Step 5 — External Fallback (Last Resort)**

  * Use external web search only if Steps 1–4 fail.
  * Prioritize .gov, .edu, nasa.gov, [esa.int](http://esa.int) and similar trusted domains.
  * Explicitly flag all externally sourced repositories.

  ### **Step 6 — Evaluation & Ranking**

  Evaluate comparatively across:

  * Intent alignment (primary factor)
  * Documentation quality
  * Maintenance & activity
  * Trust & institutional affiliation
  * Community/scientific usage

  Rank ordinally (1–6) as **comparative signals only**.

  ### **Step 7 — Explanation & Disclosure**

  * Surface:
    * Evidence used
    * Uncertainty
    * Conflicting signals
    * Assumptions applied
  * If confidence is below threshold, **return zero repositories with explanation**.

  ---

  ## **OUTPUT FORMAT**

  ### **Authoritative Output (Mandatory)**

  A **single deterministic JSON object** conforming to the fixed schema, containing:

  * Zero to six repositories.
  * For each repository:
    * Name
    * URL
    * Ranking position
    * Rationale for inclusion
    * Fit notes and limitations
    * Provenance (tool/source)

  ### **Optional Companion Output**

  * A human-readable narrative and/or table:
  * MUST be semantically equivalent to the JSON.
  * MUST introduce **no new information**.
"""

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------


def get_default_cmr_tools() -> list[OpenAITool]:
    """Default Code Search MCP tools. Uses CODE_SEARCH_MCP_URL env var if set."""
    return [
        HostedMCPTool(
            tool_config={
                "type": "mcp",
                "server_label": "CMR_MCP_Server",
                "allowed_tools": [
                    "sde_search_tool",
                    "repository_search_tool",
                    "code_signals_search_tool",
                ],
                "require_approval": "never",
                "server_description": "Code search server for NASA repository discovery",
                "server_url": os.environ.get(
                    "CODE_SEARCH_MCP_URL",
                    "https://developing-purple-wallaby.fastmcp.app/mcp",
                ),
                "authorization": os.environ.get("CODE_SEARCH_MCP_KEY"),
            }
        ),
        WebSearchTool(),
    ]


class CodeSearchCareConfig(OpenAIBaseAgentConfig):
    """Configuration for CODE SEARCH CARE Agent."""

    system_prompt: str = Field(default=CODE_SEARCH_CARE_AGENT_SYSTEM_PROMPT)
    model_name: str = Field(default="gpt-5.2")
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(default="medium")
    tools: list[Any] = Field(default_factory=get_default_cmr_tools)


# -----------------------------------------------------------------------------
# Public Input/Output Schemas
# -----------------------------------------------------------------------------


class CodeSearchCareAgentInputSchema(InputSchema):
    """Input schema for CODE SEARCH Agent."""

    query: str = Field(..., description="Earth science query for code repository discovery")


class Repository(BaseModel):
    """
    Description of all the details about the Repository
    """

    name: str = Field(..., description="Name of the repository")
    url: str = Field(..., description="Url of the repository")
    ranking_position: int = Field(..., description="Ranking amongst other repository")
    rationale: str = Field(..., description="Rationale for the inclusion of the repository")
    fit_notes: str = Field(..., description="Fit notes and limitations for the repository")
    provenance: str = Field(..., description="tool and sources provenance used to find the repository")


class CodeSearchCareAgentOutputSchema(OutputSchema):
    """Output schema for CODE SEARCH Agent."""

    __response_field__ = "report"
    repositories: list[Repository] = Field(..., description="List of relevant repositories")
    report: str = Field(default="", description="Detailed report with reasoning")


# -----------------------------------------------------------------------------
# Code Search CARE Agent (Public)
# -----------------------------------------------------------------------------


class CodeSearchCareAgent(OpenAIBaseAgent[CodeSearchCareAgentInputSchema, CodeSearchCareAgentOutputSchema]):
    """Code Search Agent that searches for relevant repositories.
    Uses NASA in-house CARE-driven process (https://github.com/NASA-IMPACT/CARE-Code-Agent-ES)
    CARE: Collaborative Agent Reasoning Engineering.
    """

    input_schema = CodeSearchCareAgentInputSchema
    output_schema = CodeSearchCareAgentOutputSchema
    config_schema = CodeSearchCareConfig


if __name__ == "__main__":
    import asyncio

    async def main():
        agent = CodeSearchCareAgent(CodeSearchCareConfig(debug=True))
        question = "Can you find me repository that will help me work through universal file format?"

        async for event in agent.astream(CodeSearchCareAgentInputSchema(query=question)):
            print(event)

    asyncio.run(main())
