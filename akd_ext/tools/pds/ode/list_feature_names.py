"""Get names of planetary features by class."""

import os

from loguru import logger

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.ode.types import TargetType
from akd_ext.tools.pds.utils.ode_client import ODEClient, ODEClientError


MAX_FEATURE_NAMES_LIMIT = 50  # Max feature names


class ODEListFeatureNamesInputSchema(InputSchema):
    """Input schema for ODEListFeatureNamesTool."""

    target: TargetType = Field(..., description="Planetary body to query")
    feature_class: str = Field(..., description="Feature type (e.g., 'crater', 'chasma', 'mons', 'vallis', 'mare')")
    limit: int = Field(50, ge=1, le=50, description="Maximum names to return (default 50, max 50)")


class ODEListFeatureNamesOutputSchema(OutputSchema):
    """Output schema for ODEListFeatureNamesTool."""

    status: str = Field(..., description="Response status ('success' or 'error')")
    target: str | None = Field(None, description="Planetary body that was queried")
    feature_class: str | None = Field(None, description="Feature type that was queried")
    feature_names: list[str] = Field(default_factory=list, description="List of feature names")
    count: int = Field(..., description="Number of feature names returned")
    error: str | None = Field(None, description="Error message if status is 'error'")


class ODEListFeatureNamesToolConfig(BaseToolConfig):
    """Configuration for ODEListFeatureNamesTool."""

    base_url: str = Field(
        default=os.getenv("ODE_BASE_URL", "https://oderest.rsl.wustl.edu/live2/"),
        description="ODE API base URL (override with ODE_BASE_URL env var)",
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts for failed requests")


@mcp_tool
class ODEListFeatureNamesTool(BaseTool[ODEListFeatureNamesInputSchema, ODEListFeatureNamesOutputSchema]):
    """Get names of planetary features by class.

    Returns names of features of the specified type (e.g., all named craters on Mars).
    Use this to discover specific feature names that can be used with ODEGetFeatureBoundsTool
    to get geographic bounds for searching data products.

    Workflow:
    1. Use ODEListFeatureClassesTool to discover available feature types
    2. Use this tool to get names of features in a specific class
    3. Use ODEGetFeatureBoundsTool to get bounds for a specific feature
    4. Use ODESearchProductsTool with those bounds to find data
    """

    input_schema = ODEListFeatureNamesInputSchema
    output_schema = ODEListFeatureNamesOutputSchema
    config_schema = ODEListFeatureNamesToolConfig

    async def _arun(self, params: ODEListFeatureNamesInputSchema) -> ODEListFeatureNamesOutputSchema:
        """Execute the feature names query.

        Args:
            params: Input parameters for the query

        Returns:
            List of feature names for the specified class and target

        Raises:
            ODEClientError: If the API request fails
        """
        try:
            async with ODEClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                # Enforce maximum limit
                limit = min(params.limit, MAX_FEATURE_NAMES_LIMIT)

                response = await client.list_feature_names(
                    target=params.target,
                    feature_class=params.feature_class,
                    limit=limit,
                )

            if response.status == "ERROR":
                return ODEListFeatureNamesOutputSchema(
                    status="error",
                    count=0,
                    error=response.error,
                )

            return ODEListFeatureNamesOutputSchema(
                status="success",
                target=params.target,
                feature_class=params.feature_class,
                feature_names=response.feature_names,
                count=len(response.feature_names),
            )

        except ODEClientError as e:
            logger.error(f"ODE client error in list_feature_names: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in list_feature_names: {e}")
            raise RuntimeError(f"Internal error during feature names query: {e}") from e
