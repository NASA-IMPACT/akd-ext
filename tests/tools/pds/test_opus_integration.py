"""Integration tests for OPUS tools using the real OPUS API."""

import pytest

from akd_ext.tools.pds.opus.opus_search import (
    OPUSObservationSummary,
    OPUSSearchInputSchema,
    OPUSSearchOutputSchema,
    OPUSSearchTool,
)
from akd_ext.tools.pds.opus.opus_count import (
    OPUSCountInputSchema,
    OPUSCountOutputSchema,
    OPUSCountTool,
)
from akd_ext.tools.pds.opus.opus_get_metadata import (
    OPUSGetMetadataInputSchema,
    OPUSGetMetadataOutputSchema,
    OPUSGetMetadataTool,
)
from akd_ext.tools.pds.opus.opus_get_files import (
    OPUSGetFilesInputSchema,
    OPUSGetFilesOutputSchema,
    OPUSGetFilesTool,
)


# ---------------------------------------------------------------------------
# OPUSSearchTool -- integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestOPUSSearchIntegration:
    """Integration tests for OPUSSearchTool against the real OPUS API."""

    async def test_search_saturn_cassini(self):
        """Search for Saturn observations from Cassini returns results."""
        tool = OPUSSearchTool()
        result = await tool.arun(
            OPUSSearchInputSchema(planet="Saturn", mission="Cassini", limit=5)
        )

        assert isinstance(result, OPUSSearchOutputSchema)
        assert result.status == "success"
        assert result.count > 0
        assert len(result.observations) <= 5
        for obs in result.observations:
            assert isinstance(obs, OPUSObservationSummary)
            assert obs.opusid

    async def test_search_by_target(self):
        """Search by target returns observations for that target."""
        tool = OPUSSearchTool()
        result = await tool.arun(
            OPUSSearchInputSchema(target="Titan", limit=5)
        )

        assert result.status == "success"
        assert result.count > 0
        for obs in result.observations:
            assert obs.target == "Titan"

    async def test_search_by_instrument(self):
        """Search by instrument returns observations from that instrument."""
        tool = OPUSSearchTool()
        result = await tool.arun(
            OPUSSearchInputSchema(instrument="Cassini ISS", limit=5)
        )

        assert result.status == "success"
        assert result.count > 0
        for obs in result.observations:
            assert obs.instrument == "Cassini ISS"

    async def test_search_with_time_range(self):
        """Search with a time range returns results within that window."""
        tool = OPUSSearchTool()
        result = await tool.arun(
            OPUSSearchInputSchema(
                time_min="2010-01-01",
                time_max="2010-12-31",
                limit=5,
            )
        )

        assert result.status == "success"
        assert result.count > 0
        assert len(result.observations) <= 5

    async def test_search_pagination(self):
        """Paginated searches return different sets of observations."""
        tool = OPUSSearchTool()

        page1 = await tool.arun(
            OPUSSearchInputSchema(planet="Saturn", limit=5, startobs=1)
        )
        page2 = await tool.arun(
            OPUSSearchInputSchema(planet="Saturn", limit=5, startobs=6)
        )

        assert page1.status == "success"
        assert page2.status == "success"

        page1_ids = {obs.opusid for obs in page1.observations}
        page2_ids = {obs.opusid for obs in page2.observations}
        assert page1_ids.isdisjoint(page2_ids), "Paginated pages should not overlap"


# ---------------------------------------------------------------------------
# OPUSCountTool -- integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestOPUSCountIntegration:
    """Integration tests for OPUSCountTool against the real OPUS API."""

    async def test_count_all_saturn(self):
        """Counting Saturn observations returns a large number."""
        tool = OPUSCountTool()
        result = await tool.arun(OPUSCountInputSchema(planet="Saturn"))

        assert isinstance(result, OPUSCountOutputSchema)
        assert result.status == "success"
        assert result.count > 1000

    async def test_count_cassini_iss(self):
        """Counting Cassini ISS observations returns a positive number."""
        tool = OPUSCountTool()
        result = await tool.arun(
            OPUSCountInputSchema(instrument="Cassini ISS")
        )

        assert result.status == "success"
        assert result.count > 0

    async def test_count_with_mission(self):
        """Counting observations for a mission returns a positive number."""
        tool = OPUSCountTool()
        result = await tool.arun(OPUSCountInputSchema(mission="Cassini"))

        assert result.status == "success"
        assert result.count > 0


# ---------------------------------------------------------------------------
# OPUSGetMetadataTool -- integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestOPUSGetMetadataIntegration:
    """Integration tests for OPUSGetMetadataTool against the real OPUS API."""

    async def test_get_metadata_known_observation(self):
        """Getting metadata for a known observation returns detailed data."""
        tool = OPUSGetMetadataTool()
        result = await tool.arun(
            OPUSGetMetadataInputSchema(opusid="co-iss-n1460960653")
        )

        assert isinstance(result, OPUSGetMetadataOutputSchema)
        assert result.status == "success"
        assert result.opusid == "co-iss-n1460960653"
        assert result.general is not None
        assert len(result.general) > 0

    async def test_get_metadata_nonexistent(self):
        """Getting metadata for a nonexistent observation returns not_found or error."""
        tool = OPUSGetMetadataTool()
        result = await tool.arun(
            OPUSGetMetadataInputSchema(opusid="nonexistent-obs-id-xyz")
        )

        assert isinstance(result, OPUSGetMetadataOutputSchema)
        assert result.status in ("not_found", "error")


# ---------------------------------------------------------------------------
# OPUSGetFilesTool -- integration
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestOPUSGetFilesIntegration:
    """Integration tests for OPUSGetFilesTool against the real OPUS API."""

    async def test_get_files_known_observation(self):
        """Getting files for a known observation returns file URLs."""
        tool = OPUSGetFilesTool()
        result = await tool.arun(
            OPUSGetFilesInputSchema(opusid="co-iss-n1460960653")
        )

        assert isinstance(result, OPUSGetFilesOutputSchema)
        assert result.status == "success"
        assert result.opusid == "co-iss-n1460960653"

        # At least one category of files should be present
        has_files = (
            (result.raw_files is not None and len(result.raw_files) > 0)
            or (result.calibrated_files is not None and len(result.calibrated_files) > 0)
            or (result.all_file_categories is not None and len(result.all_file_categories) > 0)
            or result.browse_images is not None
        )
        assert has_files, "Expected at least one category of files for a known observation"

    async def test_get_files_nonexistent(self):
        """Getting files for a nonexistent observation returns not_found or error."""
        tool = OPUSGetFilesTool()
        result = await tool.arun(
            OPUSGetFilesInputSchema(opusid="nonexistent-obs-id-xyz")
        )

        assert isinstance(result, OPUSGetFilesOutputSchema)
        assert result.status in ("not_found", "error")
