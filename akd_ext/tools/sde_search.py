"""
NASA Science Discovery Engine (SDE) search tool.

This tool wraps the SDE Elastic Wrapper API to enable searching NASA's Science
Discovery Engine for relevant scientific documents, datasets, and resources using
natural language queries.
"""

import asyncio
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
    validate_urls: bool = Field(
        default=False,
        description="Validate document URLs with HTTP HEAD requests to filter out 404s",
    )
    url_check_timeout: float = Field(
        default=5.0,
        description="Timeout for individual URL validation requests in seconds",
    )
    result_multiplier: float = Field(
        default=2.0,
        ge=1.0,
        le=10.0,
        description="Multiplier for initial results to fetch (e.g., 2.0 fetches 2x limit from API before filtering)",
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


class SDESearchTool(BaseTool[SDESearchToolInputSchema, SDESearchToolOutputSchema]):
    """
    Search NASA's Science Discovery Engine (SDE) using the unified /api/search endpoint.

    The Science Discovery Engine (SDE) is NASA's centralized search platform that indexes
    scientific data, publications, and resources from multiple NASA data sources including
    CMR (Earth observation), PDS (planetary science), SPASE (heliophysics), GCN (astronomy),
    code repositories, and documentation.

    This tool uses the /api/search endpoint which provides cross-source search with vector, keyword and hybrid
    (vector + keyword) semantic search capabilities, returning unified results across all
    indexed NASA content.

    Input parameters (query-time, LLM-controllable):
    - query: Natural language search query (e.g., "Mars rover spectroscopy data")
    - limit: Maximum number of results to return (1-100, default: 10)
    - doc_type: Optional filter by document type (Data, Documentation, Software and Tools,
                Images, Missions and Instruments)

    Configuration parameters (instance-time, user-controlled):
    - search_type: Search mode - "hybrid" (default, vector+keyword), "vector" (semantic only),
                   or "keyword" (text-based only). Fixed at tool instantiation.
    - division: Optional NASA SMD division filter (Astrophysics, Earth Science, Heliophysics,
                Planetary Science). If set, all searches are scoped to this division.
    - validate_urls: Whether to validate result URLs with HTTP HEAD requests (default: False).
                     Filters out inaccessible resources.
    - result_multiplier: When validate_urls=True, fetches this multiple of the limit to account
                        for filtered results (default: 2.0, range: 1.0-10.0)
    - timeout: HTTP request timeout in seconds (default: 30.0)
    - url_check_timeout: Timeout for URL validation requests in seconds (default: 5.0)

    Returns documents with:
    - title: Document or dataset title
    - url: Direct link to the resource
    - content: Description, abstract, or relevant text snippet
    - score: Relevance score from search engine
    - division: NASA SMD division (Astrophysics, Earth Science, Heliophysics, Planetary Science)
    - doc_type: Type of document/resource
    - source: Origin data source (sde-cmr, sde-pds4, sde-web, sde-code, etc.)
    """

    input_schema = SDESearchToolInputSchema
    output_schema = SDESearchToolOutputSchema
    config_schema = SDESearchToolConfig

    async def _check_url_exists(self, url: str) -> bool:
        """
        Check if a URL is accessible using HTTP HEAD request.

        Args:
            url: The URL to check

        Returns:
            bool: True if URL is accessible (status < 400), False otherwise
        """
        if not url:
            return False

        try:
            async with httpx.AsyncClient(timeout=self.config.url_check_timeout, follow_redirects=True) as client:
                response = await client.head(url)
                return response.status_code < 400
        except Exception as e:
            logger.debug(f"URL check failed for {url}: {e}")
            return False

    def _parse_document(self, doc: dict, query: str) -> SDEDocument:
        """
        Parse a single document from the SDE API response.

        Args:
            doc: Raw document dictionary from the API response
            query: The search query that produced this result

        Returns:
            SDEDocument: Parsed and structured document
        """
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

        return SDEDocument(
            query=query,
            title=title,
            content=snippet,
            score=score,
            url=url,
            division=NASASMDDivision(division) if division else None,
            doc_type=SDEIndexedDocumentType(doc_type) if doc_type else None,
            source=source,
        )

    async def _arun(self, params: SDESearchToolInputSchema) -> SDESearchToolOutputSchema:
        """Execute SDE search query and return formatted results."""
        # Calculate fetch size: if URL validation is enabled, fetch more to account for filtering
        fetch_size = params.limit
        if self.config.validate_urls:
            fetch_size = min(int(params.limit * self.config.result_multiplier), 100)
            logger.debug(
                f"Fetching {fetch_size} results (limit={params.limit}, multiplier={self.config.result_multiplier})"
            )

        # Build request payload
        request_body = {
            "search_term": params.query,
            "page": 1,
            "pageSize": fetch_size,
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

        documents = [self._parse_document(doc, params.query) for doc in data.get("documents", [])]

        # Validate URLs if configured
        if self.config.validate_urls:
            logger.debug(f"Validating {len(documents)} document URLs")
            # Check all URLs in parallel using asyncio.gather
            url_checks = await asyncio.gather(
                *[self._check_url_exists(doc.url) for doc in documents],
                return_exceptions=True,
            )

            # Filter out documents with invalid URLs
            validated_documents = []
            for doc, is_valid in zip(documents, url_checks, strict=False):
                # Handle exceptions as invalid
                if isinstance(is_valid, Exception):
                    logger.debug(f"URL validation exception for {doc.url}: {is_valid}")
                    continue
                if is_valid:
                    validated_documents.append(doc)
                else:
                    logger.debug(f"Filtered out document with inaccessible URL: {doc.url}")

            documents = validated_documents
            logger.debug(f"Retained {len(documents)} documents after URL validation")

        # Limit results to requested limit (in case we fetched more for validation)
        final_documents = documents[: params.limit]

        if len(documents) > params.limit:
            logger.debug(f"Truncating {len(documents)} results to requested limit of {params.limit}")

        return SDESearchToolOutputSchema(
            results=final_documents,
            extra={
                "total_count": data.get("total_count", 0),
                "query_used": params.query,
                "filtered_count": len(final_documents) if self.config.validate_urls else None,
                "requested_limit": params.limit,
            },
        )
