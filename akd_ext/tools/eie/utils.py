"""Utility functions for EIE tools."""

import httpx
import concurrent.futures


def fetch_statistics_batch(
    items: list[dict],
    geometry: dict,
    dst_crs: str = "+proj=cea",
    raster_api_url: str | None = None,
    timeout: float = 60.0,
) -> list[dict]:
    """Fetch raster statistics for multiple COGs in parallel.

    Args:
        items: List of dicts with 'url' and optionally 'datetime', 'id'
        geometry: GeoJSON geometry (Polygon or MultiPolygon) to clip the raster
        dst_crs: Destination CRS for area-weighted stats
        raster_api_url: Base URL for the VEDA raster API
        timeout: HTTP request timeout in seconds

    Returns:
        List of dicts with 'url', 'datetime', 'statistics', 'error' for each item
    """
    if not items:
        return []

    def fetch_one(item: dict) -> dict:
        url = item.get("url")
        item_id = item.get("id")
        result = fetch_statistics(
            url=url,
            geometry=geometry,
            dst_crs=dst_crs,
            raster_api_url=raster_api_url,
            timeout=30.0,  # Reduced timeout per item
        )
        return {
            "url": url,
            "id": item_id,
            "datetime": item.get("datetime"),
            "statistics": result.get("statistics", {}),
            "error": result.get("error"),
        }

    # Fetch in parallel (max 5 concurrent)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(fetch_one, items))

    return results


def fetch_statistics(
    url: str,
    geometry: dict,
    dst_crs: str = "+proj=cea",
    raster_api_url: str | None = None,
    timeout: float = 60.0,
) -> dict:
    """Fetch raster statistics from the VEDA raster API.

    Args:
        url: URL to the COG file (S3 or HTTP)
        geometry: GeoJSON geometry (Polygon or MultiPolygon) to clip the raster
        dst_crs: Destination CRS for area-weighted stats (default: Equal Area)
        raster_api_url: Base URL for the VEDA raster API
        timeout: HTTP request timeout in seconds

    Returns:
        Dict with 'statistics' (per-band stats) and optional 'error'
    """
    if not geometry:
        return {"statistics": {}, "error": "geometry is required"}

    endpoint = f"{raster_api_url.rstrip('/')}/cog/statistics"

    geojson_feature = {
        "type": "Feature",
        "properties": {},
        "geometry": geometry,
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                endpoint,
                params={"url": url, "dst_crs": dst_crs},
                json=geojson_feature,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

        # Parse response - VEDA returns {"properties": {"statistics": {...}}}
        properties = data.get("properties", data)
        stats_data = properties.get("statistics", properties)

        return {"statistics": stats_data, "error": None}

    except httpx.TimeoutException:
        return {"statistics": {}, "error": f"Request timed out after {timeout}s"}
    except httpx.HTTPStatusError as e:
        return {"statistics": {}, "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
    except Exception as e:
        return {"statistics": {}, "error": str(e)}
