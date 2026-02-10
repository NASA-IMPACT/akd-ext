"""OPUS Get Fields Tool - Get available search fields."""

import logging

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import BaseModel, Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.utils.opus_client import OPUSClient, OPUSClientError

logger = logging.getLogger(__name__)


class OPUSFieldItem(BaseModel):
    """Field definition item."""

    id: str
    label: str
    search_label: str | None = None


class OPUSGetFieldsInputSchema(InputSchema):
    """Input schema for OPUSGetFieldsTool.

    This tool takes no parameters - it retrieves all available fields.
    """

    pass


class OPUSGetFieldsOutputSchema(OutputSchema):
    """Output schema for OPUSGetFieldsTool."""

    status: str = Field(..., description="Status of the field retrieval")
    categories: list[str] = Field(
        default_factory=list,
        description="List of field categories",
    )
    fields_by_category: dict[str, list[OPUSFieldItem]] = Field(
        default_factory=dict,
        description="Field definitions organized by category",
    )
    total_fields: int = Field(..., description="Total number of fields available")


class OPUSGetFieldsToolConfig(BaseToolConfig):
    """Configuration for OPUSGetFieldsTool."""

    base_url: str = Field(
        default="https://opus.pds-rings.seti.org/opus/api/",
        description="OPUS API base URL",
    )
    timeout: float = Field(
        default=30.0,
        description="Request timeout in seconds",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts",
    )


@mcp_tool
class OPUSGetFieldsTool(BaseTool[OPUSGetFieldsInputSchema, OPUSGetFieldsOutputSchema]):
    """Get all available search fields in OPUS.

    Returns field definitions organized by category, useful for understanding
    what parameters can be used in advanced searches. Categories include:
    - General Constraints
    - PDS Constraints
    - Image Constraints
    - Wavelength Constraints
    - Ring Geometry Constraints
    - Surface Geometry Constraints
    - Instrument-specific Constraints
    """

    input_schema = OPUSGetFieldsInputSchema
    output_schema = OPUSGetFieldsOutputSchema
    config_schema = OPUSGetFieldsToolConfig

    async def _arun(self, params: OPUSGetFieldsInputSchema) -> OPUSGetFieldsOutputSchema:
        """Execute the fields retrieval."""
        try:
            async with OPUSClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            ) as client:
                response = await client.get_fields()

            if response.status == "error":
                logger.error(f"OPUS fields error: {response.error}")
                return OPUSGetFieldsOutputSchema(
                    status="error",
                    categories=[],
                    fields_by_category={},
                    total_fields=0,
                )

            # Organize fields by category
            fields_by_category: dict[str, list[OPUSFieldItem]] = {}
            for field in response.fields:
                category = field.category or "Other"
                if category not in fields_by_category:
                    fields_by_category[category] = []

                field_item = OPUSFieldItem(
                    id=field.field_id,
                    label=field.label,
                    search_label=field.search_label,
                )
                fields_by_category[category].append(field_item)

            return OPUSGetFieldsOutputSchema(
                status="success",
                categories=response.categories,
                fields_by_category=fields_by_category,
                total_fields=len(response.fields),
            )

        except OPUSClientError as e:
            logger.error(f"OPUS client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in OPUS get fields: {e}")
            raise RuntimeError(f"Internal error: {e}") from e
