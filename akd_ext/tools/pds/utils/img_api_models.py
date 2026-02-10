"""Pydantic models for IMG Atlas API responses.

The PDS Imaging Node Atlas API uses Apache Solr for querying planetary imagery
from various missions including MER, MSL, Mars 2020, Cassini, Voyager, LRO, and MESSENGER.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _unwrap_value(value: Any) -> Any:
    """Unwrap a value that might be a list (Solr sometimes returns arrays)."""
    if value is None:
        return None
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _parse_float(value: Any) -> float | None:
    """Parse a value to float, returning None if not possible."""
    value = _unwrap_value(value)
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_int(value: Any) -> int | None:
    """Parse a value to int, returning None if not possible."""
    value = _unwrap_value(value)
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _parse_str(value: Any) -> str | None:
    """Parse a value to string, handling arrays."""
    value = _unwrap_value(value)
    if value is None:
        return None
    return str(value)


class IMGProduct(BaseModel):
    """IMG Atlas product representation."""

    model_config = ConfigDict(populate_by_name=True)

    # Identifiers
    uuid: str | None = None
    pds_standard: str | None = Field(None, alias="pds_standard")
    product_id: str | None = Field(None, alias="PRODUCT_ID")

    # Target
    target: str | None = Field(None, alias="TARGET")

    # Product type
    product_type: str | None = Field(None, alias="PRODUCT_TYPE")

    # Mission/Spacecraft/Instrument
    mission_name: str | None = Field(None, alias="ATLAS_MISSION_NAME")
    spacecraft_name: str | None = Field(None, alias="ATLAS_SPACECRAFT_NAME")
    instrument_name: str | None = Field(None, alias="ATLAS_INSTRUMENT_NAME")

    # Time
    start_time: str | None = Field(None, alias="START_TIME")
    stop_time: str | None = Field(None, alias="STOP_TIME")
    product_creation_time: str | None = Field(None, alias="PRODUCT_CREATION_TIME")

    # Mars rover specific
    planet_day_number: int | None = Field(None, alias="PLANET_DAY_NUMBER")
    local_true_solar_time: str | None = Field(None, alias="LOCAL_TRUE_SOLAR_TIME")

    # Solar geometry
    solar_azimuth: float | None = Field(None, alias="SOLAR_AZIMUTH")
    solar_elevation: float | None = Field(None, alias="SOLAR_ELEVATION")

    # Spacecraft clock
    spacecraft_clock_start_count: str | None = Field(None, alias="SPACECRAFT_CLOCK_START_COUNT")

    # Image properties
    exposure_duration: float | None = Field(None, alias="EXPOSURE_DURATION")
    compression_ratio: float | None = Field(None, alias="INST_CMPRS_RATIO")
    frame_type: str | None = Field(None, alias="FRAME_TYPE")
    lines: int | None = Field(None, alias="LINES")
    line_samples: int | None = Field(None, alias="LINE_SAMPLES")

    # Geographic
    center_latitude: float | None = Field(None, alias="center_latitude")
    center_longitude: float | None = Field(None, alias="center_longitude")

    # URLs
    data_url: str | None = Field(None, alias="ATLAS_DATA_URL")
    label_url: str | None = Field(None, alias="ATLAS_LABEL_URL")
    browse_url: str | None = Field(None, alias="ATLAS_BROWSE_URL")
    thumbnail_url: str | None = Field(None, alias="ATLAS_THUMBNAIL_URL")

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "IMGProduct":
        """Create IMGProduct from raw Solr document."""
        # Pre-process fields that need parsing (Solr sometimes returns arrays)
        processed_data = {
            "uuid": _parse_str(data.get("uuid")),
            "pds_standard": _parse_str(data.get("pds_standard")),
            "PRODUCT_ID": _parse_str(data.get("PRODUCT_ID")),
            "TARGET": _parse_str(data.get("TARGET")),
            "PRODUCT_TYPE": _parse_str(data.get("PRODUCT_TYPE")),
            "ATLAS_MISSION_NAME": _parse_str(data.get("ATLAS_MISSION_NAME")),
            "ATLAS_SPACECRAFT_NAME": _parse_str(data.get("ATLAS_SPACECRAFT_NAME")),
            "ATLAS_INSTRUMENT_NAME": _parse_str(data.get("ATLAS_INSTRUMENT_NAME")),
            "START_TIME": _parse_str(data.get("START_TIME")),
            "STOP_TIME": _parse_str(data.get("STOP_TIME")),
            "PRODUCT_CREATION_TIME": _parse_str(data.get("PRODUCT_CREATION_TIME")),
            "PLANET_DAY_NUMBER": _parse_int(data.get("PLANET_DAY_NUMBER")),
            "LOCAL_TRUE_SOLAR_TIME": _parse_str(data.get("LOCAL_TRUE_SOLAR_TIME")),
            "SOLAR_AZIMUTH": _parse_float(data.get("SOLAR_AZIMUTH")),
            "SOLAR_ELEVATION": _parse_float(data.get("SOLAR_ELEVATION")),
            "SPACECRAFT_CLOCK_START_COUNT": _parse_str(data.get("SPACECRAFT_CLOCK_START_COUNT")),
            "EXPOSURE_DURATION": _parse_float(data.get("EXPOSURE_DURATION")),
            "INST_CMPRS_RATIO": _parse_float(data.get("INST_CMPRS_RATIO")),
            "FRAME_TYPE": _parse_str(data.get("FRAME_TYPE")),
            "LINES": _parse_int(data.get("LINES")),
            "LINE_SAMPLES": _parse_int(data.get("LINE_SAMPLES")),
            "center_latitude": _parse_float(data.get("center_latitude")),
            "center_longitude": _parse_float(data.get("center_longitude")),
            "ATLAS_DATA_URL": _parse_str(data.get("ATLAS_DATA_URL")),
            "ATLAS_LABEL_URL": _parse_str(data.get("ATLAS_LABEL_URL")),
            "ATLAS_BROWSE_URL": _parse_str(data.get("ATLAS_BROWSE_URL")),
            "ATLAS_THUMBNAIL_URL": _parse_str(data.get("ATLAS_THUMBNAIL_URL")),
        }
        return cls.model_validate(processed_data)


class IMGSearchResponse(BaseModel):
    """IMG Atlas search response wrapper."""

    status: str = "success"
    num_found: int = 0
    start: int = 0
    query_time_ms: int = 0
    products: list[IMGProduct] = Field(default_factory=list)
    error: str | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "IMGSearchResponse":
        """Create from raw Solr API response."""
        # Check for error response
        if "error" in data:
            error_info = data.get("error", {})
            return cls(
                status="error",
                error=error_info.get("msg", "Unknown error"),
            )

        # Parse response header
        response_header = data.get("responseHeader", {})
        status_code = response_header.get("status", 0)
        query_time = response_header.get("QTime", 0)

        if status_code != 0:
            return cls(
                status="error",
                error=f"Solr error status: {status_code}",
                query_time_ms=query_time,
            )

        # Parse response body
        response = data.get("response", {})
        num_found = response.get("numFound", 0)
        start = response.get("start", 0)
        docs = response.get("docs", [])

        products = [IMGProduct.from_raw_data(doc) for doc in docs]

        return cls(
            status="success",
            num_found=num_found,
            start=start,
            query_time_ms=query_time,
            products=products,
        )


class IMGCountResponse(BaseModel):
    """IMG Atlas count response."""

    status: str = "success"
    count: int = 0
    query_time_ms: int = 0
    error: str | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "IMGCountResponse":
        """Create from raw Solr API response."""
        # Check for error response
        if "error" in data:
            error_info = data.get("error", {})
            return cls(
                status="error",
                error=error_info.get("msg", "Unknown error"),
            )

        # Parse response header
        response_header = data.get("responseHeader", {})
        status_code = response_header.get("status", 0)
        query_time = response_header.get("QTime", 0)

        if status_code != 0:
            return cls(
                status="error",
                error=f"Solr error status: {status_code}",
                query_time_ms=query_time,
            )

        # Parse response body - just need numFound
        response = data.get("response", {})
        num_found = response.get("numFound", 0)

        return cls(
            status="success",
            count=num_found,
            query_time_ms=query_time,
        )


class IMGFacetValue(BaseModel):
    """A single facet value with its count."""

    value: str
    count: int


class IMGFacetResponse(BaseModel):
    """IMG Atlas facet response for dynamic field discovery."""

    status: str = "success"
    facet_field: str = ""
    values: list[IMGFacetValue] = Field(default_factory=list)
    query_time_ms: int = 0
    error: str | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any], facet_field: str) -> "IMGFacetResponse":
        """Create from raw Solr API response with facet data.

        Solr returns facets in the format:
        {
            "facet_counts": {
                "facet_fields": {
                    "FIELD_NAME": ["value1", count1, "value2", count2, ...]
                }
            }
        }
        """
        # Check for error response
        if "error" in data:
            error_info = data.get("error", {})
            return cls(
                status="error",
                facet_field=facet_field,
                error=error_info.get("msg", "Unknown error"),
            )

        # Parse response header
        response_header = data.get("responseHeader", {})
        status_code = response_header.get("status", 0)
        query_time = response_header.get("QTime", 0)

        if status_code != 0:
            return cls(
                status="error",
                facet_field=facet_field,
                error=f"Solr error status: {status_code}",
                query_time_ms=query_time,
            )

        # Parse facet data
        facet_counts = data.get("facet_counts", {})
        facet_fields = facet_counts.get("facet_fields", {})
        raw_values = facet_fields.get(facet_field, [])

        # Convert alternating list [value, count, value, count, ...] to list of dicts
        values: list[IMGFacetValue] = []
        for i in range(0, len(raw_values), 2):
            if i + 1 < len(raw_values):
                value = str(raw_values[i])
                count = int(raw_values[i + 1])
                if count > 0:  # Only include values with counts
                    values.append(IMGFacetValue(value=value, count=count))

        return cls(
            status="success",
            facet_field=facet_field,
            values=values,
            query_time_ms=query_time,
        )
