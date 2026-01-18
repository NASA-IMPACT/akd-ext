"""Functional tests for CMR CARE Agent.

Co-Authored-By: Sanjog Thapa <sanzog03@gmail.com>
"""

import pytest

from akd_ext.agents import CMRCareAgent, CMRCareConfig, CMRCareInput, CMRCareOutput


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "Find datasets related to sea surface temperature in the Pacific Ocean",
        "Find atmospheric CO2 concentration datasets from satellite observations",
        "Find MODIS vegetation index datasets for monitoring forest health",
    ],
)
async def test_cmr_care_agent(query: str):
    """Test CMR CARE Agent search functionality."""
    agent = CMRCareAgent(config=CMRCareConfig(), debug=True)
    result = await agent.arun(CMRCareInput(query=query))

    assert isinstance(result, CMRCareOutput)
    assert len(result.dataset_concept_ids) > 0
