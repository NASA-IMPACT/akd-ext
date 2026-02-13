"""PDS4 API client wrapper with httpx.

Recommended Discovery Workflow:
1. search_bundles() - Discover high-level data bundles via faceting
2. search_collections() - Find specific collections with limit > 0
3. get_collection_products() - Use lidvid from step 2 to explore products
4. search_observational() - Direct search for observational data products

Context-based Discovery:
- search_context_investigations() - Find missions/projects
- search_context_targets() - Find celestial bodies
- search_context_instruments() - Find scientific instruments
- search_context_instrument_hosts() - Find spacecraft/rovers
- search_context_collections() - Find data collections by context references

Always extract URNs dynamically from search results rather than using hardcoded values.
"""

import asyncio
from loguru import logger
import re
from types import TracebackType
from typing import Any
from urllib.parse import urlencode, urljoin

import httpx
from pydantic import ValidationError


def validate_urn(urn: str) -> str:
    """Validate and return a PDS4 URN.

    Args:
        urn: The URN to validate

    Returns:
        The validated URN

    Raises:
        ValueError: If the URN format is invalid
    """
    # Basic URN pattern - starts with urn:nasa:pds: and contains valid characters
    pattern = r"^urn:nasa:pds:[a-z_]+:[a-z_\.\-\w:]+$"
    if not re.match(pattern, urn, re.IGNORECASE):
        raise ValueError(f"Invalid URN format: {urn}")
    return urn


def validate_coordinates(
    bbox_north: float | None = None,
    bbox_south: float | None = None,
    bbox_east: float | None = None,
    bbox_west: float | None = None,
) -> None:
    """Validate geographic bounding box coordinates.

    Args:
        bbox_north: North latitude (-90 to 90)
        bbox_south: South latitude (-90 to 90)
        bbox_east: East longitude (-180 to 360, planetary bodies can use 0-360)
        bbox_west: West longitude (-180 to 360)

    Raises:
        ValueError: If coordinates are out of valid range
    """
    if bbox_north is not None and not (-90 <= bbox_north <= 90):
        raise ValueError(f"bbox_north must be between -90 and 90, got {bbox_north}")
    if bbox_south is not None and not (-90 <= bbox_south <= 90):
        raise ValueError(f"bbox_south must be between -90 and 90, got {bbox_south}")
    if bbox_north is not None and bbox_south is not None and bbox_north < bbox_south:
        raise ValueError(f"bbox_north ({bbox_north}) must be >= bbox_south ({bbox_south})")
    # Longitude validation - planetary data often uses 0-360 range
    if bbox_east is not None and not (-180 <= bbox_east <= 360):
        raise ValueError(f"bbox_east must be between -180 and 360, got {bbox_east}")
    if bbox_west is not None and not (-180 <= bbox_west <= 360):
        raise ValueError(f"bbox_west must be between -180 and 360, got {bbox_west}")


class PDS4ClientError(Exception):
    """Base exception for PDS4 client errors."""

    pass


