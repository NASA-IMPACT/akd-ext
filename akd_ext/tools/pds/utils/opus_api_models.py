"""Pydantic models for OPUS API responses.

The OPUS (Outer Planets Unified Search) API provides access to outer planets
observations from Cassini, Voyager, Galileo, New Horizons, Juno, and HST.

Base URL: https://opus.pds-rings.seti.org/opus/api/
"""

from typing import Any

from pydantic import BaseModel, Field


def _parse_float(value: Any) -> float | None:
    """Parse a value to float, returning None if not possible."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_int(value: Any) -> int | None:
    """Parse a value to int, returning None if not possible."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


class OPUSObservation(BaseModel):
    """OPUS observation representation from search results."""

    opusid: str
    instrument: str | None = None
    planet: str | None = None
    target: str | None = None
    mission: str | None = None
    time1: str | None = None
    time2: str | None = None
    observation_duration: float | None = None
    ring_obs_id: str | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "OPUSObservation":
        """Create OPUSObservation from raw API response data (dict format)."""
        return cls(
            opusid=data.get("opusid", ""),
            instrument=data.get("instrument"),
            planet=data.get("planet"),
            target=data.get("target"),
            mission=data.get("mission"),
            time1=data.get("time1"),
            time2=data.get("time2"),
            observation_duration=_parse_float(data.get("observationduration")),
            ring_obs_id=data.get("ringobsid"),
        )

    @classmethod
    def from_row_data(cls, columns: list[str], row: list[Any]) -> "OPUSObservation":
        """Create OPUSObservation from row data (array format from API).

        The OPUS API returns data as arrays where columns map to row values.
        """
        # Create a mapping from column names to values
        col_map = dict(zip(columns, row))

        return cls(
            opusid=col_map.get("OPUS ID", ""),
            instrument=col_map.get("Instrument Name"),
            planet=col_map.get("Planet"),
            target=col_map.get("Intended Target Name(s)"),
            time1=col_map.get("Observation Start Time (YMDhms)"),
            observation_duration=_parse_float(col_map.get("Observation Duration (secs)")),
        )


class OPUSSearchResponse(BaseModel):
    """OPUS search response wrapper."""

    status: str = "success"
    start_obs: int = 1
    limit: int = 100
    count: int = 0
    available: int = 0
    order: str = ""
    observations: list[OPUSObservation] = Field(default_factory=list)
    error: str | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "OPUSSearchResponse":
        """Create from raw API response."""
        # Check for error response
        if "error" in data:
            return cls(
                status="error",
                error=str(data.get("error")),
            )

        # Parse page data - OPUS returns arrays, not dictionaries
        page = data.get("page", [])
        columns = data.get("columns", [])

        # Handle both array format (API default) and dict format
        observations: list[OPUSObservation] = []
        if page and columns and isinstance(page[0], list):
            # Array format: columns define the keys, page rows are arrays
            observations = [OPUSObservation.from_row_data(columns, row) for row in page]
        elif page and isinstance(page[0], dict):
            # Dict format (in case API changes or different endpoint)
            observations = [OPUSObservation.from_raw_data(obs) for obs in page]

        return cls(
            status="success",
            start_obs=data.get("start_obs", 1),
            limit=data.get("limit", 100),
            count=data.get("count", len(observations)),
            available=data.get("available", 0),
            order=data.get("order", ""),
            observations=observations,
        )


class OPUSCountResponse(BaseModel):
    """OPUS count response."""

    status: str = "success"
    count: int = 0
    error: str | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "OPUSCountResponse":
        """Create from raw API response."""
        # Check for error response
        if "error" in data:
            return cls(
                status="error",
                error=str(data.get("error")),
            )

        # Extract count from data array
        data_array = data.get("data", [])
        if data_array and len(data_array) > 0:
            count = data_array[0].get("result_count", 0)
        else:
            count = 0

        return cls(
            status="success",
            count=count,
        )


