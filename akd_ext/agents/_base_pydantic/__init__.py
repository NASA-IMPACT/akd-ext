"""Pydantic AI-backed agent base class for akd_ext.

Public API:

- :class:`PydanticAIBaseAgent` — subclass this to build new agents.
- :class:`PydanticAIBaseAgentConfig` — extend for subclass-specific config.

The subpackage also exposes internal helpers (``_protocols``, ``_tool_adapter``,
``_context_adapter``, ``_event_translator``, ``_capabilities``) that consumers
typically don't need to import directly.
"""

from ._base import PydanticAIBaseAgent, PydanticAIBaseAgentConfig

__all__ = [
    "PydanticAIBaseAgent",
    "PydanticAIBaseAgentConfig",
]
