"""Tests for UMMVisLookupTool."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
import pytest
from pydantic import ValidationError

from akd_ext.tools.worldview.cmr_umm_vis import (
    LayerMapping,
    UMMVisLookupTool,
    UMMVisLookupToolConfig,
    UMMVisLookupToolInputSchema,
    UMMVisLookupToolOutputSchema,
)
from akd_ext.tools.worldview.cmr_umm_vis.ummvis_lookup import (
    _coerce_bbox,
    _coerce_datetime,
    _dedupe_layers,
    _extract_source_cids,
    _map_projections,
    _resolve_layer_id,
    _to_layer_mapping,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


def _airs_record(
    *,
    name: str = "AIRS_L2_Carbon_Monoxide_500hPa_Volume_Mixing_Ratio_Day_v7_STD",
    vis_concept_id: str = "VIS1277379058-CMR_TEST",
    source_cid: str = "C3550187110-ESDIS",
) -> dict[str, Any]:
    """Build a UMM-Vis record matching the live UAT shape we observed."""
    return {
        "meta": {"concept-id": vis_concept_id, "provider-id": "CMR_TEST"},
        "umm": {
            "Name": name,
            "Title": "Carbon Monoxide (L2, 500 hPa, Day)",
            "Subtitle": "AIRS / Aqua",
            "Description": "YET_TO_SUPPLY",
            "VisualizationType": "tiles",
            "ConceptIds": [
                {
                    "Type": "STD",
                    "Value": "C9876543210-ABCDAAC",
                    "ShortName": "SHORTNAME PLACEHOLDER",
                    "Title": "TITLE PLACEHOLDER",
                    "Version": "1.0",
                    "DataCenter": "DATACENTER PLACEHOLDER",
                }
            ],
            "Specification": {
                "ProductIdentification": {
                    "InternalIdentifier": name,
                    "GIBSTitle": "Carbon Monoxide (Daytime, 500 hPa, L2)",
                    "WorldviewTitle": "Carbon Monoxide",
                    "WorldviewSubtitle": "Daytime / 500 hPa, L2 / AIRS / Aqua",
                },
                "ProductMetadata": {
                    "InternalIdentifier": name,
                    "SourceDatasets": [source_cid],
                    "RepresentingDatasets": [source_cid],
                    "Measurement": "Carbon Monoxide",
                    "ParameterUnits": ["ppbv"],
                    "Daynight": "Day",
                    "OrbitDirection": "Ascending",
                    "Ongoing": True,
                    "LayerPeriod": "Daily",
                    "TemporalCoverage": {
                        "StartDate": "2002-08-30T00:00:00Z",
                        "EndDate": "2024-12-31T23:59:59Z",
                    },
                    "WGS84SpatialCoverage": [-180.0, -90.0, 180.0, 90.0],
                    "ColorMap": (
                        "https://gibs.earthdata.nasa.gov/colormaps/v1.3/AIRS_Carbon_Monoxide_Volume_Mixing_Ratio.xml"
                    ),
                },
            },
            "Generation": {
                "SourceProjection": "EPSG:4326",
                "OutputProjection": "EPSG:4326",
                "OutputResolution": "2km",
                "OutputFormat": "PPNG",
            },
            "MetadataSpecification": {
                "URL": "https://cdn.earthdata.nasa.gov/umm/visualization/v1.1.0",
                "Name": "UMM-Vis",
                "Version": "1.1.0",
            },
        },
    }


# -----------------------------------------------------------------------------
# Schema-level / pure-function unit tests
# -----------------------------------------------------------------------------


@pytest.mark.unit
class TestInputSchema:
    def test_accepts_valid_concept_id(self) -> None:
        schema = UMMVisLookupToolInputSchema(collection_concept_id="C1701805619-GES_DISC")
        assert schema.collection_concept_id == "C1701805619-GES_DISC"

    @pytest.mark.parametrize(
        "bad_value",
        [
            "",
            "not-a-cid",
            "G1701805619-GES_DISC",  # G prefix is granule, not collection
            "C1701805619",  # missing provider
            "C1701805619-",  # empty provider
            "1701805619-GES_DISC",  # missing C prefix
            "C1701805619-ges_disc",  # lowercase provider
        ],
    )
    def test_rejects_invalid_concept_id(self, bad_value: str) -> None:
        with pytest.raises(ValidationError):
            UMMVisLookupToolInputSchema(collection_concept_id=bad_value)


@pytest.mark.unit
class TestHelpers:
    def test_extract_source_cids_from_live_string_shape(self) -> None:
        """UMM-Vis v1.1.0 in UAT uses plain-string entries (the live shape)."""
        item = {
            "umm": {
                "Specification": {
                    "ProductMetadata": {
                        "SourceDatasets": ["C1-A", "C2-A"],
                        "RepresentingDatasets": ["C2-A", "C3-B"],
                    }
                }
            }
        }
        assert _extract_source_cids(item) == {"C1-A", "C2-A", "C3-B"}

    def test_extract_source_cids_from_dict_shape(self) -> None:
        """Tolerate the older ``[{Value: ...}]`` dict shape too."""
        item = {
            "umm": {
                "Specification": {
                    "ProductMetadata": {
                        "SourceDatasets": [{"Value": "C1-A"}, {"Value": "C2-A"}],
                        "RepresentingDatasets": [{"Value": "C3-B"}],
                    }
                }
            }
        }
        assert _extract_source_cids(item) == {"C1-A", "C2-A", "C3-B"}

    def test_extract_source_cids_handles_missing_fields(self) -> None:
        assert _extract_source_cids({}) == set()
        assert _extract_source_cids({"umm": {}}) == set()
        assert _extract_source_cids({"umm": {"Specification": {"ProductMetadata": {"SourceDatasets": None}}}}) == set()

    def test_extract_source_cids_skips_non_string_values(self) -> None:
        item = {
            "umm": {
                "Specification": {
                    "ProductMetadata": {
                        "SourceDatasets": [
                            "C1-A",
                            None,
                            42,
                            {"Value": "C2-A"},
                            {"NotValue": "C3-A"},
                        ],
                    }
                }
            }
        }
        assert _extract_source_cids(item) == {"C1-A", "C2-A"}

    def test_coerce_datetime_iso_with_z(self) -> None:
        result = _coerce_datetime("2002-08-30T00:00:00Z")
        assert result == datetime(2002, 8, 30, 0, 0, 0, tzinfo=timezone.utc)

    @pytest.mark.parametrize("bad", [None, "", "  ", "not-a-date", 42])
    def test_coerce_datetime_returns_none_on_garbage(self, bad: Any) -> None:
        assert _coerce_datetime(bad) is None

    def test_coerce_bbox_from_list(self) -> None:
        assert _coerce_bbox([-180, -90, 180, 90]) == [-180.0, -90.0, 180.0, 90.0]

    def test_coerce_bbox_from_dict(self) -> None:
        assert _coerce_bbox(
            {
                "MinLongitude": -180,
                "MinLatitude": -90,
                "MaxLongitude": 180,
                "MaxLatitude": 90,
            }
        ) == [-180.0, -90.0, 180.0, 90.0]

    @pytest.mark.parametrize(
        "bad",
        [None, "", [], [1, 2, 3], {"MinLongitude": "not-a-number"}],
    )
    def test_coerce_bbox_returns_none_on_garbage(self, bad: Any) -> None:
        assert _coerce_bbox(bad) is None

    def test_map_projections_string(self) -> None:
        assert _map_projections("EPSG:4326") == ["geographic"]
        assert _map_projections("EPSG:3413") == ["arctic"]
        assert _map_projections("EPSG:3031") == ["antarctic"]

    def test_map_projections_list(self) -> None:
        assert _map_projections(["EPSG:3413", "EPSG:3031"]) == ["arctic", "antarctic"]

    def test_map_projections_unknown_returns_none(self) -> None:
        assert _map_projections("EPSG:9999") is None
        assert _map_projections([]) is None
        assert _map_projections(None) is None


@pytest.mark.unit
class TestNormalizer:
    def test_full_record_round_trip(self) -> None:
        mapping = _to_layer_mapping(_airs_record())
        assert mapping is not None
        # Fixture has no BestAvailableExternalIdentifier, so resolution falls back
        # to umm.Name with the trailing "_v7_STD" suffix stripped — that matches
        # the public GIBS layer identifier.
        assert mapping.layer_id == "AIRS_L2_Carbon_Monoxide_500hPa_Volume_Mixing_Ratio_Day"
        assert mapping.layer_id_source == "name_stripped"
        assert mapping.available_in_gibs is None  # validation not requested
        assert mapping.visualization_concept_id == "VIS1277379058-CMR_TEST"
        assert mapping.visualization_type == "tiles"
        assert mapping.title == "Carbon Monoxide (L2, 500 hPa, Day)"
        assert mapping.subtitle == "AIRS / Aqua"
        assert mapping.measurement == "Carbon Monoxide"
        assert mapping.daynight == "Day"
        assert mapping.spatial_coverage == [-180.0, -90.0, 180.0, 90.0]
        assert mapping.temporal_start == datetime(2002, 8, 30, tzinfo=timezone.utc)
        assert mapping.temporal_end == datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        assert mapping.ongoing is True
        assert mapping.layer_period == "Daily"
        assert mapping.worldview_projections == ["geographic"]
        assert mapping.colormap_url and "AIRS_Carbon_Monoxide" in mapping.colormap_url

    def test_placeholder_strings_become_none(self) -> None:
        record = _airs_record()
        record["umm"]["Title"] = "TITLE PLACEHOLDER"
        record["umm"]["Subtitle"] = "YET_TO_SUPPLY"
        # Also clear the WorldviewTitle/Subtitle fallback so we can verify
        # placeholder handling all the way through.
        record["umm"]["Specification"]["ProductIdentification"]["WorldviewTitle"] = "TITLE PLACEHOLDER"
        record["umm"]["Specification"]["ProductIdentification"]["WorldviewSubtitle"] = "YET_TO_SUPPLY"
        mapping = _to_layer_mapping(record)
        assert mapping is not None
        assert mapping.title is None
        assert mapping.subtitle is None

    def test_title_falls_back_to_worldview_title(self) -> None:
        """When ``umm.Title`` is missing, the Worldview title is used as fallback."""
        record = _airs_record()
        del record["umm"]["Title"]
        del record["umm"]["Subtitle"]
        mapping = _to_layer_mapping(record)
        assert mapping is not None
        assert mapping.title == "Carbon Monoxide"
        assert mapping.subtitle == "Daytime / 500 hPa, L2 / AIRS / Aqua"

    def test_returns_none_when_layer_id_missing(self) -> None:
        record = _airs_record()
        record["umm"].pop("Name")
        assert _to_layer_mapping(record) is None

    def test_returns_none_when_concept_id_missing(self) -> None:
        record = _airs_record()
        record["meta"].pop("concept-id")
        assert _to_layer_mapping(record) is None

    def test_handles_missing_optional_blocks(self) -> None:
        record = {
            "meta": {"concept-id": "VIS1-X"},
            "umm": {"Name": "L1", "VisualizationType": "tiles"},
        }
        mapping = _to_layer_mapping(record)
        assert mapping is not None
        assert mapping.layer_id == "L1"
        assert mapping.layer_id_source == "name_raw"
        assert mapping.title is None
        assert mapping.spatial_coverage is None
        assert mapping.temporal_start is None
        assert mapping.worldview_projections is None

    def test_best_field_takes_priority_over_name(self) -> None:
        record = _airs_record()
        record["umm"]["Specification"]["ProductIdentification"]["BestAvailableExternalIdentifier"] = (
            "AIRS_L2_Carbon_Monoxide_500hPa_Volume_Mixing_Ratio_Day"
        )
        mapping = _to_layer_mapping(record)
        assert mapping is not None
        assert mapping.layer_id == "AIRS_L2_Carbon_Monoxide_500hPa_Volume_Mixing_Ratio_Day"
        assert mapping.layer_id_source == "best"

    def test_junk_best_falls_back_to_name_strip(self) -> None:
        """``DUJUAN`` and similar test pollution must not leak through as a layer id."""
        record = _airs_record()
        record["umm"]["Specification"]["ProductIdentification"]["BestAvailableExternalIdentifier"] = "DUJUAN"
        mapping = _to_layer_mapping(record)
        assert mapping is not None
        assert mapping.layer_id == "AIRS_L2_Carbon_Monoxide_500hPa_Volume_Mixing_Ratio_Day"
        assert mapping.layer_id_source == "name_stripped"

    def test_gibs_validation_tags_available_in_gibs(self) -> None:
        record = _airs_record()
        record["umm"]["Specification"]["ProductIdentification"]["BestAvailableExternalIdentifier"] = (
            "AIRS_L2_Carbon_Monoxide_500hPa_Volume_Mixing_Ratio_Day"
        )
        gibs = frozenset({"AIRS_L2_Carbon_Monoxide_500hPa_Volume_Mixing_Ratio_Day"})
        mapping = _to_layer_mapping(record, gibs_layers=gibs)
        assert mapping is not None
        assert mapping.available_in_gibs is True

    def test_gibs_validation_marks_pending_when_best_not_in_catalog(self) -> None:
        """Layers awaiting GIBS publication should surface as best_pending_gibs, not be dropped."""
        record = _airs_record()
        # Clear Name so the strip-fallback can't rescue it.
        record["umm"]["Name"] = "AMSRU2_L3_Cloud_Liquid_Water_Daily"
        record["umm"]["Specification"]["ProductIdentification"]["BestAvailableExternalIdentifier"] = (
            "AMSRU2_L3_Cloud_Liquid_Water_Daily"
        )
        gibs = frozenset({"some_other_layer"})
        mapping = _to_layer_mapping(record, gibs_layers=gibs)
        assert mapping is not None
        assert mapping.layer_id == "AMSRU2_L3_Cloud_Liquid_Water_Daily"
        assert mapping.layer_id_source == "best_pending_gibs"
        assert mapping.available_in_gibs is False


@pytest.mark.unit
class TestResolveLayerId:
    def test_prefers_best_when_present(self) -> None:
        umm = {
            "Name": "MODIS_Aqua_NDVI_v1_STD",
            "Specification": {"ProductIdentification": {"BestAvailableExternalIdentifier": "MODIS_Aqua_NDVI"}},
        }
        assert _resolve_layer_id(umm) == ("MODIS_Aqua_NDVI", "best")

    @pytest.mark.parametrize("junk", ["DUJUAN", "test", "PLACEHOLDER", "YET_TO_SUPPLY", "", "abc"])
    def test_rejects_junk_best(self, junk: str) -> None:
        umm = {
            "Name": "MODIS_Aqua_NDVI_v1_STD",
            "Specification": {"ProductIdentification": {"BestAvailableExternalIdentifier": junk}},
        }
        layer_id, source = _resolve_layer_id(umm)
        assert layer_id == "MODIS_Aqua_NDVI"
        assert source == "name_stripped"

    @pytest.mark.parametrize(
        "name,expected,source",
        [
            ("MODIS_Aqua_NDVI_v1_STD", "MODIS_Aqua_NDVI", "name_stripped"),
            ("VIIRS_AOT_v12_NRT", "VIIRS_AOT", "name_stripped"),
            (
                "OPERA_L3_Dynamic_Surface_Water_Extent-HLS_v1_STD",
                "OPERA_L3_Dynamic_Surface_Water_Extent-HLS",
                "name_stripped",
            ),
            ("MODIS_Aqua_NDVI", "MODIS_Aqua_NDVI", "name_raw"),
            ("MODIS_Aqua_NDVI_8Day", "MODIS_Aqua_NDVI_8Day", "name_raw"),
        ],
    )
    def test_strips_version_suffix_from_name(self, name: str, expected: str, source: str) -> None:
        umm = {"Name": name}
        assert _resolve_layer_id(umm) == (expected, source)

    def test_returns_none_when_both_missing(self) -> None:
        assert _resolve_layer_id({}) == (None, "unresolved")

    def test_best_pending_gibs_when_strip_does_not_help(self) -> None:
        """Best is set, valid-looking, but not in the GIBS catalog and Name doesn't help."""
        umm = {
            "Name": "AMSRU2_L3_Ocean_Wind_Speed_Daily_vV01_STD",  # vV01 not matched by suffix regex
            "Specification": {
                "ProductIdentification": {"BestAvailableExternalIdentifier": "AMSRU2_L3_Ocean_Wind_Speed_Daily"}
            },
        }
        layer_id, source = _resolve_layer_id(umm, gibs_layers=frozenset({"unrelated"}))
        assert layer_id == "AMSRU2_L3_Ocean_Wind_Speed_Daily"
        assert source == "best_pending_gibs"


