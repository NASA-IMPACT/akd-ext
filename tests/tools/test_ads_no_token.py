"""Offline tests for the ADS tools' missing-token handling.

Unlike test_ads.py, these run WITHOUT ``ADS_API_TOKEN``: they force an empty
token via config and assert the tools report it cleanly instead of raising.
This is the behavior that keeps the MCP server — which instantiates every tool
at import time — from crashing when the token is unset. No network is used;
both tools short-circuit before making a request.
"""

import pytest

from akd_ext.tools import (
    ADSLinksResolverInputSchema,
    ADSLinksResolverTool,
    ADSSearchTool,
    ADSSearchToolInputSchema,
    ADSToolConfig,
)


def test_ads_config_accepts_empty_token():
    """Config construction must NOT raise on an empty token.

    A raising validator here would take down the whole MCP server at import,
    since every tool is instantiated eagerly.
    """
    config = ADSToolConfig(api_token="")
    assert config.api_token == ""


@pytest.mark.asyncio
async def test_ads_search_without_token_reports_error():
    """Search with no token returns an error (no network call), not an exception."""
    tool = ADSSearchTool(config=ADSToolConfig(api_token=""))
    result = await tool.arun(ADSSearchToolInputSchema(query="dark matter"))

    assert result.papers == []
    assert result.num_found == 0
    assert result.error is not None
    assert "ADS_API_TOKEN" in result.error


@pytest.mark.asyncio
async def test_ads_resolver_without_token_reports_error():
    """Resolver with no token returns an error (no network call), not an exception."""
    tool = ADSLinksResolverTool(config=ADSToolConfig(api_token=""))
    result = await tool.arun(ADSLinksResolverInputSchema(bibcode="2010ascl.soft10082F"))

    assert result.associated_bibcodes == []
    assert result.error is not None
    assert "ADS_API_TOKEN" in result.error
    assert result.bibcode == "2010ascl.soft10082F"
