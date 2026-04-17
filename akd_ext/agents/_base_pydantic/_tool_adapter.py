"""Adapter from AKD ``BaseTool``-protocol instances to ``pydantic_ai.Tool``.

``BaseTool.as_function()`` already returns a typed async callable with the
right signature metadata for framework introspection. We only need to:

1. Wrap it so ``pydantic.ValidationError`` / ``akd.SchemaValidationError``
   become ``pydantic_ai.ModelRetry`` (so the LLM can self-correct on bad
   tool-call args); all other exceptions propagate and halt the run per
   pydantic_ai conventions.
2. Preserve the signature metadata that pydantic_ai introspects to build
   the tool's JSON schema.
3. Hand the callable to ``pydantic_ai.Tool`` with name/description pulled
   from the AKD tool.

``sequential``, ``timeout``, and per-tool ``max_retries`` stay at their
pydantic_ai defaults. AKD tools are stateless by design so parallel
execution is safe; per-tool knobs can arrive later via a dedicated
``PydanticAIBaseTool(BaseTool)`` that extends ``BaseToolConfig``.
"""

from __future__ import annotations

from pydantic import ValidationError
from pydantic_ai import ModelRetry
from pydantic_ai import Tool as PAITool

from akd._base.errors import SchemaValidationError

from ._protocols import AKDTool


def akd_to_pai_tool(akd_tool: AKDTool) -> PAITool:
    """Adapt an AKD-protocol tool into a ``pydantic_ai.Tool``."""
    raw_fn = akd_tool.as_function()

    async def wrapped(*args, **kwargs):
        try:
            return await raw_fn(*args, **kwargs)
        except (ValidationError, SchemaValidationError) as e:
            raise ModelRetry(str(e)) from e

    wrapped.__name__ = raw_fn.__name__
    wrapped.__doc__ = raw_fn.__doc__
    wrapped.__signature__ = raw_fn.__signature__
    wrapped.__annotations__ = raw_fn.__annotations__

    return PAITool(
        wrapped,
        name=akd_tool.name,
        description=akd_tool.description or akd_tool.__class__.__doc__,
    )


__all__ = ["akd_to_pai_tool"]
