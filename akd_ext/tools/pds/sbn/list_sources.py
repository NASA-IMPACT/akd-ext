"""List available CATCH data sources with their current status."""

import os

from loguru import logger

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import BaseModel, Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.utils.sbn_client import SBNCatchClient, SBNCatchClientError


class SBNSourceSummary(BaseModel):
    """Source item in list_sources results."""

    source: str
    source_name: str | None = None
    count: int
    start_date: str | None = None
    stop_date: str | None = None
    nights: int | None = None
    updated: str | None = None


class SBNListSourcesInputSchema(InputSchema):
    """Input schema for SBNListSourcesTool.

    This tool requires no input parameters.
    """

    pass


class SBNListSourcesOutputSchema(OutputSchema):
    """Output schema for SBNListSourcesTool."""

    total_sources: int = Field(..., description="Total number of data sources available")
    sources: list[SBNSourceSummary] = Field(default_factory=list, description="List of data sources with metadata")


class SBNListSourcesToolConfig(BaseToolConfig):
    """Configuration for SBNListSourcesTool."""

    base_url: str = Field(
        default=os.getenv("SBN_BASE_URL", "https://catch-api.astro.umd.edu/"),
        description="CATCH API base URL (override with SBN_BASE_URL env var)",
    )
    timeout: float = Field(default=60.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts for failed requests")


@mcp_tool
class SBNListSourcesTool(BaseTool[SBNListSourcesInputSchema, SBNListSourcesOutputSchema]):
    """List available CATCH data sources with their current status.

    This tool queries the SBN CATCH API to retrieve information about all available
    astronomical survey data sources. Each source represents a different survey that
    has observed comets and asteroids.

    The response includes for each source:
    - source: Short identifier (e.g., "neat_palomar_tricam", "ps1dr2")
    - source_name: Human-readable name
    - count: Number of observations available
    - start_date/stop_date: Temporal coverage range
    - nights: Number of observing nights
    - updated: Last update timestamp

    Use this tool to:
    1. Discover available data sources before searching
    2. Check temporal coverage and observation counts
    3. Verify source availability and last update times
    """

    input_schema = SBNListSourcesInputSchema
    output_schema = SBNListSourcesOutputSchema
    config_schema = SBNListSourcesToolConfig

    async def _arun(self, params: SBNListSourcesInputSchema) -> SBNListSourcesOutputSchema:
        """Execute the tool to list available data sources."""
        try:
            async with SBNCatchClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                response = await client.list_sources()

            if response.error:
                logger.error(f"CATCH API returned error: {response.error}")
                raise SBNCatchClientError(response.error)

            sources = [
                SBNSourceSummary(
                    source=s.source,
                    source_name=s.source_name,
                    count=s.count,
                    start_date=s.start_date,
                    stop_date=s.stop_date,
                    nights=s.nights,
                    updated=s.updated,
                )
                for s in response.sources
            ]

            return SBNListSourcesOutputSchema(
                total_sources=len(sources),
                sources=sources,
            )

        except SBNCatchClientError as e:
            logger.error(f"SBN client error in list_sources: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in list_sources: {e}")
            raise RuntimeError(f"Internal error: {e}") from e
