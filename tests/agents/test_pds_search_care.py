"""Functional tests for Planetary Data Search Agent."""

import pytest

from akd._base import TextOutput
from akd_ext.agents.pds_search_care import (
    PlanetaryDataSearchAgent,
    PlanetaryDataSearchAgentInputSchema,
    PlanetaryDataSearchAgentOutputSchema,
    PlanetaryDataSearchAgentConfig,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "Find datasets about Mars surface mineralogy",
        "Find Saturn ring observations from Cassini",
        "Find lunar topography datasets from LRO",
    ],
)
async def test_pds_search_agent(query: str, reasoning_effort: str):
    """Test Planetary Data Search Agent functionality.

    Args:
        query: Planetary science query to test
        reasoning_effort: CLI param --reasoning-effort (low/medium/high)
    """
    config = PlanetaryDataSearchAgentConfig(reasoning_effort=reasoning_effort)
    agent = PlanetaryDataSearchAgent(config=config, debug=True)
    result = await agent.arun(PlanetaryDataSearchAgentInputSchema(query=query))

    assert isinstance(result, (PlanetaryDataSearchAgentOutputSchema, TextOutput))
    if isinstance(result, PlanetaryDataSearchAgentOutputSchema):
        assert result.result.strip()
