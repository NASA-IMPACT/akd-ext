"""Search PDS observational products with advanced filtering."""

import os

from loguru import logger

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import BaseModel, Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.pds4.types import PROCESSING_LEVEL
from akd_ext.tools.pds.utils.pds4_client import PDS4Client, PDS4ClientError


class ProductSummary(BaseModel):
    """Product item in search results."""

    id: str
    lid: str | None = None
    lidvid: str | None = None
    title: str | None = None
    ref_lid_target: str | None = None
    time_coordinates: dict | None = None
    processing_level: str | None = None
    bounding_coordinates: dict[str, float] | None = None


class PDS4SearchProductsInputSchema(InputSchema):
    """Input schema for PDS4SearchProductsTool."""

    keywords: str | None = Field(None, description="Search terms for product titles (e.g., 'HiRISE', 'spectra')")
    start_time: str | None = Field(
        None, description="Start of time range in ISO 8601 format (e.g., '2020-01-01T00:00:00Z')"
    )
    end_time: str | None = Field(
        None, description="End of time range in ISO 8601 format (e.g., '2021-01-01T00:00:00Z')"
    )
    processing_level: PROCESSING_LEVEL | None = Field(None, description="Filter by calibration level")
    bbox_north: float | None = Field(None, ge=-90, le=90, description="North bounding coordinate (latitude, -90 to 90)")
    bbox_south: float | None = Field(None, ge=-90, le=90, description="South bounding coordinate (latitude, -90 to 90)")
    bbox_east: float | None = Field(
        None, ge=-180, le=180, description="East bounding coordinate (longitude, -180 to 180)"
    )
    bbox_west: float | None = Field(
        None, ge=-180, le=180, description="West bounding coordinate (longitude, -180 to 180)"
    )
    ref_lid_target: str | None = Field(
        None, description="URN identifier for target (e.g., 'urn:nasa:pds:context:target:planet.mars')"
    )
    limit: int = Field(100, ge=0, le=100, description="Maximum results to return (default 100)")


class PDS4SearchProductsOutputSchema(OutputSchema):
    """Output schema for PDS4SearchProductsTool."""

    total_hits: int = Field(..., description="Total number of matching products")
    query_time_ms: int | None = Field(None, description="Query execution time in milliseconds")
    query: str | None = Field(None, description="The query string that was executed")
    limit: int = Field(..., description="Number of results requested")
    products: list[ProductSummary] = Field(default_factory=list, description="List of matching products with metadata")


class PDS4SearchProductsToolConfig(BaseToolConfig):
    """Configuration for PDS4SearchProductsTool."""

    base_url: str = Field(
        default=os.getenv("PDS4_BASE_URL", "https://pds.mcp.nasa.gov/api/search/1/"),
        description="PDS4 API base URL (override with PDS4_BASE_URL env var)",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts for failed requests")


@mcp_tool
class PDS4SearchProductsTool(BaseTool[PDS4SearchProductsInputSchema, PDS4SearchProductsOutputSchema]):
    """Search PDS observational products with advanced filtering.

    This tool searches for actual science data products in the NASA Planetary Data System (PDS4).
    Supports temporal, processing level, spatial (bounding box), and target filters.

    Use this tool for finding specific observational data products like images, spectra, and
    other scientific measurements.

    Processing Levels:
    - Raw: Unprocessed instrument data as received from spacecraft
    - Calibrated: Instrument effects removed, science-ready data
    - Derived: Higher-level data products (maps, mosaics, etc.)

    Bounding Box Coordinates:
    - Latitude (North/South): -90 to 90 degrees
    - Longitude (East/West): -180 to 180 degrees
    - Products that intersect the query box will be returned
    """

    input_schema = PDS4SearchProductsInputSchema
    output_schema = PDS4SearchProductsOutputSchema
    config_schema = PDS4SearchProductsToolConfig

    async def _arun(self, params: PDS4SearchProductsInputSchema) -> PDS4SearchProductsOutputSchema:
        """Execute the product search.

        Args:
            params: Input parameters for the search

        Returns:
            Search results with products and metadata

        Raises:
            PDS4ClientError: If the API request fails
            ValueError: If coordinate values are invalid
        """
        try:
            # Create client and perform search
            async with PDS4Client(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                response = await client.search_products_advanced(
                    keywords=params.keywords,
                    start_time=params.start_time,
                    end_time=params.end_time,
                    processing_level=params.processing_level,
                    bbox_north=params.bbox_north,
                    bbox_south=params.bbox_south,
                    bbox_east=params.bbox_east,
                    bbox_west=params.bbox_west,
                    ref_lid_target=params.ref_lid_target,
                    limit=params.limit,
                )

            # Format response
            products: list[ProductSummary] = []
            for product in response.data:
                processing_level_val = None
                bbox = None

                if product.properties:
                    props = product.properties
                    if "pds:Primary_Result_Summary.pds:processing_level" in props:
                        level = props["pds:Primary_Result_Summary.pds:processing_level"]
                        processing_level_val = level[0] if isinstance(level, list) else level

                    # Build bounding coordinates
                    bbox_dict: dict[str, float] = {}
                    for coord_key, bbox_key in [
                        ("cart:Bounding_Coordinates.cart:north_bounding_coordinate", "north"),
                        ("cart:Bounding_Coordinates.cart:south_bounding_coordinate", "south"),
                        ("cart:Bounding_Coordinates.cart:east_bounding_coordinate", "east"),
                        ("cart:Bounding_Coordinates.cart:west_bounding_coordinate", "west"),
                    ]:
                        if coord_key in props:
                            val = props[coord_key]
                            val = val[0] if isinstance(val, list) else val
                            if val and val != "null":
                                bbox_dict[bbox_key] = float(val) if isinstance(val, str) else val
                    if bbox_dict:
                        bbox = bbox_dict

                product_summary = ProductSummary(
                    id=product.id,
                    lid=product.lid,
                    lidvid=product.lidvid,
                    title=product.title,
                    ref_lid_target=product.ref_lid_target,
                    time_coordinates=(
                        product.time_coordinates.model_dump(exclude_none=True) if product.time_coordinates else None
                    ),
                    processing_level=processing_level_val,
                    bounding_coordinates=bbox,
                )
                products.append(product_summary)

            return PDS4SearchProductsOutputSchema(
                total_hits=response.summary.hits,
                query_time_ms=response.summary.took,
                query=response.summary.q,
                limit=params.limit,
                products=products,
            )

        except PDS4ClientError as e:
            logger.error(f"PDS4 client error in search_products: {e}")
            raise
        except ValueError as e:
            # Re-raise validation errors (e.g., invalid coordinates)
            logger.error(f"Validation error in search_products: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in search_products: {e}")
            raise RuntimeError(f"Internal error during product search: {e}") from e
