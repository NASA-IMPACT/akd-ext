"""Shared helpers for VEDA raster and CMR tools."""
from __future__ import annotations

import concurrent.futures
import time
from urllib.parse import quote

import httpx
from loguru import logger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Human-readable time density labels → ISO 8601 durations
LABEL_TO_DURATION = {"day": "P1D", "month": "P1M", "year": "P1Y"}

_CMR_MAX_RETRIES = 2
_CMR_RETRY_DELAY = 1.0  # seconds

# ---------------------------------------------------------------------------
# Collection metadata helpers
# ---------------------------------------------------------------------------


def fetch_collection_metadata(collection_id: str, stac_url: str) -> dict | None:
    """Fetch collection metadata from STAC API.

    Returns the full collection metadata including renders.dashboard params.
    """
    url = f"{stac_url.rstrip('/')}/collections/{collection_id}"

    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.get(url, headers={"Accept": "application/json"})
            r.raise_for_status()
            return r.json()
    except Exception:
        return None


def is_cmr_backed(collection_metadata: dict | None) -> bool:
    """Return True if the collection is CMR-backed.

    Detected by the presence of collection_concept_id at the top level of the
    STAC collection JSON. Collections with this field (e.g. 'C2723754864-GES_DISC')
    are accessed via titiler-cmr instead of COG asset URLs, and their renders
    are keyed by variable name rather than 'dashboard'.
    """
    if not collection_metadata:
        return False
    return bool(collection_metadata.get("collection_concept_id"))


def get_cmr_params(collection_metadata: dict, selected_variable: str | None = None) -> dict:
    """Extract CMR-specific params from the STAC collection.

    concept_id comes from collection_concept_id (top-level field).
    Render params (backend, colormap_name, rescale) come from renders[variable],
    where the key is the variable name itself.

    Args:
        collection_metadata: Full STAC collection JSON
        selected_variable: User-selected variable (required for CMR collections)

    Returns dict with: concept_id, variable, backend, colormap_name, rescale (as "min,max" string).
    """
    variable = selected_variable
    render = collection_metadata.get("renders", {}).get(variable, {}) if variable else {}

    params: dict = {
        "concept_id": collection_metadata.get("collection_concept_id"),
        "variable": variable,
        "backend": render.get("backend", "xarray"),
        "colormap_name": render.get("colormap_name"),
    }
    rescale = render.get("rescale")
    if isinstance(rescale, list) and rescale:
        if isinstance(rescale[0], list) and len(rescale[0]) == 2:
            params["rescale"] = f"{rescale[0][0]},{rescale[0][1]}"
        elif len(rescale) == 2:
            params["rescale"] = f"{rescale[0]},{rescale[1]}"
    return params


def get_render_params(collection_metadata: dict | None) -> dict:
    """Extract render params from collection metadata.

    Looks for renders.dashboard to get colormap_name, bidx, rescale.
    Returns dict with keys: colormap_name, bidx, rescale (all optional).
    """
    if not collection_metadata:
        return {}

    renders = collection_metadata.get("renders", {})
    dashboard = renders.get("dashboard", {})

    params = {}

    if "colormap_name" in dashboard:
        params["colormap_name"] = dashboard["colormap_name"]

    if "bidx" in dashboard:
        # bidx is a list like [1]
        bidx = dashboard["bidx"]
        if isinstance(bidx, list) and bidx:
            params["bidx"] = bidx[0]

    if "rescale" in dashboard:
        # rescale is a list of [min, max] pairs like [[0, 1.5e16]]
        rescale = dashboard["rescale"]
        if isinstance(rescale, list) and rescale:
            if isinstance(rescale[0], list) and len(rescale[0]) == 2:
                params["rescale"] = f"{rescale[0][0]},{rescale[0][1]}"
            elif len(rescale) == 2:
                params["rescale"] = f"{rescale[0]},{rescale[1]}"

    return params


# ---------------------------------------------------------------------------
# Statistics functions (from eie_llm_backend.core.tools.stats)
# ---------------------------------------------------------------------------


