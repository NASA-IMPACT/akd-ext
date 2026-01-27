"""Unit tests for code_search utils module."""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta

from akd_ext.tools.code_search.utils import (
    fetch_github_metadata,
    RepositoryMetadata,
    calculate_reliability_score,
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

    @pytest.mark.asyncio
    async def test_fetch_github_metadata_failure(self):
        """Test failure fetching of GitHub metadata from a non-existent repository."""
        result = await fetch_github_metadata("non-existent-repo")
        assert result.is_null_metadata is True

    @pytest.mark.asyncio
    async def test_fetch_github_metadata_failure_with_rate_limit(self):
        """Test failure fetching of GitHub metadata from a valid repository with rate limit."""
        uncached_fetch = fetch_github_metadata.__wrapped__
        tasks = [uncached_fetch("NASA-IMPACT/veda-config-ghg", None) for _ in range(65)]
        await asyncio.gather(*tasks)
        rate_limited_result = await uncached_fetch("NASA-IMPACT/veda-config-ghg", None)
        assert rate_limited_result.is_null_metadata is True


class TestCalculateReliabilityScore:
    """Tests for calculate_reliability_score function."""

    @pytest.fixture
    def old_inactive_repository_metadata(self):
        now = datetime.now(timezone.utc)
        return RepositoryMetadata(
            stars=100,
            forks=45,
            created_at=(now - timedelta(days=730)).isoformat(),
            last_updated=(now - timedelta(days=729)).isoformat(),
        )

    @pytest.fixture
    def new_active_repository_metadata(self, old_inactive_repository_metadata):
        now = datetime.now(timezone.utc)
        return old_inactive_repository_metadata.model_copy(
            update={
                "created_at": (now - timedelta(days=25)).isoformat(),
                "last_updated": now.isoformat(),
            }
        )

    def test_null_metadata_returns_none(self):
        """Test that null metadata returns None."""
        assert calculate_reliability_score(None) is None

    def test_default_metadata_returns_none(self):
        """Test that default metadata returns None."""
        assert calculate_reliability_score(RepositoryMetadata()) is None

    def test_old_inactive_vs_new_active_repository(
        self, old_inactive_repository_metadata, new_active_repository_metadata
    ):
        """Test that old inactive repository returns low score than new one"""
        assert calculate_reliability_score(old_inactive_repository_metadata) < calculate_reliability_score(
            new_active_repository_metadata
        )
