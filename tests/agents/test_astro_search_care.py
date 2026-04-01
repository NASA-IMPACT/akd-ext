"""Functional tests for Astro Data Search Agent."""

import pytest

from akd._base import TextOutput
from akd_ext.agents.astro_search_care import (
    AstroDataSearchAgent,
    AstroDataSearchAgentInputSchema,
    AstroDataSearchAgentOutputSchema,
    AstroDataSearchAgentConfig,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "Find X-ray observations of Crab Nebula",
        "Find spectroscopic data for exoplanet WASP-39b",
        "Find radio observations of Sagittarius A*",
    ],
)
async def test_astro_search_agent(query: str, reasoning_effort: str):
    """Test Astro Data Search Agent functionality.

    Args:
        query: Astronomical query to test
        reasoning_effort: CLI param --reasoning-effort (low/medium/high)
    """
    config = AstroDataSearchAgentConfig(reasoning_effort=reasoning_effort)
    agent = AstroDataSearchAgent(config=config, debug=True)
    result = await agent.arun(AstroDataSearchAgentInputSchema(query=query))

    assert isinstance(result, (AstroDataSearchAgentOutputSchema, TextOutput))
    if isinstance(result, AstroDataSearchAgentOutputSchema):
        assert result.result.strip()
