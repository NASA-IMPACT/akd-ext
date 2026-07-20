"""Integration tests for the PSI tools against the live PSI and DataCite APIs.

Run with: uv run pytest -m integration tests/tools/psi/
PSI-117 is a stable public investigation used as a known-good fixture.
"""

import pytest

from akd_ext.tools import (
    PsiApiInput,
    PsiApiTool,
    PsiMetadataExpansionConfig,
    PsiMetadataExpansionInput,
    PsiMetadataExpansionTool,
)
from akd_ext.tools.psi.api import PsiApiConfig


@pytest.mark.integration
async def test_discover_live():
    result = await PsiApiTool().arun(
        PsiApiInput(operation="discover_investigations", query="droplet cool flame combustion", max_items=5)
    )
    assert result.data["total_available"] > 100
    assert len(result.data["investigations"]) == 5
    assert result.data["investigations"][0]["match_score"] > 0


@pytest.mark.integration
async def test_get_investigation_live():
    result = await PsiApiTool().arun(PsiApiInput(operation="get_investigation", investigation_id="PSI-117"))
    assert result.data["investigation"]["doi"] == "10.60555/gz0q-b577"
    assert result.data["investigation"]["research_area"] == "Combustion Science"


@pytest.mark.integration
async def test_get_investigation_live_nonexistent_id_maps_psi_403():
    with pytest.raises(RuntimeError, match="403"):
        await PsiApiTool().arun(PsiApiInput(operation="get_investigation", investigation_id="PSI-999999"))


@pytest.mark.integration
async def test_navigate_dataset_live():
    result = await PsiApiTool().arun(PsiApiInput(operation="navigate_dataset", investigation_id="PSI-117"))
    assert result.data["totals"]["files_scanned"] >= 16
    assert any(node["name"] == "Analyzed Data" for node in result.data["tree"])


@pytest.mark.integration
async def test_retrieve_file_live(tmp_path):
    tool = PsiApiTool(config=PsiApiConfig(download_root=str(tmp_path)))
    result = await tool.arun(
        PsiApiInput(
            operation="retrieve_file",
            investigation_id="PSI-117",
            file_name="PSI-117_Analyzed Data_MST_2024_Kavg.csv",
        )
    )
    assert result.data["size_bytes"] > 0
    assert len(result.data["sha256"]) == 64


@pytest.mark.integration
async def test_lookup_publication_live():
    result = await PsiApiTool().arun(PsiApiInput(operation="lookup_publication", doi="10.60555/gz0q-b577"))
    assert result.data["publication"]["publisher"] == "NASA PSI"
    assert result.data["publication"]["state"] == "findable"


@pytest.mark.integration
async def test_metadata_expansion_live(tmp_path):
    tool = PsiMetadataExpansionTool(config=PsiMetadataExpansionConfig(context_root=str(tmp_path)))
    result = await tool.arun(PsiMetadataExpansionInput(investigation_id="PSI-117"))
    item = result.enriched_investigations[0]
    assert item["normalized_metadata"]["doi"] == "10.60555/gz0q-b577"
    assert item["context_cache"]["status"] in {"generated", "refreshed"}
