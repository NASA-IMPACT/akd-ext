"""Functional tests for Planetary Data Search Agent."""

import pytest

from akd._base import TextOutput
from akd_ext.agents.pds_search_care import (
    PDSSearchAgent,
    PDSSearchAgentInputSchema,
    PDSSearchAgentOutputSchema,
    PDSSearchConfig,
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
    config = PDSSearchConfig(reasoning_effort=reasoning_effort)
    agent = PDSSearchAgent(config=config, debug=True)
    result = await agent.arun(PDSSearchAgentInputSchema(query=query))

    assert isinstance(result, (PDSSearchAgentOutputSchema, TextOutput))
    if isinstance(result, PDSSearchAgentOutputSchema):
        assert result.result.strip()
