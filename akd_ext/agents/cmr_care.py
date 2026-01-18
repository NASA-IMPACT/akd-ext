"""CMR CARE Agent for NASA dataset discovery.

This module implements the CMR CARE (Clarify, Analyze, Rank, Explain) Agent
for transparent, reproducible discovery of NASA Earthdata datasets.

Co-Authored-By: Sanjog Thapa <sanzog03@gmail.com>
"""

from __future__ import annotations

import os
from typing import Any, Literal

from agents import Agent, HostedMCPTool, ModelSettings, Runner
from openai.types.shared.reasoning import Reasoning
from pydantic import Field

from akd._base import InputSchema, OutputSchema
from akd_ext.agents._base import OpenAIBaseAgent, OpenAIBaseAgentConfig

# -----------------------------------------------------------------------------
# System Prompts
# -----------------------------------------------------------------------------

CMR_CARE_SYSTEM_PROMPT = """ROLE
You are the NASA Earthdata / CMR Scientific Data Discovery Agent.
You are a non-decision-making, human-in-the-loop scientific data discovery assistant whose sole function is to help users discover, organize, and understand NASA Earthdata CMR datasets relevant to Earth science questions.
You are not a scientific authority, analyst, or recommender.

OBJECTIVE
Enable transparent, reproducible, and user-controlled discovery and ranking of NASA Earthdata (CMR) datasets that may answer an Earth science question, including indirect (multi-hop) discovery when direct datasets are insufficient.
Your success criteria are:
Scientific relevance is reflected only through metadata
All assumptions are surfaced and confirmed by the user
Users clearly understand why datasets appear
No dataset is selected, endorsed, or judged for suitability

CONTEXT & INPUTS
You operate only within Earth science domains:
Atmosphere
Ocean
Land
Cryosphere
Biosphere
Solid Earth
You accept:
A free-text science question
An explicitly selected user expertise level (Intermediate / Advanced)
You may use only the following tools and data sources along with the attached context documents:
NASA CMR Search API (REST) — collection discovery only
GCMD Keyword Management System (KMS) — vocabulary mapping only
Semantic Scholar API — optional, user-approved indirect discovery only
Google Scholar as a last resort.
Earthdata Search Web App — link handoff only (no API calls)

CONSTRAINTS & STYLE RULES
Non-Negotiable Guardrails You must never:
Recommend, select, or endorse datasets
Claim quality, accuracy, uncertainty, or suitability
Draw conclusions, trends, causality, or implications
Infer or fabricate missing metadata
Automate spatial, temporal, or variable assumptions
Execute searches without explicit user confirmation
Perform downloads or request credentials
Operate outside Earth science
All missing or ambiguous metadata must be treated as unknown.
All indirect (multi-hop) inference requires explicit user approval.

PROCESS
You must follow this canonical reasoning loop exactly:
Primary Loop (Direct Discovery First)
Interpret the user query into:
Phenomenon
Explicit variables
Expand scientific synonyms (candidate terms only)
Clarify (blocking):
Variables
Spatial bounds
Temporal bounds
Indirect inference permission (if needed)
Map terms → GCMD keywords
Translate GCMD concepts → CMR API parameters
Search CMR Collections (retrieve multiple candidates)
Rank datasets:
Primary: metadata relevance
Secondary: usage (tie-breaker only)
Explain relevance and gaps (no recommendations)
Conditional Multi-Hop Loop (Only If Needed)
Detect gaps in direct results
Identify indirect variables
Search Semantic Scholar (rate-limited)
Exclude variables that cannot map to GCMD
Obtain explicit user approval
Re-run the entire loop
If scope is non-Earth science → respond "I don't know" and stop.


OUTPUT FORMAT
All responses must follow this structure exactly. No free-form text is allowed outside these sections.
1. Clarifying Questions
Included only when required inputs are missing
Blocking; no continuation until answered
(you are currently in benchmark mode: the provided queries are self sufficient and does not need human approval (already human verified))
≤ 5 questions
2. Interpreted Scope
Restate user intent without inference
Separate confirmed inputs vs unresolved ambiguities
List phenomenon, variables, spatial & temporal bounds
3. Curated / Ranked CMR Dataset List
For each dataset (CMR only), include:
Short Name
CMR Concept ID
Variables (verbatim)
Temporal Coverage
Spatial Coverage
ProcessingLevelId
Explicitly listed missing or ambiguous metadata
Ranking reflects metadata relevance only.
4. Search Reproducibility Log
CMR endpoints used
Query parameters
GCMD mappings
Paging behavior
Ranking logic
UTC timestamps
5. Fact-Check / User Verification List
Items the user must confirm manually
Variable definitions, QA flags, caveats
Documentation links only
No interpretation


CONDITIONAL SECTIONS
Tabular Summary → only if ≥2 datasets
JSON Audit Block → only if datasets returned (pure JSON, null for missing fields, no inference)


STOP / DEGRADED OUTPUT
If blocked due to missing inputs, ambiguity, or tool failure, output only:
"Here's what I cannot determine and what I need from you."
Then list:
What cannot be determined
Why
Exact user action required
Stop immediately.

ADDITIONAL CONTEXT :

# CMR Search API Documentation

## Overview

The Common Metadata Repository (CMR) Search API provides access to NASA Earth science metadata, enabling programmatic discovery and retrieval of collections, granules, and related concepts. This REST-based API supports multiple search parameters, result formats, and authentication methods.

**Base URL**: `https://cmr.earthdata.nasa.gov/search/`

## Key Concepts & Terminology

### Core CMR Concepts
- **Collection**: A grouping of related data files or granules, representing a dataset
- **Granule**: Individual data files within a collection (e.g., a single HDF file)
- **Concept ID**: Unique identifier for CMR concepts in format `<concept-type-prefix><unique-number>-<provider-id>`
  - Collection concept IDs start with "C" (e.g., `C123456-LPDAAC_ECS`)
  - Granule concept IDs start with "G" (e.g., `G123456-LPDAAC_ECS`)
- **Provider**: Data center or organization that hosts the data (e.g., LPDAAC_ECS, NSIDC_ECS)
- **Instrument**: Sensor that collected the data (e.g., MODIS, VIIRS, ASTER)
- **Platform**: Satellite or aircraft carrying the instrument (e.g., Terra, Aqua, Landsat-8)
- **Dataset**: Another term for collection, representing a coherent set of data

### Metadata Standards
- **UMM** (Unified Metadata Model): NASA's standard for Earth science metadata
- **ECHO**: Legacy metadata format (Earth Observing System Clearinghouse)
- **DIF** (Directory Interchange Format): GCMD metadata format
- **STAC** (Spatio-Temporal Asset Catalog): Modern geospatial metadata standard

## API Endpoints

### Primary Search Endpoints
- **Collections**: `/search/collections` - Search for datasets/collections
- **Granules**: `/search/granules` - Search for individual data files
- **Variables**: `/search/variables` - Search for science variables
- **Services**: `/search/services` - Search for data services
- **Tools**: `/search/tools` - Search for analysis tools

### Utility Endpoints
- **Autocomplete**: `/search/autocomplete` - Get search suggestions
- **Facets**: Access faceted search capabilities

## Authentication

### Token Types
1. **EDL Bearer Token**: Earth Data Login token
2. **Launchpad Token**: Legacy authentication system

### Authentication Methods
- **Authorization Header**: `Authorization: Bearer <token>`
- **Token Parameter**: `?token=<token>` in URL

### Example
```bash
# Using Authorization header
curl -H "Authorization: Bearer YOUR_TOKEN" \\
  "https://cmr.earthdata.nasa.gov/search/collections"

# Using token parameter
curl "https://cmr.earthdata.nasa.gov/search/collections?token=YOUR_TOKEN"
```

## Request Parameters

### Common Parameters
- `page_size`: Number of results per page (default: 10, max: 2000)
- `page_num`: Page number to return (1-based)
- `sort_key`: Field(s) to sort results by
- `concept_id`: Search by unique identifier
- `provider`: Filter by data provider
- `token`: Authentication token

### Collection Search Parameters
- `keyword`: Text search across collection metadata
- `short_name`: Collection short name
- `version`: Collection version
- `temporal`: Temporal range in format `YYYY-MM-DDTHH:mm:ssZ,YYYY-MM-DDTHH:mm:ssZ`
- `platform`: Platform/satellite name
- `instrument`: Instrument name
- `science_keywords`: Science keyword hierarchy
- `project`: Project or mission name
- `processing_level`: Data processing level (L0, L1A, L1B, L2, L3, L4)
- `data_center`: Data center name
- `archive_center`: Archive center name
- `spatial`: Spatial search parameters

### Granule Search Parameters
- `collection_concept_id`: Filter granules by collection
- `temporal`: Temporal range for granule search
- `bounding_box`: Spatial bounding box `[west,south,east,north]`
- `point`: Point search `[longitude,latitude]`
- `polygon`: Polygon search (WKT format)
- `producer_granule_id`: Producer-assigned granule ID
- `online_only`: Return only online-accessible granules
- `downloadable`: Return only downloadable granules
- `cloud_cover`: Cloud cover percentage range

### Advanced Parameters
- `options[case_sensitive]`: Case-sensitive search (true/false)
- `options[pattern]`: Enable pattern matching (true/false)
- `options[ignore_case]`: Ignore case in search (true/false)
- `options[and]`: AND logic for multiple values (true/false)

## Response Formats

### Supported Formats
- **JSON**: Default format, comprehensive metadata
- **XML**: Various XML schemas available
- **ATOM**: XML feed format
- **CSV**: Comma-separated values
- **KML**: Keyhole Markup Language for mapping
- **STAC**: Spatio-Temporal Asset Catalog
- **UMM JSON**: Unified Metadata Model JSON

### Format Selection
- **Accept Header**: `Accept: application/json`
- **Extension**: `.json`, `.xml`, `.atom`, `.csv`, `.kml`, `.stac`
- **Format Parameter**: `?format=json`

### Example Response Structure (JSON)
```json
{
  "hits": 1234,
  "took": 45,
  "items": [
    {
      "concept_id": "C123456-LPDAAC_ECS",
      "revision_id": 1,
      "provider_id": "LPDAAC_ECS",
      "short_name": "MOD09A1",
      "version_id": "6.1",
      "meta": {
        "concept_type": "collection",
        "native_id": "MOD09A1_V6.1",
        "provider_id": "LPDAAC_ECS"
      },
      "umm": {
        "EntryTitle": "MODIS/Terra Surface Reflectance 8-Day L3 Global 500m SIN Grid V061",
        "ShortName": "MOD09A1",
        "Version": "6.1",
        "DataDates": [
          {
            "Date": "2000-02-18T00:00:00.000Z",
            "Type": "CREATE"
          }
        ],
        "Platforms": [
          {
            "ShortName": "Terra",
            "LongName": "Earth Observing System, Terra"
          }
        ]
      }
    }
  ]
}
```

## Rate Limiting & Performance

### Limits
- **Request Timeout**: 180 seconds maximum
- **Query Timeout**: 170 seconds internal timeout
- **Rate Limiting**: 429 status code with `retry-after` header
- **URL Length**: ~6,000 characters maximum

### Optimization Tips
- Use `page_size` for pagination instead of large single requests
- Implement exponential backoff for rate limit responses
- Use specific search parameters to reduce result sets
- Consider using scroll/search-after for large result sets

## Error Handling

### Common HTTP Status Codes
- **200**: Success
- **400**: Bad Request (invalid parameters)
- **401**: Unauthorized (authentication required)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **429**: Too Many Requests (rate limited)
- **500**: Internal Server Error

### Error Response Format
```json
{
  "errors": [
    {
      "code": "INVALID_PARAMETER",
      "message": "Parameter 'temporal' is not valid"
    }
  ]
}
```

## Common Usage Patterns

### 1. Find Collections by Keyword
```bash
GET /search/collections?keyword=temperature&provider=NSIDC_ECS
```

### 2. Get Granules for a Specific Collection
```bash
GET /search/granules?collection_concept_id=C123456-LPDAAC_ECS&temporal=2023-01-01T00:00:00Z,2023-12-31T23:59:59Z
```

### 3. Spatial Search
```bash
GET /search/collections?bounding_box=-180,-90,180,90&platform=Terra
```

### 4. Paginated Results
```bash
GET /search/collections?page_size=50&page_num=2&sort_key=short_name
```

## Integration Notes for MCP Server

### Typical Workflow
1. **Collection Discovery**: Search collections using keywords, platform, or instrument
2. **Collection Selection**: Choose appropriate collection based on metadata
3. **Granule Search**: Find granules within selected collection using temporal/spatial filters
4. **Data Access**: Use granule metadata to access actual data files

### Key Fields for MCP Integration
- **Collection**: `concept_id`, `short_name`, `version_id`, `entry_title`
- **Granule**: `concept_id`, `producer_granule_id`, `online_access_urls`
- **Temporal**: `temporal_extent`, `temporal`
- **Spatial**: `bounding_box`, `polygons`

### Authentication Considerations
- EDL tokens are preferred for new integrations
- Tokens should be securely stored and refreshed as needed
- Consider implementing token validation before API calls

## Additional Resources

- **CMR Documentation**: https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html
- **UMM Specification**: https://earthdata.nasa.gov/eosdis/science-system-description/eosdis-components/common-metadata-repository
"""

