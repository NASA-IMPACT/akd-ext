"""Pydantic models for SBN CATCH API responses.

The CATCH (Comet Asteroid Telescopic Catalog Hunter) API provides access to
observations of comets and asteroids from various astronomical surveys.

Base URL: https://catch-api.astro.umd.edu/
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


class CatchSource(BaseModel):
    """CATCH data source information."""

    source: str
    source_name: str | None = None
    count: int = 0
    start_date: str | None = None
    stop_date: str | None = None
    nights: int | None = None
    updated: str | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "CatchSource":
        """Create CatchSource from raw API response data."""
        return cls(
            source=data.get("source", ""),
            source_name=data.get("source_name"),
            count=_parse_int(data.get("count")) or 0,
            start_date=data.get("start_date"),
            stop_date=data.get("stop_date"),
            nights=_parse_int(data.get("nights")),
            updated=data.get("updated"),
        )


class CatchSourcesResponse(BaseModel):
    """CATCH sources list response."""

    status: str = "success"
    sources: list[CatchSource] = Field(default_factory=list)
    error: str | None = None

    @classmethod
    def from_raw_data(cls, data: list[dict[str, Any]] | dict[str, Any]) -> "CatchSourcesResponse":
        """Create from raw API response."""
        if isinstance(data, dict) and "error" in data:
            return cls(
                status="error",
                error=str(data.get("error")),
            )

        if isinstance(data, list):
            sources = [CatchSource.from_raw_data(s) for s in data]
            return cls(
                status="success",
                sources=sources,
            )

        return cls(status="error", error="Unexpected response format")


class CatchObservation(BaseModel):
    """CATCH observation/detection from a survey."""

    product_id: str
    source: str
    mjd_start: float | None = None
    mjd_stop: float | None = None
    filter: str | None = None
    exposure: float | None = None
    seeing: float | None = None
    airmass: float | None = None
    maglimit: float | None = None
    archive_url: str | None = None
    cutout_url: str | None = None
    preview_url: str | None = None

    # Ephemeris fields (for moving targets)
    ra: float | None = None
    dec: float | None = None
    dra: float | None = None
    ddec: float | None = None
    rh: float | None = None
    delta: float | None = None
    phase: float | None = None
    vmag: float | None = None
    unc_a: float | None = None
    unc_b: float | None = None
    unc_theta: float | None = None
    date: str | None = None

    # Field of view (can be string or list depending on source)
    fov: str | list[list[float]] | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "CatchObservation":
        """Create CatchObservation from raw API response data."""
        return cls(
            product_id=data.get("product_id", ""),
            source=data.get("source", ""),
            mjd_start=_parse_float(data.get("mjd_start")),
            mjd_stop=_parse_float(data.get("mjd_stop")),
            filter=data.get("filter"),
            exposure=_parse_float(data.get("exposure")),
            seeing=_parse_float(data.get("seeing")),
            airmass=_parse_float(data.get("airmass")),
            maglimit=_parse_float(data.get("maglimit")),
            archive_url=data.get("archive_url"),
            cutout_url=data.get("cutout_url"),
            preview_url=data.get("preview_url"),
            ra=_parse_float(data.get("ra")),
            dec=_parse_float(data.get("dec")),
            dra=_parse_float(data.get("dra")),
            ddec=_parse_float(data.get("ddec")),
            rh=_parse_float(data.get("rh")),
            delta=_parse_float(data.get("delta")),
            phase=_parse_float(data.get("phase")),
            vmag=_parse_float(data.get("vmag")),
            unc_a=_parse_float(data.get("unc_a")),
            unc_b=_parse_float(data.get("unc_b")),
            unc_theta=_parse_float(data.get("unc_theta")),
            date=data.get("date"),
            fov=data.get("fov"),
        )


class CatchSourceStatus(BaseModel):
    """Status of a data source in a job."""

    source: str
    status: str
    count: int | None = None
    elapsed: str | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "CatchSourceStatus":
        """Create from raw API response data."""
        return cls(
            source=data.get("source", ""),
            status=data.get("status", "unknown"),
            count=_parse_int(data.get("count")),
            elapsed=data.get("elapsed"),
        )


class CatchJobResponse(BaseModel):
    """CATCH job submission response."""

    status: str = "success"
    job_id: str | None = None
    queued: bool = False
    results_url: str | None = None
    message_stream: str | None = None
    query: dict[str, Any] = Field(default_factory=dict)
    version: str | None = None
    error: str | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "CatchJobResponse":
        """Create from raw API response."""
        if "error" in data:
            return cls(
                status="error",
                error=str(data.get("error")),
            )

        return cls(
            status="success",
            job_id=data.get("job_id"),
            queued=data.get("queued", False),
            results_url=data.get("results"),
            message_stream=data.get("message_stream"),
            query=data.get("query", {}),
            version=data.get("version"),
        )


class CatchResultsResponse(BaseModel):
    """CATCH job results response."""

    status: str = "success"
    job_id: str = ""
    count: int = 0
    observations: list[CatchObservation] = Field(default_factory=list)
    source_status: list[CatchSourceStatus] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    version: str | None = None
    error: str | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "CatchResultsResponse":
        """Create from raw API response."""
        if "error" in data:
            return cls(
                status="error",
                error=str(data.get("error")),
            )

        # Parse observations from data array
        observations_data = data.get("data", [])
        observations = [CatchObservation.from_raw_data(obs) for obs in observations_data]

        # Parse source status
        status_data = data.get("status", [])
        source_status = [CatchSourceStatus.from_raw_data(s) for s in status_data]

        return cls(
            status="success",
            job_id=data.get("job_id", ""),
            count=_parse_int(data.get("count")) or len(observations),
            observations=observations,
            source_status=source_status,
            parameters=data.get("parameters", {}),
            version=data.get("version"),
        )


class CatchStatusResponse(BaseModel):
    """CATCH job status response."""

    status: str = "success"
    job_id: str = ""
    source_status: list[CatchSourceStatus] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    version: str | None = None
    error: str | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "CatchStatusResponse":
        """Create from raw API response."""
        if "error" in data:
            return cls(
                status="error",
                error=str(data.get("error")),
            )

        # Parse source status
        status_data = data.get("status", [])
        source_status = [CatchSourceStatus.from_raw_data(s) for s in status_data]

        return cls(
            status="success",
            job_id=data.get("job_id", ""),
            source_status=source_status,
            parameters=data.get("parameters", {}),
            version=data.get("version"),
        )


class CatchFixedResponse(BaseModel):
    """CATCH fixed coordinate search response."""

    status: str = "success"
    count: int = 0
    observations: list[CatchObservation] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> "CatchFixedResponse":
        """Create from raw API response."""
        if "error" in data:
            return cls(
                status="error",
                error=str(data.get("error")),
            )

        # Parse observations from data array
        observations_data = data.get("data", [])
        observations = [CatchObservation.from_raw_data(obs) for obs in observations_data]

        return cls(
            status="success",
            count=_parse_int(data.get("count")) or len(observations),
            observations=observations,
            parameters=data.get("parameters", {}),
        )