@pytest.mark.unit
class TestDedupe:
    def _layer(
        self,
        layer_id: str,
        source: str = "best",
        vis_concept_id: str = "VIS1-X",
        title: str | None = None,
    ) -> LayerMapping:
        return LayerMapping(
            layer_id=layer_id,
            layer_id_source=source,  # type: ignore[arg-type]
            visualization_concept_id=vis_concept_id,
            visualization_type="tiles",
            title=title,
        )

    def test_collapses_by_layer_id_and_visualization_type(self) -> None:
        layers = [
            self._layer("FOO", source="best", vis_concept_id="VIS1-X"),
            self._layer("FOO", source="best", vis_concept_id="VIS2-X"),
            self._layer("BAR", source="best", vis_concept_id="VIS3-X"),
        ]
        deduped = _dedupe_layers(layers)
        assert sorted(layer.layer_id for layer in deduped) == ["BAR", "FOO"]

    def test_prefers_higher_quality_source(self) -> None:
        """A canonical 'best' mapping should win over a 'best_pending_gibs' duplicate."""
        layers = [
            self._layer("FOO", source="best_pending_gibs", vis_concept_id="VIS1-X"),
            self._layer("FOO", source="best", vis_concept_id="VIS2-X"),
        ]
        deduped = _dedupe_layers(layers)
        assert len(deduped) == 1
        assert deduped[0].visualization_concept_id == "VIS2-X"
        assert deduped[0].layer_id_source == "best"

    def test_tiebreaks_by_populated_fields(self) -> None:
        layers = [
            self._layer("FOO", source="best", vis_concept_id="VIS1-X", title=None),
            self._layer("FOO", source="best", vis_concept_id="VIS2-X", title="Something"),
        ]
        deduped = _dedupe_layers(layers)
        assert len(deduped) == 1
        assert deduped[0].visualization_concept_id == "VIS2-X"


