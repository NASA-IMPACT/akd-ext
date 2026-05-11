"""Pydantic AI-backed agent base class for akd_ext.

Public API:

- :class:`PydanticAIBaseAgent` — subclass this to build new agents.
- :class:`PydanticAIBaseAgentConfig` — extend for subclass-specific config.

The subpackage also exposes internal helpers (``_tool_adapter``,
``_context_adapter``, ``_event_translator``, ``_capabilities``) that consumers
typically don't need to import directly. Structural protocols
(``AKDExecutable``, ``AKDTool``, ``RunContextProtocol``, ``TokenCounts``) are
sourced from ``akd._base.protocols``.
"""

from ._base import PydanticAIBaseAgent, PydanticAIBaseAgentConfig

__all__ = [
    "PydanticAIBaseAgent",
    "PydanticAIBaseAgentConfig",
]
