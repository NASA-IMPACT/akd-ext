"""Type aliases and type constants for akd_ext."""

from typing import get_args, get_origin

from agents import Tool as OpenAITool
from akd.tools._base import BaseTool as AKDTool

# Resolved tuple of OpenAI SDK tool types for isinstance() checks.
# get_origin strips generics (e.g., ComputerTool[Any] → ComputerTool).
OPENAI_TOOL_TYPES = tuple(get_origin(t) or t for t in get_args(OpenAITool))

__all__ = ["AKDTool", "OpenAITool", "OPENAI_TOOL_TYPES"]
