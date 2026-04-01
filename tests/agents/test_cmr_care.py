"""Functional tests for CMR Data Search Agent."""

import pytest

from akd._base import TextOutput
from akd_ext.agents import (
    CMRDataSearchAgent,
    CMRDataSearchAgentInputSchema,
    CMRDataSearchAgentOutputSchema,
    CMRDataSearchAgentConfig,
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
    """Test CMR Data Search Agent search functionality.

    Args:
        query: Earth science query to test
        reasoning_effort: CLI param --reasoning-effort (low/medium/high)
    """
    config = CMRDataSearchAgentConfig(reasoning_effort=reasoning_effort)
    agent = CMRDataSearchAgent(config=config, debug=True)
    result = await agent.arun(CMRDataSearchAgentInputSchema(query=query))

    assert isinstance(result, (CMRDataSearchAgentOutputSchema, TextOutput))
    if isinstance(result, CMRDataSearchAgentOutputSchema):
        assert len(result.dataset_concept_ids) > 0


# To test the markdown heading format, uncomment the following test function and run the test
# @pytest.mark.asyncio
# async def test_cmr_care_agent_markdown_heading_format(reasoning_effort: str):
#     """Test that CMR Data Search Agent produces valid markdown headings with spaces after # characters."""
#     config = CMRDataSearchAgentConfig(reasoning_effort=reasoning_effort)
#     agent = CMRDataSearchAgent(config=config)
#     result = await agent.arun(
#         CMRDataSearchAgentInputSchema(query="Find datasets related to sea surface temperature in the Pacific Ocean")
#     )
#     assert isinstance(result, (CMRDataSearchAgentOutputSchema, TextOutput))
#     if isinstance(result, CMRDataSearchAgentOutputSchema):
#         broken_headings = re.findall(r"^#{1,6}[^ #\n]", result.report, re.MULTILINE)
#         assert broken_headings == [], f"Malformed headings (missing space after #): {broken_headings}"
