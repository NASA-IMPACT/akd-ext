"""Search ODE planetary data products with geographic and temporal filtering."""

import logging
from typing import Annotated

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import BaseModel, Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.ode.types import TargetType
from akd_ext.tools.pds.utils.ode_client import ODEClient, ODEClientError

logger = logging.getLogger(__name__)

# Response size limits to prevent overwhelming LLM context windows
MAX_SEARCH_LIMIT = 10  # Max products per search
MAX_FILES_PER_PRODUCT = 3  # Max files shown per product


class ODEProductFileSummary(BaseModel):
    """File item in product search results."""

    name: str | None = None
    url: str | None = None
    type: str | None = None
    size_kb: str | None = None


class ODEProductSummary(BaseModel):
    """Product item in search results."""

    pdsid: str | None = None
    ode_id: str | None = None
    data_set_id: str | None = None
    instrument_host: str | None = None
    instrument: str | None = None
    product_type: str | None = None
    center_latitude: float | None = None
    center_longitude: float | None = None
    observation_time: str | None = None
    min_latitude: float | None = None
    max_latitude: float | None = None
    west_longitude: float | None = None
    east_longitude: float | None = None
    emission_angle: float | None = None
    incidence_angle: float | None = None
    phase_angle: float | None = None
    map_scale: float | None = None
    label_url: str | None = None
    files: list[ODEProductFileSummary] = Field(default_factory=list)
    files_truncated: bool | None = None
    total_files: int | None = None


class ODESearchProductsInputSchema(InputSchema):
    """Input schema for ODESearchProductsTool."""

    target: TargetType = Field(..., description="Planetary body to search")
    ihid: str | None = Field(
        None,
        description="Instrument Host ID (e.g., 'MRO' for Mars Reconnaissance Orbiter, 'LRO' for Lunar Reconnaissance Orbiter, 'MESS' for MESSENGER)",
    )
    iid: str | None = Field(None, description="Instrument ID (e.g., 'HIRISE', 'CTX', 'LROC', 'MDIS')")
    pt: str | None = Field(None, description="Product Type (e.g., 'RDRV11', 'EDR')")
    pdsid: str | None = Field(None, description="PDS Product ID for direct lookup (e.g., 'ESP_012600_1655_RED')")
    minlat: Annotated[float, Field(ge=-90, le=90)] | None = Field(None, description="Minimum latitude (-90 to 90)")
    maxlat: Annotated[float, Field(ge=-90, le=90)] | None = Field(None, description="Maximum latitude (-90 to 90)")
    westlon: Annotated[float, Field(ge=0, le=360)] | None = Field(None, description="Western longitude (0 to 360)")
    eastlon: Annotated[float, Field(ge=0, le=360)] | None = Field(None, description="Eastern longitude (0 to 360)")
    minobtime: str | None = Field(
        None, description="Minimum observation time in UTC format (e.g., '2018-05-01' or '2018-05-01T00:00:00')"
    )
    maxobtime: str | None = Field(
        None, description="Maximum observation time in UTC format (e.g., '2018-08-31' or '2018-08-31T23:59:59')"
    )
    limit: Annotated[int, Field(ge=1, le=10)] = Field(10, description="Maximum products to return (default 10)")
    offset: Annotated[int, Field(ge=0)] = Field(0, description="Pagination offset (default 0)")


class ODESearchProductsOutputSchema(OutputSchema):
    """Output schema for ODESearchProductsTool."""

    status: str = Field(..., description="Response status ('success' or 'error')")
    target: str = Field(..., description="Planetary body that was searched")
    count: int = Field(..., description="Number of products returned in this response")
    total_available: int = Field(..., description="Total number of products matching criteria")
    offset: int = Field(..., description="Pagination offset used")
    has_more: bool = Field(..., description="Whether more products are available")
    products: list[ODEProductSummary] = Field(
        default_factory=list, description="List of matching products with metadata"
    )
    error: str | None = Field(None, description="Error message if status is 'error'")


