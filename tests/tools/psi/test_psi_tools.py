"""Offline unit tests for the PSI tools (httpx.MockTransport, no network)."""

import hashlib
import json

import httpx
import pytest
from pydantic import ValidationError

from akd_ext.tools import (
    PsiApiInput,
    PsiApiOutput,
    PsiApiTool,
    PsiMetadataExpansionConfig,
    PsiMetadataExpansionInput,
    PsiMetadataExpansionTool,
)
from akd_ext.tools.psi._normalize import (
    logical_path,
    normalize_investigation_id,
    normalize_selector,
    relevance_score,
)
from akd_ext.tools.psi.api import PsiApiConfig

DISCOVERY_PAYLOAD = [
    {
        "accession": 117,
        "public": True,
        "metadata": {
            "investigation_title": "Cool Flame Dynamics CFD Analysis",
            "investigation_objective": "Quantify droplet cool flames in microgravity.",
            "public_release_date": "10-Jun-2026",
        },
    },
    {
        "accession": 42,
        "public": True,
        "metadata": {
            "investigation_title": "Plant Growth Experiment",
            "investigation_objective": "Grow lettuce on orbit.",
            "public_release_date": "01-Jan-2020",
        },
    },
]

INVESTIGATION_PAYLOAD = {
    "accession": 117,
    "title": "Cool Flame Dynamics CFD Analysis",
    "objective": "Quantify droplet cool flames.",
    "researchArea": "Combustion Science",
    "doi": "10.60555/gz0q-b577",
    "publications": [
        {"title": "Cool flame paper", "doi": "10.1016/x", "authorList": "Farouk T."},
    ],
}

CSV_BYTES = b"Pressure,Kavg\n0.5,0.315\n"

FILES_PAYLOAD = {
    "hits": 1,
    "total_hits": 3,
    "studies": {
        "117": {
            "file_count": 3,
            "study_files": [
                {
                    "file_name": "kavg.csv",
                    "file_size": len(CSV_BYTES),
                    "category": "Analyzed Data",
                    "subcategory": "Reduced Gravity",
                    "subdirectory": "Simulation/MST",
                    "remote_url": "/api/download/kavg.csv",
                },
                {
                    "file_name": "dext.csv",
                    "file_size": 100,
                    "category": "Analyzed Data",
                    "subcategory": "Reduced Gravity",
                    "subdirectory": "Simulation/MST",
                    "remote_url": "/api/download/dext.csv",
                },
                {
                    "file_name": "talk.pdf",
                    "file_size": 999,
                    "category": "Presentations",
                    "subcategory": "",
                    "subdirectory": "",
                    "remote_url": "/api/download/talk.pdf",
                },
            ],
        }
    },
}

DATACITE_PAYLOAD = {
    "data": {
        "id": "10.60555/gz0q-b577",
        "attributes": {
            "doi": "10.60555/gz0q-b577",
            "titles": [{"title": "Cool Flame Dynamics Dataset"}],
            "creators": [{"name": "Farouk, Tanvir"}],
            "publisher": "NASA PSI",
            "publicationYear": 2025,
            "types": {"resourceTypeGeneral": "Dataset"},
            "url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-117",
            "state": "findable",
        },
    }
}


def psi_transport(download_failures: list[int] | None = None) -> httpx.MockTransport:
    """Route mock requests by URL path; optionally fail downloads with given statuses first."""

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/geode-py/ws/api/investigations/metadata":
            return httpx.Response(200, json=DISCOVERY_PAYLOAD)
        if path == "/geode-py/ws/repo/investigations/PSI-117":
            return httpx.Response(200, json=INVESTIGATION_PAYLOAD)
        if path.startswith("/geode-py/ws/api/investigations/files/search/"):
            return httpx.Response(200, json=FILES_PAYLOAD)
        if path == "/api/download/kavg.csv":
            if download_failures:
                return httpx.Response(download_failures.pop(0))
            return httpx.Response(200, content=CSV_BYTES, headers={"content-type": "text/csv"})
        if path == "/dois/10.60555/gz0q-b577":
            return httpx.Response(200, json=DATACITE_PAYLOAD)
        if path.startswith("/dois/"):
            return httpx.Response(404, json={"errors": [{"status": "404"}]})
        return httpx.Response(500)

    return httpx.MockTransport(handler)


