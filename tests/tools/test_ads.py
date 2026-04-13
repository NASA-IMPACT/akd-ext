"""Integration tests for ADS Search and Links Resolver tools.

All tests hit the real ADS API and require ``ADS_API_TOKEN`` in the environment.
Tests are skipped at module level when the token is missing so the rest of the
suite can still run locally.

Reference bibcodes used as fixtures:
- 2013PASP..125..306F — Foreman-Mackey emcee paper
- 2019ApJ...879..125L — illustrative paper with linked data archives
"""

import os

import pytest

from akd_ext.tools import (
    ADSLinksResolverInputSchema,
    ADSLinksResolverOutputSchema,
    ADSLinksResolverTool,
    ADSSearchTool,
    ADSSearchToolConfig,
    ADSSearchToolInputSchema,
    ADSSearchToolOutputSchema,
)

pytestmark = pytest.mark.skipif(
    not os.environ.get("ADS_API_TOKEN"),
    reason="ADS_API_TOKEN not set",
)


# ---------------------------------------------------------------------------
# ADSSearchTool tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ads_search_by_title():
    """Search for the emcee paper by distinctive title phrase."""
    tool = ADSSearchTool()
    try:
        result = await tool.arun(ADSSearchToolInputSchema(query='title:"emcee: The MCMC Hammer"', rows=5))
    finally:
        await tool.aclose()

    assert isinstance(result, ADSSearchToolOutputSchema)
    assert result.num_found > 0
    assert result.num_returned == len(result.papers)
    assert result.num_returned <= 5

    bibcodes = [p.bibcode for p in result.papers]
    assert "2013PASP..125..306F" in bibcodes


@pytest.mark.asyncio
async def test_ads_search_honors_rows():
    """`rows` is authoritative — no silent truncation below the requested value."""
    tool = ADSSearchTool()
    try:
        result = await tool.arun(ADSSearchToolInputSchema(query="dark energy", rows=15))
    finally:
        await tool.aclose()

    assert result.num_returned == len(result.papers)
    # When enough matches exist (they do for "dark energy"), we should get exactly rows.
    if result.num_found >= 15:
        assert result.num_returned == 15


@pytest.mark.asyncio
async def test_ads_search_field_preset_minimal():
    """Minimal preset returns the minimal field set."""
    tool = ADSSearchTool()
    try:
        result = await tool.arun(ADSSearchToolInputSchema(query="emcee", rows=3, field_preset="minimal"))
    finally:
        await tool.aclose()

    assert "bibcode" in result.fields_returned
    assert "title" in result.fields_returned
    # Abstract is not in minimal preset
    assert "abstract" not in result.fields_returned


@pytest.mark.asyncio
async def test_ads_search_rate_limit_surfaced():
    """Rate-limit headers from ADS are surfaced in the response."""
    tool = ADSSearchTool()
    try:
        result = await tool.arun(ADSSearchToolInputSchema(query="emcee", rows=1))
    finally:
        await tool.aclose()

    # ADS consistently returns X-RateLimit-Remaining; if it's missing, the API changed.
    assert "remaining" in result.rate_limit
    assert isinstance(result.rate_limit["remaining"], int)


@pytest.mark.asyncio
async def test_ads_search_github_enrichment_opt_in_default():
    """By default, no secondary GitHub query is issued and urls are empty."""
    tool = ADSSearchTool()
    try:
        result = await tool.arun(ADSSearchToolInputSchema(query="emcee", rows=3))
    finally:
        await tool.aclose()

    assert result.enrichment_errors == []
    for paper in result.papers:
        assert paper.github_urls == []


@pytest.mark.asyncio
async def test_ads_search_github_enrichment_when_enabled():
    """With fetch_github_urls=True, emcee's paper should surface its GitHub URL."""
    tool = ADSSearchTool()
    try:
        result = await tool.arun(
            ADSSearchToolInputSchema(
                query='bibcode:"2013PASP..125..306F"',
                rows=1,
                fetch_github_urls=True,
            )
        )
    finally:
        await tool.aclose()

    assert result.num_returned == 1
    paper = result.papers[0]
    assert paper.bibcode == "2013PASP..125..306F"
    # The emcee paper links to github.com/dfm/emcee in its full text.
    assert any("github.com" in u for u in paper.github_urls)


@pytest.mark.asyncio
async def test_ads_search_abstract_truncation_per_call():
    """Per-call truncate_abstract overrides the config default."""
    tool = ADSSearchTool(config=ADSSearchToolConfig(truncate_abstract=0))
    try:
        result = await tool.arun(ADSSearchToolInputSchema(query='title:"emcee"', rows=3, truncate_abstract=50))
    finally:
        await tool.aclose()

    for paper in result.papers:
        if paper.abstract:
            assert len(paper.abstract) <= 53  # 50 + "..."


@pytest.mark.asyncio
async def test_ads_search_empty_result():
    """A nonsense query returns zero results gracefully."""
    tool = ADSSearchTool()
    try:
        result = await tool.arun(ADSSearchToolInputSchema(query='title:"xyznonexistent123456qweasd"', rows=5))
    finally:
        await tool.aclose()

    assert isinstance(result, ADSSearchToolOutputSchema)
    assert result.papers == []
    assert result.num_returned == 0


@pytest.mark.asyncio
async def test_ads_search_num_found_independent_of_rows():
    """num_found is the Solr total, unaffected by the rows cap."""
    tool = ADSSearchTool()
    try:
        result = await tool.arun(ADSSearchToolInputSchema(query="dark matter", rows=1))
    finally:
        await tool.aclose()

    assert result.num_returned == 1
    # "dark matter" easily has thousands of matches in ADS.
    assert result.num_found > 1


# ---------------------------------------------------------------------------
# ADSLinksResolverTool tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ads_resolver_for_emcee_paper():
    """Resolver returns at least one link for the emcee paper."""
    tool = ADSLinksResolverTool()
    try:
        result = await tool.arun(ADSLinksResolverInputSchema(bibcode="2013PASP..125..306F"))
    finally:
        await tool.aclose()

    assert isinstance(result, ADSLinksResolverOutputSchema)
    assert result.bibcode == "2013PASP..125..306F"
    assert len(result.links) > 0
    for link in result.links:
        assert link.url.startswith("http")


@pytest.mark.asyncio
async def test_ads_resolver_rate_limit_surfaced():
    """Rate-limit headers are also surfaced on resolver responses."""
    tool = ADSLinksResolverTool()
    try:
        result = await tool.arun(ADSLinksResolverInputSchema(bibcode="2013PASP..125..306F"))
    finally:
        await tool.aclose()

    # Resolver sometimes omits rate-limit headers; accept either presence or empty dict,
    # but when present the value must be an int.
    if "remaining" in result.rate_limit:
        assert isinstance(result.rate_limit["remaining"], int)


# ---------------------------------------------------------------------------
# Config-level tests (no network)
# ---------------------------------------------------------------------------


def test_ads_config_rejects_empty_token():
    """The shared ADSToolConfig validator refuses empty api_token."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ADSSearchToolConfig(api_token="")
