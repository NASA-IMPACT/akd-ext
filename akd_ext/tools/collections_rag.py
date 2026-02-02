"""
STAC Collections RAG tool for semantic search over Earth science data collections.

This tool uses vector embeddings (via Ollama) and LanceDB to perform semantic
search over STAC collection metadata, helping users find relevant Earth science
datasets based on natural language queries.
"""

import os
from datetime import datetime, timezone
from typing import Literal

import httpx
import lancedb
from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field
from loguru import logger

from akd_ext.mcp import mcp_tool


class CollectionsRagToolConfig(BaseToolConfig):
    """Configuration for the Collections RAG Tool."""

    db_path: str = Field(
        default=os.getenv("COLLECTIONS_RAG_DB_PATH", "/tmp/veda_collections.lancedb"),
        description="Path to the LanceDB database containing collection embeddings",
    )
    ollama_url: str = Field(
        default=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        description="Base URL for the Ollama embeddings API",
    )
    embedding_model: str = Field(
        default=os.getenv("COLLECTIONS_RAG_MODEL", "nomic-embed-text"),
        description="Name of the Ollama embedding model to use",
    )
    timeout: float = Field(
        default=60.0,
        description="HTTP request timeout for embedding requests in seconds",
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Default number of results to return",
    )


class CollectionMatchInfo(OutputSchema):
    """Information about a matched collection including coverage overlap."""

    id: str = Field(..., description="STAC collection ID")
    title: str | None = Field(None, description="Collection title")
    spatial_overlap: bool = Field(
        default=True,
        description="Whether the collection spatially overlaps the requested bbox",
    )
    temporal_overlap: bool = Field(
        default=True,
        description="Whether the collection temporally overlaps the requested time range",
    )


class CollectionsRagInputSchema(InputSchema):
    """Input schema for the Collections RAG tool."""

    query: str = Field(
        ...,
        description="Natural language description of the data you're looking for (e.g., 'NO2 air quality', 'sea surface temperature')",
    )
    bbox: list[float] | None = Field(
        None,
        description="Optional bounding box [west, south, east, north] to check spatial coverage",
    )
    datetime: str | None = Field(
        None,
        description="Optional ISO-8601 datetime range (e.g., '2021-10-01/2021-12-31') to check temporal coverage",
    )
    limit: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Maximum number of collections to return",
    )


class CollectionsRagOutputSchema(OutputSchema):
    """Output schema for the Collections RAG tool."""

    collections: list[str] = Field(
        default_factory=list,
        description="List of matched collection IDs",
    )
    matches: list[CollectionMatchInfo] = Field(
        default_factory=list,
        description="Detailed match information including spatial/temporal overlap flags",
    )
    error: str | None = Field(
        None,
        description="Error message if search failed",
    )


def _bboxes_overlap(bbox1: list[float], bbox2: list[float]) -> bool:
    """Check if two bounding boxes overlap.
    
    Args:
        bbox1: First bounding box as [west, south, east, north]
        bbox2: Second bounding box in the same format
    
    Returns:
        True if the boxes overlap, False otherwise
    """
    if len(bbox1) < 4 or len(bbox2) < 4:
        return False
    
    w1, s1, e1, n1 = bbox1[:4]
    w2, s2, e2, n2 = bbox2[:4]
    
    # Two boxes do NOT overlap if one is entirely to the left, right, above, or below
    return not (e1 < w2 or e2 < w1 or n1 < s2 or n2 < s1)


def _parse_iso_date(s: str | None) -> datetime | None:
    """Parse ISO-8601 date string to UTC-aware datetime."""
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, AttributeError):
        return None


def _intervals_overlap(interval: list[str | None], start: str, end: str) -> bool:
    """Check if a collection's temporal interval overlaps with a requested time range."""
    if not interval or len(interval) < 2:
        return False
    
    col_start = _parse_iso_date(interval[0])
    col_end = _parse_iso_date(interval[1])
    req_start = _parse_iso_date(start)
    req_end = _parse_iso_date(end)
    
    # Open-ended intervals: assume overlap if we can't determine otherwise
    if (req_start is None and req_end is None) or (col_start is None and col_end is None):
        return True
    
    # Collection ends before requested range starts → no overlap
    if col_end and req_start and col_end < req_start:
        return False
    
    # Collection starts after requested range ends → no overlap
    if col_start and req_end and col_start > req_end:
        return False
    
    return True


