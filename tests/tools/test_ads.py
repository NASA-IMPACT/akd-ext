"""Integration tests for ADS search and links-resolver tools.

These tests hit the live ADS API and require ``ADS_API_TOKEN`` in the
environment. The whole module is skipped when the token is missing so the
rest of the test suite can still run.

Reference bibcodes used as fixtures:
- 2010ascl.soft10082F — ASCL record for FLASH.
- 2000ApJS..131..273F — Fryxell+ 2000, the canonical FLASH paper (~2100 cites).
- 2005Ap&SS.298..341W — Weirs+ 2005, a FLASH update paper (used to test
                       URL encoding — the '&' must be percent-escaped).
- 2013PASP..125..306F — Foreman-Mackey emcee paper.
"""

import os

import pytest

from akd_ext.tools import (
    ADSLinksResolverInputSchema,
    ADSLinksResolverOutputSchema,
    ADSLinksResolverTool,
    ADSSearchTool,
    ADSSearchToolInputSchema,
    ADSSearchToolOutputSchema,
    ADSToolConfig,
)

pytestmark = pytest.mark.skipif(
    not os.environ.get("ADS_API_TOKEN"),
    reason="ADS_API_TOKEN not set",
)


@pytest.mark.asyncio
async def test_ads_search_by_title():
    """A title search for the "Source Code" paper should return it."""
    tool = ADSSearchTool()
    result = await tool.arun(
        ADSSearchToolInputSchema(query='title:"FLASH"', rows=5, fq='property:refereed')
    )

    assert isinstance(result, ADSSearchToolOutputSchema)
    assert result.error is None
    assert result.num_found > 0
    assert len(result.papers) <= 5

    bibcodes = [p.bibcode for p in result.papers]
    # 2000ApJS..131..273F is the canonical FLASH paper (Fryxell et al. 2000, ~2100 citations).
    assert "2000ApJS..131..273F" in bibcodes


@pytest.mark.asyncio
async def test_ads_search_honors_rows():
    """When enough matches exist, we should get exactly `rows` papers."""
    tool = ADSSearchTool()
    result = await tool.arun(ADSSearchToolInputSchema(query="dark energy", rows=15))

    assert result.error is None
    if result.num_found >= 15:
        assert len(result.papers) == 15


@pytest.mark.asyncio
async def test_ads_search_empty_result():
    """A nonsense query returns zero papers and no error."""
    tool = ADSSearchTool()
    result = await tool.arun(
        ADSSearchToolInputSchema(query='title:"xyznonexistent123456qweasd"', rows=5)
    )

    assert result.error is None
    assert result.papers == []
    assert result.num_found == 0


@pytest.mark.asyncio
async def test_ads_search_num_found_is_global_total():
    """`num_found` is the total match count in ADS, independent of `rows`."""
    tool = ADSSearchTool()
    result = await tool.arun(ADSSearchToolInputSchema(query="dark matter", rows=1))

    assert len(result.papers) == 1
    # "dark matter" easily has thousands of matches.
    assert result.num_found > 1


@pytest.mark.asyncio
async def test_ads_search_fq_filters_to_refereed():
    """The `fq` param filters results — refereed-only should still hit emcee."""
    tool = ADSSearchTool()
    result = await tool.arun(
        ADSSearchToolInputSchema(
            query='title:"emcee: The MCMC Hammer"',
            rows=5,
            fq="property:refereed",
        )
    )

    assert result.error is None
    assert result.num_found > 0
    for paper in result.papers:
        assert "REFEREED" in paper.property


@pytest.mark.asyncio
async def test_ads_search_by_bibcode_exact_lookup():
    """Looking up a paper by its exact bibcode returns that one paper."""
    tool = ADSSearchTool()
    result = await tool.arun(
        ADSSearchToolInputSchema(
            query='bibcode:"2000ApJS..131..273F"',
            rows=1,
        )
    )

    assert result.error is None
    assert result.num_found == 1
    assert len(result.papers) == 1

    paper = result.papers[0]
    assert paper.bibcode == "2000ApJS..131..273F"
    assert "FLASH" in paper.title
    assert paper.first_author.startswith("Fryxell")
    assert paper.year == "2000"
    assert paper.citation_count > 1000  # canonical paper with ~2100 citations



def test_ads_config_rejects_empty_token():
    """The config validator refuses an empty api_token."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ADSToolConfig(api_token="")


# ---------------------------------------------------------------------------
# ADSLinksResolverTool tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ads_resolver_for_flash_ascl_record():
    """FLASH's ASCL record (2010ascl.soft10082F) should resolve to both
    describing papers: the canonical Fryxell+ 2000 paper AND the Weirs+ 2005
    update paper. This is exactly the case ASCL's own `described_in` field
    misses.
    """
    tool = ADSLinksResolverTool()
    result = await tool.arun(
        ADSLinksResolverInputSchema(bibcode="2010ascl.soft10082F")
    )

    assert isinstance(result, ADSLinksResolverOutputSchema)
    assert result.error is None
    assert result.bibcode == "2010ascl.soft10082F"
    # Canonical FLASH paper (Fryxell et al. 2000) — the whole reason we need
    # this tool; ASCL's own described_in does not list it.
    assert "2000ApJS..131..273F" in result.associated_bibcodes
    # The update paper should also appear.
    assert "2005Ap&SS.298..341W" in result.associated_bibcodes


@pytest.mark.asyncio
async def test_ads_resolver_handles_url_encoded_bibcode():
    """Bibcodes with special chars (e.g. '&' in 2005Ap&SS.298..341W) must be
    URL-encoded in the path. Passing such a bibcode directly should work.
    """
    tool = ADSLinksResolverTool()
    result = await tool.arun(
        ADSLinksResolverInputSchema(bibcode="2005Ap&SS.298..341W")
    )

    assert result.error is None
    assert result.bibcode == "2005Ap&SS.298..341W"


@pytest.mark.asyncio
async def test_ads_resolver_unknown_bibcode_is_empty_not_error():
    """A non-existent bibcode should return an empty list, not raise."""
    tool = ADSLinksResolverTool()
    result = await tool.arun(
        ADSLinksResolverInputSchema(bibcode="9999invalid..000..000X")
    )

    # ADS may return an empty records list OR a 404 depending on internal
    # behavior; either way the tool should surface it cleanly.
    assert result.bibcode == "9999invalid..000..000X"
    if result.error is None:
        assert result.associated_bibcodes == []
