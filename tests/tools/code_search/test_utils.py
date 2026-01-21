"""Unit tests for code_search utils module."""

import pytest

from akd_ext.tools.code_search.utils import (
    fetch_github_metadata,
    RepositoryMetadata,
)


class TestFetchGithubMetadata:
    """Tests for fetch_github_metadata function."""

    @pytest.mark.asyncio
    async def test_fetch_github_metadata_success(self):
        """Test successful fetching of GitHub metadata from a real repository."""
        result = await fetch_github_metadata("NASA-IMPACT/veda-config-ghg")

        # Verify result is a RepositoryMetadata instance
        assert isinstance(result, RepositoryMetadata)

        # Verify all expected fields are present with correct types
        assert isinstance(result.stars, int)
        assert isinstance(result.forks, int)
        assert isinstance(result.watchers, int)
        assert isinstance(result.open_issues, int)
        assert isinstance(result.pulls, int)
        assert isinstance(result.closed_pulls, int)
        assert isinstance(result.last_updated, str)
        assert isinstance(result.created_at, str)