class ODESearchProductsToolConfig(BaseToolConfig):
    """Configuration for ODESearchProductsTool."""

    base_url: str = Field(
        default="https://oderest.rsl.wustl.edu/live2/",
        description="ODE API base URL (can be overridden with ODE_BASE_URL env var)",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts for failed requests")


@mcp_tool
class ODESearchProductsTool(BaseTool[ODESearchProductsInputSchema, ODESearchProductsOutputSchema]):
    """Search ODE planetary data products with geographic and temporal filtering.

    This tool searches for Mars, Moon, Mercury, Phobos, Deimos, or Venus data products in the
    Orbital Data Explorer (ODE). Use either instrument identifiers (ihid+iid+pt) or a PDS Product ID (pdsid).

    Key Features:
    - Geographic filtering: Search by latitude/longitude bounds
    - Temporal filtering: Search by observation time ranges
    - Instrument filtering: Search by specific instruments and product types
    - Pagination: Handle large result sets with offset/limit

    Common Instruments:
    Mars:
    - MRO/HIRISE: High Resolution Imaging Science Experiment
    - MRO/CTX: Context Camera
    - MRO/CRISM: Compact Reconnaissance Imaging Spectrometer

    Moon:
    - LRO/LROC: Lunar Reconnaissance Orbiter Camera
    - LRO/DIVINER: Diviner Lunar Radiometer

    Mercury:
    - MESS/MDIS: Mercury Dual Imaging System
    """

    input_schema = ODESearchProductsInputSchema
    output_schema = ODESearchProductsOutputSchema
    config_schema = ODESearchProductsToolConfig

    async def _arun(self, params: ODESearchProductsInputSchema) -> ODESearchProductsOutputSchema:
        """Execute the product search.

        Args:
            params: Input parameters for the search

        Returns:
            Search results with products and metadata

        Raises:
            ODEClientError: If the API request fails
            ValueError: If parameters are invalid
        """
        try:
            async with ODEClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                # Enforce maximum limit to prevent large responses
                limit = min(params.limit, MAX_SEARCH_LIMIT)

                response = await client.search_products(
                    target=params.target,
                    ihid=params.ihid,
                    iid=params.iid,
                    pt=params.pt,
                    pdsid=params.pdsid,
                    minlat=params.minlat,
                    maxlat=params.maxlat,
                    westlon=params.westlon,
                    eastlon=params.eastlon,
                    minobtime=params.minobtime,
                    maxobtime=params.maxobtime,
                    results="fpc",
                    limit=limit,
                    offset=params.offset,
                )

            if response.status == "ERROR":
                return ODESearchProductsOutputSchema(
                    status="error",
                    target=params.target,
                    count=0,
                    total_available=0,
                    offset=params.offset,
                    has_more=False,
                    error=response.error,
                )

            products = []
            for product in response.products:
                files_list = product.product_files or []
                truncated = len(files_list) > MAX_FILES_PER_PRODUCT

                product_summary = ODEProductSummary(
                    pdsid=product.pdsid,
                    ode_id=product.ode_id,
                    data_set_id=product.data_set_id,
                    instrument_host=product.ihid,
                    instrument=product.iid,
                    product_type=product.pt,
                    center_latitude=product.center_latitude,
                    center_longitude=product.center_longitude,
                    observation_time=product.observation_time,
                    min_latitude=product.minimum_latitude,
                    max_latitude=product.maximum_latitude,
                    west_longitude=product.westernmost_longitude,
                    east_longitude=product.easternmost_longitude,
                    emission_angle=product.emission_angle,
                    incidence_angle=product.incidence_angle,
                    phase_angle=product.phase_angle,
                    map_scale=product.map_scale,
                    label_url=product.label_url,
                    files=[
                        ODEProductFileSummary(
                            name=f.file_name,
                            url=f.url,
                            type=f.file_type,
                            size_kb=f.kbytes,
                        )
                        for f in files_list[:MAX_FILES_PER_PRODUCT]
                    ],
                    files_truncated=True if truncated else None,
                    total_files=len(files_list) if truncated else None,
                )
                products.append(product_summary)

            return ODESearchProductsOutputSchema(
                status="success",
                target=params.target,
                count=len(products),
                total_available=response.count,
                offset=params.offset,
                has_more=params.offset + len(products) < response.count,
                products=products,
            )

        except ODEClientError as e:
            logger.error(f"ODE client error in search_products: {e}")
            raise
        except ValueError as e:
            logger.error(f"Validation error in search_products: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in search_products: {e}")
            raise RuntimeError(f"Internal error during product search: {e}") from e
