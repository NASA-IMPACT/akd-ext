"""Get a single PDS product by its URN identifier."""

import logging
from typing import Any

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.utils.pds4_client import PDS4Client, PDS4ClientError

logger = logging.getLogger(__name__)


class PDS4GetProductInputSchema(InputSchema):
    """Input schema for PDS4GetProductTool."""

    urn: str = Field(..., description="URN identifier for the product")


class PDS4GetProductOutputSchema(OutputSchema):
    """Output schema for PDS4GetProductTool."""

    product: dict[str, Any] = Field(..., description="Raw product data from PDS4 API")


class PDS4GetProductToolConfig(BaseToolConfig):
    """Configuration for PDS4GetProductTool."""

    base_url: str = Field(default="https://pds.mcp.nasa.gov/api/search/1/", description="PDS4 API base URL")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


@mcp_tool
class PDS4GetProductTool(BaseTool[PDS4GetProductInputSchema, PDS4GetProductOutputSchema]):
    """Get a single PDS product by its URN identifier.

    Retrieves detailed information about a specific product from the PDS4 registry.
    The URN can be obtained from other search tools or known in advance.

    Example URNs:
    - urn:nasa:pds:context:investigation:mission.juno
    - urn:nasa:pds:context:target:planet.mars
    - urn:nasa:pds:cassini_iss

    The returned product data includes all available metadata fields for the product,
    including identification, investigation areas, time coordinates, and more.

    """

    input_schema = PDS4GetProductInputSchema
    output_schema = PDS4GetProductOutputSchema
    config_schema = PDS4GetProductToolConfig

    async def _arun(self, params: PDS4GetProductInputSchema) -> PDS4GetProductOutputSchema:
        """Execute the product retrieval."""
        try:
            async with PDS4Client(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                result = await client.get_product(params.urn)

            return PDS4GetProductOutputSchema(product=result)

        except PDS4ClientError as e:
            logger.error(f"PDS4 client error in get_product: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_product: {e}")
            raise RuntimeError(f"Internal error during product retrieval: {e}") from e