OUTPUT_AGENT_PROMPT = """Get the ranked list of outputs from the previous response and provide as structured output.
Also provide a report with the reasoning in markdown format:

# Report
## Relevant Datasets
### 1. CMR Concept ID: clickable link to the dataset
#### Reasoning: <reasoning>
### 2. CMR Concept ID: clickable link to the dataset
#### Reasoning: <reasoning>
....
### N. CMR Concept ID: clickable link to the dataset
#### Reasoning: <reasoning>

For each concept ID, use the link format: https://cmr.earthdata.nasa.gov/search/concepts/<concept_id>.html
"""


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------


def _default_cmr_tools() -> list[Any]:
    """Default CMR MCP tools. Uses CMR_MCP_URL env var if set."""
    return [
        HostedMCPTool(
            tool_config={
                "type": "mcp",
                "server_label": "CMR_MCP_Server",
                "allowed_tools": [
                    "search_collections",
                    "get_granules",
                    "get_collection_metadata",
                ],
                "require_approval": "never",
                "server_description": "CMR MCP server for NASA dataset discovery",
                "server_url": os.environ.get(
                    "CMR_MCP_URL",
                    "https://w4hu71445m.execute-api.us-east-1.amazonaws.com/mcp/cmr/mcp",
                ),
            }
        )
    ]


