"""
UMM-Vis lookup tool — find Worldview/GIBS layers associated with a CMR collection.

Maps a CMR collection concept-id to the GIBS visualization layer ID(s) recorded in
UMM-Vis. The output's ``layer_id`` is type-compatible with WorldviewPermalinkTool's
``LayerSpec.id``, completing the chain ``query → collection → layer → permalink``.

Lookup paths. The canonical filter ``concept-ids=<C-id>`` works for records that
populate ``umm.ConceptIds[].Value`` with the parent collection's C-id. Some UAT
records still leave that field as a placeholder; this tool falls back to a
client-side scan of ``umm.SourceDatasets`` / ``umm.RepresentingDatasets`` when the
canonical query returns empty.

Layer-ID resolution. ``umm.Name`` typically carries a processing-version suffix
(``_v1_STD`` / ``_v2_NRT`` / …) that is *not* present in the public GIBS WMTS
catalog. We prefer ``Specification.ProductIdentification.BestAvailableExternalIdentifier``
(the canonical externally-published name); failing that, we strip the version
suffix from ``umm.Name``. Validation against the live GIBS WMTS catalog is
optional and informational — set ``validate_against_gibs=True`` to populate
``LayerMapping.available_in_gibs``.
"""

from __future__ import annotations

import os
import re
import time
from datetime import datetime
from typing import Any, Literal

import httpx
from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool, BaseToolConfig
from loguru import logger
from pydantic import BaseModel, Field

from akd_ext.mcp import mcp_tool

# Worldview projection identifiers used in URLs. EPSG:3857 (Web Mercator) is
# intentionally absent — the Worldview UI does not expose it as a top-level
# projection, so an OutputProjection of "EPSG:3857" maps to None.
_EPSG_TO_WORLDVIEW: dict[str, str] = {
    "EPSG:4326": "geographic",
    "EPSG:3413": "arctic",
    "EPSG:3031": "antarctic",
}

# Strip trailing processing-version markers from umm.Name to recover the public
# GIBS layer identifier. Covers the common patterns we observed across all
# 1109 prod viz records (e.g. "..._v1_STD", "..._v7_NRT").
_VERSION_SUFFIX_RE = re.compile(r"_v\d+_(STD|NRT)$")

# Sentinel/junk values that have leaked into BestAvailableExternalIdentifier on
# both UAT and prod. These are not real GIBS layer names.
_KNOWN_JUNK_LAYER_IDS: frozenset[str] = frozenset({"DUJUAN", "TEST", "PLACEHOLDER", "YET_TO_SUPPLY"})

# GIBS WMTS GetCapabilities endpoints. Merging all four projections is required
# because polar-only layers (e.g. sea ice) are not advertised on epsg4326.
_GIBS_WMTS_PROJECTIONS = ("epsg4326", "epsg3857", "epsg3413", "epsg3031")

MatchPath = Literal["concept_ids", "source_datasets_fallback"]
LayerIdSource = Literal["best", "name_stripped", "name_raw", "best_pending_gibs", "unresolved"]

# -----------------------------------------------------------------------------
# Tool Config
# -----------------------------------------------------------------------------


class UMMVisLookupToolConfig(BaseToolConfig):
    """Configuration for the UMM-Vis Lookup Tool.
    - base_url: CMR Search base. UAT default; switch to OPS via CMR_BASE_URL env var.
    - timeout: HTTP timeout in seconds (default 15s).
    - page_size: UMM-Vis search page size (default 2000; covers UAT today).
    - fallback_cache_ttl_seconds: TTL for caching the Path B all-records fetch.
    Default 300s; set 0 to disable.
    """

    base_url: str = Field(
        default_factory=lambda: os.getenv("CMR_BASE_URL", "https://cmr.uat.earthdata.nasa.gov/search"),
        description=("CMR Search base URL. UAT default; switch to OPS via the CMR_BASE_URL env var."),
    )
    timeout: float = Field(
        default=15.0,
        description="HTTP request timeout in seconds.",
    )
    page_size: int = Field(
        default=2000,
        ge=1,
        le=2000,
        description=("UMM-Vis search page size (max 2000; UAT has ~1155 records total today)."),
    )
    fallback_cache_ttl_seconds: float = Field(
        default=300.0,
        ge=0.0,
        description=("TTL for the Path B all-records cache. Set 0 to disable caching."),
    )
    validate_against_gibs: bool = Field(
        default=False,
        description=(
            "When True, fetch the GIBS WMTS GetCapabilities catalog and tag each "
            "LayerMapping with available_in_gibs. Informational only — layers are not "
            "filtered out when missing from GIBS, since some valid records describe "
            "layers not yet published."
        ),
    )
    gibs_cache_ttl_seconds: float = Field(
        default=86400.0,
        ge=0.0,
        description=(
            "TTL for the cached merged GIBS WMTS catalog (~5 MB across 4 projections). "
            "Default 24h; the catalog changes slowly. Set 0 to disable caching."
        ),
    )


