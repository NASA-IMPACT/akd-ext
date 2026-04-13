"""Integration tests for ASCL Search and Get tools.

Test fixtures use real astrophysics codes:
- RADMC-3D (1202.015): 3D dust continuum radiative transfer
- HEALPix (1107.018): Pixelization of the sphere for CMB analysis
- MESA (1010.083): Modules for Experiments in Stellar Astrophysics
- SKIRT (1109.003): Monte Carlo radiative transfer in dusty systems
"""

import pytest

from akd_ext.tools import (
    ASCLSearchTool,
    ASCLSearchToolConfig,
    ASCLSearchToolInputSchema,
    ASCLSearchToolOutputSchema,
    ASCLGetTool,
    ASCLGetInputSchema,
    ASCLGetOutputSchema,
    ASCLEntry,
)


# ---------------------------------------------------------------------------
# ASCLSearchTool tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ascl_search_by_code_name():
    """Test searching ASCL for RADMC-3D by name returns the expected entry."""
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="RADMC-3D", rows=5))

    assert isinstance(result, ASCLSearchToolOutputSchema)
    assert result.num_found > 0

    ascl_ids = [e.ascl_id for e in result.entries]
    assert "1202.015" in ascl_ids

    radmc = next(e for e in result.entries if e.ascl_id == "1202.015")
    assert "RADMC-3D" in radmc.title
    assert radmc.ads_bibcode
    assert radmc.ascl_url == "https://ascl.net/1202.015"
    assert radmc.ads_abs_url


@pytest.mark.asyncio
async def test_ascl_search_by_capability():
    """Test searching ASCL for radiative transfer codes by capability."""
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="radiative transfer", rows=10))

    assert isinstance(result, ASCLSearchToolOutputSchema)
    assert result.num_found > 0

    # RADMC-3D and SKIRT are both radiative transfer codes and should appear
    ascl_ids = [e.ascl_id for e in result.entries]
    assert "1202.015" in ascl_ids or "1109.003" in ascl_ids

    entries_with_urls = [e for e in result.entries if e.primary_url]
    assert len(entries_with_urls) > 0


@pytest.mark.asyncio
async def test_ascl_search_returns_parsed_urls():
    """Test that PHP-serialized site_list is parsed into clean URL lists.

    RADMC-3D has two URLs: a university homepage and a GitHub repo. Both should
    be clean HTTP URLs with no PHP serialization artifacts.
    """
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="RADMC-3D", rows=3))

    assert result.num_found > 0
    for entry in result.entries:
        for url in entry.all_urls:
            assert url.startswith("http"), f"URL should be clean HTTP URL, got: {url}"
            assert "a:" not in url, f"URL contains PHP serialization artifacts: {url}"


@pytest.mark.asyncio
async def test_ascl_search_returns_described_in():
    """Test that described_in is parsed from PHP to clean ADS URLs.

    HEALPix (1107.018) has a known described_in paper (Gorski+ 2005).
    """
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="HEALPix", rows=5))

    healpix = next((e for e in result.entries if e.ascl_id == "1107.018"), None)
    assert healpix is not None

    assert len(healpix.described_in) > 0
    for url in healpix.described_in:
        assert "adsabs.harvard.edu" in url, f"described_in URL should be ADS: {url}"


@pytest.mark.asyncio
async def test_ascl_search_used_in_count():
    """Test that used_in_count matches the length of used_in list.

    RADMC-3D (1202.015) has at least one used_in paper.
    """
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="RADMC-3D", rows=3))

    radmc = next((e for e in result.entries if e.ascl_id == "1202.015"), None)
    assert radmc is not None
    assert radmc.used_in_count == len(radmc.used_in)


@pytest.mark.asyncio
async def test_ascl_search_primary_url_prefers_github():
    """Test that primary_url prefers GitHub over university homepages.

    RADMC-3D has both a Heidelberg homepage and a GitHub repo. GitHub should win.
    MESA has both a GitHub repo and a docs site. GitHub should win.
    """
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="RADMC-3D", rows=3))

    radmc = next((e for e in result.entries if e.ascl_id == "1202.015"), None)
    assert radmc is not None
    assert len(radmc.all_urls) >= 2  # has both homepage and GitHub
    assert radmc.primary_url is not None
    assert "github.com" in radmc.primary_url


@pytest.mark.asyncio
async def test_ascl_search_empty_result():
    """Test that a nonsense query returns zero results gracefully."""
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="xyznonexistent123456", rows=5))

    assert isinstance(result, ASCLSearchToolOutputSchema)
    assert result.num_found == 0
    assert result.entries == []


@pytest.mark.asyncio
async def test_ascl_search_require_github():
    """Test filtering to GitHub-hosted codes only.

    MESA (GitHub-hosted) should pass. HEALPix (SourceForge) should be filtered out.
    """
    tool = ASCLSearchTool()
    result = await tool.arun(
        ASCLSearchToolInputSchema(query="stellar astrophysics", rows=10, require_code_host="github")
    )

    assert isinstance(result, ASCLSearchToolOutputSchema)
    for entry in result.entries:
        assert entry.primary_url is not None
        assert "github.com" in entry.primary_url


