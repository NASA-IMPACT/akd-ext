"""Integration tests for the ASCL search tool.

These tests hit the live ASCL API (no auth required) and use real codes as
fixtures:
- RADMC-3D (1202.015): 3D dust continuum radiative transfer
- HEALPix (1107.018): Pixelization of the sphere for CMB analysis
"""

import pytest

from akd_ext.tools import (
    ASCLSearchTool,
    ASCLSearchToolInputSchema,
    ASCLSearchToolOutputSchema,
)


# ---------------------------------------------------------------------------
# Free-text / capability searches
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ascl_search_by_code_name():
    """Searching for 'RADMC-3D' returns the expected entry (1202.015)."""
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="RADMC-3D", rows=5))

    assert isinstance(result, ASCLSearchToolOutputSchema)
    assert result.error is None
    assert result.num_found > 0

    ids = [e.ascl_id for e in result.entries]
    assert "1202.015" in ids

    radmc = next(e for e in result.entries if e.ascl_id == "1202.015")
    assert "RADMC-3D" in radmc.title
    assert radmc.bibcode  # every entry has an ASCL record bibcode


@pytest.mark.asyncio
async def test_ascl_search_by_capability():
    """Searching by capability ('radiative transfer') returns related codes."""
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="radiative transfer", rows=10))

    assert result.error is None
    assert result.num_found > 0
    # At least some entries should have URLs in site_list.
    assert any(e.site_list for e in result.entries)


@pytest.mark.asyncio
async def test_ascl_search_empty_result():
    """A nonsense query returns zero entries and no error."""
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="xyznonexistent123456", rows=5))

    assert result.error is None
    assert result.num_found == 0
    assert result.entries == []


# ---------------------------------------------------------------------------
# PHP-serialized field parsing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ascl_site_list_is_parsed_to_urls():
    """site_list should come back as clean HTTP URLs, not PHP-serialized text."""
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="RADMC-3D", rows=3))

    for entry in result.entries:
        for url in entry.site_list:
            assert url.startswith("http"), f"Expected a URL, got: {url}"
            assert "a:" not in url, f"URL still contains PHP serialization: {url}"


@pytest.mark.asyncio
async def test_ascl_described_in_returns_ads_urls():
    """HEALPix has at least one describing paper; all should be ADS URLs."""
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="HEALPix", rows=5))

    healpix = next((e for e in result.entries if e.ascl_id == "1107.018"), None)
    assert healpix is not None
    assert len(healpix.described_in) > 0
    for url in healpix.described_in:
        assert "adsabs.harvard.edu" in url


@pytest.mark.asyncio
async def test_ascl_used_in_count_matches_list_length():
    """used_in_count should equal len(used_in)."""
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="RADMC-3D", rows=3))

    for entry in result.entries:
        assert entry.used_in_count == len(entry.used_in)


@pytest.mark.asyncio
async def test_ascl_views_is_int():
    """`views` comes from the API as a string; the tool converts it to int."""
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="HEALPix", rows=3))

    assert result.num_found > 0
    for entry in result.entries:
        assert isinstance(entry.views, int)


# ---------------------------------------------------------------------------
# ID-style queries
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ascl_search_by_id():
    """Passing an ASCL id as the query should return that exact entry."""
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="1202.015", rows=1))

    assert result.error is None
    assert len(result.entries) == 1
    assert result.entries[0].ascl_id == "1202.015"
    assert "RADMC-3D" in result.entries[0].title


@pytest.mark.asyncio
async def test_ascl_search_by_id_with_prefix():
    """The 'ascl:' prefix on an id should be stripped and the exact match returned."""
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="ascl:1107.018", rows=1))

    assert result.error is None
    assert len(result.entries) == 1
    assert result.entries[0].ascl_id == "1107.018"
    assert "HEALPix" in result.entries[0].title


@pytest.mark.asyncio
async def test_ascl_search_by_full_url():
    """A full ASCL page URL should be normalized to the id and matched exactly."""
    tool = ASCLSearchTool()
    result = await tool.arun(
        ASCLSearchToolInputSchema(query="https://ascl.net/1202.015", rows=1)
    )

    assert result.error is None
    assert len(result.entries) == 1
    assert result.entries[0].ascl_id == "1202.015"
    assert "RADMC-3D" in result.entries[0].title


@pytest.mark.asyncio
async def test_ascl_search_by_nonexistent_id():
    """A well-formed but unused ASCL id returns no entries and no error."""
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="9999.999", rows=1))

    assert result.error is None
    assert result.entries == []
