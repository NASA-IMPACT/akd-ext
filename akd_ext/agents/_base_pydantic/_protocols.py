"""Local structural Protocol stand-ins.

Mirrors the akd-core protocol hierarchy that the Accelerated Discovery team
is preparing to ship in ``akd._base.structures``. Keeping a local copy now
decouples this work from that timeline; the subpackage swaps to the akd-core
imports (or deletes this module and re-exports from akd-core) once it lands.

The structural hierarchy:

- ``SupportsUsage``      — token-counter shape (AKD ``RunUsage`` and pydantic_ai ``RunUsage`` both satisfy)
- ``RunContextProtocol`` — run-context shape (AKD ``RunContext`` and pydantic_ai ``RunContext`` both satisfy)
- ``AKDExecutable``      — base contract: schemas + ``arun`` (shared by agents and tools)
- ``AKDAgent``           — ``AKDExecutable`` + ``astream``
- ``AKDTool``            — ``AKDExecutable`` + ``name``/``description`` + conversion helpers
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SupportsUsage(Protocol):
    """Structural shape for usage / token-counter objects.

    Both ``akd._base.structures.RunUsage`` (Pydantic BaseModel) and
    ``pydantic_ai.RunUsage`` (dataclass) satisfy this structurally.
    """

    input_tokens: int
    output_tokens: int
    requests: int


@runtime_checkable
class RunContextProtocol(Protocol):
    """Structural supertype for run-context-like objects.

    Both ``akd._base.structures.RunContext`` and ``pydantic_ai.RunContext``
    satisfy this structurally for the shared fields below. For AKD-specific
    fields (``human_response``, ``extra``) or pydantic_ai-specific fields
    (``deps``, ``tool_call_id``, etc.), narrow to the concrete type at the
    call site via ``isinstance`` check.
    """

    messages: list[Any] | None
    usage: SupportsUsage
    run_id: str | None


@runtime_checkable
class AKDExecutable(Protocol):
    """Base contract: schemas + ``arun``. Shared by agents and tools."""

    input_schema: type[Any]
    output_schema: type[Any]
    config_schema: type[Any] | None

    async def arun(
        self,
        params: Any,
        run_context: RunContextProtocol | None = ...,
        **kwargs: Any,
    ) -> Any: ...


@runtime_checkable
class AKDAgent(AKDExecutable, Protocol):
    """Agent contract: ``AKDExecutable`` + ``astream``."""

    def astream(
        self,
        params: Any,
        run_context: RunContextProtocol | None = ...,
        **kwargs: Any,
    ) -> AsyncIterator[Any]: ...


@runtime_checkable
class AKDTool(AKDExecutable, Protocol):
    """Tool contract: ``AKDExecutable`` + naming and conversion helpers."""

    name: str
    description: str

    def as_function(
        self,
        mode: str | None = ...,
    ) -> Callable[..., Awaitable[Any]]: ...

    def as_tool_definition(self) -> dict[str, Any]: ...


__all__ = [
    "AKDAgent",
    "AKDExecutable",
    "AKDTool",
    "RunContextProtocol",
    "SupportsUsage",
]