def api_tool(download_failures: list[int] | None = None, **config_kwargs) -> PsiApiTool:
    return PsiApiTool(config=PsiApiConfig(**config_kwargs), transport=psi_transport(download_failures))


# ---- normalization helpers ----


@pytest.mark.unit
def test_normalize_investigation_id():
    assert normalize_investigation_id("117") == "PSI-117"
    assert normalize_investigation_id("psi-007") == "PSI-7"
    with pytest.raises(ValueError):
        normalize_investigation_id("not-an-id")


@pytest.mark.unit
def test_normalize_selector():
    assert normalize_selector("PSI-117") == "117"
    assert normalize_selector("4, 10") == "4,10"
    assert normalize_selector("20-25") == "20-25"
    with pytest.raises(ValueError):
        normalize_selector("25-20")


@pytest.mark.unit
def test_logical_path_splits_nested_subdirectories():
    record = {
        "investigation_id": "PSI-117",
        "category": "Analyzed Data",
        "subcategory": "Reduced Gravity",
        "subdirectory": "Simulation/MST",
        "file_name": "kavg.csv",
    }
    assert logical_path(record) == "PSI-117/Analyzed Data/Reduced Gravity/Simulation/MST/kavg.csv"


@pytest.mark.unit
def test_relevance_score_empty_fields_dilute():
    full, _ = relevance_score("cool flame", [("Title", 1.0, "cool flame study")])
    diluted, _ = relevance_score("cool flame", [("Title", 0.5, "cool flame study"), ("Objective", 0.5, "")])
    assert full == 1.0
    assert diluted == 0.5


# ---- psi_api_tool: one tool, dispatched by operation ----


@pytest.mark.unit
def test_it_is_a_single_tool_with_operation_input():
    tool = PsiApiTool()
    assert tool.name == "psi_api_tool"
    assert "operation" in PsiApiInput.model_fields


@pytest.mark.unit
async def test_discover_ranks_by_query():
    result = await api_tool().arun(
        PsiApiInput(operation="discover_investigations", query="droplet cool flame", max_items=5)
    )
    investigations = result.data["investigations"]
    assert result.data["total_available"] == 2
    assert investigations[0]["investigation_id"] == "PSI-117"
    assert investigations[0]["match_score"] > investigations[1]["match_score"]
    assert result.raw_response is None  # summary mode by default


@pytest.mark.unit
async def test_discover_without_query_keeps_api_order():
    result = await api_tool().arun(PsiApiInput(operation="discover_investigations", max_items=1))
    assert result.data["investigations"][0]["investigation_id"] == "PSI-117"
    assert "match_score" not in result.data["investigations"][0]


@pytest.mark.unit
async def test_response_mode_both_attaches_raw():
    result = await api_tool().arun(PsiApiInput(operation="discover_investigations", response_mode="both"))
    assert result.raw_response is not None
    assert result.raw_response["included"] is True
    assert isinstance(result.raw_response["data"], list)


@pytest.mark.unit
async def test_get_investigation_normalizes():
    result = await api_tool().arun(PsiApiInput(operation="get_investigation", investigation_id="psi-117"))
    investigation = result.data["investigation"]
    assert investigation["investigation_id"] == "PSI-117"
    assert investigation["doi"] == "10.60555/gz0q-b577"
    assert investigation["publication_count"] == 1


@pytest.mark.unit
def test_get_investigation_requires_id():
    with pytest.raises(ValidationError, match="get_investigation requires investigation_id"):
        PsiApiInput(operation="get_investigation")