# -----------------------------------------------------------------------------
# Two-path behavior tests (httpx stubbed via MockTransport)
# -----------------------------------------------------------------------------


def _make_handler(
    *,
    path_a_items: list[dict[str, Any]],
    all_items: list[dict[str, Any]],
    call_log: list[str],
) -> Any:
    """Build a MockTransport handler that branches on the `concept-ids` query param."""

    def handler(request: httpx.Request) -> httpx.Response:
        params = dict(request.url.params)
        if "concept-ids" in params:
            call_log.append("path_a")
            return httpx.Response(200, json={"hits": len(path_a_items), "items": path_a_items})
        call_log.append("path_b")
        return httpx.Response(200, json={"hits": len(all_items), "items": all_items})

    return handler


def _build_tool_with_transport(transport: httpx.MockTransport) -> UMMVisLookupTool:
    """Tool wired so its httpx.AsyncClient uses the given MockTransport."""

    tool = UMMVisLookupTool(config=UMMVisLookupToolConfig(fallback_cache_ttl_seconds=0.0))

    real_async_client = httpx.AsyncClient

    def factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        kwargs["transport"] = transport
        return real_async_client(*args, **kwargs)

    # Monkeypatch only on this tool's reference. We can't mutate httpx globally
    # without leaking into other tests.
    import akd_ext.tools.worldview.cmr_umm_vis.ummvis_lookup as module

    module.httpx.AsyncClient = factory  # type: ignore[assignment]
    tool._restore_httpx = lambda: setattr(module.httpx, "AsyncClient", real_async_client)  # type: ignore[attr-defined]
    return tool


