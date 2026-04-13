"""Functional tests for Gap Agent."""

import pytest

from akd._base import TextOutput
from akd_ext.agents import (
    GapAgent,
    GapAgentConfig,
    GapAgentInputSchema,
    GapAgentOutputSchema,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "Identify gaps in satellite-based ocean salinity measurement capabilities",
        "What are the gaps in current wildfire detection and monitoring datasets",
    ],
)
async def test_gap_agent(query: str, reasoning_effort: str):
    """Test Gap Agent produces a report for a given query."""
    config = GapAgentConfig(reasoning_effort=reasoning_effort)
    agent = GapAgent(config=config, debug=True)
    result = await agent.arun(GapAgentInputSchema(query=query))

    assert isinstance(result, (GapAgentOutputSchema, TextOutput))
    if isinstance(result, GapAgentOutputSchema):
        assert result.report.strip(), "Report should not be empty"