@pytest.mark.unit
def test_retrieve_file_requires_locator():
    with pytest.raises(ValidationError, match="requires remote_url or file_name"):
        PsiApiInput(operation="retrieve_file", investigation_id="PSI-117")


@pytest.mark.unit
async def test_search_files_filters_and_truncates(tmp_path):
    result = await api_tool(artifact_root=str(tmp_path)).arun(
        PsiApiInput(
            operation="search_files",
            investigation_selector="PSI-117",
            file_name_pattern="*.csv",
            max_items=1,
        )
    )
    limits = result.data["result_limits"]
    assert limits["files_received_from_api"] == 3
    assert limits["files_matching_filters"] == 2
    assert limits["files_returned_to_agent"] == 1
    assert limits["truncated"] is True
    assert len(result.data["investigations"][0]["files"]) == 1
    # overflow artifact holds the full filtered set
    artifact = limits["complete_inventory_artifact"]
    inventory = json.loads((tmp_path / f"{artifact['artifact_id']}.json").read_text(encoding="utf-8"))
    assert len(inventory["investigations"][0]["files"]) == 2


@pytest.mark.unit
async def test_navigate_dataset_builds_tree():
    result = await api_tool().arun(PsiApiInput(operation="navigate_dataset", investigation_id="117"))
    assert result.data["totals"] == {"files_scanned": 3, "files_matching_filters": 3}
    names = [node["name"] for node in result.data["tree"]]
    assert names == ["Analyzed Data", "Presentations"]
    directory = result.data["tree"][0]["children"][0]["children"][0]
    assert directory["file_types"] == {".csv": 2}
    assert "kavg.csv" in directory["representative_files"]


@pytest.mark.unit
async def test_retrieve_file_downloads_and_hashes(tmp_path):
    result = await api_tool(download_root=str(tmp_path)).arun(
        PsiApiInput(operation="retrieve_file", investigation_id="PSI-117", file_name="kavg.csv")
    )
    assert result.data["size_bytes"] == len(CSV_BYTES)
    assert result.data["sha256"] == hashlib.sha256(CSV_BYTES).hexdigest()
    assert result.data["logical_path"] == "PSI-117/Analyzed Data/Reduced Gravity/Simulation/MST/kavg.csv"
    stored = tmp_path / "PSI-117" / "Analyzed Data" / "Reduced Gravity" / "Simulation" / "MST" / "kavg.csv"
    assert stored.read_bytes() == CSV_BYTES


@pytest.mark.unit
async def test_retrieve_file_refreshes_expired_url(tmp_path):
    result = await api_tool(download_failures=[403], download_root=str(tmp_path)).arun(
        PsiApiInput(operation="retrieve_file", investigation_id="PSI-117", file_name="kavg.csv")
    )
    assert result.data["sha256"] == hashlib.sha256(CSV_BYTES).hexdigest()
    assert any(warning["code"] == "DOWNLOAD_URL_REFRESHED" for warning in result.warnings)


@pytest.mark.unit
async def test_retrieve_file_rejects_non_psi_host(tmp_path):
    with pytest.raises(ValueError, match="non-PSI URL"):
        await api_tool(download_root=str(tmp_path)).arun(
            PsiApiInput(
                operation="retrieve_file",
                investigation_id="PSI-117",
                remote_url="https://evil.example.com/x.csv",
            )
        )


@pytest.mark.unit
async def test_lookup_publication_normalizes():
    result = await api_tool().arun(PsiApiInput(operation="lookup_publication", doi="10.60555/gz0q-b577"))
    publication = result.data["publication"]
    assert publication["title"] == "Cool Flame Dynamics Dataset"
    assert publication["resource_type"] == "Dataset"
    assert publication["creators"] == ["Farouk, Tanvir"]


@pytest.mark.unit
async def test_lookup_publication_crossref_doi_is_not_found():
    with pytest.raises(RuntimeError, match="404"):
        await api_tool().arun(PsiApiInput(operation="lookup_publication", doi="10.1016/j.proci.2022.07.094"))


