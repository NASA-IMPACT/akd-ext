"""Comprehensive validation tests for all PDS MCP server modules.

Tests response parsing, input validation, edge cases, error handling,
type coercion, XML parsing, retry logic, and context managers across
OPUS, ODE, IMG, PDS4, SBN, and PDS Catalog modules.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock

from akd_ext.tools.pds.utils.opus_api_models import (
    OPUSObservation,
    OPUSSearchResponse,
    OPUSCountResponse,
    OPUSMetadata,
    OPUSMetadataResponse,
    OPUSFiles,
    OPUSFilesResponse,
    _parse_float as opus_parse_float,
    _parse_int as opus_parse_int,
)
from akd_ext.tools.pds.utils.opus_client import (
    OPUSClient,
    OPUSClientError,
    OPUSRateLimitError,
)
from akd_ext.tools.pds.utils.ode_api_models import (
    ODEProduct,
    ODEProductSearchResponse,
    ODEProductCountResponse,
    ODEInstrumentInfo,
    ODEIIPTResponse,
    ODEFeatureDataResponse,
    ODEFeatureClassesResponse,
    ODEFeatureNamesResponse,
    _parse_float as ode_parse_float,
    _parse_int as ode_parse_int,
)
from akd_ext.tools.pds.utils.ode_client import (
    ODEClient,
)
from akd_ext.tools.pds.utils.img_api_models import (
    IMGSearchResponse,
    IMGCountResponse,
    IMGFacetResponse,
    IMGProduct,
)
from akd_ext.tools.pds.utils.img_client import (
    IMGAtlasClient,
    IMGAtlasClientError,
)
from akd_ext.tools.pds.utils.pds4_client import (
    PDS4Client,
    PDS4RateLimitError,
    validate_urn,
    validate_coordinates,
)
from akd_ext.tools.pds.utils.sbn_api_models import (
    CatchSourcesResponse,
    CatchJobResponse,
    CatchResultsResponse,
    CatchStatusResponse,
)
from akd_ext.tools.pds.utils.sbn_client import (
    SBNCatchClient,
    SBNCatchRateLimitError,
    SBNCatchJobError,
)
from akd_ext.tools.pds.utils.pds_catalog_client import (
    CatalogIndex,
    PDSCatalogClient,
    _matches_term,
    filter_dataset,
    MISSION_ABBREVIATIONS,
    ESSENTIAL_FIELDS,
    FULL_FIELDS,
)

from datetime import date


# ╔══════════════════════════════════════════════════════════════╗
# ║                    HELPER: mock datasets                     ║
# ╚══════════════════════════════════════════════════════════════╝


def _make_ds(
    id="DS-1",
    title="Title",
    node="atm",
    missions=None,
    instruments=None,
    targets=None,
    description="desc",
    pds_version="PDS3",
    dataset_type="volume",
    start_date=None,
    stop_date=None,
    keywords=None,
):
    ds = MagicMock()
    ds.id = id
    ds.title = title
    ds.description = description
    ds.node = MagicMock(value=node)
    ds.pds_version = MagicMock(value=pds_version)
    ds.type = MagicMock(value=dataset_type)
    ds.missions = missions or []
    ds.instruments = instruments or []
    ds.targets = targets or []
    ds.instrument_hosts = []
    ds.data_types = []
    ds.start_date = start_date
    ds.stop_date = stop_date
    ds.keywords = keywords or []
    ds.processing_level = None
    ds.browse_url = f"https://pds.nasa.gov/{id}"
    ds.label_url = None
    ds.source_url = ds.browse_url
    ds.to_search_text = MagicMock(
        return_value=f"{id} {title} {' '.join(missions or [])} {' '.join(targets or [])} {' '.join(instruments or [])}".lower()
    )
    return ds


# ╔══════════════════════════════════════════════════════════════╗
# ║                       OPUS  TESTS                            ║
# ╚══════════════════════════════════════════════════════════════╝


class TestOPUSParsers:
    def test_parse_float_valid(self):
        assert opus_parse_float(3.14) == 3.14
        assert opus_parse_float("2.7") == 2.7
        assert opus_parse_float(42) == 42.0

    def test_parse_float_none_and_invalid(self):
        assert opus_parse_float(None) is None
        assert opus_parse_float("bad") is None
        assert opus_parse_float("") is None
        assert opus_parse_float([]) is None

    def test_parse_int_valid(self):
        assert opus_parse_int(42) == 42
        assert opus_parse_int("100") == 100

    def test_parse_int_none_and_invalid(self):
        assert opus_parse_int(None) is None
        assert opus_parse_int("abc") is None


class TestOPUSObservation:
    def test_from_raw_data_complete(self):
        obs = OPUSObservation.from_raw_data(
            {
                "opusid": "co-iss-test",
                "instrument": "Cassini ISS",
                "planet": "Saturn",
                "target": "Titan",
                "mission": "Cassini",
                "time1": "2004-01-01",
                "time2": "2004-01-02",
                "observationduration": "60.0",
                "ringobsid": "RING_1",
            }
        )
        assert obs.opusid == "co-iss-test"
        assert obs.observation_duration == 60.0
        assert obs.ring_obs_id == "RING_1"

    def test_from_raw_data_empty(self):
        obs = OPUSObservation.from_raw_data({})
        assert obs.opusid == ""
        assert obs.observation_duration is None

    def test_from_raw_data_bad_duration(self):
        obs = OPUSObservation.from_raw_data({"opusid": "x", "observationduration": "N/A"})
        assert obs.observation_duration is None

    def test_from_row_data(self):
        cols = [
            "OPUS ID",
            "Instrument Name",
            "Planet",
            "Intended Target Name(s)",
            "Observation Start Time (YMDhms)",
            "Observation Duration (secs)",
        ]
        row = ["id-1", "ISS", "Saturn", "Titan", "2004-01-01", "120"]
        obs = OPUSObservation.from_row_data(cols, row)
        assert obs.opusid == "id-1"
        assert obs.observation_duration == 120.0

    def test_from_row_data_mismatched(self):
        obs = OPUSObservation.from_row_data(["OPUS ID", "Extra"], ["only-id"])
        assert obs.opusid == "only-id"


class TestOPUSSearchResponse:
    def test_array_format(self):
        resp = OPUSSearchResponse.from_raw_data(
            {
                "page": [["id1", "ISS", "Saturn", "Titan", "2004", "60"]],
                "columns": [
                    "OPUS ID",
                    "Instrument Name",
                    "Planet",
                    "Intended Target Name(s)",
                    "Observation Start Time (YMDhms)",
                    "Observation Duration (secs)",
                ],
                "count": 1,
                "available": 500,
                "start_obs": 1,
                "limit": 100,
            }
        )
        assert resp.status == "success"
        assert len(resp.observations) == 1
        assert resp.available == 500

    def test_dict_format(self):
        resp = OPUSSearchResponse.from_raw_data(
            {
                "page": [{"opusid": "t1", "target": "Io"}],
                "columns": [],
                "count": 1,
                "available": 1,
            }
        )
        assert resp.observations[0].opusid == "t1"

    def test_error(self):
        resp = OPUSSearchResponse.from_raw_data({"error": "Bad param"})
        assert resp.status == "error"
        assert resp.error == "Bad param"

    def test_empty_page(self):
        resp = OPUSSearchResponse.from_raw_data({"page": [], "columns": []})
        assert len(resp.observations) == 0

    def test_non_list_page_and_columns(self):
        resp = OPUSSearchResponse.from_raw_data({"page": "bad", "columns": 42})
        assert len(resp.observations) == 0

    def test_defaults_when_keys_missing(self):
        resp = OPUSSearchResponse.from_raw_data({})
        assert resp.start_obs == 1
        assert resp.limit == 100


class TestOPUSCountResponse:
    def test_success(self):
        resp = OPUSCountResponse.from_raw_data({"data": [{"result_count": 42}]})
        assert resp.count == 42

    def test_error(self):
        resp = OPUSCountResponse.from_raw_data({"error": "fail"})
        assert resp.status == "error"

    def test_empty_data(self):
        assert OPUSCountResponse.from_raw_data({"data": []}).count == 0

    def test_non_list_data(self):
        assert OPUSCountResponse.from_raw_data({"data": "x"}).count == 0


class TestOPUSMetadata:
    def test_instrument_constraint_extraction(self):
        meta = OPUSMetadata.from_raw_data(
            "id1",
            {
                "General Constraints": {"planet": "Saturn"},
                "Cassini ISS Constraints": {"filter1": "CL1"},
            },
        )
        assert meta.instrument_constraints == {"filter1": "CL1"}

    def test_no_instrument_constraints(self):
        meta = OPUSMetadata.from_raw_data("id1", {})
        assert meta.instrument_constraints == {}

    def test_metadata_response_error(self):
        resp = OPUSMetadataResponse.from_raw_data("id1", {"error": "Not found"})
        assert resp.status == "error"


class TestOPUSFiles:
    def test_full_files(self):
        f = OPUSFiles.from_raw_data(
            "oid",
            {
                "data": {
                    "oid": {
                        "browse_thumb": ["http://t.jpg"],
                        "browse_full": ["http://f.jpg"],
                        "raw_image": ["http://r1.img", "http://r2.img"],
                        "calibrated_image": ["http://c.img"],
                    }
                }
            },
        )
        assert f.browse_thumb == "http://t.jpg"
        assert len(f.raw_files) == 2
        assert len(f.calibrated_files) == 1

    def test_empty_data(self):
        f = OPUSFiles.from_raw_data("oid", {"data": {}})
        assert f.raw_files == []

    def test_wrong_opusid(self):
        f = OPUSFiles.from_raw_data("missing", {"data": {"other": {}}})
        assert f.raw_files == []

    def test_browse_as_string(self):
        f = OPUSFiles.from_raw_data(
            "oid",
            {
                "data": {
                    "oid": {
                        "browse_thumb": "http://s.jpg",
                    }
                }
            },
        )
        assert f.browse_thumb == "http://s.jpg"

    def test_extract_first_url_edge_cases(self):
        assert OPUSFiles._extract_first_url([]) is None
        assert OPUSFiles._extract_first_url(None) is None
        assert OPUSFiles._extract_first_url(42) is None

    def test_files_response_error(self):
        resp = OPUSFilesResponse.from_raw_data("id", {"error": "nope"})
        assert resp.status == "error"


class TestOPUSClient:
    def test_defaults(self):
        c = OPUSClient()
        assert "opus.pds-rings.seti.org" in c.base_url
        assert c.max_retries == 3

    def test_build_search_params_minimal(self):
        p = OPUSClient()._build_search_params()
        assert p["limit"] == "100"
        assert "target" not in p

    def test_build_search_params_full(self):
        p = OPUSClient()._build_search_params(target="Titan", planet="saturn", time_min="2004-01-01", limit=50)
        assert p["target"] == "Titan"
        assert p["time1"] == "2004-01-01"
        assert p["limit"] == "50"

    @pytest.mark.asyncio
    async def test_context_manager(self):
        async with OPUSClient() as c:
            assert c._client is not None
        assert c._client is None

    @pytest.mark.asyncio
    async def test_no_init_raises(self):
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await OPUSClient()._request("test")

    @pytest.mark.asyncio
    async def test_rate_limit_raises(self):
        c = OPUSClient(max_retries=0, retry_delay=0.01)
        mock_resp = MagicMock(status_code=429, headers={"retry-after": "0"})
        c._client = AsyncMock()
        c._client.get = AsyncMock(return_value=mock_resp)
        with pytest.raises(OPUSRateLimitError):
            await c._request("test")

    @pytest.mark.asyncio
    async def test_http_error_retries_exhausted(self):
        c = OPUSClient(max_retries=1, retry_delay=0.01)
        c._client = AsyncMock()
        c._client.get = AsyncMock(side_effect=httpx.ConnectError("fail"))
        with pytest.raises(OPUSClientError, match="failed after"):
            await c._request("test")


# ╔══════════════════════════════════════════════════════════════╗
# ║                        ODE  TESTS                            ║
# ╚══════════════════════════════════════════════════════════════╝


class TestODEParsers:
    def test_parse_float(self):
        assert ode_parse_float("3.14") == 3.14
        assert ode_parse_float(None) is None
        assert ode_parse_float("N/A") is None

    def test_parse_int(self):
        assert ode_parse_int("42") == 42
        assert ode_parse_int(None) == 0
        assert ode_parse_int("bad") == 0


class TestODEProduct:
    def test_full_product(self):
        p = ODEProduct.from_raw_data(
            {
                "pdsid": "ESP_012600",
                "ode_id": 12345,
                "Center_latitude": "45.5",
                "Emission_angle": "5.2",
                "Product_files": {
                    "Product_file": [
                        {"FileName": "f.img", "URL": "http://x"},
                    ]
                },
            }
        )
        assert p.pdsid == "ESP_012600"
        assert p.ode_id == "12345"  # int coerced to str
        assert p.center_latitude == 45.5
        assert len(p.product_files) == 1

    def test_ode_id_none(self):
        assert ODEProduct.from_raw_data({"ode_id": None}).ode_id is None

    def test_single_file_dict(self):
        p = ODEProduct.from_raw_data({"Product_files": {"Product_file": {"FileName": "one.img"}}})
        assert len(p.product_files) == 1

    def test_no_files(self):
        assert ODEProduct.from_raw_data({}).product_files == []

    def test_bad_float_values(self):
        p = ODEProduct.from_raw_data(
            {
                "Center_latitude": "N/A",
                "Emission_angle": "",
                "Map_scale": "?",
            }
        )
        assert p.center_latitude is None
        assert p.emission_angle is None


class TestODESearchResponse:
    def test_success(self):
        r = ODEProductSearchResponse.from_raw_data(
            {
                "ODEResults": {
                    "Status": "Success",
                    "Count": "2",
                    "Products": {
                        "Product": [
                            {"pdsid": "A", "ode_id": "1"},
                            {"pdsid": "B", "ode_id": "2"},
                        ]
                    },
                }
            }
        )
        assert r.count == 2
        assert len(r.products) == 2

    def test_single_product_as_dict(self):
        r = ODEProductSearchResponse.from_raw_data(
            {
                "ODEResults": {
                    "Status": "Success",
                    "Count": "1",
                    "Products": {"Product": {"pdsid": "ONLY"}},
                }
            }
        )
        assert len(r.products) == 1

    def test_error(self):
        r = ODEProductSearchResponse.from_raw_data({"ODEResults": {"Status": "ERROR", "Error": "bad target"}})
        assert r.status == "ERROR"

    def test_no_products_string(self):
        r = ODEProductSearchResponse.from_raw_data(
            {"ODEResults": {"Status": "Success", "Count": "0", "Products": "No Products Found"}}
        )
        assert r.products == []

    def test_non_dict_top_level(self):
        r = ODEProductSearchResponse.from_raw_data("not-a-dict")
        assert r.status == "ERROR"

    def test_non_dict_items_filtered(self):
        r = ODEProductSearchResponse.from_raw_data(
            {
                "ODEResults": {
                    "Status": "Success",
                    "Products": {"Product": [{"pdsid": "OK"}, "bad", 42]},
                }
            }
        )
        assert len(r.products) == 1


class TestODECountResponse:
    def test_success(self):
        r = ODEProductCountResponse.from_raw_data({"ODEResults": {"Status": "Success", "Count": "150"}})
        assert r.count == 150

    def test_error(self):
        r = ODEProductCountResponse.from_raw_data({"ODEResults": {"Status": "ERROR", "Error": "missing"}})
        assert r.error == "missing"


class TestODEIIPT:
    def test_success(self):
        r = ODEIIPTResponse.from_raw_data(
            {
                "ODEResults": {
                    "Status": "Success",
                    "IIPT": {
                        "IIPTSet": [
                            {
                                "IHID": "MRO",
                                "IHName": "MRO",
                                "IID": "HIRISE",
                                "IName": "HiRISE",
                                "PT": "EDR",
                                "PTName": "EDR",
                                "NumberProducts": "5000",
                                "IHN": "",
                                "IIN": "",
                            },
                        ]
                    },
                }
            }
        )
        assert len(r.instruments) == 1
        assert r.instruments[0].number_products == 5000
        assert r.instruments[0].instrument_host_name == "MRO"

    def test_single_dict(self):
        r = ODEIIPTResponse.from_raw_data(
            {
                "ODEResults": {
                    "Status": "Success",
                    "IIPT": {"IIPTSet": {"IHID": "LRO", "IID": "LROC", "PT": "E", "PTName": "E"}},
                }
            }
        )
        assert len(r.instruments) == 1

    def test_fallback_property(self):
        info = ODEInstrumentInfo(
            IHID="X", IHN="Old Host", IHName="", IID="Y", IIN="Old Inst", IName="", PT="Z", PTName="Z"
        )
        assert info.instrument_host_name == "Old Host"
        assert info.instrument_name == "Old Inst"


class TestODEFeatures:
    def test_json_success(self):
        r = ODEFeatureDataResponse.from_raw_data(
            {
                "ODEResults": {
                    "Status": "Success",
                    "Count": "1",
                    "Features": {
                        "Feature": [
                            {
                                "FeatureClass": "Crater",
                                "FeatureName": "Gale",
                                "MinLat": "-6",
                                "MaxLat": "-4",
                                "WestLon": "136",
                                "EastLon": "138",
                            }
                        ]
                    },
                }
            }
        )
        assert r.features[0].feature_name == "Gale"

    def test_single_feature_dict(self):
        r = ODEFeatureDataResponse.from_raw_data(
            {
                "ODEResults": {
                    "Status": "Success",
                    "Features": {
                        "Feature": {
                            "FeatureClass": "Mons",
                            "FeatureName": "Olympus",
                            "MinLat": "15",
                            "MaxLat": "25",
                            "WestLon": "220",
                            "EastLon": "230",
                        }
                    },
                }
            }
        )
        assert len(r.features) == 1

    def test_xml_success(self):
        r = ODEFeatureDataResponse.from_xml(
            "<ODEResults><Status>Success</Status><Count>1</Count>"
            "<Features><Feature><FeatureClass>Crater</FeatureClass>"
            "<FeatureName>Jezero</FeatureName><MinLat>18</MinLat>"
            "<MaxLat>19</MaxLat><WestLon>77</WestLon><EastLon>78</EastLon>"
            "</Feature></Features></ODEResults>"
        )
        assert r.features[0].feature_name == "Jezero"

    def test_xml_error(self):
        r = ODEFeatureDataResponse.from_xml("<ODEResults><Status>ERROR</Status><Error>bad</Error></ODEResults>")
        assert r.error == "bad"

    def test_xml_parse_error(self):
        r = ODEFeatureDataResponse.from_xml("<not<valid>xml")
        assert "XML parse error" in r.error

    def test_feature_classes(self):
        r = ODEFeatureClassesResponse.from_raw_data(
            {
                "ODEResults": {
                    "Status": "Success",
                    "FeatureTypes": {"FeatureType": ["Crater", "Mons"]},
                }
            }
        )
        assert len(r.feature_classes) == 2

    def test_feature_classes_string(self):
        r = ODEFeatureClassesResponse.from_raw_data(
            {
                "ODEResults": {
                    "Status": "Success",
                    "FeatureTypes": {"FeatureType": "Crater"},
                }
            }
        )
        assert r.feature_classes == ["Crater"]

    def test_feature_names(self):
        r = ODEFeatureNamesResponse.from_raw_data(
            {
                "ODEResults": {
                    "Status": "Success",
                    "FeatureNames": {"FeatureName": ["Gale", "Jezero"]},
                }
            }
        )
        assert "Gale" in r.feature_names


class TestODEClient:
    def test_validate_target_valid(self):
        ODEClient()._validate_target("mars")

    def test_validate_target_invalid(self):
        with pytest.raises(ValueError, match="Invalid target"):
            ODEClient()._validate_target("earth")

    @pytest.mark.asyncio
    async def test_missing_required_params(self):
        async with ODEClient() as c:
            with pytest.raises(ValueError, match="Must provide"):
                await c.search_products(target="mars")

    @pytest.mark.asyncio
    async def test_context_manager(self):
        async with ODEClient() as c:
            assert c._client is not None
        assert c._client is None

    @pytest.mark.asyncio
    async def test_no_init_raises(self):
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await ODEClient()._request({"q": "x"})


# ╔══════════════════════════════════════════════════════════════╗
# ║                        IMG  TESTS                            ║
# ╚══════════════════════════════════════════════════════════════╝


class TestIMGFilters:
    def setup_method(self):
        self.c = IMGAtlasClient()

    def test_empty(self):
        assert self.c._build_filter_queries() == []

    def test_target(self):
        assert self.c._build_filter_queries(target="Mars") == ["TARGET:Mars"]

    def test_mission_with_space(self):
        fq = self.c._build_filter_queries(mission="Mars 2020")
        assert fq == ['ATLAS_MISSION_NAME:"Mars 2020"']

    def test_mission_no_space(self):
        fq = self.c._build_filter_queries(mission="MSL")
        assert fq == ["ATLAS_MISSION_NAME:*MSL*"]

    def test_time_range_both(self):
        fq = self.c._build_filter_queries(start_time="2020-01-01", stop_time="2020-12-31")
        assert fq == ["START_TIME:[2020-01-01 TO 2020-12-31]"]

    def test_sol_range_min_zero(self):
        fq = self.c._build_filter_queries(sol_min=0)
        assert fq == ["PLANET_DAY_NUMBER:[0 TO *]"]

    def test_multiple(self):
        fq = self.c._build_filter_queries(target="Mars", mission="MSL", sol_min=0, sol_max=100)
        assert len(fq) == 3


class TestIMGResponses:
    def test_search_success(self):
        r = IMGSearchResponse.from_raw_data(
            {
                "responseHeader": {"status": 0, "QTime": 5},
                "response": {
                    "numFound": 100,
                    "start": 0,
                    "docs": [
                        {"uuid": "abc", "PRODUCT_ID": "IMG_001", "TARGET": "MARS"},
                    ],
                },
            }
        )
        assert r.status == "success"
        assert r.num_found == 100
        assert len(r.products) == 1

    def test_search_error(self):
        r = IMGSearchResponse.from_raw_data({"error": {"msg": "bad"}})
        assert r.status == "error"

    def test_search_solr_error_status(self):
        r = IMGSearchResponse.from_raw_data({"responseHeader": {"status": 400}, "response": {}})
        assert r.status == "error"

    def test_count_success(self):
        r = IMGCountResponse.from_raw_data(
            {
                "responseHeader": {"status": 0},
                "response": {"numFound": 5000},
            }
        )
        assert r.count == 5000

    def test_facet_success(self):
        r = IMGFacetResponse.from_raw_data(
            {
                "responseHeader": {"status": 0},
                "facet_counts": {
                    "facet_fields": {
                        "TARGET": ["MARS", 50000, "SATURN", 30000],
                    }
                },
            },
            "TARGET",
        )
        assert len(r.values) == 2
        assert r.values[0].value == "MARS"
        assert r.values[0].count == 50000

    def test_facet_zero_filtered(self):
        r = IMGFacetResponse.from_raw_data(
            {
                "responseHeader": {"status": 0},
                "facet_counts": {"facet_fields": {"TARGET": ["MARS", 100, "EMPTY", 0]}},
            },
            "TARGET",
        )
        assert len(r.values) == 1

    def test_facet_empty(self):
        r = IMGFacetResponse.from_raw_data(
            {
                "responseHeader": {"status": 0},
                "facet_counts": {"facet_fields": {"TARGET": []}},
            },
            "TARGET",
        )
        assert r.values == []

    @pytest.mark.asyncio
    async def test_invalid_facet_field(self):
        async with IMGAtlasClient() as c:
            with pytest.raises(IMGAtlasClientError, match="Invalid facet"):
                await c.get_facets(facet_field="BOGUS")

    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        async with IMGAtlasClient() as c:
            assert c._client is not None
        assert c._client is None


class TestIMGProduct:
    def test_solr_array_unwrapping(self):
        """Solr returns some fields as single-element arrays."""
        p = IMGProduct.from_raw_data(
            {
                "uuid": "abc",
                "TARGET": ["MARS"],
                "PLANET_DAY_NUMBER": [100],
                "EXPOSURE_DURATION": [0.5],
            }
        )
        assert p.target == "MARS"
        assert p.planet_day_number == 100
        assert p.exposure_duration == 0.5

    def test_null_string_handling(self):
        p = IMGProduct.from_raw_data(
            {
                "uuid": "abc",
                "TARGET": "null",
                "PRODUCT_TYPE": "None",
            }
        )
        assert p.target is None
        assert p.product_type is None


# ╔══════════════════════════════════════════════════════════════╗
# ║                       PDS4  TESTS                            ║
# ╚══════════════════════════════════════════════════════════════╝


class TestPDS4URNValidation:
    def test_valid(self):
        assert (
            validate_urn("urn:nasa:pds:context:investigation:mission.juno")
            == "urn:nasa:pds:context:investigation:mission.juno"
        )

    def test_valid_with_version(self):
        urn = "urn:nasa:pds:context:target:planet.mars::1.0"
        assert validate_urn(urn) == urn

    def test_digits_in_bundle_segment(self):
        """Bundle segment can contain digits (e.g. mars2020_meda)."""
        urn = "urn:nasa:pds:mars2020_meda:data_raw:collection"
        assert validate_urn(urn) == urn

    def test_hyphens_in_bundle_segment(self):
        """Bundle segment can contain hyphens."""
        urn = "urn:nasa:pds:mars-science:data_calibrated:collection_01"
        assert validate_urn(urn) == urn

    def test_invalid_prefix(self):
        with pytest.raises(ValueError):
            validate_urn("not:a:urn")

    def test_empty(self):
        with pytest.raises(ValueError):
            validate_urn("")


class TestPDS4CoordinateValidation:
    def test_valid(self):
        validate_coordinates(bbox_north=45, bbox_south=-45, bbox_east=180, bbox_west=-180)

    def test_planetary_longitude(self):
        validate_coordinates(bbox_east=350, bbox_west=10)

    def test_all_none(self):
        validate_coordinates()

    def test_north_out_of_range(self):
        with pytest.raises(ValueError, match="bbox_north"):
            validate_coordinates(bbox_north=91)

    def test_south_out_of_range(self):
        with pytest.raises(ValueError, match="bbox_south"):
            validate_coordinates(bbox_south=-91)

    def test_north_lt_south(self):
        with pytest.raises(ValueError, match="must be >="):
            validate_coordinates(bbox_north=10, bbox_south=20)

    def test_east_out_of_range(self):
        with pytest.raises(ValueError, match="bbox_east"):
            validate_coordinates(bbox_east=361)

    def test_boundaries_exact(self):
        validate_coordinates(bbox_north=90, bbox_south=-90, bbox_east=360, bbox_west=-180)

    def test_equal_north_south(self):
        validate_coordinates(bbox_north=0, bbox_south=0)


class TestPDS4Client:
    def test_clean_urn_with_version(self):
        c = PDS4Client()
        assert c._clean_urn("urn:nasa:pds:context:mission.juno::1.0") == "urn:nasa:pds:context:mission.juno"

    def test_clean_urn_no_version(self):
        urn = "urn:nasa:pds:context:target"
        assert PDS4Client()._clean_urn(urn) == urn

    def test_build_search_url_filters_none(self):
        url = PDS4Client()._build_search_url("http://api/search", {"q": "mars", "x": None, "y": ""})
        assert "q=mars" in url
        assert "x" not in url
        assert "y" not in url

    def test_build_search_url_empty_params(self):
        assert PDS4Client()._build_search_url("http://api/search", {}) == "http://api/search"

    @pytest.mark.asyncio
    async def test_context_manager(self):
        async with PDS4Client() as c:
            assert c._client is not None
        assert c._client is None

    @pytest.mark.asyncio
    async def test_no_init_raises(self):
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await PDS4Client()._request("GET", "test")

    def test_rate_limit_error(self):
        e = PDS4RateLimitError(retry_after=60)
        assert e.retry_after == 60
        assert "60" in str(e)


# ╔══════════════════════════════════════════════════════════════╗
# ║                        SBN  TESTS                            ║
# ╚══════════════════════════════════════════════════════════════╝


class TestSBNSources:
    def test_list_format(self):
        r = CatchSourcesResponse.from_raw_data(
            [
                {"source": "neat_palomar", "source_name": "NEAT"},
            ]
        )
        assert r.status == "success"
        assert len(r.sources) == 1

    def test_empty_list(self):
        r = CatchSourcesResponse.from_raw_data([])
        assert len(r.sources) == 0

    def test_error_dict(self):
        r = CatchSourcesResponse.from_raw_data({"error": "bad"})
        assert r.status == "error"


class TestSBNJob:
    def test_queued(self):
        r = CatchJobResponse.from_raw_data({"job_id": "abc", "queued": True})
        assert r.job_id == "abc"
        assert r.queued is True

    def test_error(self):
        r = CatchJobResponse.from_raw_data({"error": "not found"})
        assert r.status == "error"
        assert r.error == "not found"


class TestSBNResults:
    def test_with_data(self):
        r = CatchResultsResponse.from_raw_data(
            {
                "count": 1,
                "data": [{"product_id": "obs1", "source": "neat"}],
            }
        )
        assert r.count == 1
        assert len(r.observations) == 1

    def test_empty(self):
        r = CatchResultsResponse.from_raw_data({"count": 0, "data": []})
        assert r.count == 0

    def test_missing_data_key(self):
        r = CatchResultsResponse.from_raw_data({})
        assert r.count == 0


class TestSBNStatus:
    def test_running(self):
        r = CatchStatusResponse.from_raw_data(
            {
                "status": [{"source": "neat_palomar", "status": "running"}],
            }
        )
        assert len(r.source_status) == 1


class TestSBNClient:
    def test_defaults(self):
        c = SBNCatchClient()
        assert "catch-api" in c.base_url

    @pytest.mark.asyncio
    async def test_context_manager(self):
        async with SBNCatchClient() as c:
            assert c._client is not None
        assert c._client is None

    @pytest.mark.asyncio
    async def test_no_init_raises(self):
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await SBNCatchClient()._request("GET", "test")

    def test_job_error(self):
        e = SBNCatchJobError("j1", "timeout")
        assert "j1" in str(e) and "timeout" in str(e)

    def test_rate_limit_error(self):
        e = SBNCatchRateLimitError(retry_after=30)
        assert e.retry_after == 30


# ╔══════════════════════════════════════════════════════════════╗
# ║                    PDS CATALOG TESTS                         ║
# ╚══════════════════════════════════════════════════════════════╝


class TestMatchesTerm:
    def test_match_in_list(self):
        ds = _make_ds(missions=["Cassini-Huygens"])
        assert _matches_term(ds, "Cassini", ds.missions, MISSION_ABBREVIATIONS)

    def test_match_in_title(self):
        ds = _make_ds(title="JUNO JADE Raw Data")
        assert _matches_term(ds, "JUNO", ds.missions, MISSION_ABBREVIATIONS)

    def test_match_in_id(self):
        ds = _make_ds(id="JNO-J-JAD-2-EDR")
        assert _matches_term(ds, "jno", ds.missions, MISSION_ABBREVIATIONS)

    def test_no_match(self):
        ds = _make_ds(id="MRO-X", title="Mars", missions=["MRO"])
        assert not _matches_term(ds, "Cassini", ds.missions, MISSION_ABBREVIATIONS)


class TestFilterDataset:
    def test_essential(self):
        r = filter_dataset(_make_ds(), ESSENTIAL_FIELDS)
        assert "id" in r and "title" in r
        assert "description" not in r

    def test_full(self):
        r = filter_dataset(_make_ds(description="hello", start_date=date(2004, 1, 1)), FULL_FIELDS)
        assert "description" in r and "start_date" in r

    def test_empty_optional_excluded(self):
        r = filter_dataset(_make_ds(missions=[], targets=[], description=None), FULL_FIELDS)
        assert "missions" not in r
        assert "description" not in r


class TestNormalizeId:
    def test_clean(self):
        assert CatalogIndex._normalize_id("CLEAN-ID") == "CLEAN-ID"

    def test_braces_quotes(self):
        assert CatalogIndex._normalize_id('{"MESSY-ID",') == "MESSY-ID"

    def test_parens(self):
        assert CatalogIndex._normalize_id("(ID)") == "ID"

    def test_whitespace(self):
        assert CatalogIndex._normalize_id("  ID  ") == "ID"


class TestCatalogIndex:
    def setup_method(self):
        self.ds1 = _make_ds(
            id="CASS-1",
            title="Cassini ISS",
            node="rings",
            missions=["Cassini"],
            targets=["Saturn"],
            instruments=["ISS"],
            pds_version="PDS3",
            start_date=date(2004, 1, 1),
            stop_date=date(2017, 9, 15),
        )
        self.ds2 = _make_ds(
            id="JUNO-1",
            title="Juno JADE",
            node="ppi",
            missions=["Juno"],
            targets=["Jupiter"],
            instruments=["JADE"],
            pds_version="PDS4",
            dataset_type="bundle",
            start_date=date(2016, 7, 1),
            stop_date=date(2025, 1, 1),
        )
        self.idx = CatalogIndex([self.ds1, self.ds2])

    def test_search_all(self):
        _, total = self.idx.search()
        assert total == 2

    def test_search_by_node(self):
        res, total = self.idx.search(node="rings")
        assert total == 1

    def test_search_by_mission(self):
        res, total = self.idx.search(mission="Cassini")
        assert total == 1

    def test_search_by_pds_version(self):
        res, total = self.idx.search(pds_version="PDS4")
        assert total == 1

    def test_search_pagination(self):
        res, total = self.idx.search(limit=1)
        assert len(res) == 1 and total == 2

    def test_search_offset_beyond(self):
        res, _ = self.idx.search(offset=10)
        assert len(res) == 0

    def test_get_dataset_by_id(self):
        assert self.idx.get_dataset_by_id("CASS-1") is not None
        assert self.idx.get_dataset_by_id("NOPE") is None

    def test_get_dataset_normalized(self):
        ds = _make_ds(id='{"MALFORMED-ID",')
        idx = CatalogIndex([ds])
        assert idx.get_dataset_by_id("MALFORMED-ID") is not None

    def test_stats(self):
        stats = self.idx.get_stats()
        assert stats["total_datasets"] == 2
        assert "rings" in stats["by_node"]

    def test_list_missions(self):
        ms = self.idx.list_missions()
        assert len(ms) == 2

    def test_list_missions_node_filter(self):
        ms = self.idx.list_missions(node="rings")
        assert len(ms) == 1

    def test_list_targets(self):
        ts = self.idx.list_targets()
        assert len(ts) == 2

    def test_find_similar(self):
        similar = self.idx.find_similar_dataset_ids("CASS")
        assert len(similar) >= 1
        assert similar[0][1] >= 50  # score


class TestPDSCatalogClient:
    @pytest.mark.asyncio
    async def test_search_empty_dir(self):
        c = PDSCatalogClient(catalog_dir="/nonexistent")
        res, total = await c.search()
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_dataset_not_found(self):
        c = PDSCatalogClient(catalog_dir="/nonexistent")
        assert await c.get_dataset("NOPE") is None
