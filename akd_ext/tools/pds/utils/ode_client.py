"""ODE REST API client wrapper with httpx.

The Orbital Data Explorer (ODE) provides access to NASA's planetary science
data archives for Mars, Moon, Mercury, and other bodies.

Base URL: https://oderest.rsl.wustl.edu/live2/
"""

import asyncio
import logging
from types import TracebackType
from typing import Any, Literal

import httpx

from akd_ext.tools.pds.utils.ode_api_models import (
    ODEFeatureClassesResponse,
    ODEFeatureDataResponse,
    ODEFeatureNamesResponse,
    ODEIIPTResponse,
    ODEProductCountResponse,
    ODEProductSearchResponse,
)

logger = logging.getLogger(__name__)

# Valid ODE targets
ODETarget = Literal["mars", "moon", "mercury", "phobos", "deimos", "venus"]

# Valid result types
ODEResultType = Literal["op", "m", "f", "fpc", "c", "cm"]


class ODEClientError(Exception):
    """Base exception for ODE client errors."""

    pass


class ODERateLimitError(ODEClientError):
    """Rate limit error for ODE API."""

    def __init__(self, retry_after: int | None = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


class ODEClient:
    """Async HTTP client for ODE REST API."""

    BASE_URL = "https://oderest.rsl.wustl.edu/live2/"
    DEFAULT_TIMEOUT = 30.0

    VALID_TARGETS: set[str] = {"mars", "moon", "mercury", "phobos", "deimos", "venus"}

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize ODE client.

        Args:
            base_url: ODE API base URL (default: https://oderest.rsl.wustl.edu/live2/)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
        """
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "ODEClient":
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
            "User-Agent": "AKD-EXT-ODE-Client/0.1.0",
        }

    def _validate_target(self, target: str) -> None:
        """Validate that target is a valid ODE target."""
        if target.lower() not in self.VALID_TARGETS:
            raise ValueError(f"Invalid target: {target}. Must be one of: {', '.join(sorted(self.VALID_TARGETS))}")

    async def _request(
        self,
        params: dict[str, Any],
    ) -> httpx.Response:
        """Make HTTP request with retry logic."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.get("", params=params)

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
                        raise ODERateLimitError(retry_after)

                response.raise_for_status()
                return response

            except httpx.HTTPError as e:
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2**attempt)
                    logger.warning(f"Request failed (attempt {attempt + 1}). Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise ODEClientError(f"Request failed after {self.max_retries} retries: {e}")

        raise ODEClientError("Maximum retries exceeded")

    async def search_products(
        self,
        target: str,
        ihid: str | None = None,
        iid: str | None = None,
        pt: str | None = None,
        pdsid: str | None = None,
        minlat: float | None = None,
        maxlat: float | None = None,
        westlon: float | None = None,
        eastlon: float | None = None,
        minobtime: str | None = None,
        maxobtime: str | None = None,
        results: ODEResultType = "fpc",
        limit: int = 100,
        offset: int = 0,
    ) -> ODEProductSearchResponse:
        """Search for ODE products.

        Args:
            target: Planetary body (mars, moon, mercury, phobos, deimos, venus)
            ihid: Instrument Host ID (e.g., "MRO", "LRO", "MESS")
            iid: Instrument ID (e.g., "HIRISE", "CTX", "LROC")
            pt: Product Type (e.g., "RDRV11", "EDR")
            pdsid: PDS Product ID for direct lookup
            minlat: Minimum latitude (-90 to 90)
            maxlat: Maximum latitude (-90 to 90)
            westlon: Western longitude
            eastlon: Eastern longitude
            minobtime: Minimum observation time in UTC format (e.g., "2018-05-01")
            maxobtime: Maximum observation time in UTC format (e.g., "2018-08-31")
            results: Result type (op, m, f, fpc, c, cm)
            limit: Maximum products to return
            offset: Pagination offset

        Returns:
            ODEProductSearchResponse with products and metadata
        """
        self._validate_target(target)

        # Validate that we have either ihid+iid+pt or pdsid
        if not pdsid and not (ihid and iid and pt):
            raise ValueError("Must provide either 'pdsid' or all of 'ihid', 'iid', and 'pt'")

        params: dict[str, Any] = {
            "target": target.lower(),
            "query": "product",
            "results": results,
            "output": "JSON",
            "limit": str(limit),
            "offset": str(offset),
        }

        if pdsid:
            params["pdsid"] = pdsid
        else:
            params["ihid"] = ihid
            params["iid"] = iid
            params["pt"] = pt

        # Add geographic bounds
        if minlat is not None:
            params["minlat"] = str(minlat)
        if maxlat is not None:
            params["maxlat"] = str(maxlat)
        if westlon is not None:
            params["westlon"] = str(westlon)
        if eastlon is not None:
            params["eastlon"] = str(eastlon)

        # Add temporal bounds
        if minobtime is not None:
            params["minobtime"] = minobtime
        if maxobtime is not None:
            params["maxobtime"] = maxobtime

        response = await self._request(params)

        try:
            data = response.json()
            return ODEProductSearchResponse.from_raw_data(data)
        except Exception as e:
            logger.error(f"Failed to parse ODE product search response: {e}")
            raise ODEClientError(f"Invalid response format: {e}")

    async def count_products(
        self,
        target: str,
        ihid: str,
        iid: str,
        pt: str,
        minlat: float | None = None,
        maxlat: float | None = None,
        westlon: float | None = None,
        eastlon: float | None = None,
        minobtime: str | None = None,
        maxobtime: str | None = None,
    ) -> ODEProductCountResponse:
        """Count products matching criteria.

        Args:
            target: Planetary body
            ihid: Instrument Host ID
            iid: Instrument ID
            pt: Product Type
            minlat: Minimum latitude
            maxlat: Maximum latitude
            westlon: Western longitude
            eastlon: Eastern longitude
            minobtime: Minimum observation time in UTC format (e.g., "2020-01-01")
            maxobtime: Maximum observation time in UTC format (e.g., "2020-01-31")

        Returns:
            ODEProductCountResponse with count
        """
        self._validate_target(target)

        params: dict[str, Any] = {
            "target": target.lower(),
            "query": "product",
            "results": "c",
            "output": "JSON",
            "ihid": ihid,
            "iid": iid,
            "pt": pt,
        }

        if minlat is not None:
            params["minlat"] = str(minlat)
        if maxlat is not None:
            params["maxlat"] = str(maxlat)
        if westlon is not None:
            params["westlon"] = str(westlon)
        if eastlon is not None:
            params["eastlon"] = str(eastlon)

        # Add temporal bounds
        if minobtime is not None:
            params["minobtime"] = minobtime
        if maxobtime is not None:
            params["maxobtime"] = maxobtime

        response = await self._request(params)

        try:
            data = response.json()
            return ODEProductCountResponse.from_raw_data(data)
        except Exception as e:
            logger.error(f"Failed to parse ODE count response: {e}")
            raise ODEClientError(f"Invalid response format: {e}")

    async def list_instruments(
        self,
        target: str,
    ) -> ODEIIPTResponse:
        """Get valid instrument/product type combinations for a target.

        Args:
            target: Planetary body

        Returns:
            ODEIIPTResponse with instrument combinations
        """
        self._validate_target(target)

        params = {
            "query": "iipt",
            "target": target.lower(),
            "output": "JSON",
        }

        response = await self._request(params)

        try:
            data = response.json()
            return ODEIIPTResponse.from_raw_data(data)
        except Exception as e:
            logger.error(f"Failed to parse ODE IIPT response: {e}")
            raise ODEClientError(f"Invalid response format: {e}")

    async def get_feature_bounds(
        self,
        target: str,
        feature_class: str,
        feature_name: str,
    ) -> ODEFeatureDataResponse:
        """Get lat/lon bounds for a named planetary feature.

        Args:
            target: Planetary body (mars, moon, etc.)
            feature_class: Feature type (crater, chasma, mons, etc.)
            feature_name: Name of the feature (Gale, Jezero, Olympus Mons, etc.)

        Returns:
            ODEFeatureDataResponse with geographic bounds
        """
        params = {
            "query": "featuredata",
            "odemetadb": target.lower(),
            "featureclass": feature_class.lower(),
            "featurename": feature_name,
        }

        response = await self._request(params)

        try:
            content_type = response.headers.get("content-type", "").lower()
            if "json" in content_type:
                data = response.json()
                return ODEFeatureDataResponse.from_raw_data(data)
            else:
                # Parse XML response
                return ODEFeatureDataResponse.from_xml(response.text)
        except Exception as e:
            logger.error(f"Failed to parse ODE feature data response: {e}")
            raise ODEClientError(f"Invalid response format: {e}")

    async def list_feature_classes(
        self,
        target: str,
    ) -> ODEFeatureClassesResponse:
        """Get available feature types for a target.

        Args:
            target: Planetary body

        Returns:
            ODEFeatureClassesResponse with feature classes
        """
        params = {
            "query": "featureclasses",
            "odemetadb": target.lower(),
            "output": "JSON",
        }

        response = await self._request(params)

        try:
            data = response.json()
            return ODEFeatureClassesResponse.from_raw_data(data)
        except Exception as e:
            logger.error(f"Failed to parse ODE feature classes response: {e}")
            raise ODEClientError(f"Invalid response format: {e}")

    async def list_feature_names(
        self,
        target: str,
        feature_class: str,
        limit: int = 100,
    ) -> ODEFeatureNamesResponse:
        """Get names of features by class.

        Args:
            target: Planetary body
            feature_class: Feature type (crater, chasma, etc.)
            limit: Maximum names to return

        Returns:
            ODEFeatureNamesResponse with feature names
        """
        params = {
            "query": "featurenames",
            "odemetadb": target.lower(),
            "featureclass": feature_class.lower(),
            "limit": str(limit),
            "output": "JSON",
        }

        response = await self._request(params)

        try:
            data = response.json()
            return ODEFeatureNamesResponse.from_raw_data(data)
        except Exception as e:
            logger.error(f"Failed to parse ODE feature names response: {e}")
            raise ODEClientError(f"Invalid response format: {e}")