# ---- metadata_expansion_tool: the second tool ----


def metadata_tool(transport=None, **config_kwargs) -> PsiMetadataExpansionTool:
    return PsiMetadataExpansionTool(
        config=PsiMetadataExpansionConfig(**config_kwargs), transport=transport or psi_transport()
    )


@pytest.mark.unit
async def test_metadata_expansion_cache_lifecycle(tmp_path):
    tool = metadata_tool(context_root=str(tmp_path))

    first = await tool.arun(PsiMetadataExpansionInput(investigation_id="PSI-117"))
    item = first.enriched_investigations[0]
    assert item["context_cache"]["status"] == "generated"
    assert item["relevance"]["score"] == 1.0
    assert item["suggested_next_call"]["tool"] == "psi_api_tool"
    assert item["suggested_next_call"]["arguments"]["operation"] == "navigate_dataset"
    cache_file = tmp_path / "PSI-117" / "investigation_metadata.md"
    assert "psi-context-cache" in cache_file.read_text(encoding="utf-8").splitlines()[0]

    second = await tool.arun(PsiMetadataExpansionInput(investigation_id="PSI-117"))
    assert second.enriched_investigations[0]["context_cache"]["status"] == "hit"

    third = await tool.arun(PsiMetadataExpansionInput(investigation_id="PSI-117", refresh_cache=True))
    assert third.enriched_investigations[0]["context_cache"]["status"] == "refreshed"


@pytest.mark.unit
async def test_metadata_expansion_stale_fallback(tmp_path):
    seed = metadata_tool(context_root=str(tmp_path), cache_ttl_seconds=-1)
    await seed.arun(PsiMetadataExpansionInput(investigation_id="PSI-117"))

    broken = PsiMetadataExpansionTool(
        config=PsiMetadataExpansionConfig(context_root=str(tmp_path), cache_ttl_seconds=-1),
        transport=httpx.MockTransport(lambda request: httpx.Response(503)),
    )
    result = await broken.arun(PsiMetadataExpansionInput(investigation_id="PSI-117"))
    item = result.enriched_investigations[0]
    assert item["context_cache"]["status"] == "stale_fallback"
    assert item["normalized_metadata"]["doi"] == "10.60555/gz0q-b577"
    assert any(warning["code"] == "STALE_CONTEXT_USED" for warning in result.warnings)


@pytest.mark.unit
async def test_metadata_expansion_ranks_candidates(tmp_path):
    tool = metadata_tool(context_root=str(tmp_path))
    result = await tool.arun(
        PsiMetadataExpansionInput(
            query="droplet cool flame combustion",
            discovery_results=[
                {"investigation_id": "PSI-117", "title": "Cool Flame Dynamics CFD Analysis"},
            ],
        )
    )
    item = result.enriched_investigations[0]
    assert item["relevance"]["score"] > 0
    assert "PSI-117" in result.summary


@pytest.mark.unit
def test_metadata_expansion_requires_query_for_multiple_candidates():
    with pytest.raises(ValidationError, match="query is required"):
        PsiMetadataExpansionInput(discovery_results=[{"investigation_id": "PSI-117"}, {"investigation_id": "PSI-42"}])


@pytest.mark.unit
def test_only_two_psi_tools_are_registered():
    from akd_ext.mcp.registry import MCPToolRegistry

    import akd_ext.tools  # noqa: F401  (fire @mcp_tool registration)

    registry = MCPToolRegistry()
    tools = getattr(registry, "_tools", None) or getattr(registry, "tools", None) or []
    psi = sorted(t().name for t in tools if t.__module__.startswith("akd_ext.tools.psi"))
    assert psi == ["metadata_expansion_tool", "psi_api_tool"]


@pytest.mark.unit
def test_output_schema_serializes_to_json():
    payload = PsiApiOutput(operation="discover_investigations", data={"x": 1}, summary="ok")
    assert json.loads(payload.model_dump_json())["operation"] == "discover_investigations"
