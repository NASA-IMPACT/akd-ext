"""Functional tests for Repository Search Tool."""

import httpx
import pytest

from akd.structures import SearchResultItem
from akd.tools.misc import HttpUrlAdapter
from akd_ext.tools.code_search.repository_search import (
    RepositorySearchTool,
    RepositorySearchToolConfig,
    RepositorySearchToolInputSchema,
    RepositorySearchToolOutputSchema,
)


class TestRepositorySearchBackend:
    """Guards the SDE backend contract: current code endpoint + min_score on every request."""

    @pytest.mark.unit
    def test_default_base_url_is_the_current_host(self):
        # SDE_BASE_URL is a bare host (consistent with sde_search / code_signals),
        # not the full endpoint; the code-search path is appended per request.
        config = RepositorySearchToolConfig()
        assert config.base_url == "https://dyejsbdumgpqz.cloudfront.net"
        assert config.min_score == 0.0

    @pytest.mark.unit
    async def test_sde_search_appends_path_and_sends_min_score(self, monkeypatch):
        """The bare host gets /api/code/search appended (rstrip guards a trailing slash), and
        min_score is on every payload — the endpoint's 0.55 default drops everything without it."""
        captured: dict = {}

        class _Response:
            def raise_for_status(self) -> None: ...

            @staticmethod
            def json() -> dict:
                return {"documents": []}

        async def _post(self, url, headers=None, json=None):
            captured["url"] = url
            captured["payload"] = json
            return _Response()

        monkeypatch.setattr(httpx.AsyncClient, "post", _post)

        tool = RepositorySearchTool(config=RepositorySearchToolConfig(base_url="https://example.org/"))
        async with httpx.AsyncClient() as client:
            await tool._sde_search(client, page=1, query="anything")

        assert captured["url"] == "https://example.org/api/code/search"
        assert captured["payload"]["min_score"] == 0.0

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://github.com/NASA-IMPACT/veda-config-ghg", "NASA-IMPACT/veda-config-ghg"),
            ("https://github.com/SnowEx/uavsar_snow/", "SnowEx/uavsar_snow"),
            ("https://www.github.com/owner/repo/tree/main", "owner/repo"),
            ("https://github.com/some-org", None),  # org page, no repo
            ("https://github.com/", None),
            ("https://heliopython.org/projects/", None),  # not github at all
        ],
    )
    def test_github_repo_name_guard(self, url: str, expected):
        """A non-owner/repo URL must return None, not IndexError — otherwise one odd result
        crashes the whole gather in _enrich_code_search_with_metadata."""
        assert RepositorySearchTool._github_repo_name(url) == expected

    @pytest.mark.unit
    async def test_enrich_skips_non_github_url(self):
        """A non-GitHub result is returned with empty metadata rather than raising."""
        tool = RepositorySearchTool()
        item = SearchResultItem(
            query="q",
            title="projects",
            content="",
            url=HttpUrlAdapter.validate_python("https://heliopython.org/projects/"),
        )
        enriched = await tool._enrich_code_search_with_metadata(item)
        assert enriched.reliability_score is None
        assert enriched.repository_metadata.is_null_metadata


class TestRepositorySearchTool:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "query",
        [
            "nasa python",
            "pds software",
        ],
    )
    async def test_repository_search_tool(self, query: str):
        """Test Repository Search Tool functionality.

        Args:
            query: Code search query to test
        """
        config = RepositorySearchToolConfig(page_size=2)
        tool = RepositorySearchTool(config=config)
        result = await tool.arun(RepositorySearchToolInputSchema(queries=[query]))

        assert isinstance(result, RepositorySearchToolOutputSchema)
        assert len(result.results) > 0

        # Verify each result has repository metadata and reliability score
        for item in result.results:
            assert hasattr(item, "repository_metadata")
            assert hasattr(item, "reliability_score")
            assert item.repository_metadata.stars >= 0
            assert item.repository_metadata.forks >= 0

    @pytest.mark.parametrize(
        "page_size,result_size",
        [
            (3, 3),
            (8, 8),
            (10, 10),
            (11, 10),  # Capped at max 10
            (55, 10),  # Capped at max 10
            (100, 10),  # Capped at max 10
        ],
    )
    @pytest.mark.asyncio
    async def test_repository_search_tool_results_number(self, page_size: int, result_size: int):
        """Test Repository Search Tool results number."""
        config = RepositorySearchToolConfig(page_size=page_size)
        tool = RepositorySearchTool(config=config)
        # "nasa python" has >100 results in the SDE code index so any page_size up to the 10 cap works
        result = await tool.arun(RepositorySearchToolInputSchema(queries=["nasa python"]))
        assert len(result.results) == result_size