@mcp_tool
class CollectionsRagTool(BaseTool[CollectionsRagInputSchema, CollectionsRagOutputSchema]):
    """
    Search for relevant STAC collections using semantic search.

    This tool performs vector similarity search over STAC collection metadata
    using embeddings generated by Ollama. It helps users find Earth science
    datasets that match their natural language queries.

    The tool also checks spatial and temporal overlap between the user's
    requested extent and each collection's coverage, returning flags that
    indicate whether the collection actually covers the area/time of interest.

    Input parameters (query-time, LLM-controllable):
    - query: Natural language description of desired data (e.g., "NO2 air quality")
    - bbox: Optional bounding box [west, south, east, north] to check spatial coverage
    - datetime: Optional ISO-8601 range (e.g., "2021-10-01/2021-12-31") for temporal coverage
    - limit: Maximum number of results (1-20, default: 3)

    Configuration parameters (instance-time, user-controlled):
    - db_path: Path to LanceDB database with collection embeddings
    - ollama_url: Ollama API URL for generating query embeddings
    - embedding_model: Model name for embeddings (default: nomic-embed-text)
    - timeout: HTTP timeout for embedding requests (default: 60s)

    Returns:
    - collections: List of matched collection IDs
    - matches: Detailed info with spatial_overlap and temporal_overlap flags
    - error: Error message if search failed
    """

    input_schema = CollectionsRagInputSchema
    output_schema = CollectionsRagOutputSchema
    config_schema = CollectionsRagToolConfig

    async def _embed_query(self, query: str) -> list[float]:
        """Generate embedding vector for a query using Ollama."""
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                f"{self.config.ollama_url.rstrip('/')}/api/embeddings",
                json={"model": self.config.embedding_model, "prompt": query},
            )
            response.raise_for_status()
            embedding = response.json().get("embedding")
            if not embedding:
                raise ValueError(f"No embedding returned from Ollama for query: {query[:100]}")
            return [float(x) for x in embedding]

    async def _arun(self, params: CollectionsRagInputSchema) -> CollectionsRagOutputSchema:
        """Execute semantic search over collections and return matches."""
        try:
            # Generate query embedding
            logger.debug(f"Generating embedding for query: {params.query[:100]}")
            query_vector = await self._embed_query(params.query)

            # Connect to LanceDB and search
            db = lancedb.connect(self.config.db_path)
            table = db.open_table("veda_collections")
            
            # Perform vector similarity search
            results = (
                table.search(query_vector, vector_column_name="vector")
                .metric("cosine")
                .limit(params.limit)
                .to_list()
            )

            # Parse datetime range if provided
            req_start, req_end = None, None
            if params.datetime and "/" in params.datetime:
                parts = params.datetime.split("/")
                if len(parts) == 2:
                    req_start, req_end = parts[0].strip(), parts[1].strip()

            # Process results and check overlaps
            matches: list[CollectionMatchInfo] = []
            collection_ids: list[str] = []

            for r in results:
                if not r.get("id"):
                    continue

                meta = r.get("meta") or {}
                spatial_bboxes = meta.get("extent_spatial_bbox")
                temporal_intervals = meta.get("extent_temporal_interval")

                # Check spatial overlap if bbox provided
                spatial_overlap = True
                if params.bbox and spatial_bboxes:
                    spatial_overlap = any(
                        _bboxes_overlap(params.bbox, sb)
                        for sb in spatial_bboxes
                        if sb
                    )

                # Check temporal overlap if datetime range provided
                temporal_overlap = True
                if req_start and req_end and temporal_intervals:
                    temporal_overlap = any(
                        _intervals_overlap(ti, req_start, req_end)
                        for ti in temporal_intervals
                        if ti
                    )

                collection_ids.append(r["id"])
                matches.append(
                    CollectionMatchInfo(
                        id=r["id"],
                        title=meta.get("title"),
                        spatial_overlap=spatial_overlap,
                        temporal_overlap=temporal_overlap,
                    )
                )

            return CollectionsRagOutputSchema(
                collections=collection_ids,
                matches=matches,
                error=None,
            )

        except FileNotFoundError as e:
            msg = f"LanceDB database not found at {self.config.db_path}. Run index refresh first."
            logger.error(msg)
            return CollectionsRagOutputSchema(collections=[], matches=[], error=msg)

        except httpx.TimeoutException as e:
            msg = f"Ollama embedding request timed out after {self.config.timeout}s"
            logger.error(msg)
            return CollectionsRagOutputSchema(collections=[], matches=[], error=msg)

        except Exception as e:
            msg = f"Collections search failed: {e}"
            logger.error(msg)
            return CollectionsRagOutputSchema(collections=[], matches=[], error=msg)
