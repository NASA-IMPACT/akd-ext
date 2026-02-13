"""Count products matching criteria without retrieving them."""

import os

from loguru import logger

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.ode.types import TargetType
from akd_ext.tools.pds.utils.ode_client import ODEClient, ODEClientError


class ODECountProductsInputSchema(InputSchema):
    """Input schema for ODECountProductsTool."""

    target: TargetType = Field(..., description="Planetary body to search")
    ihid: str = Field(..., description="Instrument Host ID (e.g., 'MRO', 'LRO', 'MESS')")
    iid: str = Field(..., description="Instrument ID (e.g., 'HIRISE', 'CTX', 'LROC', 'MDIS')")
    pt: str = Field(..., description="Product Type (e.g., 'RDRV11', 'EDR')")
    minlat: float | None = Field(None, ge=-90, le=90, description="Minimum latitude filter")
    maxlat: float | None = Field(None, ge=-90, le=90, description="Maximum latitude filter")
    westlon: float | None = Field(None, ge=0, le=360, description="Western longitude filter")
    eastlon: float | None = Field(None, ge=0, le=360, description="Eastern longitude filter")
    minobtime: str | None = Field(
        None, description="Minimum observation time in UTC format (e.g., '2020-01-01' or '2020-01-01T00:00:00')"
    )
    maxobtime: str | None = Field(
        None, description="Maximum observation time in UTC format (e.g., '2020-01-31' or '2020-01-31T23:59:59')"
    )


class ODECountProductsOutputSchema(OutputSchema):
    """Output schema for ODECountProductsTool."""

    status: str = Field(..., description="Response status ('success' or 'error')")
    target: str | None = Field(None, description="Planetary body that was searched")
    instrument_host: str | None = Field(None, description="Instrument Host ID")
    instrument: str | None = Field(None, description="Instrument ID")
    product_type: str | None = Field(None, description="Product Type")
    count: int = Field(..., description="Number of products matching criteria")
    error: str | None = Field(None, description="Error message if status is 'error'")


class ODECountProductsToolConfig(BaseToolConfig):
    """Configuration for ODECountProductsTool."""

    base_url: str = Field(
        default=os.getenv("ODE_BASE_URL", "https://oderest.rsl.wustl.edu/live2/"),
        description="ODE API base URL (override with ODE_BASE_URL env var)",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts for failed requests")


@mcp_tool
class ODECountProductsTool(BaseTool[ODECountProductsInputSchema, ODECountProductsOutputSchema]):
    """Count products matching criteria without retrieving them.

    This tool provides a fast count of products matching your search criteria without
    returning the actual product data. This is useful for:
    - Understanding data availability before running full searches
    - Determining if you need to narrow your search criteria
    - Checking if data exists for a specific region/time period

    Note: Unlike ODESearchProductsTool, this tool requires all three identifiers
    (ihid, iid, pt) to be specified - it does not support searching by pdsid alone.
    """

    input_schema = ODECountProductsInputSchema
    output_schema = ODECountProductsOutputSchema
    config_schema = ODECountProductsToolConfig

    async def _arun(self, params: ODECountProductsInputSchema) -> ODECountProductsOutputSchema:
        """Execute the product count query.

        Args:
            params: Input parameters for the count query

        Returns:
            Count of products matching the criteria

        Raises:
            ODEClientError: If the API request fails
        """
        try:
            async with ODEClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                response = await client.count_products(
                    target=params.target,
                    ihid=params.ihid,
                    iid=params.iid,
                    pt=params.pt,
                    minlat=params.minlat,
                    maxlat=params.maxlat,
                    westlon=params.westlon,
                    eastlon=params.eastlon,
                    minobtime=params.minobtime,
                    maxobtime=params.maxobtime,
                )

            if response.status == "ERROR":
                return ODECountProductsOutputSchema(
                    status="error",
                    count=0,
                    error=response.error,
                )

            return ODECountProductsOutputSchema(
                status="success",
                target=params.target,
                instrument_host=params.ihid,
                instrument=params.iid,
                product_type=params.pt,
                count=response.count,
            )

        except ODEClientError as e:
            logger.error(f"ODE client error in count_products: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in count_products: {e}")
            raise RuntimeError(f"Internal error during product count: {e}") from e