def fetch_statistics(
    url: str,
    geometry: dict,
    dst_crs: str = "+proj=cea",
    raster_api_url: str = "",
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


def fetch_statistics_batch(
    items: list[dict],
    geometry: dict,
    dst_crs: str = "+proj=cea",
    raster_api_url: str = "",
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

    logger.info(f"Fetching stats for {len(items)} items in parallel...")

    def fetch_one(item: dict) -> dict:
        url = item.get("url")
        item_id = item.get("id")
        logger.info(f"  Starting fetch for {item_id}...")
        result = fetch_statistics(
            url=url,
            geometry=geometry,
            dst_crs=dst_crs,
            raster_api_url=raster_api_url,
            timeout=30.0,  # Reduced timeout per item
        )
        logger.info(f"  Completed fetch for {item_id}: error={result.get('error')}")
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

    logger.info(f"Completed all {len(items)} stats fetches")
    return results


def fetch_cmr_statistics(
    collection_metadata: dict,
    datetime_range: str,
    geometry: dict,
    titiler_cmr_url: str = "",
    timeout: float = 60.0,
    selected_variable: str | None = None,
) -> dict:
    """Fetch zonal statistics from the titiler-cmr timeseries endpoint.

    Args:
        collection_metadata: Full STAC collection JSON (concept_id, variable, backend from renders.dashboard)
        datetime_range: ISO-8601 range "start/end"
        geometry: GeoJSON geometry (Polygon or MultiPolygon) for the AOI
        titiler_cmr_url: Base URL for the titiler-cmr service
        timeout: HTTP request timeout in seconds
        selected_variable: User-selected variable (if None, auto-picks default)

    Returns:
        Dict with 'statistics' (per-band stats) and optional 'error'
    """
    if not geometry:
        return {"statistics": {}, "error": "geometry is required"}

    cmr_params = get_cmr_params(collection_metadata, selected_variable)
    endpoint = f"{titiler_cmr_url.rstrip('/')}/xarray/timeseries/statistics"

    def _to_full_iso(dt_str: str) -> str:
        if "T" not in dt_str:
            return dt_str + "T00:00:00Z"
        return dt_str if dt_str.endswith("Z") else dt_str + "Z"

    if "/" in datetime_range:
        start, end = datetime_range.split("/", 1)
        end_full = end + "T23:59:59Z" if "T" not in end else (end if end.endswith("Z") else end + "Z")
        cmr_datetime = f"{_to_full_iso(start)}/{end_full}"
    else:
        cmr_datetime = _to_full_iso(datetime_range)

    params: dict = {
        "collection_concept_id": cmr_params["concept_id"],
        "temporal": cmr_datetime,
        "backend": cmr_params["backend"],
        "temporal_mode": "point",
    }

    # Add step if time_density is available
    time_density = collection_metadata.get("dashboard:time_density")
    if time_density:
        step = LABEL_TO_DURATION.get(time_density)
        if step:
            params["step"] = step
    if cmr_params.get("variable"):
        params["variables"] = cmr_params["variable"]

    # API expects a Feature, not FeatureCollection
    feature = {
        "type": "Feature",
        "properties": {},
        "geometry": geometry,
    }

    try:
        logger.info(f"CMR stats request: {endpoint} params={params}")
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                endpoint,
                params=params,
                json=feature,
                headers={"Content-Type": "application/json"},
            )
            logger.info(f"CMR stats response: status={response.status_code} len={len(response.content)}")
            response.raise_for_status()

            if not response.content:
                return {"statistics": {}, "error": "Empty response from CMR statistics endpoint"}

            data = response.json()

        properties = data.get("properties", data)
        stats_data = properties.get("statistics", properties)

        return {"statistics": stats_data, "error": None}

    except httpx.TimeoutException:
        return {"statistics": {}, "error": f"CMR statistics request timed out after {timeout}s"}
    except httpx.HTTPStatusError as e:
        return {"statistics": {}, "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
    except Exception as e:
        logger.exception("CMR stats error")
        return {"statistics": {}, "error": str(e)}


# ---------------------------------------------------------------------------
# Visualization functions (from eie_llm_backend.core.tools.viz)
# ---------------------------------------------------------------------------


def build_tile_urls_batch(
    items: list[dict],
    collection_id: str | None = None,
    raster_api_url: str = "",
    stac_url: str = "",
    collection_metadata: dict | None = None,
) -> dict:
    """Build PNG tile URL templates with colormap for multiple COG items.

    Args:
        items: List of dicts with 'url' (COG URL), optionally 'id', 'datetime'
        collection_id: Collection ID to fetch render params from
        raster_api_url: Base URL for the VEDA raster API
        stac_url: Base URL for the STAC API (used to fetch collection metadata)
        collection_metadata: Pre-fetched collection metadata (avoids a second STAC call if already fetched)

    Returns:
        Dict with 'items' (list of tile info) and collection-level fields for frontend
    """
    if not items:
        return {"items": [], "collection_id": None}

    # Fetch collection metadata for render params if not provided
    render_params = {}
    if collection_metadata is None and collection_id:
        collection_metadata = fetch_collection_metadata(collection_id, stac_url)
    if collection_metadata:
        render_params = get_render_params(collection_metadata)

    results = []
    for item in items:
        url = item.get("url")
        if not url:
            continue

        # Build PNG tile URL with colormap params
        encoded_url = quote(url, safe="")

        # Start with base URL - note .png extension for PNG output
        tile_url = f"{raster_api_url.rstrip('/')}/cog/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}.png?url={encoded_url}"

        # Add render params if available
        if render_params.get("bidx"):
            tile_url += f"&bidx={render_params['bidx']}"
        if render_params.get("colormap_name"):
            tile_url += f"&colormap_name={render_params['colormap_name']}"
        if render_params.get("rescale"):
            tile_url += f"&rescale={render_params['rescale']}"

        results.append(
            {
                "id": item.get("id"),
                "datetime": item.get("datetime"),
                "tile_url": tile_url,
            }
        )

    # Extract collection-level fields for frontend
    output = {
        "items": results,
        "collection_id": collection_id,
        "title": None,
        "description": None,
        "colormap_name": render_params.get("colormap_name"),
        "rescale": None,
        "units": None,
        "time_density": None,
    }

    if collection_metadata:
        output["title"] = collection_metadata.get("title")
        output["description"] = collection_metadata.get("description")
        output["time_density"] = collection_metadata.get("dashboard:time_density")

        # Extract rescale as [min, max] list
        rescale = render_params.get("rescale")
        if rescale and "," in rescale:
            parts = rescale.split(",")
            try:
                output["rescale"] = [float(parts[0]), float(parts[1])]
            except (ValueError, IndexError):
                pass

        # Try to find units in item_assets or summaries
        item_assets = collection_metadata.get("item_assets", {})
        for asset_info in item_assets.values():
            if "unit" in asset_info:
                output["units"] = asset_info["unit"]
                break

    return output


def build_cmr_tile_urls(
    collection_metadata: dict,
    datetime_range: str,
    titiler_cmr_url: str = "",
    selected_variable: str | None = None,
) -> dict:
    """Call the titiler-cmr timeseries tilejson endpoint and return tile URLs for each timestep.

    Args:
        collection_metadata: Full STAC collection JSON
        datetime_range: ISO-8601 range "start/end"
        titiler_cmr_url: Base URL for the titiler-cmr service
        selected_variable: User-selected variable (if None, auto-picks default)

    Returns:
        Dict with 'items' (list of {datetime, tile_url}) and collection-level fields
    """
    cmr_params = get_cmr_params(collection_metadata, selected_variable)
    tilejson_endpoint = f"{titiler_cmr_url.rstrip('/')}/xarray/timeseries/WebMercatorQuad/tilejson.json"

    def _to_full_iso(dt_str: str) -> str:
        if "T" not in dt_str:
            return dt_str + "T00:00:00Z"
        return dt_str if dt_str.endswith("Z") else dt_str + "Z"

    if "/" in datetime_range:
        start, end = datetime_range.split("/", 1)
        end_full = end + "T23:59:59Z" if "T" not in end else (end if end.endswith("Z") else end + "Z")
        cmr_datetime = f"{_to_full_iso(start)}/{end_full}"
    else:
        cmr_datetime = _to_full_iso(datetime_range)

    params: dict = {
        "collection_concept_id": cmr_params["concept_id"],
        "temporal": cmr_datetime,
        "backend": cmr_params["backend"],
        "temporal_mode": "point",
    }

    # Add step if time_density is available
    time_density = collection_metadata.get("dashboard:time_density")
    if time_density:
        step = LABEL_TO_DURATION.get(time_density)
        if step:
            params["step"] = step

    if cmr_params.get("variable"):
        params["variables"] = cmr_params["variable"]
    if cmr_params.get("colormap_name"):
        params["colormap_name"] = cmr_params["colormap_name"]
    if cmr_params.get("rescale"):
        params["rescale"] = cmr_params["rescale"]

    with httpx.Client(timeout=60.0) as client:
        logger.debug("titiler-cmr viz request: %s params=%s", tilejson_endpoint, params)
        r = client.get(tilejson_endpoint, params=params)
        for attempt in range(_CMR_MAX_RETRIES):
            if r.status_code < 500:
                break
            logger.warning("titiler-cmr viz returned %d, retrying (%d/%d)", r.status_code, attempt + 1, _CMR_MAX_RETRIES)
            time.sleep(_CMR_RETRY_DELAY * (attempt + 1))
            r = client.get(tilejson_endpoint, params=params)
        if r.status_code >= 400:
            logger.error("titiler-cmr error: status=%d body=%s", r.status_code, r.text[:500])
            return {
                "items": [],
                "error": f"titiler-cmr error {r.status_code}: {r.text[:500]}",
                "collection_id": collection_metadata.get("id"),
                "title": collection_metadata.get("title"),
            }
        tilejsons = r.json()

    # tilejsons is a dict keyed by datetime, each value is a tilejson
    items = []
    for dt_str, tilejson in tilejsons.items():
        if "tiles" in tilejson and tilejson["tiles"]:
            items.append(
                {
                    "datetime": dt_str,
                    "tile_url": tilejson["tiles"][0],
                }
            )

    output: dict = {
        "items": items,
        "collection_id": collection_metadata.get("id"),
        "title": collection_metadata.get("title"),
        "description": collection_metadata.get("description"),
        "time_density": time_density,
        "colormap_name": cmr_params.get("colormap_name"),
        "rescale": None,
        "units": None,
    }

    rescale_str = cmr_params.get("rescale")
    if rescale_str and "," in rescale_str:
        parts = rescale_str.split(",")
        try:
            output["rescale"] = [float(parts[0]), float(parts[1])]
        except (ValueError, IndexError):
            pass

    variable = cmr_params.get("variable")
    cube_vars = collection_metadata.get("cube:variables", {})
    if variable and variable in cube_vars:
        output["units"] = cube_vars[variable].get("unit")

    return output