@pytest.mark.unit
class TestTwoPath:
    @pytest.fixture(autouse=True)
    def _restore_httpx(self):
        # Capture the original before each test, restore after.
        import akd_ext.tools.worldview.cmr_umm_vis.ummvis_lookup as module

        original = module.httpx.AsyncClient
        yield
        module.httpx.AsyncClient = original

    async def test_path_a_hit_does_not_invoke_path_b(self) -> None:
        cid = "C1-PROV"
        record = _airs_record(source_cid=cid)
        call_log: list[str] = []
        transport = httpx.MockTransport(_make_handler(path_a_items=[record], all_items=[], call_log=call_log))
        tool = _build_tool_with_transport(transport)

        result = await tool.arun(UMMVisLookupToolInputSchema(collection_concept_id=cid))

        assert isinstance(result, UMMVisLookupToolOutputSchema)
        assert result.match_path == "concept_ids"
        assert result.collection_concept_id == cid
        assert len(result.layers) == 1
        assert call_log == ["path_a"]

    async def test_path_b_fires_when_path_a_empty(self) -> None:
        cid = "C1701805619-GES_DISC"
        match_record = _airs_record(name="LAYER_THAT_MATCHES", source_cid=cid)
        nonmatch_record = _airs_record(
            name="LAYER_THAT_DOES_NOT_MATCH",
            vis_concept_id="VIS9999-CMR_TEST",
            source_cid="C9999-OTHER",
        )
        call_log: list[str] = []
        transport = httpx.MockTransport(
            _make_handler(
                path_a_items=[],
                all_items=[match_record, nonmatch_record],
                call_log=call_log,
            )
        )
        tool = _build_tool_with_transport(transport)

        result = await tool.arun(UMMVisLookupToolInputSchema(collection_concept_id=cid))

        assert result.match_path == "source_datasets_fallback"
        assert len(result.layers) == 1
        assert result.layers[0].layer_id == "LAYER_THAT_MATCHES"
        assert call_log == ["path_a", "path_b"]

    async def test_path_b_returns_empty_when_no_match(self) -> None:
        cid = "C1701805619-GES_DISC"
        unrelated = _airs_record(source_cid="C9999-OTHER")
        call_log: list[str] = []
        transport = httpx.MockTransport(_make_handler(path_a_items=[], all_items=[unrelated], call_log=call_log))
        tool = _build_tool_with_transport(transport)

        result = await tool.arun(UMMVisLookupToolInputSchema(collection_concept_id=cid))

        assert result.match_path == "source_datasets_fallback"
        assert result.layers == []
        assert call_log == ["path_a", "path_b"]

    async def test_path_b_cache_avoids_second_fetch(self) -> None:
        cid = "C1701805619-GES_DISC"
        match_record = _airs_record(source_cid=cid)
        call_log: list[str] = []
        transport = httpx.MockTransport(
            _make_handler(
                path_a_items=[],
                all_items=[match_record],
                call_log=call_log,
            )
        )
        # Override the default-zero TTL so the cache is active.
        tool = _build_tool_with_transport(transport)
        tool.config.fallback_cache_ttl_seconds = 60.0

        await tool.arun(UMMVisLookupToolInputSchema(collection_concept_id=cid))
        await tool.arun(UMMVisLookupToolInputSchema(collection_concept_id=cid))

        # Two Path A calls (each invocation hits the server first), one Path B (cached).
        assert call_log == ["path_a", "path_b", "path_a"]