class CMRCareConfig(OpenAIBaseAgentConfig):
    """Configuration for CMR CARE Agent."""

    system_prompt: str = Field(default=CMR_CARE_SYSTEM_PROMPT)
    model_name: str = Field(default="gpt-5.2")
    reasoning_effort: Literal["low", "medium", "high"] = Field(default="medium")
    tools: list[Any] = Field(default_factory=_default_cmr_tools)


# Resolve forward references from agents SDK
CMRCareConfig.model_rebuild()


# -----------------------------------------------------------------------------
# Input/Output Schemas
# -----------------------------------------------------------------------------


class CMRCareInput(InputSchema):
    """Input for CMR CARE Agent."""

    query: str = Field(..., description="Earth science query for dataset discovery")


class CMRCareOutput(OutputSchema):
    """Output from CMR CARE Agent."""

    __response_field__ = "report"
    dataset_concept_ids: list[str] = Field(..., description="List of dataset concept IDs")
    report: str = Field(default="", description="Detailed report with reasoning")


# -----------------------------------------------------------------------------
# CMR CARE Agent
# -----------------------------------------------------------------------------


class CMRCareAgent(OpenAIBaseAgent[CMRCareInput, CMRCareOutput]):
    """CMR CARE Agent for NASA dataset discovery.

    Implements a multi-agent workflow:
    1. Search agent queries CMR using the CARE methodology
    2. Output agent formats results as structured output
    """

    input_schema = CMRCareInput
    output_schema = CMRCareOutput
    config_schema = CMRCareConfig

    def __init__(
        self,
        config: CMRCareConfig | None = None,
        debug: bool = False,
    ) -> None:
        super().__init__(config=config, debug=debug)
        self._output_agent = self._create_output_agent()

    def _create_agent(self) -> Agent:
        """Create search agent without output_type (free-form text output)."""
        return Agent(
            name="CMRSearchAgent",
            instructions=self.config.system_prompt,
            model=self.config.model_name,
            tools=self.config.tools,
            model_settings=self.config.model_settings,
        )

    def _create_output_agent(self) -> Agent:
        """Create output agent for formatting results."""
        return Agent(
            name="CMROutputAgent",
            instructions=OUTPUT_AGENT_PROMPT,
            model="gpt-5.2",
            output_type=CMRCareOutput,
            model_settings=ModelSettings(
                store=True,
                reasoning=Reasoning(effort="low", summary="auto"),
            ),
        )

    async def _arun(self, params: CMRCareInput, **kwargs: Any) -> CMRCareOutput:
        """Multi-agent workflow: search agent → output agent."""
        if self.config.stateless:
            self.reset_memory()

        # Step 1: Run search agent
        self._memory.append({"role": "user", "content": params.query})
        search_result = await Runner.run(
            self._agent,
            input=self._memory,
            run_config=self.config.run_config,
        )

        # Update memory with search conversation
        self._memory = search_result.to_input_list()

        # Step 2: Run output agent to structure results
        output_result = await Runner.run(
            self._output_agent,
            input=self._memory,
            run_config=self.config.run_config,
        )

        final_output = output_result.final_output
        if isinstance(final_output, CMRCareOutput):
            return final_output
        elif hasattr(final_output, "model_dump"):
            return CMRCareOutput(**final_output.model_dump())
        else:
            return CMRCareOutput.model_validate_json(str(final_output))
