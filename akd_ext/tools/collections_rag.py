"""Collections RAG tool: search STAC collections via the external RAG service."""
from __future__ import annotations

import os

import httpx
from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from loguru import logger
from pydantic import Field

from akd_ext.mcp import mcp_tool


class CollectionsRAGToolConfig(BaseToolConfig):
    """Configuration for the Collections RAG Search Tool."""

    base_url: str = Field(
        default=os.getenv(
            "COLLECTIONS_RAG_URL",
            "https://k8s-eiellm-eiellmng-3bfff7cd13-5b11596fb1756b2e.elb.us-west-2.amazonaws.com",
        ),
        description="Base URL for the collections RAG service",
    )


class CollectionMatch(OutputSchema):
    """A single collection match with extent metadata."""

    id: str = Field(..., description="Collection ID")
    title: str | None = Field(None, description="Collection title")
    description: str | None = Field(None, description="Collection description")
    collection_concept_id: str | None = Field(None, description="CMR concept ID")
    spatial_bbox: list[list[float]] | None = Field(None, description="Spatial bounding boxes")
    temporal_interval: list[list[str | None]] | None = Field(None, description="Temporal intervals")
    spatial_overlap: bool = Field(..., description="Whether the collection spatially overlaps the query bbox")
    temporal_overlap: bool = Field(..., description="Whether the collection temporally overlaps the query range")
    cosine_distance: float | None = Field(None, description="Cosine distance from query (None for CMR results)")
    cosine_similarity: float | None = Field(None, description="Cosine similarity to query (None for CMR results)")
    source: str = Field(..., description="Result source: 'veda' or 'cmr'")
    cmr_rank: int | None = Field(None, description="Position in CMR results (None for VEDA)")
    time_density: str | None = Field(None, description="Temporal density: 'day', 'month', 'year', or None")


class CollectionsRAGToolInputSchema(InputSchema):
    """Input schema for collections RAG search."""

    query: str = Field(..., description="Semantic search query for finding relevant collections")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results to return")
    bbox: list[float] | None = Field(
        None, description="Optional bounding box [west, south, east, north] for spatial overlap check"
    )
    datetime_range: str | None = Field(
        None, description="Optional ISO-8601 range 'start/end' for temporal overlap check"
    )


class CollectionsRAGToolOutputSchema(OutputSchema):
    """Output schema for collections RAG search."""

    matches: list[CollectionMatch] = Field(..., description="Ranked collection matches")


@mcp_tool
class CollectionsRAGTool(BaseTool[CollectionsRAGToolInputSchema, CollectionsRAGToolOutputSchema]):
    """
    Search for relevant STAC collections using semantic similarity.

    Calls the external collections RAG service which bundles LanceDB +
    embedding model + CMR fallback. Returns ranked collection matches
    with spatial/temporal overlap flags.

    Input parameters (query-time, LLM-controllable):
    - query: Semantic search query (e.g. "methane plumes")
    - top_k: Number of results (1-50, default 5)
    - bbox: Optional [west, south, east, north] for spatial overlap checking
    - datetime_range: Optional 'start/end' ISO-8601 range for temporal overlap checking

    Configuration parameters (instance-time, user-controlled):
    - base_url: Base URL for the collections RAG service

    Returns matches with:
    - id, title, description: Collection metadata
    - spatial_overlap / temporal_overlap: Whether the collection overlaps the query area/time
    - cosine_distance / cosine_similarity: Embedding similarity (VEDA results only)
    - source: 'veda' or 'cmr'
    - cmr_rank: CMR relevance position (CMR results only)
    - time_density: Temporal resolution
    """

    input_schema = CollectionsRAGToolInputSchema
    output_schema = CollectionsRAGToolOutputSchema
    config_schema = CollectionsRAGToolConfig

    async def _arun(self, params: CollectionsRAGToolInputSchema) -> CollectionsRAGToolOutputSchema:
        """Execute collections search via the external RAG service."""
        url = f"{self.config.base_url.rstrip('/')}/agent/search/collections"

        request_body: dict = {
            "query": params.query,
            "top_k": params.top_k,
        }
        if params.bbox is not None:
            request_body["bbox"] = params.bbox
        if params.datetime_range is not None:
            request_body["datetime_range"] = params.datetime_range

        logger.debug(f"Collections RAG request: {request_body}")

        async with httpx.AsyncClient(timeout=30, verify=False) as client:
            try:
                response = await client.post(url, json=request_body)
                response.raise_for_status()
                data = response.json()
            except httpx.TimeoutException as e:
                msg = f"Collections RAG service timed out after 30s"
                raise TimeoutError(msg) from e
            except httpx.HTTPStatusError as e:
                msg = f"Collections RAG service returned {e.response.status_code}: {e.response.text}"
                raise RuntimeError(msg) from e

        matches = [CollectionMatch(**item) for item in data]

        logger.debug(f"Collections RAG returned {len(matches)} matches")

        return CollectionsRAGToolOutputSchema(matches=matches)
