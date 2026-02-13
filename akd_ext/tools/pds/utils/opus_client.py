"""OPUS API client wrapper with httpx.

The OPUS (Outer Planets Unified Search) API provides access to outer planets
observations from Cassini, Voyager, Galileo, New Horizons, Juno, and HST.

Base URL: https://opus.pds-rings.seti.org/opus/api/
"""

import asyncio
import logging
from types import TracebackType
from typing import Any

import httpx

from .opus_api_models import (
    OPUSCountResponse,
    OPUSFilesResponse,
    OPUSMetadataResponse,
    OPUSSearchResponse,
)

logger = logging.getLogger(__name__)


class OPUSClientError(Exception):
    """Base exception for OPUS client errors."""

    pass


class OPUSRateLimitError(OPUSClientError):
    """Rate limit error for OPUS API."""

    def __init__(self, retry_after: int | None = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


class OPUSClient:
    """Async HTTP client for OPUS REST API."""

    BASE_URL = "https://opus.pds-rings.seti.org/opus/api/"
    DEFAULT_TIMEOUT = 30.0

    # Valid planets from the API documentation
    VALID_PLANETS: set[str] = {"jupiter", "saturn", "uranus", "neptune", "pluto", "other"}

    # Valid missions
    VALID_MISSIONS: set[str] = {
        "cassini",
        "voyager",
        "galileo",
        "new horizons",
        "juno",
        "hst",
    }

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize OPUS client.

        Args:
            base_url: API base URL (default: https://opus.pds-rings.seti.org/opus/api/)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
        """
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "OPUSClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self._get_headers(),
        )
        return self

    async def __aexit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for requests."""
        return {
            "Accept": "application/json",
            "User-Agent": "akd-ext-OPUS-Client/0.1.0",
        }

    async def _request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Make HTTP request with retry logic."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.get(endpoint, params=params)

                if response.status_code == 429:
                    try:
                        retry_after = int(response.headers.get("retry-after", self.retry_delay))
                    except (ValueError, TypeError):
                        retry_after = int(self.retry_delay)
                    if attempt < self.max_retries:
                        logger.warning(f"Rate limited. Retrying in {retry_after} seconds...")
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        raise OPUSRateLimitError(retry_after)

                response.raise_for_status()
                return response

            except httpx.HTTPError as e:
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2**attempt)
                    logger.warning(f"Request failed (attempt {attempt + 1}). Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise OPUSClientError(f"Request failed after {self.max_retries} retries: {e}")

        raise OPUSClientError("Maximum retries exceeded")

    def _build_search_params(
        self,
        target: str | None = None,
        mission: str | None = None,
        instrument: str | None = None,
        planet: str | None = None,
        time_min: str | None = None,
        time_max: str | None = None,
        limit: int = 100,
        startobs: int = 1,
        order: str = "time1,opusid",
    ) -> dict[str, Any]:
        """Build search parameters for OPUS API."""
        params: dict[str, Any] = {
            "limit": str(limit),
            "startobs": str(startobs),
            "order": order,
        }

        if target:
            params["target"] = target

        if mission:
            params["mission"] = mission

        if instrument:
            params["instrument"] = instrument

        if planet:
            params["planet"] = planet

        if time_min:
            params["time1"] = time_min

        if time_max:
            params["time2"] = time_max

        return params

    async def search_observations(
        self,
        target: str | None = None,
        mission: str | None = None,
        instrument: str | None = None,
        planet: str | None = None,
        time_min: str | None = None,
        time_max: str | None = None,
        limit: int = 100,
        startobs: int = 1,
        order: str = "time1,opusid",
    ) -> OPUSSearchResponse:
        """Search for observations in OPUS.

        Args:
            target: Target body (e.g., "Saturn", "Titan", "Saturn Rings")
            mission: Mission name (e.g., "Cassini", "Voyager")
            instrument: Instrument name (e.g., "Cassini ISS", "Voyager ISS")
            planet: Planet filter (jupiter, saturn, uranus, neptune, pluto)
            time_min: Start of time range (ISO 8601 format)
            time_max: End of time range (ISO 8601 format)
            limit: Maximum observations to return (default 100)
            startobs: Starting observation index for pagination (default 1)
            order: Sort order (default "time1,opusid")

        Returns:
            OPUSSearchResponse with observations and metadata
        """
        params = self._build_search_params(
            target=target,
            mission=mission,
            instrument=instrument,
            planet=planet,
            time_min=time_min,
            time_max=time_max,
            limit=limit,
            startobs=startobs,
            order=order,
        )

        response = await self._request("data.json", params)

        try:
            data = response.json()
            return OPUSSearchResponse.from_raw_data(data)
        except Exception as e:
            logger.error(f"Failed to parse OPUS search response: {e}")
            raise OPUSClientError(f"Invalid response format: {e}")

    async def count_observations(
        self,
        target: str | None = None,
        mission: str | None = None,
        instrument: str | None = None,
        planet: str | None = None,
        time_min: str | None = None,
        time_max: str | None = None,
    ) -> OPUSCountResponse:
        """Count observations matching criteria without retrieving them.

        Args:
            target: Target body filter
            mission: Mission name filter
            instrument: Instrument name filter
            planet: Planet filter
            time_min: Start of time range
            time_max: End of time range

        Returns:
            OPUSCountResponse with count
        """
        params = self._build_search_params(
            target=target,
            mission=mission,
            instrument=instrument,
            planet=planet,
            time_min=time_min,
            time_max=time_max,
            limit=1,  # We only need the count
            startobs=1,
        )
        # Remove limit and startobs for count request
        del params["limit"]
        del params["startobs"]
        del params["order"]

        response = await self._request("meta/result_count.json", params)

        try:
            data = response.json()
            return OPUSCountResponse.from_raw_data(data)
        except Exception as e:
            logger.error(f"Failed to parse OPUS count response: {e}")
            raise OPUSClientError(f"Invalid response format: {e}")

    async def get_metadata(
        self,
        opusid: str,
    ) -> OPUSMetadataResponse:
        """Get detailed metadata for a specific observation.

        Args:
            opusid: OPUS observation ID (e.g., "co-iss-n1460960653")

        Returns:
            OPUSMetadataResponse with full observation metadata
        """
        response = await self._request(f"metadata/{opusid}.json")

        try:
            data = response.json()
            return OPUSMetadataResponse.from_raw_data(opusid, data)
        except Exception as e:
            logger.error(f"Failed to parse OPUS metadata response: {e}")
            raise OPUSClientError(f"Invalid response format: {e}")

    async def get_files(
        self,
        opusid: str,
    ) -> OPUSFilesResponse:
        """Get downloadable file URLs for an observation.

        Args:
            opusid: OPUS observation ID (e.g., "co-iss-n1460960653")

        Returns:
            OPUSFilesResponse with raw, calibrated, and browse image URLs
        """
        response = await self._request(f"files/{opusid}.json")

        try:
            data = response.json()
            return OPUSFilesResponse.from_raw_data(opusid, data)
        except Exception as e:
            logger.error(f"Failed to parse OPUS files response: {e}")
            raise OPUSClientError(f"Invalid response format: {e}")

