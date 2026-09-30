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
async def test_ascl_used_in_count_is_derived_and_serialized():
    """used_in_count is a computed field derived from used_in: it equals
    len(used_in) and is still present in the serialized output."""
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="RADMC-3D", rows=3))

    for entry in result.entries:
        assert entry.used_in_count == len(entry.used_in)
        assert entry.model_dump()["used_in_count"] == len(entry.used_in)


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


# ---------------------------------------------------------------------------
# Multi-word (AND) free-text search
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ascl_search_is_word_order_independent():
    """Multi-word free text is ANDed order-independently: reordering the words
    yields the same match count. This is the behavior the client-side
    intersection adds on top of ASCL's exact-phrase-only matching.
    """
    tool = ASCLSearchTool()
    forward = await tool.arun(ASCLSearchToolInputSchema(query="radiative transfer", rows=10))
    reverse = await tool.arun(ASCLSearchToolInputSchema(query="transfer radiative", rows=10))

    assert forward.error is None and reverse.error is None
    assert forward.num_found > 0
    assert forward.num_found == reverse.num_found


@pytest.mark.asyncio
async def test_ascl_free_text_ignores_leading_ascl_prefix():
    """A capability query accidentally prefixed with 'ascl:' still matches:
    the prefix is stripped rather than becoming a required AND term that would
    zero out the results."""
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="ascl: RADMC", rows=5))

    assert result.error is None
    assert "1202.015" in {e.ascl_id for e in result.entries}


# ---------------------------------------------------------------------------
# Empty / whitespace queries
# ---------------------------------------------------------------------------


def test_ascl_empty_query_rejected_by_schema():
    """An empty query is rejected at validation time (min_length=1)."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ASCLSearchToolInputSchema(query="")


@pytest.mark.asyncio
async def test_ascl_whitespace_query_returns_empty():
    """A whitespace-only query has no search terms, so it returns no matches
    (and makes no API call) rather than raising."""
    tool = ASCLSearchTool()
    result = await tool.arun(ASCLSearchToolInputSchema(query="   "))

    assert result.error is None
    assert result.entries == []
    assert result.num_found == 0


# ---------------------------------------------------------------------------
# Offline unit tests (no network) for id normalization and AND intersection
# ---------------------------------------------------------------------------

from akd_ext.tools.ascl import _intersect_by_id, _normalize_ascl_id, _quote_term  # noqa: E402


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("1303.002", "1303.002"),
        ("ascl:1303.002", "1303.002"),
        ("ASCL:1303.002", "1303.002"),
        ("ascl: 1303.002", "1303.002"),
        ("ascl:ascl:1303.002", "1303.002"),
        ("https://ascl.net/1303.002", "1303.002"),
        ("  ascl:1303.002  ", "1303.002"),
    ],
)
def test_normalize_ascl_id(raw, expected):
    assert _normalize_ascl_id(raw) == expected


def test_quote_term_wraps_and_drops_embedded_quotes():
    assert _quote_term("radiative") == '"radiative"'
    assert _quote_term('rad"iative') == '"radiative"'


def test_intersect_by_id_keeps_only_common_records_in_first_term_order():
    term_a = [{"ascl_id": "1"}, {"ascl_id": "2"}, {"ascl_id": "3"}]
    term_b = [{"ascl_id": "3"}, {"ascl_id": "1"}]
    result = _intersect_by_id([term_a, term_b])

    assert [d["ascl_id"] for d in result] == ["1", "3"]


def test_intersect_by_id_empty_when_a_term_has_no_matches():
    assert _intersect_by_id([[{"ascl_id": "1"}], []]) == []


def test_intersect_by_id_empty_input():
    assert _intersect_by_id([]) == []
