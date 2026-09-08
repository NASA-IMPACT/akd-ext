"""psi_api_tool — the single runtime tool for NASA PSI API operations.

One tool exposes an ``operation`` selector over the PSI Public Investigations
API, file search, download, dataset navigation, and DataCite DOI lookup. This
mirrors the reference ``psi-agent-tools`` design (one API tool + one metadata
tool) rather than one akd-ext tool per operation.
"""

import json
import os
from typing import Literal

from pydantic import Field, model_validator

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool
from akd_ext.mcp import mcp_tool

from ._client import PsiToolConfig
from ._operations import OPERATIONS

Operation = Literal[
    "discover_investigations",
    "get_investigation",
    "search_files",
    "navigate_dataset",
    "retrieve_file",
    "lookup_publication",
]


def _search_categories_from_env() -> list[str]:
    """Parse PSI_SEARCH_CATEGORIES (comma-separated; default 'Reports')."""
    raw = os.getenv("PSI_SEARCH_CATEGORIES", "Reports")
    return [item.strip() for item in raw.split(",") if item.strip()]


class PsiApiInput(InputSchema):
    """Input schema for psi_api_tool (fields are per-operation; see ``operation``)."""

    operation: Operation = Field(..., description="Which PSI operation to run")
    query: str | None = Field(default=None, description="discover_investigations: keywords to rank investigations by")
    investigation_id: str | None = Field(default=None, description="Target investigation id, e.g. 'PSI-117' or '117'")
    investigation_selector: str | None = Field(
        default=None,
        description="search_files: investigation id or selector ('117', '4,10', '20-25')",
    )
    fields: list[str] | None = Field(
        default=None, description="get_investigation: optional upstream field names to restrict to"
    )
    file_type: Literal["all", "img", "video"] = Field(
        default="all", description="search_files/navigate_dataset: restrict to image or video files"
    )
    file_name_pattern: str | None = Field(
        default=None, description="search_files/navigate_dataset: case-insensitive glob, e.g. '*.csv'"
    )
    category: str | None = Field(
        default=None,
        description="File filter: exact category (search_files only honors categories inside the configured scope)",
    )
    subcategory: str | None = Field(default=None, description="File filter: exact subcategory")
    subdirectory_prefix: str | None = Field(default=None, description="File filter: subdirectory prefix")
    max_items: int = Field(default=250, ge=1, le=10_000, description="Maximum records to return inline")
    remote_url: str | None = Field(default=None, description="retrieve_file: direct PSI download URL")
    file_name: str | None = Field(default=None, description="retrieve_file: exact file name to download")
    destination: str | None = Field(default=None, description="retrieve_file: local directory to store the file in")
    preserve_folder_structure: bool = Field(
        default=True, description="retrieve_file: mirror the PSI category/subdirectory layout"
    )
    doi: str | None = Field(default=None, description="lookup_publication: DOI to resolve via DataCite")
    response_mode: Literal["summary", "raw", "both"] = Field(
        default="summary",
        description="'summary' (default) returns normalized data; 'raw'/'both' also attach the raw API JSON",
    )

    @model_validator(mode="after")
    def _validate_operation_fields(self) -> "PsiApiInput":
        if self.operation == "get_investigation" and not self.investigation_id:
            raise ValueError("get_investigation requires investigation_id")
        if self.operation == "search_files" and not (self.investigation_selector or self.investigation_id):
            raise ValueError("search_files requires investigation_selector or investigation_id")
        if self.operation == "navigate_dataset" and not self.investigation_id:
            raise ValueError("navigate_dataset requires investigation_id")
        if self.operation == "retrieve_file":
            if not self.investigation_id:
                raise ValueError("retrieve_file requires investigation_id")
            if not (self.remote_url or self.file_name):
                raise ValueError("retrieve_file requires remote_url or file_name")
        if self.operation == "lookup_publication" and not self.doi:
            raise ValueError("lookup_publication requires doi")
        return self


