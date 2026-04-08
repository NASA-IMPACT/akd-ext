"""Get detailed information about a specific PDS dataset."""

import re

from loguru import logger
from typing import Any

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from pydantic import Field

from akd_ext.mcp.decorators import mcp_tool
from akd_ext.tools.pds.utils.pds_catalog_client import (
    FIELD_PROFILES,
    PDSCatalogClient,
    PDSCatalogClientError,
    filter_dataset,
)

_PDS3_ID_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_\-\.]+$", re.IGNORECASE)
_PDS4_URN_PATTERN = re.compile(r"^urn:nasa:pds:", re.IGNORECASE)


def _sanitize_dataset_id(raw_id: str) -> str:
    """Strip set-notation braces, whitespace, quotes from malformed inputs."""
    cleaned = raw_id.strip()
    if cleaned.startswith("{") or cleaned.startswith("["):
        cleaned = cleaned.strip("{}[]")
        if "," in cleaned:
            cleaned = cleaned.split(",")[0]
        cleaned = cleaned.strip().strip("\"'")
    return cleaned


class PDSCatalogGetDatasetInputSchema(InputSchema):
    """Input schema for PDSCatalogGetDatasetTool."""

    dataset_id: str = Field(
        ...,
        description=(
            "The exact dataset ID to look up. Must be a real ID returned by a prior search tool — "
            "do NOT guess or fabricate IDs. "
            "PDS4 format: LIDVID (e.g., 'urn:nasa:pds:cassini_iss::1.0'). "
            "PDS3 format: DATA_SET_ID (e.g., 'MRO-M-HIRISE-3-RDR-V1.1')."
        ),
    )


class PDSCatalogGetDatasetOutputSchema(OutputSchema):
    """Output schema for PDSCatalogGetDatasetTool."""

    status: str = Field(..., description="Status of the request ('success', 'not_found', or 'invalid_input')")
    dataset: dict[str, Any] | None = Field(None, description="Full dataset information if found")
    error: str | None = Field(None, description="Error message if dataset not found or input is invalid")
    suggestions: list[str] | None = Field(None, description="Similar dataset IDs if the requested ID was not found")


class PDSCatalogGetDatasetToolConfig(BaseToolConfig):
    """Configuration for PDSCatalogGetDatasetTool."""

    catalog_dir: str | None = Field(
        default=None,
        description="Directory containing catalog JSONL files (uses PDS_CATALOG_DIR env var or default if None)",
    )


@mcp_tool
class PDSCatalogGetDatasetTool(BaseTool[PDSCatalogGetDatasetInputSchema, PDSCatalogGetDatasetOutputSchema]):
    """Get detailed information about a specific dataset.

    This tool retrieves full metadata for a specific PDS dataset by its ID.
    Use this ONLY with dataset IDs that were returned by a prior search tool.
    Do NOT guess or fabricate dataset IDs.

    If the exact ID is not found, similar IDs will be suggested.

    Dataset IDs:
    - PDS4: LIDVID format (e.g., "urn:nasa:pds:cassini_iss::1.0")
    - PDS3: DATA_SET_ID format (e.g., "MRO-M-HIRISE-3-RDR-V1.1")

    """

    input_schema = PDSCatalogGetDatasetInputSchema
    output_schema = PDSCatalogGetDatasetOutputSchema
    config_schema = PDSCatalogGetDatasetToolConfig

    async def _arun(self, params: PDSCatalogGetDatasetInputSchema) -> PDSCatalogGetDatasetOutputSchema:
        try:
            dataset_id = _sanitize_dataset_id(params.dataset_id)

            if not dataset_id:
                return PDSCatalogGetDatasetOutputSchema(
                    status="invalid_input",
                    error="Empty dataset ID provided.",
                )

            is_pds4 = bool(_PDS4_URN_PATTERN.match(dataset_id))
            is_pds3 = bool(_PDS3_ID_PATTERN.match(dataset_id)) and not is_pds4

            if not is_pds4 and not is_pds3:
                return PDSCatalogGetDatasetOutputSchema(
                    status="invalid_input",
                    error=(
                        f"Malformed dataset ID: '{dataset_id}'. "
                        "Expected PDS3 format (e.g., 'MRO-M-HIRISE-3-RDR-V1.1') or "
                        "PDS4 LIDVID (e.g., 'urn:nasa:pds:cassini_iss::1.0'). "
                        "Use pds_catalog_search_tool to find valid dataset IDs first."
                    ),
                )

            client = PDSCatalogClient(catalog_dir=self.config.catalog_dir)
            dataset = await client.get_dataset(dataset_id)

            if dataset is None:
                similar = client.index.find_similar_dataset_ids(dataset_id, max_suggestions=5)
                suggestion_ids = [sid for sid, score in similar if score >= 55]

                error_msg = f"Dataset not found: {dataset_id}"
                if suggestion_ids:
                    error_msg += f". Did you mean one of: {', '.join(suggestion_ids)}?"
                else:
                    error_msg += ". Use pds_catalog_search_tool to find valid dataset IDs."

                return PDSCatalogGetDatasetOutputSchema(
                    status="not_found",
                    error=error_msg,
                    suggestions=suggestion_ids if suggestion_ids else None,
                )

            field_set = FIELD_PROFILES["full"]
            filtered_dataset = filter_dataset(dataset, field_set)

            return PDSCatalogGetDatasetOutputSchema(
                status="success",
                dataset=filtered_dataset,
            )

        except PDSCatalogClientError as e:
            logger.error(f"PDS Catalog client error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_dataset: {e}")
            raise RuntimeError(f"Internal error retrieving dataset: {e}") from e
