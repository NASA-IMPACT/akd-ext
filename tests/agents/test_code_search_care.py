"""Functional tests for Code Search Agent."""

import pytest

from akd_ext.agents.code_search_care import (
    CodeSearchAgent,
    CodeSearchAgentConfig,
    CodeSearchAgentInputSchema,
    CodeSearchAgentOutputSchema,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "Find Python libraries for processing satellite imagery",
        "Find NPM modules for accessing astronomical archival data",
        "Find repositories for climate model data analysis",
    ],
)
async def test_code_search_agent(query: str, reasoning_effort: str):
    """Test Code Search Agent functionality.

    Args:
        query: Code search query to test
        reasoning_effort: CLI param --reasoning-effort (low/medium/high)
    """
    config = CodeSearchAgentConfig(reasoning_effort=reasoning_effort)
    agent = CodeSearchAgent(config=config, debug=True)
    result = await agent.arun(CodeSearchAgentInputSchema(query=query))

    assert isinstance(result, CodeSearchAgentOutputSchema)
    assert len(result.repositories) > 0