class PDS4RateLimitError(PDS4ClientError):
    """Rate limit error for PDS4 API."""

    def __init__(self, retry_after: int | None = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


class PDS4Client:
    """Async HTTP client for NASA PDS4 Search API."""

    BASE_URL = "https://pds.mcp.nasa.gov/api/search/1/"
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_PAGE_SIZE = 25
    MAX_PAGE_SIZE = 1000

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize PDS4 client.

        Args:
            base_url: PDS4 API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
        """
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "PDS4Client":
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
        headers = {
            "Accept": "application/json",
            "User-Agent": "PDS4-MCP-Server/0.1.0",
        }
        return headers

    def _clean_urn(self, urn: str) -> str:
        """Clean a URN by removing version information.

        Args:
            urn: The URN to clean (e.g., "urn:nasa:pds:context:investigation:mission.juno::1.0")

        Returns:
            Cleaned URN without version (e.g., "urn:nasa:pds:context:investigation:mission.juno")
        """
        if "::" in urn:
            return urn.split("::")[0]
        return urn

    def _build_search_url(self, base_url: str, params: dict[str, Any]) -> str:
        """Build a search URL from base URL and parameters.

        Args:
            base_url: The base API URL
            params: Dictionary of query parameters

        Returns:
            Complete URL with query parameters
        """
        # Filter out None values and empty strings
        filtered_params = {k: v for k, v in params.items() if v is not None and v != ""}
        query_string = urlencode(filtered_params)
        return f"{base_url}?{query_string}" if query_string else base_url

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        **kwargs,
    ) -> httpx.Response:
        """Make HTTP request with retry logic."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        url = urljoin(self.base_url, endpoint)

        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.request(
                    method=method,
                    url=url,
                    params=params,
                    **kwargs,
                )

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
                        raise PDS4RateLimitError(retry_after)

                response.raise_for_status()
                return response

            except httpx.HTTPError as e:
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2**attempt)
                    logger.warning(f"Request failed (attempt {attempt + 1}). Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise PDS4ClientError(f"Request failed after {self.max_retries} retries: {e}")

        raise PDS4ClientError("Maximum retries exceeded")

    async def search_bundles(
        self,
        title_query: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        processing_level: str | None = None,
        limit: int | None = None,
        facet_fields: list[str] | None = None,
        facet_limit: int = 25,
    ):
        """Search for bundles in PDS4.

        Args:
            title_query: Search query for bundle titles (e.g., "Lunar")
            start_time: Start of time range (ISO 8601 format, e.g., "2020-01-01T00:00:00Z")
            end_time: End of time range (ISO 8601 format)
            processing_level: Filter by processing level ("Raw", "Calibrated", "Derived")
            limit: Number of actual products to return (set to 0 for facets only)
            facet_fields: List of fields to facet on (e.g., ["pds:Identification_Area.pds:title", "lidvid"])
            facet_limit: Maximum number of facet values to return

        Returns:
            PDS4SearchResponse containing bundles and facets
        """
        # Import here to avoid circular dependency
        from akd_ext.tools.pds.utils.pds4_api_models import PDS4SearchResponse

        params: dict[str, str] = {}
        filters: list[str] = []

        if title_query:
            filters.append(f'(title like "{title_query}")')

        # Temporal filters
        if start_time:
            filters.append(f'(pds:Time_Coordinates.pds:start_date_time ge "{start_time}")')
        if end_time:
            filters.append(f'(pds:Time_Coordinates.pds:stop_date_time lt "{end_time}")')

        # Processing level filter
        if processing_level:
            filters.append(f'(pds:Primary_Result_Summary.pds:processing_level eq "{processing_level}")')

        if filters:
            params["q"] = f"({' and '.join(filters)})"

        if facet_fields:
            params["facet-fields"] = ",".join(facet_fields)

        params["facet-limit"] = str(facet_limit)
        params["limit"] = str(limit or 0)

        response = await self._request("GET", "classes/bundle", params=params)

        try:
            data = response.json()
            return PDS4SearchResponse.from_raw_data(data)
        except ValidationError as e:
            logger.error(f"Failed to parse bundle search response: {e}")
            raise PDS4ClientError(f"Invalid response format: {e}")

    async def search_collections(
        self,
        title_query: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        processing_level: str | None = None,
        limit: int | None = None,
        facet_fields: list[str] | None = None,
        facet_limit: int = 25,
    ):
        """Search for collections in PDS4.

        Args:
            title_query: Search query for collection titles (e.g., "Lunar")
            start_time: Start of time range (ISO 8601 format, e.g., "2020-01-01T00:00:00Z")
            end_time: End of time range (ISO 8601 format)
            processing_level: Filter by processing level ("Raw", "Calibrated", "Derived")
            limit: Number of actual products to return (set to 0 for facets only)
            facet_fields: List of fields to facet on (e.g., ["pds:Identification_Area.pds:title", "lidvid"])
            facet_limit: Maximum number of facet values to return

        Returns:
            PDS4SearchResponse containing collections and facets
        """
        # Import here to avoid circular dependency
        from akd_ext.tools.pds.utils.pds4_api_models import PDS4SearchResponse

        params: dict[str, str] = {}
        filters: list[str] = []

        if title_query:
            filters.append(f'(title like "{title_query}")')

        # Temporal filters
        if start_time:
            filters.append(f'(pds:Time_Coordinates.pds:start_date_time ge "{start_time}")')
        if end_time:
            filters.append(f'(pds:Time_Coordinates.pds:stop_date_time lt "{end_time}")')

        # Processing level filter
        if processing_level:
            filters.append(f'(pds:Primary_Result_Summary.pds:processing_level eq "{processing_level}")')

        if filters:
            params["q"] = f"({' and '.join(filters)})"

        if facet_fields:
            params["facet-fields"] = ",".join(facet_fields)

        params["facet-limit"] = str(facet_limit)
        params["limit"] = str(limit or 0)

        response = await self._request("GET", "classes/collection", params=params)

        try:
            data = response.json()
            return PDS4SearchResponse.from_raw_data(data)
        except ValidationError as e:
            logger.error(f"Failed to parse collection search response: {e}")
            raise PDS4ClientError(f"Invalid response format: {e}")

    async def search_observational(
        self,
        title_query: str | None = None,
        limit: int | None = None,
        facet_fields: list[str] | None = None,
        facet_limit: int = 25,
    ):
        """Search for observational products in PDS4.

        Args:
            title_query: Search query for product titles (e.g., "LRO")
            limit: Number of actual products to return (set to 0 for facets only)
            facet_fields: List of fields to facet on (e.g., ["pds:Identification_Area.pds:title", "lidvid"])
            facet_limit: Maximum number of facet values to return

        Returns:
            PDS4SearchResponse containing observational products and facets
        """
        # Import here to avoid circular dependency
        from akd_ext.tools.pds.utils.pds4_api_models import PDS4SearchResponse

        params: dict[str, str] = {}

        if title_query:
            params["q"] = f'((title like "{title_query}"))'

        if facet_fields:
            params["facet-fields"] = ",".join(facet_fields)

        params["facet-limit"] = str(facet_limit)
        params["limit"] = str(limit or 0)

        response = await self._request("GET", "classes/observational", params=params)

        try:
            data = response.json()
            return PDS4SearchResponse.from_raw_data(data)
        except ValidationError as e:
            logger.error(f"Failed to parse observational search response: {e}")
            raise PDS4ClientError(f"Invalid response format: {e}")

    async def get_collection_products(
        self,
        collection_urn: str,
        limit: int | None = None,
    ):
        """Get products from a specific collection.

        Best Practice: Extract collection_urn from search_collections results, not hardcoded values.

        Typical workflow:
        1. Call search_collections() to discover available collections
        2. Extract 'lidvid' field from interesting collections in the response
        3. Use that lidvid as collection_urn parameter here
        4. Iterate through multiple collections if some are empty

        Args:
            collection_urn: URN of the collection from search results (e.g., extracted from response.data[0].lidvid)
            limit: Number of products to return

        Returns:
            PDS4SearchResponse containing collection products (uses /members endpoint)
        """
        # Import here to avoid circular dependency
        from akd_ext.tools.pds.utils.pds4_api_models import PDS4SearchResponse

        params = {}

        if limit:
            params["limit"] = str(limit)

        response = await self._request("GET", f"products/{collection_urn}/members", params=params)

        try:
            data = response.json()
            return PDS4SearchResponse.from_raw_data(data)
        except ValidationError as e:
            logger.error(f"Failed to parse collection products response: {e}")
            raise PDS4ClientError(f"Invalid response format: {e}")

    async def search_context_investigations(
        self,
        keywords: str | None = None,
        limit: int = 10,
    ):
        """Search PDS Context products that are Investigations (missions/projects).

        Args:
            keywords: Search terms for investigations (e.g., "mars rover", "jupiter cassini")
            limit: Maximum number of results to return

        Returns:
            PDS4SearchResponse containing investigation context products
        """
        # Import here to avoid circular dependency
        from akd_ext.tools.pds.utils.pds4_api_models import PDS4SearchResponse

        params = {
            "q": r'(product_class eq "Product_Context" and lid like "urn:nasa:pds:context:investigation:*")',
            "fields": (
                "title,lid,pds:Investigation.pds:stop_date,pds:Investigation.pds:start_date,"
                "pds:Investigation.pds:type,ops:Label_File_Info.ops:file_ref"
            ),
            "limit": str(limit),
        }

        if keywords:
            keywords_str = " ".join(keywords.split())
            keyword_query = f'((title like "{keywords_str}") or (description like "{keywords_str}"))'
            params["q"] = f"({params['q']} and {keyword_query})"

        response = await self._request("GET", "products", params=params)

        try:
            data = response.json()
            return PDS4SearchResponse.from_raw_data(data)
        except ValidationError as e:
            logger.error(f"Failed to parse investigation search response: {e}")
            raise PDS4ClientError(f"Invalid response format: {e}")

    async def search_context_targets(
        self,
        keywords: str | None = None,
        target_type: str | None = None,
        limit: int = 10,
    ):
        """Search PDS Context products that are Targets (celestial bodies, phenomena).

        Args:
            keywords: Search terms for targets (e.g., "jupiter moon", "asteroid belt")
            target_type: Filter by target type (e.g., "Planet", "Satellite")
            limit: Maximum number of results to return

        Returns:
            PDS4SearchResponse containing target context products
        """
        # Import here to avoid circular dependency
        from akd_ext.tools.pds.utils.pds4_api_models import PDS4SearchResponse

        params = {
            "q": r'(product_class eq "Product_Context" and lid like "urn:nasa:pds:context:target:*")',
            "fields": "title,lid,pds:Target.pds:type,pds:Alias.pds:alternate_title",
            "limit": str(limit),
        }

        if keywords:
            keyword_query = f'((title like "{keywords}") or (pds:Target.pds:description like "{keywords}"))'
            params["q"] = f"({params['q']} and {keyword_query})"

        if target_type:
            params["q"] = f'({params["q"]} and (pds:Target.pds:type like "{target_type}"))'

        response = await self._request("GET", "products", params=params)

        try:
            data = response.json()
            return PDS4SearchResponse.from_raw_data(data)
        except ValidationError as e:
            logger.error(f"Failed to parse target search response: {e}")
            raise PDS4ClientError(f"Invalid response format: {e}")

    async def search_context_instrument_hosts(
        self,
        keywords: str | None = None,
        instrument_host_type: str | None = None,
        limit: int = 10,
    ):
        """Search PDS Context products that are Instrument Hosts (spacecraft, rovers, telescopes).

        Args:
            keywords: Search terms for instrument hosts (e.g., "mars rover", "voyager spacecraft")
            instrument_host_type: Filter by type (e.g., "Rover", "Spacecraft")
            limit: Maximum number of results to return

        Returns:
            PDS4SearchResponse containing instrument host context products
        """
        # Import here to avoid circular dependency
        from akd_ext.tools.pds.utils.pds4_api_models import PDS4SearchResponse

        params = {
            "q": r'(product_class eq "Product_Context" and lid like "urn:nasa:pds:context:instrument_host:*")',
            "fields": "pds:Instrument_Host.pds:type",
            "limit": str(limit),
        }

        if keywords:
            keyword_query = f'((title like "{keywords}") or (pds:Instrument_Host.pds:description like "{keywords}"))'
            params["q"] = f"({params['q']} and {keyword_query})"

        if instrument_host_type:
            params["q"] = f'({params["q"]} and (pds:Instrument_Host.pds:type like "{instrument_host_type}"))'

        response = await self._request("GET", "products", params=params)

        try:
            data = response.json()
            return PDS4SearchResponse.from_raw_data(data)
        except ValidationError as e:
            logger.error(f"Failed to parse instrument host search response: {e}")
            raise PDS4ClientError(f"Invalid response format: {e}")

    async def search_context_instruments(
        self,
        keywords: str | None = None,
        instrument_type: str | None = None,
        limit: int = 10,
    ):
        """Search PDS Context products that are Instruments.

        Args:
            keywords: Search terms for instruments (e.g., "camera mars", "spectrometer cassini")
            instrument_type: Filter by instrument type (e.g., "Spectrometer", "Imager")
            limit: Maximum number of results to return

        Returns:
            PDS4SearchResponse containing instrument context products
        """
        # Import here to avoid circular dependency
        from akd_ext.tools.pds.utils.pds4_api_models import PDS4SearchResponse

        params = {
            "q": r'(product_class eq "Product_Context" and lid like "urn:nasa:pds:context:instrument:*")',
            "fields": "pds:Instrument.pds:type",
            "limit": str(limit),
        }

        if keywords:
            # Search title, description, and LID (where abbreviations like "jade", "jedi" appear)
            keyword_query = (
                f'((title like "{keywords}") or '
                f'(pds:Instrument.pds:description like "{keywords}") or '
                f'(lid like "*{keywords.lower()}*"))'
            )
            params["q"] = f"({params['q']} and {keyword_query})"

        if instrument_type:
            params["q"] = f'({params["q"]} and (pds:Instrument.pds:type like "{instrument_type}"))'

        response = await self._request("GET", "products", params=params)

        try:
            data = response.json()
            return PDS4SearchResponse.from_raw_data(data)
        except ValidationError as e:
            logger.error(f"Failed to parse instrument search response: {e}")
            raise PDS4ClientError(f"Invalid response format: {e}")

    async def search_context_collections(
        self,
        ref_lid_instrument: str | None = None,
        ref_lid_target: str | None = None,
        ref_lid_instrument_host: str | None = None,
        ref_lid_investigation: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        processing_level: str | None = None,
        limit: int = 10,
    ):
        """Search PDS data collections filtered by context references and advanced filters.

        Args:
            ref_lid_instrument: URN identifier for instrument
            ref_lid_target: URN identifier for target
            ref_lid_instrument_host: URN identifier for instrument host
            ref_lid_investigation: URN identifier for investigation
            start_time: Start of time range (ISO 8601 format, e.g., "2020-01-01T00:00:00Z")
            end_time: End of time range (ISO 8601 format)
            processing_level: Filter by processing level ("Raw", "Calibrated", "Derived")
            limit: Maximum number of results to return

        Returns:
            PDS4SearchResponse containing collection products
        """
        # Import here to avoid circular dependency
        from akd_ext.tools.pds.utils.pds4_api_models import PDS4SearchResponse

        params = {
            "q": r'(product_class eq "Product_Collection")',
            "fields": (
                "title,lid,ref_lid_instrument,ref_lid_target,ref_lid_instrument_host,"
                "ref_lid_investigation,ops:Label_File_Info.ops:file_ref,"
                "pds:Time_Coordinates.pds:start_date_time,"
                "pds:Time_Coordinates.pds:stop_date_time,"
                "pds:Primary_Result_Summary.pds:processing_level"
            ),
            "limit": str(limit),
        }

        # Add filters for each provided parameter
        filters = []

        if ref_lid_instrument:
            clean_instrument = self._clean_urn(ref_lid_instrument)
            filters.append(f'(ref_lid_instrument eq "{clean_instrument}")')

        if ref_lid_target:
            clean_target = self._clean_urn(ref_lid_target)
            filters.append(f'(ref_lid_target eq "{clean_target}")')

        if ref_lid_instrument_host:
            clean_host = self._clean_urn(ref_lid_instrument_host)
            filters.append(f'(ref_lid_instrument_host eq "{clean_host}")')

        if ref_lid_investigation:
            clean_investigation = self._clean_urn(ref_lid_investigation)
            filters.append(f'(ref_lid_investigation eq "{clean_investigation}")')

        # Temporal filters - don't escape datetime values as colons are part of ISO 8601 format
        if start_time:
            filters.append(f'(pds:Time_Coordinates.pds:start_date_time ge "{start_time}")')
        if end_time:
            # Use stop_date_time for end filter to properly filter by when data collection ended
            filters.append(f'(pds:Time_Coordinates.pds:stop_date_time lt "{end_time}")')

        # Processing level filter
        if processing_level:
            filters.append(f'(pds:Primary_Result_Summary.pds:processing_level eq "{processing_level}")')

        # Combine all filters
        if filters:
            params["q"] = f"({params['q']} and {' and '.join(filters)})"

        response = await self._request("GET", "products", params=params)

        try:
            data = response.json()

            # Process file_ref paths to remove filename and show directory
            for item in data.get("data", []):
                if "ops:Label_File_Info.ops:file_ref" in item:
                    file_ref = item["ops:Label_File_Info.ops:file_ref"]
                    if file_ref and isinstance(file_ref, list) and file_ref:
                        # Split by '/' and remove the last part (filename), then rejoin
                        path_parts = file_ref[0].split("/")
                        if len(path_parts) > 1:
                            # Remove the last part (filename) to get the directory
                            directory_path = "/".join(path_parts[:-1])
                            item["ops:Label_File_Info.ops:file_ref"] = [directory_path]

            return PDS4SearchResponse.from_raw_data(data)
        except ValidationError as e:
            logger.error(f"Failed to parse collection search response: {e}")
            raise PDS4ClientError(f"Invalid response format: {e}")

    async def get_product(self, urn: str) -> dict[str, Any]:
        """Get a single PDS product by its URN identifier.

        Args:
            urn: URN identifier for the product

        Returns:
            Raw JSON response containing the product details
        """
        # Clean the URN to remove version information
        clean_urn_id = self._clean_urn(urn)

        response = await self._request("GET", f"products/{clean_urn_id}")

        try:
            result: dict[str, Any] = response.json()
            return result
        except Exception as e:
            logger.error(f"Failed to parse product response: {e}")
            raise PDS4ClientError(f"Invalid response format: {e}")

    async def search_products_advanced(
        self,
        keywords: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        processing_level: str | None = None,
        bbox_north: float | None = None,
        bbox_south: float | None = None,
        bbox_east: float | None = None,
        bbox_west: float | None = None,
        ref_lid_target: str | None = None,
        limit: int = 100,
    ):
        """Search for observational products with advanced filtering.

        Supports temporal, processing level, and spatial (bounding box) filters.

        Args:
            keywords: Search terms for product titles
            start_time: Start of time range (ISO 8601 format, e.g., "2020-01-01T00:00:00Z")
            end_time: End of time range (ISO 8601 format)
            processing_level: Filter by processing level ("Raw", "Calibrated", "Derived")
            bbox_north: North bounding coordinate (latitude, -90 to 90)
            bbox_south: South bounding coordinate (latitude, -90 to 90)
            bbox_east: East bounding coordinate (longitude)
            bbox_west: West bounding coordinate (longitude)
            ref_lid_target: URN identifier for target (e.g., "urn:nasa:pds:context:target:planet.mars")
            limit: Maximum number of results to return

        Returns:
            PDS4SearchResponse containing matching observational products

        Raises:
            ValueError: If coordinate values are out of valid range
        """
        # Import here to avoid circular dependency
        from akd_ext.tools.pds.utils.pds4_api_models import PDS4SearchResponse

        # Validate coordinates
        validate_coordinates(bbox_north, bbox_south, bbox_east, bbox_west)

        filters = ['(product_class eq "Product_Observational")']

        # Keywords filter
        if keywords:
            filters.append(f'(title like "{keywords}")')

        # Temporal filters
        if start_time:
            filters.append(f'(pds:Time_Coordinates.pds:start_date_time ge "{start_time}")')
        if end_time:
            # Use stop_date_time for end filter to properly filter by when data collection ended
            filters.append(f'(pds:Time_Coordinates.pds:stop_date_time lt "{end_time}")')

        # Processing level filter
        if processing_level:
            filters.append(f'(pds:Primary_Result_Summary.pds:processing_level eq "{processing_level}")')

        # Spatial (bounding box) filters - find products that intersect the query box
        if bbox_north is not None:
            filters.append(f"(cart:Bounding_Coordinates.cart:south_bounding_coordinate le {bbox_north})")
        if bbox_south is not None:
            filters.append(f"(cart:Bounding_Coordinates.cart:north_bounding_coordinate ge {bbox_south})")
        if bbox_east is not None:
            filters.append(f"(cart:Bounding_Coordinates.cart:west_bounding_coordinate le {bbox_east})")
        if bbox_west is not None:
            filters.append(f"(cart:Bounding_Coordinates.cart:east_bounding_coordinate ge {bbox_west})")

        # Target filter
        if ref_lid_target:
            clean_target = self._clean_urn(ref_lid_target)
            filters.append(f'(ref_lid_target eq "{clean_target}")')

        # Build query
        query = " and ".join(filters)
        params = {
            "q": f"({query})",
            "fields": (
                "title,lid,lidvid,ref_lid_target,"
                "pds:Time_Coordinates.pds:start_date_time,"
                "pds:Time_Coordinates.pds:stop_date_time,"
                "pds:Primary_Result_Summary.pds:processing_level,"
                "cart:Bounding_Coordinates.cart:north_bounding_coordinate,"
                "cart:Bounding_Coordinates.cart:south_bounding_coordinate,"
                "cart:Bounding_Coordinates.cart:east_bounding_coordinate,"
                "cart:Bounding_Coordinates.cart:west_bounding_coordinate"
            ),
            "limit": str(limit),
        }

        response = await self._request("GET", "products", params=params)

        try:
            data = response.json()
            return PDS4SearchResponse.from_raw_data(data)
        except ValidationError as e:
            logger.error(f"Failed to parse advanced product search response: {e}")
            raise PDS4ClientError(f"Invalid response format: {e}")

    async def crawl_context_product(self, urn: str) -> dict[str, Any]:
        """Crawl a single PDS Context product and return associated context products.

        This method fetches related products concurrently using async HTTP requests.

        Args:
            urn: URN identifier for the context product to crawl

        Returns:
            Dictionary containing the associated context products with keys:
            - "investigations": Related investigation products
            - "observing_system_components": Related instrument/host products
            - "targets": Related target products
            - "errors": List of any fetch errors encountered (if any)
        """
        # Clean the URN to remove version information
        clean_urn_id = self._clean_urn(urn)

        # Get the main product
        product_response = await self._request("GET", f"products/{clean_urn_id}")
        response_data = product_response.json()

        # Filter to keep only relevant keys
        response_data = {
            k: v
            for k, v in response_data.items()
            if k in ("investigations", "observing_system_components", "targets", "title", "id")
        }

        urn_dict: dict[str, dict[str, str]] = {
            "investigations": {},
            "observing_system_components": {},
            "targets": {},
        }

        if "investigations" in response_data:
            for item in response_data["investigations"]:
                urn_dict["investigations"][item["id"]] = item["href"]
        if "observing_system_components" in response_data:
            for item in response_data["observing_system_components"]:
                urn_dict["observing_system_components"][item["id"]] = item["href"]
        if "targets" in response_data:
            for item in response_data["targets"]:
                urn_dict["targets"][item["id"]] = item["href"]

        # Create a results dict with the same structure as urn_dict
        results: dict[str, Any] = {
            "investigations": {},
            "observing_system_components": {},
            "targets": {},
        }
        errors: list[str] = []

        # Async helper to fetch a single related product
        async def fetch_related(category: str, urn_id: str, href: str) -> tuple[str, str, dict[str, Any] | None]:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(href, headers={"Accept": "application/kvp+json"})
                    if resp.status_code == 200:
                        data = resp.json()
                        subset_keys = ["title", "description", "id"]
                        return category, urn_id, {k: v for k, v in data.items() if k in subset_keys}
                    else:
                        logger.warning(f"Failed to fetch {href}: {resp.status_code}")
                        return category, urn_id, None
            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching {href}: {e}")
                errors.append(f"Failed to fetch {urn_id}: {e}")
                return category, urn_id, None
            except Exception as e:
                logger.error(f"Error fetching {href}: {e}")
                errors.append(f"Failed to fetch {urn_id}: {e}")
                return category, urn_id, None

        # Build list of fetch tasks
        tasks = []
        for category in urn_dict:
            for urn_id, href in urn_dict[category].items():
                tasks.append(fetch_related(category, urn_id, href))

        # Execute all fetches concurrently
        if tasks:
            fetch_results = await asyncio.gather(*tasks)
            for category, urn_id, data in fetch_results:
                if data is not None:
                    results[category][urn_id] = data

        # Include errors in response if any occurred
        if errors:
            results["errors"] = errors

        return results