@pytest.mark.asyncio
async def test_ascl_search_views_is_int():
    """Test that views is parsed as int, not string (ASCL API returns it as a string)."""
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="HEALPix", rows=3))

    assert result.num_found > 0
    for entry in result.entries:
        assert isinstance(entry.views, int)


@pytest.mark.asyncio
async def test_ascl_search_authors_parsed():
    """Test that semicolon-separated credit string is parsed into author list.

    RADMC-3D has 6+ authors in its credit field.
    """
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="RADMC-3D", rows=3))

    radmc = next((e for e in result.entries if e.ascl_id == "1202.015"), None)
    assert radmc is not None
    assert len(radmc.authors) > 1
    assert "Dullemond, C. P." in radmc.authors


@pytest.mark.asyncio
async def test_ascl_search_abstract_truncation():
    """Test abstract truncation config.

    MESA (1010.083) has a 1540-char abstract. With truncate_abstract=100,
    the returned abstract should be at most 103 chars (100 + '...').
    """
    config = ASCLSearchToolConfig(truncate_abstract=100)
    tool = ASCLSearchTool(config=config)
    result = await tool.arun(ASCLSearchToolInputSchema(query="MESA", rows=3))

    assert result.num_found > 0
    for entry in result.entries:
        if entry.abstract:
            assert len(entry.abstract) <= 103  # 100 + "..."


@pytest.mark.asyncio
async def test_ascl_search_field_preset_minimal():
    """Test that minimal preset returns the minimal field set."""
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="HEALPix", rows=3, field_preset="minimal"))

    assert isinstance(result, ASCLSearchToolOutputSchema)
    assert "ascl_id" in result.fields_returned
    assert "title" in result.fields_returned


# ---------------------------------------------------------------------------
# ASCLGetTool tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ascl_get_radmc3d():
    """Test fetching RADMC-3D by its ASCL id."""
    tool = ASCLGetTool()
    result = await tool.arun(ASCLGetInputSchema(ascl_id="1202.015"))

    assert isinstance(result, ASCLGetOutputSchema)
    assert result.found is True
    assert result.entry is not None
    assert result.entry.ascl_id == "1202.015"
    assert "RADMC-3D" in result.entry.title
    assert result.entry.ads_bibcode
    assert result.entry.ascl_url == "https://ascl.net/1202.015"


@pytest.mark.asyncio
async def test_ascl_get_with_prefix():
    """Test that 'ascl:' prefix is stripped correctly."""
    tool = ASCLGetTool()
    result = await tool.arun(ASCLGetInputSchema(ascl_id="ascl:1107.018"))

    assert result.found is True
    assert result.entry is not None
    assert result.entry.ascl_id == "1107.018"
    assert "HEALPix" in result.entry.title


@pytest.mark.asyncio
async def test_ascl_get_full_abstract():
    """Test that single lookups return full abstract (truncate_abstract=0 by default).

    MESA has a 1540-char abstract — it should come back untruncated.
    """
    tool = ASCLGetTool()
    result = await tool.arun(ASCLGetInputSchema(ascl_id="1010.083"))

    assert result.found is True
    assert result.entry is not None
    assert "MESA" in result.entry.title
    assert len(result.entry.abstract) > 300


@pytest.mark.asyncio
async def test_ascl_get_all_authors():
    """Test that single lookups return all authors (max_authors=0 by default).

    MESA has 6 authors — all should be returned without truncation.
    """
    tool = ASCLGetTool()
    result = await tool.arun(ASCLGetInputSchema(ascl_id="1010.083"))

    assert result.found is True
    assert result.entry is not None
    assert len(result.entry.authors) >= 6
    # No "... and N more" truncation marker
    assert not any("... and" in a for a in result.entry.authors)


@pytest.mark.asyncio
async def test_ascl_get_missing_id():
    """Test that a nonexistent ASCL id returns found=False."""
    tool = ASCLGetTool()
    result = await tool.arun(ASCLGetInputSchema(ascl_id="9999.999"))

    assert isinstance(result, ASCLGetOutputSchema)
    assert result.found is False
    assert result.entry is None


@pytest.mark.asyncio
async def test_ascl_get_returns_parsed_urls():
    """Test that site_list is parsed into clean URLs for RADMC-3D."""
    tool = ASCLGetTool()
    result = await tool.arun(ASCLGetInputSchema(ascl_id="1202.015"))

    assert result.found is True
    assert result.entry is not None
    assert len(result.entry.all_urls) >= 2  # homepage + GitHub
    for url in result.entry.all_urls:
        assert url.startswith("http")
        assert "a:" not in url
