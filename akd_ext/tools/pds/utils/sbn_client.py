"""SBN CATCH API client wrapper with httpx.

The CATCH (Comet Asteroid Telescopic Catalog Hunter) API provides access to
observations of comets and asteroids from various astronomical surveys.

Base URL: https://catch-api.astro.umd.edu/
"""

import asyncio
from loguru import logger
from types import TracebackType
from typing import Any

import httpx

from .sbn_api_models import (
    CatchFixedResponse,
    CatchJobResponse,
    CatchResultsResponse,
    CatchSourcesResponse,
    CatchStatusResponse,
)


class SBNCatchClientError(Exception):
    """Base exception for SBN CATCH client errors."""

    pass


class SBNCatchRateLimitError(SBNCatchClientError):
    """Rate limit error for CATCH API."""

    def __init__(self, retry_after: int | None = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


class SBNCatchJobError(SBNCatchClientError):
    """Job-related error for CATCH API."""

    def __init__(self, job_id: str, message: str):
        self.job_id = job_id
        super().__init__(f"Job {job_id}: {message}")


class SBNCatchClient:
    """Async HTTP client for SBN CATCH API."""

    BASE_URL = "https://catch-api.astro.umd.edu/"
    DEFAULT_TIMEOUT = 60.0

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize CATCH client.

        Args:
            base_url: CATCH API base URL (default: https://catch-api.astro.umd.edu/)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
        """
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "SBNCatchClient":
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
            "User-Agent": "SBN-AKD-EXT/0.1.0",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Make HTTP request with retry logic."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.request(method, endpoint, params=params)

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
                        raise SBNCatchRateLimitError(retry_after)

                response.raise_for_status()
                return response

            except httpx.HTTPError as e:
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2**attempt)
                    logger.warning(f"Request failed (attempt {attempt + 1}). Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise SBNCatchClientError(f"Request failed after {self.max_retries} retries: {e}")

        raise SBNCatchClientError("Maximum retries exceeded")

    async def list_sources(self) -> CatchSourcesResponse:
        """List available data sources.

        Returns:
            CatchSourcesResponse with available survey sources
        """
        response = await self._request("GET", "status/sources")

        try:
            data = response.json()
            return CatchSourcesResponse.from_raw_data(data)
        except Exception as e:
            logger.error(f"Failed to parse CATCH sources response: {e}")
            raise SBNCatchClientError(f"Invalid response format: {e}")

    async def search_moving_target(
        self,
        target: str,
        sources: list[str] | None = None,
        start_date: str | None = None,
        stop_date: str | None = None,
        uncertainty_ellipse: bool = False,
        padding: float = 0.0,
        cached: bool = True,
    ) -> CatchJobResponse:
        """Search for observations of a moving target (comet/asteroid).

        Args:
            target: JPL Horizons-resolvable designation (e.g., "65803", "1P/Halley", "2019 DQ123")
            sources: List of data sources to search (None = all sources)
            start_date: Start date filter (format: "YYYY-MM-DD HH:MM")
            stop_date: Stop date filter (format: "YYYY-MM-DD HH:MM")
            uncertainty_ellipse: Include ephemeris uncertainty in search
            padding: Search margin in arcminutes (0-120)
            cached: Use cached results if available

        Returns:
            CatchJobResponse with job_id and status
        """
        params: dict[str, Any] = {
            "target": target,
            "cached": str(cached).lower(),
        }

        if sources:
            params["sources"] = sources
        if start_date:
            params["start_date"] = start_date
        if stop_date:
            params["stop_date"] = stop_date
        if uncertainty_ellipse:
            params["uncertainty_ellipse"] = "true"
        if padding > 0:
            params["padding"] = str(padding)

        response = await self._request("GET", "catch", params=params)

        try:
            data = response.json()
            return CatchJobResponse.from_raw_data(data)
        except Exception as e:
            logger.error(f"Failed to parse CATCH job response: {e}")
            raise SBNCatchClientError(f"Invalid response format: {e}")

    async def get_caught_results(self, job_id: str) -> CatchResultsResponse:
        """Get results for a completed job.

        Args:
            job_id: Job ID from search_moving_target

        Returns:
            CatchResultsResponse with observations
        """
        response = await self._request("GET", f"caught/{job_id}")

        try:
            data = response.json()
            return CatchResultsResponse.from_raw_data(data)
        except Exception as e:
            logger.error(f"Failed to parse CATCH results response: {e}")
            raise SBNCatchClientError(f"Invalid response format: {e}")

    async def get_job_status(self, job_id: str) -> CatchStatusResponse:
        """Check status of a job.

        Args:
            job_id: Job ID to check

        Returns:
            CatchStatusResponse with job status
        """
        response = await self._request("GET", f"status/{job_id}")

        try:
            data = response.json()
            return CatchStatusResponse.from_raw_data(data)
        except Exception as e:
            logger.error(f"Failed to parse CATCH status response: {e}")
            raise SBNCatchClientError(f"Invalid response format: {e}")

    async def wait_for_job(
        self,
        job_id: str,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> CatchResultsResponse:
        """Wait for a job to complete and return results.

        Args:
            job_id: Job ID to wait for
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds

        Returns:
            CatchResultsResponse with observations

        Raises:
            SBNCatchJobError: If job fails or times out
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise SBNCatchJobError(job_id, f"Job timed out after {timeout} seconds")

            status = await self.get_job_status(job_id)

            if status.error:
                raise SBNCatchJobError(job_id, status.error)

            # Check if all sources are complete
            all_complete = True
            has_error = False
            for source_status in status.source_status:
                if source_status.status in ("queued", "running"):
                    all_complete = False
                elif source_status.status == "error":
                    has_error = True

            if all_complete:
                if has_error:
                    logger.warning(f"Job {job_id} completed with some source errors")
                return await self.get_caught_results(job_id)

            await asyncio.sleep(poll_interval)

    async def search_fixed_target(
        self,
        ra: str,
        dec: str,
        sources: list[str] | None = None,
        radius: float = 10.0,
        start_date: str | None = None,
        stop_date: str | None = None,
        intersection_type: str | None = None,
    ) -> CatchFixedResponse:
        """Search for observations at fixed sky coordinates.

        Args:
            ra: Right ascension (sexagesimal HH:MM:SS or decimal degrees)
            dec: Declination (sexagesimal ±DD:MM:SS or decimal degrees)
            sources: List of data sources to search (None = all sources)
            radius: Search radius in arcminutes (0-120)
            start_date: Start date filter (format: "YYYY-MM-DD HH:MM")
            stop_date: Stop date filter (format: "YYYY-MM-DD HH:MM")
            intersection_type: How search area intersects images
                (ImageIntersectsArea, ImageContainsArea, AreaContainsImage)

        Returns:
            CatchFixedResponse with observations
        """
        params: dict[str, Any] = {
            "ra": ra,
            "dec": dec,
            "radius": str(radius),
        }

        if sources:
            params["sources"] = sources
        if start_date:
            params["start_date"] = start_date
        if stop_date:
            params["stop_date"] = stop_date
        if intersection_type:
            params["intersection_type"] = intersection_type

        response = await self._request("GET", "fixed", params=params)

        try:
            data = response.json()
            return CatchFixedResponse.from_raw_data(data)
        except Exception as e:
            logger.error(f"Failed to parse CATCH fixed response: {e}")
            raise SBNCatchClientError(f"Invalid response format: {e}")

    async def search_and_wait(
        self,
        target: str,
        sources: list[str] | None = None,
        start_date: str | None = None,
        stop_date: str | None = None,
        uncertainty_ellipse: bool = False,
        padding: float = 0.0,
        cached: bool = True,
        timeout: float = 120.0,
        poll_interval: float = 2.0,
    ) -> CatchResultsResponse:
        """Search for a moving target and wait for results.

        Convenience method that combines search_moving_target and wait_for_job.

        Args:
            target: JPL Horizons-resolvable designation
            sources: List of data sources to search
            start_date: Start date filter
            stop_date: Stop date filter
            uncertainty_ellipse: Include ephemeris uncertainty
            padding: Search margin in arcminutes
            cached: Use cached results if available
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds

        Returns:
            CatchResultsResponse with observations
        """
        job = await self.search_moving_target(
            target=target,
            sources=sources,
            start_date=start_date,
            stop_date=stop_date,
            uncertainty_ellipse=uncertainty_ellipse,
            padding=padding,
            cached=cached,
        )

        if job.error:
            raise SBNCatchClientError(job.error)

        if not job.job_id:
            raise SBNCatchClientError("No job ID returned from search")

        # If not queued, results are already available
        if not job.queued:
            return await self.get_caught_results(job.job_id)

        # Wait for job to complete
        return await self.wait_for_job(
            job_id=job.job_id,
            timeout=timeout,
            poll_interval=poll_interval,
        )
