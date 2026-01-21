"""
NASA Science Discovery Engine (SDE) search tool.

This tool wraps the SDE Elastic Wrapper API to enable searching NASA's Science
Discovery Engine for relevant scientific documents, datasets, and resources using
natural language queries.
"""

import os
import httpx
from akd._base import InputSchema
from akd.tools.search import SearchToolOutputSchema
from akd.structures import SearchResult
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field
from typing import Literal
from loguru import logger

from akd_ext.structures import SDEIndexedDocumentType, NASASMDDivision


class SDESearchToolConfig(BaseToolConfig):
    """Configuration for the SDE Search Tool."""

    base_url: str = Field(
        default=os.getenv("SDE_BASE_URL", "https://dyejsbdumgpqz.cloudfront.net"),
        description="Base URL for the SDE API",
    )
    timeout: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds",
    )
    division: NASASMDDivision | None = Field(
        None,
        description="Filter results by NASA SMD division",
    )
    search_type: Literal["hybrid", "vector", "keyword"] = Field(
        default="hybrid",
        description="Search type: 'hybrid' (vector + keyword), 'vector' (semantic), 'keyword' (text-based)",
    )


class SDEDocument(SearchResult):
    """
    A single document result from SDE search.

    Extends SearchResult with SDE-specific fields. Parsed from the HitBase structure
    returned by the SDE Elastic Wrapper API. Maps common fields from multiple index
    types (web, CMR, PDS3/4, SPASE, GCN, etc.) into a unified structure.

    Common fields inherited from SearchResult:
    - query: Search query that produced this result
    - title: Document title
    - content: Snippet or abstract (mapped from snippet field)
    - score: Relevance score from OpenSearch
    """

    url: str = Field(..., description="URL to access the document")
    division: NASASMDDivision | None = Field(
        None, description="NASA SMD division (e.g., Astrophysics, Planetary Science)"
    )
    doc_type: SDEIndexedDocumentType | None = Field(
        None, description="Document type (e.g., Data, Documentation, Software and Tools)"
    )
    source: str | None = Field(None, description="Source index (e.g., sde-web, sde-cmr, sde-pds4, sde-code)")


# cannot use SearchToolInputSchema because it has plural 'queries' field
class SDESearchToolInputSchema(InputSchema):
    """Input schema for SDE search queries."""

    query: str = Field(..., description="Natural language search query")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results to return")

    doc_type: SDEIndexedDocumentType | None = Field(
        None,
        description="Filter results by document type",
    )


class SDESearchToolOutputSchema(SearchToolOutputSchema):
    """Output schema for SDE search results."""

    results: list[SDEDocument] = Field(..., description="List of matching documents from SDE")


# not basing it on SearchTool because this just a wrapper around SDE API
class SDESearchTool(BaseTool[SDESearchToolInputSchema, SDESearchToolOutputSchema]):
    """
    Search the NASA Science Discovery Engine for scientific documents and resources.

    This tool queries the SDE API to find datasets, documentation, publications,
    software, and other scientific resources across NASA's Science Mission Directorate
    divisions (Astrophysics, Earth Science, Heliophysics, Planetary Science, etc.).
    """

    input_schema = SDESearchToolInputSchema
    output_schema = SDESearchToolOutputSchema
    config_schema = SDESearchToolConfig

    async def _arun(self, params: SDESearchToolInputSchema) -> SDESearchToolOutputSchema:
        """Execute SDE search query and return formatted results."""
        # Build request payload
        request_body = {
            "search_term": params.query,
            "page": 1,
            "pageSize": params.limit,
            "search_type": self.config.search_type,
        }

        # Add optional filters
        filters = {}
        if self.config.division:
            filters["division"] = [self.config.division.value]
        if params.doc_type:
            filters["document_type"] = [params.doc_type.value]

        if filters:
            request_body["filters"] = filters

        logger.debug(f"Request body for SDE API: {request_body}")

        # Make API request
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                response = await client.post(
                    f"{self.config.base_url}/api/search",
                    json=request_body,
                )
                response.raise_for_status()
                data = response.json()
            except httpx.TimeoutException as e:
                msg = f"SDE API request timed out after {self.config.timeout}s"
                raise TimeoutError(msg) from e
            except httpx.HTTPStatusError as e:
                msg = f"SDE API returned error status {e.response.status_code}: {e.response.text}"
                raise RuntimeError(msg) from e
            except Exception as e:
                msg = f"Failed to query SDE API: {e}"
                raise RuntimeError(msg) from e

        # Parse response
        if not data.get("success", False):
            msg = f"SDE API returned unsuccessful response: {data}"
            raise RuntimeError(msg)

        documents = []
        for doc in data.get("documents", []):
            # Parse HitBase structure
            # Extract core fields
            score = doc.get("score") or doc.get("_score") or 0.0
            source_index = doc.get("index") or doc.get("_index") or "unknown"

            # Extract title with multiple fallbacks
            title = doc.get("title") or doc.get("name") or doc.get("id") or "Untitled"

            # Extract URL with fallbacks
            url = doc.get("url") or doc.get("readme_url") or ""

            # Extract snippet/description with priority order
            snippet = (
                doc.get("full_text")
                or doc.get("data_product_desc")
                or doc.get("description")
                or doc.get("relevant_content")
                or ""
            )

            # Extract metadata from HitBase common fields
            division = doc.get("division")
            doc_type = doc.get("document_type")

            # Determine source from api_source or index name
            source = doc.get("api_source") or source_index

            documents.append(
                SDEDocument(
                    query=params.query,
                    title=title,
                    content=snippet,
                    score=score,
                    url=url,
                    division=NASASMDDivision(division) if division else None,
                    doc_type=SDEIndexedDocumentType(doc_type) if doc_type else None,
                    source=source,
                )
            )

        return SDESearchToolOutputSchema(
            results=documents,
            extra={
                "total_count": data.get("total_count", 0),
                "query_used": params.query,
            },
        )
