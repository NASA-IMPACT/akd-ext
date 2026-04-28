"""Base classes for closed-loop workflow stages.

Provides ClosedLoopStageConfig and a _create_agent() mixin pattern that
generalizes the context-file-loading shared across all closed-loop stages.

Concrete stage agents (e.g., CapabilityFeasibilityMapperAgent) inherit from
OpenAIBaseAgent with their specific schemas and use ClosedLoopStageConfig
to get the context_files field. The _create_agent_with_context() helper
appends context files to agent instructions.

Public API:
    ClosedLoopStageConfig
"""

from __future__ import annotations

from agents import Agent
from pydantic import Field

from akd_ext.agents._base import OpenAIBaseAgentConfig


class ClosedLoopStageConfig(OpenAIBaseAgentConfig):
    """Configuration for a closed-loop workflow stage.

    Extends OpenAIBaseAgentConfig with a generic context_files dict.
    Each entry's key becomes a section heading appended to the agent's
    instructions, and the value is the content of that section.
    """

    context_files: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of context label to content string. Each entry is appended to agent instructions as a named section.",
    )


def append_context_to_agent(agent: Agent, context_files: dict[str, str]) -> Agent:
    """Append context file sections to an agent's instructions.

    This is the shared logic that replaces the per-stage _create_agent()
    overrides in the old per-stage agents.
    """
    for label, content in context_files.items():
        if content:
            agent.instructions += f"\n\n---\n\n## {label}\n\n{content}"
    return agent