# -----------------------------------------------------------------------------
# Tool Input/Output Schema
# -----------------------------------------------------------------------------


class UMMVisLookupToolInputSchema(InputSchema):
    """Input: a single CMR collection concept-id."""

    collection_concept_id: str = Field(
        ...,
        pattern=r"^C\d+-[A-Z0-9_]+$",
        description="CMR collection concept-id, e.g. 'C1701805619-GES_DISC'.",
        examples=["C1701805619-GES_DISC"],
    )


class LayerMapping(BaseModel):
    """A single Worldview/GIBS layer associated with a CMR collection.

    ``layer_id`` is the resolved GIBS layer identifier — the name a Worldview URL
    or WMTS request actually accepts. It is derived from
    ``umm.Specification.ProductIdentification.BestAvailableExternalIdentifier`` when
    that field is set and valid; otherwise it falls back to ``umm.Name`` with any
    trailing processing-version suffix (``_v\\d+_(STD|NRT)``) stripped. Optional
    fields carry display, disambiguation, and permalink-default hints; each is
    ``None`` when the source record omits it or carries a placeholder value.
    """

    layer_id: str = Field(
        ...,
        description=(
            "Resolved GIBS layer identifier suitable for WorldviewPermalinkTool's "
            "LayerSpec.id. See ``layer_id_source`` for which UMM-Vis field was used."
        ),
    )
    layer_id_source: LayerIdSource = Field(
        ...,
        description=(
            "Which UMM-Vis field produced layer_id: 'best' (BestAvailableExternalIdentifier "
            "matched the GIBS catalog), 'name_stripped' (Name with version suffix removed), "
            "'name_raw' (Name had no version suffix), 'best_pending_gibs' (Best is set but "
            "the layer is not yet in GIBS WMTS — likely a pre-publication record)."
        ),
    )
    available_in_gibs: bool | None = Field(
        None,
        description=(
            "Whether layer_id appears in the live GIBS WMTS catalog. None when validation "
            "was not performed (config.validate_against_gibs=False)."
        ),
    )
    visualization_concept_id: str = Field(
        ...,
        description=("UMM-Vis record concept-id (VIS<n>-<PROVIDER>). Useful for traceability."),
    )
    visualization_type: str = Field(
        ...,
        description="UMM-Vis VisualizationType: 'tiles' (Worldview-renderable) or 'maps'.",
    )

    title: str | None = Field(None, description="umm.Title.")
    subtitle: str | None = Field(
        None,
        description="umm.Subtitle, e.g. 'AIRS / Aqua' — sensor / platform context.",
    )
    measurement: str | None = Field(
        None,
        description="ProductMetadata.Measurement, e.g. 'Carbon Monoxide'.",
    )
    daynight: str | None = Field(
        None,
        description="'Day' / 'Night' / 'Both' — daynight discrimination.",
    )

    spatial_coverage: list[float] | None = Field(
        None,
        min_length=4,
        max_length=4,
        description="WGS84 bounding box: [west, south, east, north].",
    )
    temporal_start: datetime | None = Field(
        None,
        description="Layer's TemporalCoverage start.",
    )
    temporal_end: datetime | None = Field(
        None,
        description="Layer's TemporalCoverage end. None means ongoing.",
    )
    ongoing: bool | None = Field(
        None,
        description="Whether the layer is still being updated (ProductMetadata.Ongoing).",
    )
    layer_period: str | None = Field(
        None,
        description="LayerPeriod, e.g. 'Daily' or 'Monthly'.",
    )

    worldview_projections: list[str] | None = Field(
        None,
        description=(
            "Worldview-compatible projections derived from Generation.OutputProjection: "
            "any of 'geographic', 'arctic', 'antarctic'."
        ),
    )

    colormap_url: str | None = Field(
        None,
        description="ColorMap XML URL — useful for legend rendering or palette overrides.",
    )


