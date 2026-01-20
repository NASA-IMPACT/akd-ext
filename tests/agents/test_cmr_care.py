"""Functional tests for CMR CARE Agent.

Co-Authored-By: Sanjog Thapa <sanzog03@gmail.com>
"""

import pytest

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

    assert isinstance(result, CMRCareAgentOutputSchema)
    assert len(result.dataset_concept_ids) > 0
