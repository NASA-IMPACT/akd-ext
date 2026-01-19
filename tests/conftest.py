"""Pytest configuration and fixtures."""

import pytest


def pytest_addoption(parser):
    """Add custom CLI options for tests."""
    parser.addoption(
        "--reasoning-effort",
        action="store",
        default="medium",
        choices=["low", "medium", "high"],
        help="Reasoning effort level for CMR agent tests (default: medium)",
    )


@pytest.fixture
def reasoning_effort(request):
    """Fixture to get reasoning effort from CLI."""
    return request.config.getoption("--reasoning-effort")