class OPUSMetadata(BaseModel):
    """OPUS observation metadata."""

    opusid: str
    general_constraints: dict[str, Any] = Field(default_factory=dict)
    pds_constraints: dict[str, Any] = Field(default_factory=dict)
    image_constraints: dict[str, Any] = Field(default_factory=dict)
    wavelength_constraints: dict[str, Any] = Field(default_factory=dict)
    ring_geometry_constraints: dict[str, Any] = Field(default_factory=dict)
    surface_geometry_constraints: dict[str, Any] = Field(default_factory=dict)
    instrument_constraints: dict[str, Any] = Field(default_factory=dict)
    raw_data: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_raw_data(cls, opusid: str, data: dict[str, Any]) -> "OPUSMetadata":
        """Create from raw API response."""
        return cls(
            opusid=opusid,
            general_constraints=data.get("General Constraints", {}),
            pds_constraints=data.get("PDS Constraints", {}),
            image_constraints=data.get("Image Constraints", {}),
            wavelength_constraints=data.get("Wavelength Constraints", {}),
            ring_geometry_constraints=data.get("Ring Geometry Constraints", {}),
            surface_geometry_constraints=data.get("Surface Geometry Constraints", {}),
            instrument_constraints=cls._extract_instrument_constraints(data),
            raw_data=data,
        )

    @staticmethod
    def _extract_instrument_constraints(data: dict[str, Any]) -> dict[str, Any]:
        """Extract instrument-specific constraints from metadata."""
        instrument_keys = [
            "Cassini ISS Constraints",
            "Cassini VIMS Constraints",
            "Cassini UVIS Constraints",
            "Cassini CIRS Constraints",
            "Voyager ISS Constraints",
            "Galileo SSI Constraints",
            "New Horizons LORRI Constraints",
            "New Horizons MVIC Constraints",
            "Juno JunoCam Constraints",
            "Juno JIRAM Constraints",
            "HST Constraints",
        ]
        for key in instrument_keys:
            if key in data:
                return data[key]
        return {}


class OPUSMetadataResponse(BaseModel):
    """OPUS metadata response wrapper."""

    status: str = "success"
    metadata: OPUSMetadata | None = None
    error: str | None = None

    @classmethod
    def from_raw_data(cls, opusid: str, data: dict[str, Any]) -> "OPUSMetadataResponse":
        """Create from raw API response."""
        if "error" in data:
            return cls(
                status="error",
                error=str(data.get("error")),
            )

        metadata = OPUSMetadata.from_raw_data(opusid, data)
        return cls(
            status="success",
            metadata=metadata,
        )


class OPUSFileInfo(BaseModel):
    """OPUS file information."""

    category: str
    version: str = "Current"
    files: list[str] = Field(default_factory=list)


class OPUSFiles(BaseModel):
    """OPUS files for an observation."""

    opusid: str
    raw_files: list[str] = Field(default_factory=list)
    calibrated_files: list[str] = Field(default_factory=list)
    browse_thumb: str | None = None
    browse_small: str | None = None
    browse_medium: str | None = None
    browse_full: str | None = None
    all_files: dict[str, list[str]] = Field(default_factory=dict)

    @classmethod
    def from_raw_data(cls, opusid: str, data: dict[str, Any]) -> "OPUSFiles":
        """Create from raw API response.

        The OPUS files API returns::

            {"data": {opusid: {category: [url, ...], ...}}, "versions": {...}}

        All categories (including browse images) are lists of URL strings.
        """
        # API nests files under data -> opusid
        file_data = data.get("data", {}).get(opusid, {})

        raw_files: list[str] = []
        calibrated_files: list[str] = []
        all_files: dict[str, list[str]] = {}
        browse_thumb: str | None = None
        browse_small: str | None = None
        browse_medium: str | None = None
        browse_full: str | None = None

        for category, category_data in file_data.items():
            if category.startswith("browse_"):
                # Browse images are lists of URLs; extract first element
                url = cls._extract_first_url(category_data)
                if category == "browse_thumb":
                    browse_thumb = url
                elif category == "browse_small":
                    browse_small = url
                elif category == "browse_medium":
                    browse_medium = url
                elif category == "browse_full":
                    browse_full = url
            elif isinstance(category_data, list):
                # Data file categories are flat lists of URL strings
                all_files[category] = category_data
                if "raw" in category.lower():
                    raw_files.extend(category_data)
                elif "calib" in category.lower():
                    calibrated_files.extend(category_data)

        return cls(
            opusid=opusid,
            raw_files=raw_files,
            calibrated_files=calibrated_files,
            browse_thumb=browse_thumb,
            browse_small=browse_small,
            browse_medium=browse_medium,
            browse_full=browse_full,
            all_files=all_files,
        )

    @staticmethod
    def _extract_first_url(value: Any) -> str | None:
        """Extract the first URL from a value that may be a list or string."""
        if isinstance(value, list) and value:
            return str(value[0])
        if isinstance(value, str):
            return value
        return None


class OPUSFilesResponse(BaseModel):
    """OPUS files response wrapper."""

    status: str = "success"
    files: OPUSFiles | None = None
    error: str | None = None

    @classmethod
    def from_raw_data(cls, opusid: str, data: dict[str, Any]) -> "OPUSFilesResponse":
        """Create from raw API response."""
        if "error" in data:
            return cls(
                status="error",
                error=str(data.get("error")),
            )

        files = OPUSFiles.from_raw_data(opusid, data)
        return cls(
            status="success",
            files=files,
        )


