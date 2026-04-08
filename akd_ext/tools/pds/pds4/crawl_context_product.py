"""Crawl a single PDS Context product and return other PDS Context products it is associated with."""

import os

from loguru import logger

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.utils.pds4_client import PDS4Client, PDS4ClientError


class PDS4CrawlContextProductInputSchema(InputSchema):
    """Input schema for PDS4CrawlContextProductTool."""

    urn: str = Field(..., description="URN identifier for the context product to crawl")


class PDS4CrawlContextProductOutputSchema(OutputSchema):
    """Output schema for PDS4CrawlContextProductTool."""

    investigations: dict[str, dict] = Field(
        default_factory=dict, description="Related investigation products keyed by URN"
    )
    observing_system_components: dict[str, dict] = Field(
        default_factory=dict, description="Related instrument/host products keyed by URN"
    )
    targets: dict[str, dict] = Field(default_factory=dict, description="Related target products keyed by URN")
    errors: list[str] | None = Field(None, description="List of any fetch errors encountered")


class PDS4CrawlContextProductToolConfig(BaseToolConfig):
    """Configuration for PDS4CrawlContextProductTool."""

    base_url: str = Field(
        default=os.getenv("PDS4_BASE_URL", "https://pds.mcp.nasa.gov/api/search/1/"),
        description="PDS4 API base URL (override with PDS4_BASE_URL env var)",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


@mcp_tool
class PDS4CrawlContextProductTool(BaseTool[PDS4CrawlContextProductInputSchema, PDS4CrawlContextProductOutputSchema]):
    """Crawl a single PDS Context product and return other PDS Context products it is associated with.

    Example: Mars 2020: Perseverance Rover (Investigation) is associated with Mars (Target)
    and Mastcam (Instrument), so it returns Mars and Mastcam.

    **WARNING: Takes a long time to run and performs several sequential API calls. Use wisely.**

    This tool fetches a context product and then concurrently fetches all related products
    (investigations, instruments, instrument hosts, and targets).

    Each related product includes:
    - id: URN identifier
    - title: Product title
    - description: Product description (if available)
    """

    input_schema = PDS4CrawlContextProductInputSchema
    output_schema = PDS4CrawlContextProductOutputSchema
    config_schema = PDS4CrawlContextProductToolConfig

    async def _arun(self, params: PDS4CrawlContextProductInputSchema) -> PDS4CrawlContextProductOutputSchema:
        """Execute the context product crawl."""
        try:
            async with PDS4Client(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                results = await client.crawl_context_product(params.urn)

            return PDS4CrawlContextProductOutputSchema(
                investigations=results.get("investigations", {}),
                observing_system_components=results.get("observing_system_components", {}),
                targets=results.get("targets", {}),
                errors=results.get("errors"),
            )

        except PDS4ClientError as e:
            logger.error(f"PDS4 client error in crawl_context_product: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in crawl_context_product: {e}")
            raise RuntimeError(f"Internal error during context product crawl: {e}") from e
