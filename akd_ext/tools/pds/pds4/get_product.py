"""Get a single PDS product by its URN identifier."""

import os

from loguru import logger
from typing import Any

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.utils.pds4_client import PDS4Client, PDS4ClientError

_RELEVANT_KEYS = {
    "id", "type", "title", "description", "lid", "lidvid",
    "investigations", "observing_system_components", "targets",
    "pds:Time_Coordinates.pds:start_date_time",
    "pds:Time_Coordinates.pds:stop_date_time",
    "pds:Primary_Result_Summary.pds:processing_level",
    "ref_lid_instrument", "ref_lid_target",
    "ref_lid_instrument_host", "ref_lid_investigation",
    "metadata",
}


def _filter_product_response(raw: dict[str, Any]) -> dict[str, Any]:
    """Filter a raw product response to keep only relevant keys."""
    filtered: dict[str, Any] = {}
    for key, value in raw.items():
        if key in _RELEVANT_KEYS:
            filtered[key] = value
        elif key == "properties" and isinstance(value, dict):
            useful_props = {}
            for prop_key, prop_val in value.items():
                if any(term in prop_key.lower() for term in [
                    "title", "description", "processing_level",
                    "time_coordinates", "target", "instrument",
                    "investigation", "purpose", "collection_type",
                ]):
                    useful_props[prop_key] = prop_val
            if useful_props:
                filtered["properties"] = useful_props
    return filtered


class PDS4GetProductInputSchema(InputSchema):
    """Input schema for PDS4GetProductTool."""

    urn: str = Field(..., description="URN identifier for the product")


class PDS4GetProductOutputSchema(OutputSchema):
    """Output schema for PDS4GetProductTool."""

    product: dict[str, Any] = Field(..., description="Filtered product data from PDS4 API")


class PDS4GetProductToolConfig(BaseToolConfig):
    """Configuration for PDS4GetProductTool."""

    base_url: str = Field(
        default=os.getenv("PDS4_BASE_URL", "https://pds.mcp.nasa.gov/api/search/1/"),
        description="PDS4 API base URL (override with PDS4_BASE_URL env var)",
    )
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

    Returns filtered product data including identification, related context products,
    time coordinates, and processing level.

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

            filtered = _filter_product_response(result)
            return PDS4GetProductOutputSchema(product=filtered)

        except PDS4ClientError as e:
            logger.error(f"PDS4 client error in get_product: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_product: {e}")
            raise RuntimeError(f"Internal error during product retrieval: {e}") from e