class PsiApiOutput(OutputSchema):
    """Output schema for psi_api_tool (a normalized envelope; data is per-operation)."""

    operation: str = Field(default="", description="The operation that produced this result")
    data: dict = Field(default_factory=dict, description="Operation-specific normalized payload")
    summary: str = Field(default="", description="One-sentence description of the result")
    warnings: list[dict] = Field(default_factory=list, description="Non-fatal data-quality warnings")
    sources: list[dict] = Field(default_factory=list, description="Provenance of the returned data")
    raw_response: dict | None = Field(
        default=None, description="Raw upstream JSON, present only when response_mode is 'raw' or 'both'"
    )


class PsiApiConfig(PsiToolConfig):
    """Configuration for psi_api_tool (endpoints, download, and artifact paths)."""

    name: str = Field(default="psi_api_tool", description="Tool name")
    search_categories: list[str] = Field(
        default_factory=_search_categories_from_env,
        description="search_files only returns files in these categories (default: Reports); "
        "an empty list disables the restriction. Env: PSI_SEARCH_CATEGORIES (comma-separated).",
    )
    datacite_doi_url_template: str = Field(
        default=os.getenv("DATACITE_DOI_URL_TEMPLATE", "https://api.datacite.org/dois/{doi}"),
        description="DataCite endpoint template for DOI lookups",
    )
    download_root: str = Field(
        default=os.getenv("PSI_DOWNLOAD_ROOT", "./artifacts/psi_downloads"),
        description="Default directory for downloaded files",
    )
    max_download_bytes: int = Field(
        default=int(os.getenv("PSI_MAX_DOWNLOAD_BYTES", str(5 * 1024**3))),
        description="Refuse downloads larger than this many bytes",
    )
    artifact_root: str = Field(
        default=os.getenv("PSI_ARTIFACT_ROOT", "./artifacts"),
        description="Directory for overflow/raw JSON artifacts",
    )
    max_inline_json_bytes: int = Field(
        default=int(os.getenv("PSI_MAX_INLINE_JSON_BYTES", str(512 * 1024))),
        description="Raw responses larger than this are spilled to an artifact instead of inlined",
    )


@mcp_tool
class PsiApiTool(BaseTool[PsiApiInput, PsiApiOutput]):
    """Query the NASA PSI (Physical Sciences Informatics) API.

    Set ``operation`` to one of: discover_investigations, get_investigation,
    search_files, navigate_dataset, retrieve_file, lookup_publication. All PSI
    endpoints are public. Returns normalized data by default; pass
    response_mode='raw' or 'both' to also receive the raw upstream JSON.
    search_files is scoped to the 'Reports' file category by default
    (config ``search_categories`` / env ``PSI_SEARCH_CATEGORIES``);
    navigate_dataset still shows the full dataset structure.
    """

    config_schema = PsiApiConfig
    input_schema = PsiApiInput
    output_schema = PsiApiOutput

    async def _arun(self, params: PsiApiInput, **kwargs) -> PsiApiOutput:
        handler = OPERATIONS[params.operation]
        result = await handler(self.config, params, getattr(self, "transport", None))

        raw_response = None
        raw = result.get("raw")
        if params.response_mode in ("raw", "both") and raw is not None:
            body = json.dumps(raw, ensure_ascii=False, default=str)
            if len(body.encode("utf-8")) <= self.config.max_inline_json_bytes:
                raw_response = {"included": True, "data": raw}
            else:
                from ._operations import store_json_artifact

                artifact = store_json_artifact(self.config.artifact_root, raw, prefix="raw_response")
                raw_response = {
                    "included": False,
                    "reason": "The upstream response exceeded the inline size limit.",
                    **artifact,
                }

        return PsiApiOutput(
            operation=params.operation,
            data=result["data"],
            summary=result["summary"],
            warnings=result["warnings"],
            sources=result["sources"],
            raw_response=raw_response,
        )
