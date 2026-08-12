"""Shared system-prompt assembly for the code-generator sub-agents.

Designer, generator, and intent-checker all build their runtime system prompt
the same way: start from a base prompt, then append optional ``## SECTION``
blocks (allowed libraries, data-format reference, analysis methodology).

Centralised here so a change to the assembly — a new section, ordering, or
caching — happens in one place instead of being triplicated across the three
agent modules. The per-agent *content* (e.g. each agent's forbidden-library
wording) stays in that agent; only the structure and composition live here.
"""

from __future__ import annotations

# Single source of truth for the ``data_format_context`` field description.
# (It had drifted between designer.py and generator.py.)
DATA_FORMAT_CONTEXT_DESC = (
    "Domain-specific data format description appended to the system prompt: "
    "file formats, variable inventories, directory structure, and code "
    "examples for reading them. Ground truth for any data-reading code — "
    "without it an agent second-guesses reader logic it cannot verify."
)


def section(title: str, body: str) -> str:
    """Render one ``--- / ## TITLE / body`` prompt block.

    Returns an empty string when ``body`` is blank, so optional sections
    contribute nothing rather than an empty header.
    """
    body = body.strip()
    if not body:
        return ""
    return f"\n\n---\n\n## {title}\n\n{body}"


def assemble_prompt(base: str, *blocks: str) -> str:
    """Compose a base prompt with appended section blocks, in order.

    ``blocks`` are pre-rendered strings (typically from :func:`section`);
    empty ones are harmless. This is the single seam for the assembly step —
    add ordering or caching here, not in each agent.
    """
    return "".join([base, *blocks])