class UMMVisLookupToolOutputSchema(OutputSchema):
    """Output for the UMM-Vis Lookup Tool."""

    collection_concept_id: str = Field(
        ...,
        description="Echo of the input collection concept-id.",
    )
    layers: list[LayerMapping] = Field(
        ...,
        description=("Matched UMM-Vis layers. May be empty when no association exists yet."),
    )
    match_path: MatchPath = Field(
        ...,
        description=(
            "Which lookup path produced the layers: 'concept_ids' (canonical "
            "`concept-ids=` filter) or 'source_datasets_fallback' (client-side scan "
            "of umm.SourceDatasets / umm.RepresentingDatasets)."
        ),
    )


# -----------------------------------------------------------------------------
# UMM VisLookup AKD Tool
# -----------------------------------------------------------------------------


@mcp_tool
class UMMVisLookupTool(BaseTool[UMMVisLookupToolInputSchema, UMMVisLookupToolOutputSchema]):
    """
    Find Worldview/GIBS layers associated with a CMR collection.

    Given a collection concept-id (e.g. 'C1701805619-GES_DISC'), returns the GIBS
    visualization layer(s) that render data from that collection. Output ``layer_id``
    is type-compatible with the ``LayerSpec.id`` consumed by WorldviewPermalinkTool,
    completing the agent chain ``user query → collection → layer → permalink``.
    """

    input_schema = UMMVisLookupToolInputSchema
    output_schema = UMMVisLookupToolOutputSchema
    config_schema = UMMVisLookupToolConfig

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._all_records_cache: tuple[float, list[dict[str, Any]]] | None = None
        self._gibs_layers_cache: tuple[float, frozenset[str]] | None = None

    async def _fetch(
        self,
        client: httpx.AsyncClient,
        params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        url = f"{self.config.base_url.rstrip('/')}/visualizations.umm_json"
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
        except httpx.TimeoutException as e:
            raise TimeoutError(f"CMR request timed out after {self.config.timeout}s") from e
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"CMR returned status {e.response.status_code}: {e.response.text}") from e
        except httpx.RequestError as e:
            raise RuntimeError(f"Failed to reach CMR: {e}") from e

        data = response.json()
        items = data.get("items", [])
        if not isinstance(items, list):
            raise RuntimeError(f"Unexpected CMR response shape: {data!r}")
        return items

    async def _fetch_all_records(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """Fetch one page of all UMM-Vis records (Path B), with TTL cache."""
        ttl = self.config.fallback_cache_ttl_seconds
        if ttl > 0 and self._all_records_cache is not None:
            fetched_at, cached_items = self._all_records_cache
            if (time.monotonic() - fetched_at) < ttl:
                logger.debug("Path B: using cached all-records ({} items)", len(cached_items))
                return cached_items

        items = await self._fetch(client, {"page_size": self.config.page_size})
        if ttl > 0:
            self._all_records_cache = (time.monotonic(), items)
        return items

    async def _fetch_gibs_layers(self, client: httpx.AsyncClient) -> frozenset[str]:
        """Fetch the merged GIBS WMTS layer catalog across all 4 projections."""
        ttl = self.config.gibs_cache_ttl_seconds
        if ttl > 0 and self._gibs_layers_cache is not None:
            fetched_at, cached_layers = self._gibs_layers_cache
            if (time.monotonic() - fetched_at) < ttl:
                return cached_layers

        layers: set[str] = set()
        for proj in _GIBS_WMTS_PROJECTIONS:
            url = f"https://gibs.earthdata.nasa.gov/wmts/{proj}/best/wmts.cgi"
            try:
                response = await client.get(url, params={"SERVICE": "WMTS", "request": "GetCapabilities"})
                response.raise_for_status()
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                logger.warning("GIBS GetCapabilities fetch failed for {}: {}", proj, e)
                continue
            layers.update(re.findall(r"<ows:Identifier>([^<]+)</ows:Identifier>", response.text))

        result = frozenset(layers)
        if ttl > 0:
            self._gibs_layers_cache = (time.monotonic(), result)
        logger.debug("GIBS WMTS catalog loaded: {} unique layer identifiers", len(result))
        return result

    async def _arun(self, params: UMMVisLookupToolInputSchema) -> UMMVisLookupToolOutputSchema:
        cid = params.collection_concept_id

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            path_a_items = await self._fetch(
                client,
                {"concept-ids": cid, "page_size": self.config.page_size},
            )
            if path_a_items:
                logger.debug("Path A hit for {}: {} items", cid, len(path_a_items))
                items = path_a_items
                match_path: MatchPath = "concept_ids"
            else:
                logger.debug("Path A empty for {}; falling back to scan", cid)
                all_items = await self._fetch_all_records(client)
                items = [item for item in all_items if cid in _extract_source_cids(item)]
                match_path = "source_datasets_fallback"
                logger.debug(
                    "Path B for {}: matched {} of {} records",
                    cid,
                    len(items),
                    len(all_items),
                )

            gibs_layers: frozenset[str] | None = None
            if self.config.validate_against_gibs:
                gibs_layers = await self._fetch_gibs_layers(client)

        layers: list[LayerMapping] = []
        for item in items:
            mapping = _to_layer_mapping(item, gibs_layers=gibs_layers)
            if mapping is not None:
                layers.append(mapping)

        deduped = _dedupe_layers(layers)

        return UMMVisLookupToolOutputSchema(
            collection_concept_id=cid,
            layers=deduped,
            match_path=match_path,
        )


# -----------------------------------------------------------------------------
# Utils
# -----------------------------------------------------------------------------


def _as_dict(value: Any) -> dict[str, Any]:
    """Return ``value`` if it is a dict, else an empty dict.

    UMM-Vis records sometimes substitute strings for nested objects. Treat those
    as missing rather than crashing on ``.get(...)``.
    """
    return value if isinstance(value, dict) else {}


def _placeholder_value(text: Any) -> bool:
    if not isinstance(text, str):
        return False
    upper = text.strip().upper()
    return "PLACEHOLDER" in upper or upper == "YET_TO_SUPPLY"


def _clean_str(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    if not value.strip() or _placeholder_value(value):
        return None
    return value


def _coerce_datetime(value: Any) -> datetime | None:
    """Best-effort coerce an ISO-8601 string to a datetime."""
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate:
        return None
    candidate = candidate.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        logger.debug("Could not parse temporal value: {!r}", value)
        return None


def _coerce_bbox(value: Any) -> list[float] | None:
    """Coerce a UMM-Vis WGS84SpatialCoverage entry to ``[west, south, east, north]``.

    Accepts either a 4-element list/tuple ``[W, S, E, N]`` or a dict with
    ``MinLongitude`` / ``MinLatitude`` / ``MaxLongitude`` / ``MaxLatitude`` keys.
    """
    if isinstance(value, (list, tuple)) and len(value) == 4:
        try:
            return [float(v) for v in value]
        except (TypeError, ValueError):
            return None
    if isinstance(value, dict):
        try:
            return [
                float(value["MinLongitude"]),
                float(value["MinLatitude"]),
                float(value["MaxLongitude"]),
                float(value["MaxLatitude"]),
            ]
        except (KeyError, TypeError, ValueError):
            return None
    return None


def _map_projections(value: Any) -> list[str] | None:
    """Map UMM-Vis OutputProjection (EPSG strings) to Worldview projection names."""
    if isinstance(value, str):
        mapped = _EPSG_TO_WORLDVIEW.get(value.strip())
        return [mapped] if mapped else None
    if isinstance(value, list):
        mapped = [
            _EPSG_TO_WORLDVIEW[p.strip()] for p in value if isinstance(p, str) and p.strip() in _EPSG_TO_WORLDVIEW
        ]
        return mapped or None
    return None


def _extract_source_cids(item: dict[str, Any]) -> set[str]:
    """Pull all C-ids from a record's SourceDatasets and RepresentingDatasets.

    UMM-Vis v1.1.0 nests these under ``umm.Specification.ProductMetadata`` and
    populates them as a plain list of C-id strings. Older fixture shapes used
    a list of ``{Value: ...}`` dicts, and some records hoist the lists directly
    onto ``umm``; both variants are tolerated.
    """
    umm = _as_dict(item.get("umm"))
    product_metadata = _as_dict(_as_dict(umm.get("Specification")).get("ProductMetadata"))
    cids: set[str] = set()
    for source in (product_metadata, umm):
        for field_name in ("SourceDatasets", "RepresentingDatasets"):
            entries = source.get(field_name)
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if isinstance(entry, str) and entry:
                    cids.add(entry)
                elif isinstance(entry, dict):
                    value = entry.get("Value")
                    if isinstance(value, str) and value:
                        cids.add(value)
    return cids


def _looks_like_layer_id(value: str | None) -> bool:
    """Cheap sanity check to reject obvious junk in BestAvailableExternalIdentifier."""
    if not value or len(value) < 4:
        return False
    if value.upper() in _KNOWN_JUNK_LAYER_IDS:
        return False
    return True


def _resolve_layer_id(
    umm: dict[str, Any],
    *,
    gibs_layers: frozenset[str] | None = None,
) -> tuple[str | None, LayerIdSource]:
    """Resolve a UMM-Vis record to its public GIBS layer identifier.

    Resolution order:
      1. ``Specification.ProductIdentification.BestAvailableExternalIdentifier`` —
         the canonical externally-published name. When ``gibs_layers`` is given,
         we also confirm the value is in the live catalog before returning it.
      2. ``umm.Name`` with the trailing ``_v\\d+_(STD|NRT)`` processing-version
         suffix stripped. Rescues records where Best is missing or junk.
      3. If Best is set but isn't in the GIBS catalog (and the suffix-strip
         didn't help either), surface it as ``best_pending_gibs`` — these are
         legitimate records describing layers not yet published to GIBS.

    Validated against 1109 prod viz records: ~98.7% resolve through paths 1 or 2;
    the remainder fall into ``best_pending_gibs`` (e.g. the AMSRU2 L3 series).
    """
    pid = _as_dict(_as_dict(umm.get("Specification")).get("ProductIdentification"))
    best_raw = pid.get("BestAvailableExternalIdentifier")
    best = best_raw if isinstance(best_raw, str) and _looks_like_layer_id(best_raw) else None
    name = _clean_str(umm.get("Name"))

    # 1. Best is canonical — return it if it's plausibly a layer name.
    #    When we have a GIBS catalog, prefer Best only if it's actually in the
    #    catalog; otherwise fall through to the suffix-strip rescue.
    if best and (gibs_layers is None or best in gibs_layers):
        return best, "best"

    # 2. Strip processing-version suffix from Name.
    if name:
        stripped = _VERSION_SUFFIX_RE.sub("", name)
        if gibs_layers is None:
            return stripped, ("name_stripped" if stripped != name else "name_raw")
        if stripped in gibs_layers:
            return stripped, ("name_stripped" if stripped != name else "name_raw")

    # 3. Best was set but didn't validate; surface it as pending-GIBS rather
    #    than dropping the record. Worldview will silently skip unknown layers,
    #    but downstream code can use available_in_gibs to warn the user.
    if best:
        return best, "best_pending_gibs"

    # 4. Last resort: return raw Name (already None-guarded above).
    if name:
        return name, "name_raw"

    return None, "unresolved"


def _to_layer_mapping(
    item: dict[str, Any],
    *,
    gibs_layers: frozenset[str] | None = None,
) -> LayerMapping | None:
    """Normalize a UMM-Vis item into a LayerMapping. Returns None when the
    record lacks the minimum required identity fields."""
    meta = _as_dict(item.get("meta"))
    umm = _as_dict(item.get("umm"))

    vis_concept_id = meta.get("concept-id")
    if not isinstance(vis_concept_id, str) or not vis_concept_id:
        return None

    layer_id, source = _resolve_layer_id(umm, gibs_layers=gibs_layers)
    if layer_id is None:
        return None

    spec = _as_dict(umm.get("Specification"))
    product_id = _as_dict(spec.get("ProductIdentification"))
    product_metadata = _as_dict(spec.get("ProductMetadata"))
    generation = _as_dict(umm.get("Generation"))

    temporal = _as_dict(product_metadata.get("TemporalCoverage"))
    ongoing_raw = product_metadata.get("Ongoing")

    title = _clean_str(umm.get("Title")) or _clean_str(product_id.get("WorldviewTitle"))
    subtitle = _clean_str(umm.get("Subtitle")) or _clean_str(product_id.get("WorldviewSubtitle"))

    available_in_gibs = (layer_id in gibs_layers) if gibs_layers is not None else None

    return LayerMapping(
        layer_id=layer_id,
        layer_id_source=source,
        available_in_gibs=available_in_gibs,
        visualization_concept_id=vis_concept_id,
        visualization_type=str(umm.get("VisualizationType") or ""),
        title=title,
        subtitle=subtitle,
        measurement=_clean_str(product_metadata.get("Measurement")),
        daynight=_clean_str(product_metadata.get("Daynight")),
        spatial_coverage=_coerce_bbox(product_metadata.get("WGS84SpatialCoverage")),
        temporal_start=_coerce_datetime(temporal.get("StartDate")),
        temporal_end=_coerce_datetime(temporal.get("EndDate")),
        ongoing=ongoing_raw if isinstance(ongoing_raw, bool) else None,
        layer_period=_clean_str(product_metadata.get("LayerPeriod")),
        worldview_projections=_map_projections(generation.get("OutputProjection")),
        colormap_url=_clean_str(product_metadata.get("ColorMap")),
    )


# Source ranking for de-duplication: prefer mappings derived from the canonical
# Best field over name-stripped variants over pending-GIBS fallbacks.
_SOURCE_RANK: dict[LayerIdSource, int] = {
    "best": 0,
    "name_stripped": 1,
    "name_raw": 2,
    "best_pending_gibs": 3,
    "unresolved": 4,
}


def _dedupe_layers(layers: list[LayerMapping]) -> list[LayerMapping]:
    """Collapse duplicate (layer_id, visualization_type) pairs, keeping the
    highest-quality mapping. CMR commonly returns multiple revisions of the
    same logical layer (NRT vs STD, test-provider duplicates); without this
    a downstream agent picking ``layers[0]`` can land on a junk record."""
    best_by_key: dict[tuple[str, str], LayerMapping] = {}
    for layer in layers:
        key = (layer.layer_id, layer.visualization_type)
        existing = best_by_key.get(key)
        if existing is None:
            best_by_key[key] = layer
            continue
        # Prefer better source; on tie, prefer the one with more populated optional fields.
        if _SOURCE_RANK[layer.layer_id_source] < _SOURCE_RANK[existing.layer_id_source]:
            best_by_key[key] = layer
        elif _SOURCE_RANK[layer.layer_id_source] == _SOURCE_RANK[existing.layer_id_source]:
            if _populated_field_count(layer) > _populated_field_count(existing):
                best_by_key[key] = layer
    return list(best_by_key.values())


def _populated_field_count(layer: LayerMapping) -> int:
    """Count optional fields set to non-None on a LayerMapping (tiebreaker)."""
    optional_fields = (
        "title",
        "subtitle",
        "measurement",
        "daynight",
        "spatial_coverage",
        "temporal_start",
        "temporal_end",
        "ongoing",
        "layer_period",
        "worldview_projections",
        "colormap_url",
    )
    return sum(1 for f in optional_fields if getattr(layer, f) is not None)


if __name__ == "__main__":
    import asyncio

    # Two probes that exercise both paths against live UAT:
    # - C9876543210-ABCDAAC: the universal placeholder C-id → Path A returns ~1100 records.
    # - C3550187110-ESDIS:   a real C-id present in live SourceDatasets → Path B fires.
    SAMPLE_CIDS: list[str] = [
        "C9876543210-ABCDAAC",
        "C3550187110-ESDIS",
    ]

    async def _smoke() -> None:
        tool = UMMVisLookupTool()
        for cid in SAMPLE_CIDS:
            logger.info("Looking up layers for {}", cid)
            out = await tool.arun(UMMVisLookupToolInputSchema(collection_concept_id=cid))
            logger.info(
                "{} -> match_path={!s}, layers={}",
                cid,
                out.match_path,
                len(out.layers),
            )
            for layer in out.layers[:3]:
                logger.info(
                    "  - {} ({}): title={!r} subtitle={!r} bbox={} projections={}",
                    layer.layer_id,
                    layer.visualization_concept_id,
                    layer.title,
                    layer.subtitle,
                    layer.spatial_coverage,
                    layer.worldview_projections,
                )
            if len(out.layers) > 3:
                logger.info("  ... and {} more", len(out.layers) - 3)

    asyncio.run(_smoke())
