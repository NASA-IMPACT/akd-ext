"""Functional tests for CMR CARE Agent."""

import pytest

from akd._base import TextOutput
from akd_ext.agents import (
    CMRCareAgent,
    CMRCareAgentInputSchema,
    CMRCareAgentOutputSchema,
    CMRCareConfig,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "Find datasets related to sea surface temperature in the Pacific Ocean",
        "Find atmospheric CO2 concentration datasets from satellite observations",
        "Find MODIS vegetation index datasets for monitoring forest health",
    ],
)
async def test_cmr_care_agent(query: str, reasoning_effort: str):
    """Test CMR CARE Agent search functionality.

    Args:
        query: Earth science query to test
        reasoning_effort: CLI param --reasoning-effort (low/medium/high)
    """
    config = CMRCareConfig(reasoning_effort=reasoning_effort)
    agent = CMRCareAgent(config=config, debug=True)
    result = await agent.arun(CMRCareAgentInputSchema(query=query))

    assert isinstance(result, (CMRCareAgentOutputSchema, TextOutput))
    if isinstance(result, CMRCareAgentOutputSchema):
        assert len(result.dataset_concept_ids) > 0


# To test the markdown heading format, uncomment the following test function and run the test
# @pytest.mark.asyncio
# async def test_cmr_care_agent_markdown_heading_format(reasoning_effort: str):
#     """Test that CMR CARE Agent produces valid markdown headings with spaces after # characters."""
#     config = CMRCareConfig(reasoning_effort=reasoning_effort)
#     agent = CMRCareAgent(config=config)
#     result = await agent.arun(
#         CMRCareAgentInputSchema(query="Find datasets related to sea surface temperature in the Pacific Ocean")
#     )
#     assert isinstance(result, (CMRCareAgentOutputSchema, TextOutput))
#     if isinstance(result, CMRCareAgentOutputSchema):
#         broken_headings = re.findall(r"^#{1,6}[^ #\n]", result.report, re.MULTILINE)
#         assert broken_headings == [], f"Malformed headings (missing space after #): {broken_headings}"
