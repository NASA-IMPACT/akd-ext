"""Integration tests for SBN CATCH tools using the real CATCH API."""

import pytest

from akd_ext.tools.pds.sbn.list_sources import (
    SBNListSourcesInputSchema,
    SBNListSourcesOutputSchema,
    SBNListSourcesTool,
    SBNSourceSummary,
)
from akd_ext.tools.pds.sbn.search_object import (
    SBNSearchObjectInputSchema,
    SBNSearchObjectOutputSchema,
    SBNSearchObjectTool,
)
from akd_ext.tools.pds.sbn.search_coordinates import (
    SBNSearchCoordinatesInputSchema,
    SBNSearchCoordinatesOutputSchema,
    SBNSearchCoordinatesTool,
)


# ---------------------------------------------------------------------------
# SBNListSourcesTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestSBNListSourcesIntegration:
    """Integration tests for SBNListSourcesTool against the real CATCH API."""

    async def test_list_all_sources(self):
        """List sources returns a non-trivial number of sources with expected fields."""
        tool = SBNListSourcesTool()
        result = await tool.arun(SBNListSourcesInputSchema())

        assert isinstance(result, SBNListSourcesOutputSchema)
        assert result.total_sources > 5
        assert len(result.sources) == result.total_sources
        for source in result.sources:
            assert isinstance(source, SBNSourceSummary)
            assert source.source
            assert source.count >= 0

    async def test_known_sources_present(self):
        """Well-known sources like neat_palomar_tricam or ps1dr2 are in the list."""
        tool = SBNListSourcesTool()
        result = await tool.arun(SBNListSourcesInputSchema())

        source_names = [s.source for s in result.sources]
        known_sources = {"neat_palomar_tricam", "ps1dr2"}
        found = known_sources & set(source_names)
        assert len(found) > 0, (
            f"Expected at least one of {known_sources} in source list, got: {source_names}"
        )


# ---------------------------------------------------------------------------
# SBNSearchObjectTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestSBNSearchObjectIntegration:
    """Integration tests for SBNSearchObjectTool against the real CATCH API."""

    async def test_search_known_asteroid(self):
        """Search for Didymos (65803) returns observations."""
        tool = SBNSearchObjectTool()
        result = await tool.arun(
            SBNSearchObjectInputSchema(
                target="65803",
                cached=True,
                limit=5,
                timeout=120,
            )
        )

        assert isinstance(result, SBNSearchObjectOutputSchema)
        assert result.target == "65803"
        assert result.count > 0
        assert result.total_available >= result.count
        assert len(result.observations) == result.count
        assert len(result.observations) <= 5

    async def test_search_known_comet(self):
        """Search for Halley's Comet (1P) returns observations."""
        tool = SBNSearchObjectTool()
        result = await tool.arun(
            SBNSearchObjectInputSchema(
                target="1P",
                cached=True,
                limit=5,
                timeout=120,
            )
        )

        assert isinstance(result, SBNSearchObjectOutputSchema)
        assert result.target == "1P"
        assert result.count >= 0
        assert result.total_available >= result.count

    async def test_search_with_essential_fields(self):
        """Search with essential field profile returns product_id, source, date."""
        tool = SBNSearchObjectTool()
        result = await tool.arun(
            SBNSearchObjectInputSchema(
                target="65803",
                cached=True,
                limit=5,
                timeout=120,
                fields="essential",
            )
        )

        assert result.fields == "essential"
        for obs in result.observations:
            assert "product_id" in obs
            assert "source" in obs
            assert "date" in obs
            # Summary-only fields should not be present in essential profile
            for extra_field in ("vmag", "filter", "exposure"):
                assert extra_field not in obs

    async def test_search_no_results(self):
        """Search for a target unlikely to have observations returns count=0."""
        tool = SBNSearchObjectTool()
        result = await tool.arun(
            SBNSearchObjectInputSchema(
                target="9999999",
                cached=True,
                limit=5,
                timeout=120,
            )
        )

        assert isinstance(result, SBNSearchObjectOutputSchema)
        assert result.count == 0
        assert result.observations == []


# ---------------------------------------------------------------------------
# SBNSearchCoordinatesTool – integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestSBNSearchCoordinatesIntegration:
    """Integration tests for SBNSearchCoordinatesTool against the real CATCH API."""

    async def test_search_known_coordinates(self):
        """Search at a well-covered sky position returns observations."""
        tool = SBNSearchCoordinatesTool()
        result = await tool.arun(
            SBNSearchCoordinatesInputSchema(
                ra="12:00:00",
                dec="+10:00:00",
                radius=30,
            )
        )

        assert isinstance(result, SBNSearchCoordinatesOutputSchema)
        assert result.ra == "12:00:00"
        assert result.dec == "+10:00:00"
        assert result.radius == 30
        assert result.count > 0
        assert result.total_available >= result.count
        assert len(result.observations) == result.count

    async def test_search_with_summary_fields(self):
        """Search with summary field profile includes ra and dec fields."""
        tool = SBNSearchCoordinatesTool()
        result = await tool.arun(
            SBNSearchCoordinatesInputSchema(
                ra="12:00:00",
                dec="+10:00:00",
                radius=30,
                fields="summary",
            )
        )

        assert result.fields == "summary"
        for obs in result.observations:
            assert "ra" in obs
            assert "dec" in obs
