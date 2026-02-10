"""Get available feature types for a planetary target."""

import logging

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.ode.types import TargetType
from akd_ext.tools.pds.utils.ode_client import ODEClient, ODEClientError

logger = logging.getLogger(__name__)


class ODEListFeatureClassesInputSchema(InputSchema):
    """Input schema for ODEListFeatureClassesTool."""

    target: TargetType = Field(..., description="Planetary body to query")


class ODEListFeatureClassesOutputSchema(OutputSchema):
    """Output schema for ODEListFeatureClassesTool."""

    status: str = Field(..., description="Response status ('success' or 'error')")
    target: str | None = Field(None, description="Planetary body that was queried")
    feature_classes: list[str] = Field(default_factory=list, description="List of available feature types")
    count: int = Field(..., description="Number of feature classes available")
    error: str | None = Field(None, description="Error message if status is 'error'")


class ODEListFeatureClassesToolConfig(BaseToolConfig):
    """Configuration for ODEListFeatureClassesTool."""

    base_url: str = Field(
        default="https://oderest.rsl.wustl.edu/live2/",
        description="ODE API base URL (can be overridden with ODE_BASE_URL env var)",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts for failed requests")


@mcp_tool
class ODEListFeatureClassesTool(BaseTool[ODEListFeatureClassesInputSchema, ODEListFeatureClassesOutputSchema]):
    """Get available feature types for a planetary target.

    Returns all feature classes (crater, chasma, mons, vallis, etc.)
    available for the specified planetary body. Use this to discover what
    types of features can be queried before using ODEGetFeatureBoundsTool
    or ODEListFeatureNamesTool.

    Common Feature Classes by Target:

    Mars:
    - crater: Impact craters
    - chasma: Canyons and deep valleys
    - mons: Mountains and volcanoes
    - vallis: Valleys
    - planum: Plains
    - labyrinthus: Complex canyon systems
    - mensa: Mesa features
    - patera: Shallow craters

    Moon:
    - crater: Lunar craters
    - mare: Lunar maria (dark plains)
    - mons: Lunar mountains
    - lacus: Small lunar maria
    - oceanus: Large lunar maria
    - sinus: Bays

    Mercury:
    - crater: Impact craters
    - planitia: Smooth plains
    - vallis: Valleys
    - rupes: Scarps
    """

    input_schema = ODEListFeatureClassesInputSchema
    output_schema = ODEListFeatureClassesOutputSchema
    config_schema = ODEListFeatureClassesToolConfig

    async def _arun(self, params: ODEListFeatureClassesInputSchema) -> ODEListFeatureClassesOutputSchema:
        """Execute the feature classes query.

        Args:
            params: Input parameters for the query

        Returns:
            List of available feature classes for the target

        Raises:
            ODEClientError: If the API request fails
        """
        try:
            async with ODEClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                response = await client.list_feature_classes(params.target)

            if response.status == "ERROR":
                return ODEListFeatureClassesOutputSchema(
                    status="error",
                    count=0,
                    error=response.error,
                )

            return ODEListFeatureClassesOutputSchema(
                status="success",
                target=params.target,
                feature_classes=response.feature_classes,
                count=len(response.feature_classes),
            )

        except ODEClientError as e:
            logger.error(f"ODE client error in list_feature_classes: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in list_feature_classes: {e}")
            raise RuntimeError(f"Internal error during feature classes query: {e}") from e
