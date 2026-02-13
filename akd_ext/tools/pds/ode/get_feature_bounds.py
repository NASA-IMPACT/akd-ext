"""Get geographic bounds (lat/lon) for a named planetary feature."""

import os

from loguru import logger

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.ode.types import TargetType
from akd_ext.tools.pds.utils.ode_client import ODEClient, ODEClientError


class ODEGetFeatureBoundsInputSchema(InputSchema):
    """Input schema for ODEGetFeatureBoundsTool."""

    target: TargetType = Field(..., description="Planetary body to query")
    feature_class: str = Field(..., description="Feature type (e.g., 'crater', 'chasma', 'mons', 'vallis', 'mare')")
    feature_name: str = Field(..., description="Name of the feature (e.g., 'Gale', 'Jezero', 'Olympus Mons')")


class ODEGetFeatureBoundsOutputSchema(OutputSchema):
    """Output schema for ODEGetFeatureBoundsTool."""

    status: str = Field(..., description="Response status ('success', 'not_found', or 'error')")
    target: str | None = Field(None, description="Planetary body that was queried")
    feature_class: str | None = Field(None, description="Feature type")
    feature_name: str | None = Field(None, description="Feature name")
    bounds: dict[str, float] | None = Field(
        None, description="Geographic bounds with keys: min_lat, max_lat, west_lon, east_lon"
    )
    message: str | None = Field(None, description="Status message for not_found cases")
    error: str | None = Field(None, description="Error message if status is 'error'")


class ODEGetFeatureBoundsToolConfig(BaseToolConfig):
    """Configuration for ODEGetFeatureBoundsTool."""

    base_url: str = Field(
        default=os.getenv("ODE_BASE_URL", "https://oderest.rsl.wustl.edu/live2/"),
        description="ODE API base URL (override with ODE_BASE_URL env var)",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts for failed requests")


@mcp_tool
class ODEGetFeatureBoundsTool(BaseTool[ODEGetFeatureBoundsInputSchema, ODEGetFeatureBoundsOutputSchema]):
    """Get geographic bounds (lat/lon) for a named planetary feature.

    Look up the bounding box for named features like craters, valleys, volcanoes, etc.
    This is useful for finding data products in specific regions by using the returned
    bounds with the ODESearchProductsTool.

    Common Feature Classes:
    Mars:
    - crater: Impact craters (e.g., "Gale", "Jezero")
    - chasma: Canyons (e.g., "Valles Marineris")
    - mons: Mountains/volcanoes (e.g., "Olympus Mons")
    - vallis: Valleys (e.g., "Ma'adim Vallis")
    - planum: Plains (e.g., "Hesperia Planum")

    Moon:
    - crater: Lunar craters (e.g., "Tycho", "Copernicus")
    - mare: Lunar maria (e.g., "Mare Tranquillitatis")
    - mons: Lunar mountains

    Mercury:
    - crater: Mercurian craters (e.g., "Caloris")
    - planitia: Plains
    """

    input_schema = ODEGetFeatureBoundsInputSchema
    output_schema = ODEGetFeatureBoundsOutputSchema
    config_schema = ODEGetFeatureBoundsToolConfig

    async def _arun(self, params: ODEGetFeatureBoundsInputSchema) -> ODEGetFeatureBoundsOutputSchema:
        """Execute the feature bounds query.

        Args:
            params: Input parameters for the query

        Returns:
            Geographic bounds for the named feature

        Raises:
            ODEClientError: If the API request fails
        """
        try:
            async with ODEClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                response = await client.get_feature_bounds(
                    target=params.target,
                    feature_class=params.feature_class,
                    feature_name=params.feature_name,
                )

            if response.status == "ERROR":
                return ODEGetFeatureBoundsOutputSchema(
                    status="error",
                    error=response.error,
                )

            if not response.features:
                return ODEGetFeatureBoundsOutputSchema(
                    status="not_found",
                    message=f"Feature '{params.feature_name}' of type '{params.feature_class}' not found on {params.target}",
                )

            feature = response.features[0]
            return ODEGetFeatureBoundsOutputSchema(
                status="success",
                target=params.target,
                feature_class=feature.feature_class,
                feature_name=feature.feature_name,
                bounds={
                    "min_lat": feature.min_lat,
                    "max_lat": feature.max_lat,
                    "west_lon": feature.west_lon,
                    "east_lon": feature.east_lon,
                },
            )

        except ODEClientError as e:
            logger.error(f"ODE client error in get_feature_bounds: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_feature_bounds: {e}")
            raise RuntimeError(f"Internal error during feature bounds query: {e}") from e
