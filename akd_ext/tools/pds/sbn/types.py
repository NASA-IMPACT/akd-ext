"""Shared types and constants for SBN CATCH tools."""

from typing import Any

from pydantic import BaseModel

# Response size limits (CATCH API has no pagination, so limit client-side)
MAX_OBSERVATIONS_LIMIT = 10
DEFAULT_OBSERVATIONS_LIMIT = 10

# Field profiles for response filtering
ESSENTIAL_FIELDS = {"product_id", "source", "date", "archive_url"}
SUMMARY_FIELDS = ESSENTIAL_FIELDS | {"ra", "dec", "vmag", "filter", "exposure"}
FULL_FIELDS = SUMMARY_FIELDS | {
    "rh",
    "delta",
    "phase",
    "dra",
    "ddec",
    "seeing",
    "airmass",
    "maglimit",
    "cutout_url",
    "preview_url",
    "mjd_start",
}
FIELD_PROFILES: dict[str, set[str]] = {
    "essential": ESSENTIAL_FIELDS,
    "summary": SUMMARY_FIELDS,
    "full": FULL_FIELDS,
}

# Valid data sources description for input schema documentation
VALID_SOURCES_DESCRIPTION = (
    "List of data sources to search (None = all sources). "
    "Valid sources: neat_palomar_tricam, neat_maui_geodss, ps1dr2, catalina_bigelow, "
    "catalina_lemmon, catalina_kittpeak, skymapper_dr4, atlas_hko, atlas_mlo, atlas_rio, "
    "atlas_chl, atlas_sth, spacewatch_0.9m, spacewatch_mosaic, loneos"
)


def filter_observation(obs_dict: dict[str, Any], fields: set[str]) -> dict[str, Any]:
    """Filter observation to specified fields, excluding None values."""
    return {k: v for k, v in obs_dict.items() if k in fields and v is not None}


class SBNSourceStatusSummary(BaseModel):
    """Source status item in search results."""

    source: str
    status: str
    count: int | None = None
