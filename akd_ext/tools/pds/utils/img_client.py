"""IMG Atlas API client wrapper with httpx.

The PDS Imaging Node Atlas API uses Apache Solr for querying planetary imagery
from various missions including MER, MSL, Mars 2020, Cassini, Voyager, LRO, and MESSENGER.

Base URL: https://pds-imaging.jpl.nasa.gov/solr/pds_archives/
"""

import asyncio
from loguru import logger
from types import TracebackType
from typing import Any

import httpx

from .img_api_models import IMGCountResponse, IMGFacetResponse, IMGSearchResponse


class IMGAtlasClientError(Exception):
    """Base exception for IMG Atlas client errors."""

    pass


class IMGAtlasRateLimitError(IMGAtlasClientError):
    """Rate limit error for IMG Atlas API."""

    def __init__(self, retry_after: int | None = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


class IMGAtlasClient:
    """Async HTTP client for IMG Atlas Solr API."""

    BASE_URL = "https://pds-imaging.jpl.nasa.gov/solr/pds_archives/"
    DEFAULT_TIMEOUT = 30.0

    # Valid targets from the API documentation
    VALID_TARGETS: set[str] = {
        "mars",
        "saturn",
        "moon",
        "mercury",
        "titan",
        "enceladus",
        "jupiter",
        "io",
        "europa",
        "ganymede",
        "callisto",
    }

    # Valid facet fields that can be queried
    VALID_FACET_FIELDS: set[str] = {
        "TARGET",
        "ATLAS_MISSION_NAME",
        "ATLAS_INSTRUMENT_NAME",
        "ATLAS_SPACECRAFT_NAME",
        "PRODUCT_TYPE",
        "FRAME_TYPE",
        "FILTER_NAME",
        "pds_standard",
    }

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize IMG Atlas client.

        Args:
            base_url: API base URL (default: https://pds-imaging.jpl.nasa.gov/solr/pds_archives/)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
        """
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "IMGAtlasClient":
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
            "User-Agent": "IMG-MCP-Server/0.1.0",
        }

    def _build_filter_queries(
        self,
        target: str | None = None,
        mission: str | None = None,
        instrument: str | None = None,
        spacecraft: str | None = None,
        start_time: str | None = None,
        stop_time: str | None = None,
        sol_min: int | None = None,
        sol_max: int | None = None,
        product_type: str | None = None,
        filter_name: str | None = None,
        frame_type: str | None = None,
        exposure_min: float | None = None,
        exposure_max: float | None = None,
        local_solar_time: str | None = None,
    ) -> list[str]:
        """Build Solr filter queries from parameters."""
        fq_list: list[str] = []

        if target:
            fq_list.append(f"TARGET:{target}")

        if mission:
            # Use quotes for exact matching when spaces are present, wildcard otherwise
            if " " in mission:
                fq_list.append(f'ATLAS_MISSION_NAME:"{mission}"')
            else:
                fq_list.append(f"ATLAS_MISSION_NAME:*{mission}*")

        if instrument:
            if " " in instrument:
                fq_list.append(f'ATLAS_INSTRUMENT_NAME:"{instrument}"')
            else:
                fq_list.append(f"ATLAS_INSTRUMENT_NAME:*{instrument}*")

        if spacecraft:
            if " " in spacecraft:
                fq_list.append(f'ATLAS_SPACECRAFT_NAME:"{spacecraft}"')
            else:
                fq_list.append(f"ATLAS_SPACECRAFT_NAME:*{spacecraft}*")

        if product_type:
            fq_list.append(f"PRODUCT_TYPE:{product_type}")

        if filter_name:
            fq_list.append(f"FILTER_NAME:*{filter_name}*")

        if frame_type:
            fq_list.append(f"FRAME_TYPE:{frame_type}")

        # Time range
        if start_time or stop_time:
            time_start = start_time or "*"
            time_end = stop_time or "*"
            fq_list.append(f"START_TIME:[{time_start} TO {time_end}]")

        # Sol range (Mars missions)
        if sol_min is not None or sol_max is not None:
            sol_start = sol_min if sol_min is not None else "*"
            sol_end = sol_max if sol_max is not None else "*"
            fq_list.append(f"PLANET_DAY_NUMBER:[{sol_start} TO {sol_end}]")

        # Exposure duration range (in milliseconds)
        if exposure_min is not None or exposure_max is not None:
            exp_start = exposure_min if exposure_min is not None else "*"
            exp_end = exposure_max if exposure_max is not None else "*"
            fq_list.append(f"EXPOSURE_DURATION:[{exp_start} TO {exp_end}]")

        # Local solar time filter
        if local_solar_time:
            fq_list.append(f"LOCAL_TRUE_SOLAR_TIME:*{local_solar_time}*")

        return fq_list

    async def _request(
        self,
        endpoint: str,
        params: dict[str, Any],
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
                        raise IMGAtlasRateLimitError(retry_after)

                response.raise_for_status()
                return response

            except httpx.HTTPError as e:
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2**attempt)
                    logger.warning(f"Request failed (attempt {attempt + 1}). Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise IMGAtlasClientError(f"Request failed after {self.max_retries} retries: {e}")

        raise IMGAtlasClientError("Maximum retries exceeded")

    async def search_products(
        self,
        target: str | None = None,
        mission: str | None = None,
        instrument: str | None = None,
        spacecraft: str | None = None,
        start_time: str | None = None,
        stop_time: str | None = None,
        sol_min: int | None = None,
        sol_max: int | None = None,
        product_type: str | None = None,
        filter_name: str | None = None,
        frame_type: str | None = None,
        exposure_min: float | None = None,
        exposure_max: float | None = None,
        local_solar_time: str | None = None,
        rows: int = 100,
        start: int = 0,
        sort: str | None = None,
        fields: list[str] | None = None,
    ) -> IMGSearchResponse:
        """Search for imagery products in the Atlas archive.

        Args:
            target: Target body (e.g., "Mars", "Saturn", "Moon")
            mission: Mission name filter (e.g., "MSL", "MER", "Cassini")
            instrument: Instrument name filter (e.g., "HAZCAM", "MASTCAM", "ISS")
            spacecraft: Spacecraft name filter (e.g., "CURIOSITY", "SPIRIT")
            start_time: Start of time range (ISO 8601 format)
            stop_time: End of time range (ISO 8601 format)
            sol_min: Minimum sol number (Mars missions)
            sol_max: Maximum sol number (Mars missions)
            product_type: Product type filter (e.g., "EDR", "RDR")
            filter_name: Camera filter name (e.g., "L0", "R0", "RED")
            frame_type: Frame type filter (e.g., "FULL", "SUBFRAME")
            exposure_min: Minimum exposure duration in milliseconds
            exposure_max: Maximum exposure duration in milliseconds
            local_solar_time: Local true solar time filter (e.g., "12:00")
            rows: Maximum products to return (default 100)
            start: Pagination offset (default 0)
            sort: Sort order (e.g., "START_TIME desc")
            fields: Specific fields to return (None for all)

        Returns:
            IMGSearchResponse with products and metadata
        """
        # Build filter queries
        fq_list = self._build_filter_queries(
            target=target,
            mission=mission,
            instrument=instrument,
            spacecraft=spacecraft,
            start_time=start_time,
            stop_time=stop_time,
            sol_min=sol_min,
            sol_max=sol_max,
            product_type=product_type,
            filter_name=filter_name,
            frame_type=frame_type,
            exposure_min=exposure_min,
            exposure_max=exposure_max,
            local_solar_time=local_solar_time,
        )

        params: dict[str, Any] = {
            "q": "*:*",
            "wt": "json",
            "rows": str(rows),
            "start": str(start),
        }

        # Add filter queries
        if fq_list:
            params["fq"] = fq_list

        # Add sort if specified
        if sort:
            params["sort"] = sort

        # Add field list if specified
        if fields:
            params["fl"] = ",".join(fields)

        response = await self._request("select", params)

        try:
            data = response.json()
            return IMGSearchResponse.from_raw_data(data)
        except Exception as e:
            logger.error(f"Failed to parse IMG Atlas search response: {e}")
            raise IMGAtlasClientError(f"Invalid response format: {e}")

    async def count_products(
        self,
        target: str | None = None,
        mission: str | None = None,
        instrument: str | None = None,
        spacecraft: str | None = None,
        start_time: str | None = None,
        stop_time: str | None = None,
        sol_min: int | None = None,
        sol_max: int | None = None,
        product_type: str | None = None,
        filter_name: str | None = None,
        frame_type: str | None = None,
        exposure_min: float | None = None,
        exposure_max: float | None = None,
        local_solar_time: str | None = None,
    ) -> IMGCountResponse:
        """Count products matching criteria without retrieving them.

        Args:
            target: Target body filter
            mission: Mission name filter
            instrument: Instrument name filter
            spacecraft: Spacecraft name filter
            start_time: Start of time range
            stop_time: End of time range
            sol_min: Minimum sol number
            sol_max: Maximum sol number
            product_type: Product type filter
            filter_name: Camera filter name
            frame_type: Frame type filter
            exposure_min: Minimum exposure duration in milliseconds
            exposure_max: Maximum exposure duration in milliseconds
            local_solar_time: Local true solar time filter

        Returns:
            IMGCountResponse with count
        """
        # Build filter queries
        fq_list = self._build_filter_queries(
            target=target,
            mission=mission,
            instrument=instrument,
            spacecraft=spacecraft,
            start_time=start_time,
            stop_time=stop_time,
            sol_min=sol_min,
            sol_max=sol_max,
            product_type=product_type,
            filter_name=filter_name,
            frame_type=frame_type,
            exposure_min=exposure_min,
            exposure_max=exposure_max,
            local_solar_time=local_solar_time,
        )

        params: dict[str, Any] = {
            "q": "*:*",
            "wt": "json",
            "rows": "0",  # Don't return any documents, just count
        }

        # Add filter queries
        if fq_list:
            params["fq"] = fq_list

        response = await self._request("select", params)

        try:
            data = response.json()
            return IMGCountResponse.from_raw_data(data)
        except Exception as e:
            logger.error(f"Failed to parse IMG Atlas count response: {e}")
            raise IMGAtlasClientError(f"Invalid response format: {e}")

    async def get_product(
        self,
        product_id: str,
    ) -> IMGSearchResponse:
        """Get a single product by its ID.

        Args:
            product_id: Product identifier (uuid or PRODUCT_ID)

        Returns:
            IMGSearchResponse with the single product
        """
        # Try to find by uuid or PRODUCT_ID
        params: dict[str, Any] = {
            "q": f'uuid:"{product_id}" OR PRODUCT_ID:"{product_id}"',
            "wt": "json",
            "rows": "1",
        }

        response = await self._request("select", params)

        try:
            data = response.json()
            return IMGSearchResponse.from_raw_data(data)
        except Exception as e:
            logger.error(f"Failed to parse IMG Atlas product response: {e}")
            raise IMGAtlasClientError(f"Invalid response format: {e}")

    async def get_facets(
        self,
        facet_field: str,
        limit: int = 100,
        target: str | None = None,
        mission: str | None = None,
        instrument: str | None = None,
    ) -> IMGFacetResponse:
        """Get available values and counts for a faceted field.

        This enables dynamic discovery of targets, missions, instruments, etc.
        without relying on hardcoded lists.

        Args:
            facet_field: Field to facet on (e.g., "TARGET", "ATLAS_MISSION_NAME",
                "ATLAS_INSTRUMENT_NAME", "PRODUCT_TYPE", "FRAME_TYPE", "FILTER_NAME")
            limit: Maximum number of facet values to return (default 100)
            target: Optional target filter to narrow results
            mission: Optional mission filter to narrow results
            instrument: Optional instrument filter to narrow results

        Returns:
            IMGFacetResponse with available values and counts
        """
        # Validate facet field
        if facet_field not in self.VALID_FACET_FIELDS:
            raise IMGAtlasClientError(
                f"Invalid facet field: {facet_field}. Valid fields: {', '.join(sorted(self.VALID_FACET_FIELDS))}"
            )

        # Build filter queries for optional filters
        fq_list: list[str] = []
        if target:
            fq_list.append(f"TARGET:{target}")
        if mission:
            if " " in mission:
                fq_list.append(f'ATLAS_MISSION_NAME:"{mission}"')
            else:
                fq_list.append(f"ATLAS_MISSION_NAME:*{mission}*")
        if instrument:
            if " " in instrument:
                fq_list.append(f'ATLAS_INSTRUMENT_NAME:"{instrument}"')
            else:
                fq_list.append(f"ATLAS_INSTRUMENT_NAME:*{instrument}*")

        params: dict[str, Any] = {
            "q": "*:*",
            "wt": "json",
            "rows": "0",  # Don't return documents, just facets
            "facet": "true",
            "facet.field": facet_field,
            "facet.limit": str(limit),
            "facet.mincount": "1",  # Only values with at least 1 document
            "facet.sort": "count",  # Sort by count descending
        }

        if fq_list:
            params["fq"] = fq_list

        response = await self._request("select", params)

        try:
            data = response.json()
            return IMGFacetResponse.from_raw_data(data, facet_field)
        except Exception as e:
            logger.error(f"Failed to parse IMG Atlas facet response: {e}")
            raise IMGAtlasClientError(f"Invalid response format: {e}")