# -----------------------------------------------------------------------------
# Live integration tests against UAT
# -----------------------------------------------------------------------------


@pytest.mark.integration
class TestLiveUAT:
    async def test_path_a_hit_with_placeholder_cid(self) -> None:
        """The placeholder C-id is universally indexed in UAT today."""
        tool = UMMVisLookupTool()
        result = await tool.arun(UMMVisLookupToolInputSchema(collection_concept_id="C9876543210-ABCDAAC"))
        assert result.match_path == "concept_ids"
        assert len(result.layers) > 0
        for layer in result.layers[:3]:
            assert isinstance(layer, LayerMapping)
            assert layer.layer_id
            assert layer.visualization_concept_id.startswith("VIS")

    async def test_path_b_hit_with_real_cid(self) -> None:
        """A real C-id (verified in UAT SourceDatasets) goes through the fallback."""
        tool = UMMVisLookupTool()
        result = await tool.arun(UMMVisLookupToolInputSchema(collection_concept_id="C3550187110-ESDIS"))
        assert result.match_path == "source_datasets_fallback"
        assert len(result.layers) >= 1
        layer_ids = {layer.layer_id for layer in result.layers}
        # The Croplands layer is the canonical one associated with C3550187110-ESDIS.
        assert any("Croplands" in lid for lid in layer_ids), layer_ids

    async def test_unrelated_cid_returns_empty(self) -> None:
        tool = UMMVisLookupTool()
        result = await tool.arun(UMMVisLookupToolInputSchema(collection_concept_id="C0000000000-NOSUCHPROV"))
        # Path A returns empty; Path B scan finds no SourceDatasets hits.
        assert result.match_path == "source_datasets_fallback"
        assert result.layers == []
