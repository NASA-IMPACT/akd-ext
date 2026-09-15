"""psi_file_search_tool — search NASA PSI investigation files, restricted by category.

File search is its own tool (rather than a ``psi_api_tool`` operation) so each
call can choose which PSI categories to search. Investigations can hold tens of
thousands of raw files, so calls that omit ``categories`` fall back to the
configured default scope (Reports).
"""

import os
from typing import Literal

from pydantic import Field, model_validator

from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool
from akd_ext.mcp import mcp_tool

from ._client import PsiToolConfig
from ._normalize import absolute_psi_url
from ._operations import fetch_file_groups, store_json_artifact


def _search_categories_from_env() -> list[str]:
    """Parse PSI_SEARCH_CATEGORIES (comma-separated; default 'Reports')."""
    raw = os.getenv("PSI_SEARCH_CATEGORIES", "Reports")
    return [item.strip() for item in raw.split(",") if item.strip()]


class PsiFileSearchInput(InputSchema):
    """Input schema for psi_file_search_tool."""

    investigation_selector: str | None = Field(
        default=None, description="Investigation id or selector: '117', 'PSI-117', '4,10', or '20-25'"
    )
    investigation_id: str | None = Field(default=None, description="Single investigation id, e.g. 'PSI-117'")
    categories: list[str] | None = Field(
        default=None,
        description="Only return files in these PSI categories (case-insensitive), "
        "e.g. ['Reports', 'Analyzed Data']. Omit to use the configured default (Reports); "
        "pass [] to search every category.",
    )
    file_name_pattern: str | None = Field(default=None, description="Case-insensitive glob, e.g. '*.csv'")
    subcategory: str | None = Field(default=None, description="Exact subcategory (case-insensitive)")
    subdirectory_prefix: str | None = Field(default=None, description="Subdirectory prefix (case-insensitive)")
    file_type: Literal["all", "img", "video"] = Field(default="all", description="Restrict to image or video files")
    max_items: int = Field(default=250, ge=1, le=10_000, description="Maximum file records to return inline")

    @model_validator(mode="after")
    def _require_investigation(self) -> "PsiFileSearchInput":
        if not (self.investigation_selector or self.investigation_id):
            raise ValueError("psi_file_search_tool requires investigation_selector or investigation_id")
        return self


class PsiFileSearchOutput(OutputSchema):
    """Output schema for psi_file_search_tool."""

    data: dict = Field(
        default_factory=dict,
        description="investigations (matching files grouped per investigation, each with a download_url), "
        "result_limits (counts, truncation, category_scope), and source_metadata",
    )
    summary: str = Field(default="", description="One-sentence description of the result")
    warnings: list[dict] = Field(default_factory=list, description="Non-fatal data-quality warnings")
    sources: list[dict] = Field(default_factory=list, description="Provenance of the returned data")


class PsiFileSearchConfig(PsiToolConfig):
    """Configuration for psi_file_search_tool (default category scope and artifact path)."""

    name: str = Field(default="psi_file_search_tool", description="Tool name")
    search_categories: list[str] = Field(
        default_factory=_search_categories_from_env,
        description="Categories searched when a call omits ``categories`` (default: Reports); "
        "an empty list searches every category. Env: PSI_SEARCH_CATEGORIES (comma-separated).",
    )
    artifact_root: str = Field(
        default=os.getenv("PSI_ARTIFACT_ROOT", "./artifacts"),
        description="Directory for the complete file inventory when results are truncated",
    )


@mcp_tool
class PsiFileSearchTool(BaseTool[PsiFileSearchInput, PsiFileSearchOutput]):
    """Search the files of NASA PSI investigations, restricted to chosen categories.

    Set ``investigation_selector`` (e.g. '117', '4,10', '20-25') and optionally
    ``categories`` to limit results to those PSI file categories, such as
    Reports, Analyzed Data, Raw Data, Science Documents, Engineering Documents,
    Presentations, Calibration, or Experimental table. Omitting ``categories``
    applies the configured default (Reports); pass [] to search every category.
    ``file_name_pattern`` takes a case-insensitive glob such as '*.csv'. Every
    matching file includes ``download_url``, a direct PSI download link that
    stays valid (PSI issues a fresh signed storage URL each time it is opened).
    When more than ``max_items`` files match, the complete inventory is written
    to an artifact. Use psi_api_tool's navigate_dataset to see which categories
    an investigation contains.
    """

    config_schema = PsiFileSearchConfig
    input_schema = PsiFileSearchInput
    output_schema = PsiFileSearchOutput

    async def _arun(self, params: PsiFileSearchInput, **kwargs) -> PsiFileSearchOutput:
        selector = params.investigation_selector or params.investigation_id
        requested = self.config.search_categories if params.categories is None else params.categories
        scope = [item for item in requested if str(item).strip()]
        groups, source_metadata, warnings = await fetch_file_groups(
            self.config,
            selector,
            params.file_type,
            pattern=params.file_name_pattern,
            subcategory=params.subcategory,
            subdirectory_prefix=params.subdirectory_prefix,
            allowed_categories=scope or None,
            transport=getattr(self, "transport", None),
        )
        for group in groups:
            for record in group["files"]:
                remote_url = record.get("remote_url")
                record["download_url"] = (
                    absolute_psi_url(self.config.psi_origin, str(remote_url)) if remote_url else None
                )
        received = sum(group["returned_file_count"] for group in groups)
        matched = sum(group["matched_file_count"] for group in groups)
        truncated = matched > params.max_items

        returned_groups: list[dict] = []
        remaining = params.max_items
        for group in groups:
            if remaining <= 0:
                break
            files = group["files"][:remaining]
            remaining -= len(files)
            returned_groups.append({**group, "files": files})

        returned = min(matched, params.max_items)
        result_limits = {
            "files_received_from_api": received,
            "files_matching_filters": matched,
            "files_returned_to_agent": returned,
            "truncated": truncated,
            "category_scope": scope,
        }
        if truncated:
            result_limits["complete_inventory_artifact"] = store_json_artifact(
                self.config.artifact_root, {"investigations": groups}, prefix="file_inventory"
            )
        summary = (
            f"The PSI API returned {received} file records; {matched} matched the requested "
            f"filters and {returned} were included inline."
        )
        if scope:
            summary += f" Search was scoped to categories: {', '.join(scope)}."
        return PsiFileSearchOutput(
            data={
                "investigations": returned_groups,
                "result_limits": result_limits,
                "source_metadata": source_metadata,
            },
            summary=summary,
            warnings=warnings,
            sources=[{"type": "psi_api", "resource": f"files:{selector}"}],
        )
