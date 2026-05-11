# Creating Agents in akd-ext

This guide walks through creating a new agent in akd-ext. Two base classes are
available:

- **`OpenAIBaseAgent`** — built on the OpenAI Agents SDK. Direct path when you
  want to rely on OpenAI SDK hosted tools like `HostedMCPTool` / `WebSearchTool`.
- **`PydanticAIBaseAgent`** — built on `pydantic_ai.Agent`. Richer extension
  surface (capabilities, hooks, history processors).

Both expose the same AKD contract — `arun` / `astream`, schema-first
input/output, config-first construction — so downstream callers don't care
which base is underneath. Both import from `akd_ext.agents._base`.

## Overview

Agents in akd-ext follow a **schema-first** pattern. Every agent requires:

- **Input schema** — typed parameters the agent receives
- **Output schema** — typed structured output the agent returns
- **System prompt** — module-level constant defining agent behavior
- **Config** — model settings, system prompt, tools, (pydantic_ai) capabilities
- **Agent class** — ties everything together

### Choosing a base

| You want … | Use |
|---|---|
| OpenAI Agents SDK hosted tools (`HostedMCPTool`, `WebSearchTool`) straight through | `OpenAIBaseAgent` |
| Pydantic AI capabilities (`Thinking`, `MCP`, `WebSearch`, `Hooks`, …), native union outputs, `TestModel` for hermetic tests, `agent.last_run_context` for multi-turn continuation | `PydanticAIBaseAgent` |

Both satisfy akd-core's `AKDExecutable` protocol at runtime;
`isinstance(agent, AKDExecutable)` works either way.

### Class hierarchies

```
BaseAgent (akd-core)
├── OpenAIBaseAgent       (akd_ext.agents._base.openai)
│       └── Your agent
│
└── ConfigBindingMixin (akd-core) + pydantic_ai.Agent + AKDExecutable
        └── PydanticAIBaseAgent   (akd_ext.agents._base.pydantic_ai)
                └── Your agent
```

`OpenAIBaseAgent` follows AKD's historic single-inheritance pattern.
`PydanticAIBaseAgent` multi-inherits `ConfigBindingMixin` from akd-core to
auto-expose config fields as properties, subclasses `pydantic_ai.Agent` for
behavior, and explicitly lists `AKDExecutable` in the bases so runtime
`isinstance` checks succeed.

## Building blocks (shared)

The input schema, output schema, system prompt, `check_output` override, union
outputs, file layout, registration, tests, and streaming contract are
identical across both bases. Differences are isolated to config class, model
name format, and hosted-tool wiring (next section).

### Input schema

Extend `InputSchema` from akd-core. Every field needs `Field(...)` with a
`description`.

```python
from akd._base import InputSchema
from pydantic import Field

class MyAgentInputSchema(InputSchema):
    """Input schema for My Agent."""

    query: str = Field(..., description="The user's research question")
    data_path: str = Field(..., description="Path to the input data")
    optional_param: str | None = Field(default=None, description="An optional parameter")
```

Rules:

- Docstring is **required**.
- All fields must carry a `description` in `Field()`.
- Use modern type hints (`str | None`, `list[str]`) — not `Optional[str]` /
  `List[str]`.

### Output schema

Extend `OutputSchema`. Set `__response_field__` to indicate which field
contains the primary text response (used for streaming).

```python
from akd._base import OutputSchema
from pydantic import Field

class MyAgentOutputSchema(OutputSchema):
    """Use this schema to return the analysis report.
    Use TextOutput for clarification questions."""

    __response_field__ = "report"
    report: str = Field(default="", description="The full analysis report")
```

Multiple fields:

```python
class MyAgentOutputSchema(OutputSchema):
    """Output with separate spec and reasoning."""

    __response_field__ = "spec"
    spec: str = Field(default="", description="The specification document")
    reasoning: str = Field(default="", description="Reasoning behind design choices")
```

### Union output with TextOutput

Setting `output_schema = MyAgentOutputSchema | TextOutput` lets the agent
return either:

- **Structured output** (`MyAgentOutputSchema`) — when it has results.
- **Free-form text** (`TextOutput`) — for clarification questions or when
  inputs are insufficient.

Use a single schema (`output_schema = MyAgentOutputSchema`) if you don't need
this flexibility. On `PydanticAIBaseAgent`, the union is handled natively by
pydantic_ai.

### System prompt

Define the system prompt as a module-level constant — this is the core of your
agent's behavior.

```python
MY_AGENT_SYSTEM_PROMPT = """\
## ROLE
You are a ...

## OBJECTIVE
...

## CONSTRAINTS & STYLE RULES
...

## PROCESS
...

## OUTPUT FORMAT
...
"""
```

### `check_output()` override

Override `check_output()` to validate the agent's output before returning it.
Return `None` if valid, or a string to reject and retry:

```python
def check_output(self, output) -> str | None:
    if isinstance(output, MyAgentOutputSchema) and not output.report.strip():
        return "Report is empty. Provide a complete analysis."
    return super().check_output(output)
```

On `PydanticAIBaseAgent` this method is automatically bridged to pydantic_ai's
`@output_validator` — a non-`None` return value is raised as `ModelRetry` so
the model can self-correct. `TextOutput` always passes through (it represents
a mid-conversation clarification request, not a terminal answer).

## Config & agent class

The surface is identical on both bases — only the imports and model-name
format differ.

### On `OpenAIBaseAgent`

```python
from typing import Literal
from akd._base import TextOutput
from akd_ext.agents._base import OpenAIBaseAgent, OpenAIBaseAgentConfig
from pydantic import Field


class MyAgentConfig(OpenAIBaseAgentConfig):
    """Configuration for My Agent."""

    system_prompt: str = Field(default=MY_AGENT_SYSTEM_PROMPT)
    model_name: str = Field(default="gpt-5.2")    # bare model name
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(default="medium")


class MyAgent(OpenAIBaseAgent[MyAgentInputSchema, MyAgentOutputSchema]):
    """My Agent description."""

    input_schema = MyAgentInputSchema
    output_schema = MyAgentOutputSchema | TextOutput
    config_schema = MyAgentConfig

    def check_output(self, output) -> str | None:
        if isinstance(output, MyAgentOutputSchema) and not output.report.strip():
            return "Report is empty. Provide a complete analysis."
        return super().check_output(output)
```

### On `PydanticAIBaseAgent`

Same shape, different imports. Note the `provider:model` prefix on
`model_name` — pydantic_ai uses that format for provider resolution instead
of bare model names.

```python
from typing import Literal
from akd._base import TextOutput
from akd_ext.agents._base import PydanticAIBaseAgent, PydanticAIBaseAgentConfig
from pydantic import Field


class MyAgentConfig(PydanticAIBaseAgentConfig):
    """Configuration for My Agent."""

    system_prompt: str = Field(default=MY_AGENT_SYSTEM_PROMPT)
    model_name: str = Field(default="openai:gpt-5.2")    # provider:model
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(default="medium")


class MyAgent(PydanticAIBaseAgent[MyAgentInputSchema, MyAgentOutputSchema]):
    """My Agent description."""

    input_schema = MyAgentInputSchema
    output_schema = MyAgentOutputSchema | TextOutput
    config_schema = MyAgentConfig

    def check_output(self, output) -> str | None:
        if isinstance(output, MyAgentOutputSchema) and not output.report.strip():
            return "Report is empty. Provide a complete analysis."
        return super().check_output(output)
```

### Common config fields

Both config classes inherit from `akd.agents._base.BaseAgentConfig` and share:

- `model_name` — model identifier (format differs per base; see above).
- `system_prompt` — agent instructions.
- `tools` — list of tools (see below).
- `reasoning_effort` — `"low"` / `"medium"` / `"high"` / `None` (reasoning models only).
- `num_retries` — max retries for tool calls and output validation.
- `max_tool_iterations` / `max_tool_calls` — per-run tool-call caps.
- `reflection_prompt` — injected reflection before each model request.
- `stateless` — `False` (default) keeps conversation history, `True` for single-turn.
- `temperature`, `max_tokens`, `top_p` — sampling parameters.

### Pydantic AI-only config fields

`PydanticAIBaseAgentConfig` adds:

- `capabilities: list[Any]` — pydantic_ai capability objects (`Thinking`,
  `MCP`, `WebSearch`, `WebFetch`, `Hooks`, …). Merged with capabilities the
  base auto-derives from the scalar fields above (e.g. `reasoning_effort`
  becomes a `Thinking(effort=...)` capability).
- `history_processors: list[Any]` — per-request message-history callables.
- `extra="allow"` — any additional fields on a subclass config are forwarded
  to `pydantic_ai.Agent.__init__` via `model_extra` (forward-compat).
- `enable_trimming: bool = False` — disabled by default because the naive
  ratio-trimmer violates pydantic_ai's tool-call/assistant pairing invariant.
  Supply your own processor via `history_processors` if you need trimming.

## Tools

AKD tools (`BaseTool` subclasses) are auto-converted on both bases — just pass
instances via `config.tools=[...]`:

```python
from akd_ext.tools.dummy import DummyTool

class MyAgentConfig(OpenAIBaseAgentConfig):   # or PydanticAIBaseAgentConfig
    tools: list[Any] = Field(default_factory=lambda: [DummyTool()])
```

On `OpenAIBaseAgent`, AKD `BaseTool` instances are converted to the OpenAI
SDK's `FunctionTool`. On `PydanticAIBaseAgent`, they're adapted to
`pydantic_ai.Tool`; `ValidationError` / `SchemaValidationError` raised inside
the tool become `ModelRetry` so the model can self-correct bad arguments.

Where the two bases diverge is on **hosted / built-in tools** — each ecosystem
has its own mechanism.

### MCP tools

**On `OpenAIBaseAgent`** — register the OpenAI SDK's `HostedMCPTool` as a
tool:

```python
import os
from agents import HostedMCPTool

def get_default_tools():
    return [
        HostedMCPTool(
            tool_config={
                "type": "mcp",
                "server_label": "My_MCP_Server",
                "allowed_tools": ["tool_a", "tool_b"],
                "require_approval": "never",
                "server_description": "Description of the MCP server",
                "server_url": os.environ.get("MY_MCP_URL", "https://default-url.com/mcp"),
            },
        ),
    ]

class MyAgentConfig(OpenAIBaseAgentConfig):
    tools: list[Any] = Field(default_factory=get_default_tools)
```

**On `PydanticAIBaseAgent`** — MCP is a **capability**, not a tool. Register it
via `config.capabilities`:

```python
import os
from pydantic_ai.capabilities import MCP

def get_default_capabilities():
    return [
        MCP(
            # Trailing slash matters: the endpoint returns a 307 redirect to
            # the slashed form, and the MCP streamable-HTTP client won't
            # follow redirects on POST.
            url=os.environ.get("MY_MCP_URL", "https://default-url.com/mcp/"),
            allowed_tools=["tool_a", "tool_b"],
            description="Description of the MCP server",
        ),
    ]

class MyAgentConfig(PydanticAIBaseAgentConfig):
    capabilities: list[Any] = Field(default_factory=get_default_capabilities)
```

### Web search

**On `OpenAIBaseAgent`**:

```python
from agents import WebSearchTool

class MyAgentConfig(OpenAIBaseAgentConfig):
    tools: list[Any] = Field(default_factory=lambda: [WebSearchTool()])
```

**On `PydanticAIBaseAgent`** — `WebSearch` is a capability:

```python
from pydantic_ai.capabilities import WebSearch

class MyAgentConfig(PydanticAIBaseAgentConfig):
    capabilities: list[Any] = Field(default_factory=lambda: [WebSearch()])
```

## Pydantic AI-specific features

`PydanticAIBaseAgent` exposes a handful of extension points that have no
analogue on `OpenAIBaseAgent`.

### Capabilities

Pydantic AI's primary extension point. Capability instances registered on
`config.capabilities` run alongside capabilities the base auto-derives from
scalar config fields. Useful built-ins:

| Capability | Purpose |
|---|---|
| `Thinking(effort=...)` | Reasoning models; auto-derived from `config.reasoning_effort` |
| `MCP(url=..., allowed_tools=...)` | MCP server integration (see above) |
| `WebSearch()` / `WebFetch()` | Built-in web search / fetch (model-dependent) |
| `Hooks()` | Lifecycle hooks (see below) |
| *custom* | Subclass `pydantic_ai.capabilities.AbstractCapability` |

### Hooks

`pydantic_ai.capabilities.hooks.Hooks` lets you register decorator-style
callbacks on the run lifecycle — `before_run`, `before_model_request`,
`before_tool_execute`, `after_run`, etc. `PydanticAIBaseAgent` itself installs
an internal `Hooks` capability to capture each run's live `RunContext` onto
`self._live_pai_ctx`; subclasses can add their own `Hooks()` via
`config.capabilities`:

```python
from pydantic_ai.capabilities.hooks import Hooks

hooks = Hooks()

@hooks.on.before_tool_execute
async def audit_tool(ctx, *, call, tool_def, args):
    print(f"About to call tool {call.tool_name} with {args!r}")
    return args     # pass through unchanged

class MyAgentConfig(PydanticAIBaseAgentConfig):
    capabilities: list[Any] = Field(default_factory=lambda: [hooks])
```

### History processors

`config.history_processors: list[Callable[[list[ModelMessage]], list[ModelMessage]]]`
runs per-request and lets you transform the message history sent to the model
(trim, summarize, filter). AKD's ratio-trimmer is *off* by default on
`PydanticAIBaseAgent` because it breaks tool-call/assistant pairing; supply
your own if you need trimming.

### `RunContext` propagation and multi-turn runs

Every event `agent.astream(...)` yields carries a `run_context` populated from
pydantic_ai's live `RunContext` — AKD-shape `messages` / `usage` / `run_id`
reflected for read-only inspection, plus a lossless `pai_run_context` extra
with the full pai object. For `arun` callers (whose return is pinned to
`OutputSchema` per the AKD contract), the same wrapper is reachable via
`agent.last_run_context`:

```python
out_1 = await agent.arun(MyAgentInputSchema(query="first turn"))
ctx = agent.last_run_context       # populated AKD RunContext with pai_run_context extra

out_2 = await agent.arun(
    MyAgentInputSchema(query="follow-up"),
    run_context=ctx,               # carries prior-turn messages + usage
)
```

Passing `event.run_context` or `agent.last_run_context` verbatim into the next
call triggers lossless pai-native continuation — the agent's input-side
helpers prefer the `pai_run_context` extra over converting from the AKD-shape
typed fields.

**Concurrency note**: `PydanticAIBaseAgent` is designed for one active run per
instance. Concurrent `arun` / `astream` calls on the same agent will race
the captured `_live_pai_ctx`. Use a fresh agent per run for concurrent
workloads.

### Hermetic tests with `TestModel`

`pydantic_ai.models.test.TestModel` stands in for a real model so unit tests
don't touch a provider:

```python
from pydantic_ai.models.test import TestModel

agent = MyAgent(MyAgentConfig(capabilities=[]))     # disable MCP for hermetic run
with agent.override(model=TestModel()):
    result = await agent.arun(MyAgentInputSchema(query="x"))
```

`TestModel` auto-fills the declared output schema with stub data, so
`agent.arun` returns a real `MyAgentOutputSchema` (or `TextOutput`) with no
network call.

## File structure

Place your agent in the appropriate directory:

```
akd_ext/agents/
├── _base/                                # Base classes (don't modify)
│   ├── __init__.py                       # Re-exports both base classes
│   ├── openai.py                         # OpenAIBaseAgent
│   └── pydantic_ai/                      # PydanticAIBaseAgent + adapters
│       ├── _base.py
│       ├── _capabilities.py
│       ├── _context_adapter.py
│       ├── _event_translator.py
│       └── _tool_adapter.py
├── __init__.py                           # Top-level exports
├── cmr_care.py                           # Standalone agent (OpenAI-based)
└── research_partner/                     # Agent group
    ├── __init__.py
    ├── capability_feasibility_mapper.py
    ├── workflow_spec_builder.py
    ├── experiment_implementation.py
    └── interpretation_paper_assembly.py
```

Each agent file follows this internal layout:

1. Module docstring
2. Imports
3. System prompt constant
4. Tool / capability factory function (if applicable)
5. Config class
6. Input / output schema classes (can live above the config if they're prerequisites)
7. Agent class

## Registration

### Group `__init__.py`

```python
# akd_ext/agents/research_partner/__init__.py
from akd_ext.agents.research_partner.my_agent import (
    MyAgent,
    MyAgentConfig,
    MyAgentInputSchema,
    MyAgentOutputSchema,
)

__all__ = [
    # ... existing exports ...
    "MyAgent",
    "MyAgentConfig",
    "MyAgentInputSchema",
    "MyAgentOutputSchema",
]
```

### Top-level `akd_ext/agents/__init__.py`

```python
from akd_ext.agents.research_partner import (
    # ... existing imports ...
    MyAgent,
    MyAgentConfig,
    MyAgentInputSchema,
    MyAgentOutputSchema,
)

__all__ = [
    # ... existing exports ...
    "MyAgent",
    "MyAgentConfig",
    "MyAgentInputSchema",
    "MyAgentOutputSchema",
]
```

## Writing tests

Tests live in `tests/agents/` mirroring the source structure. Use the
`reasoning_effort` fixture from `tests/conftest.py`.

```python
"""Functional tests for My Agent."""

import pytest

from akd._base import TextOutput
from akd_ext.agents.research_partner import (
    MyAgent,
    MyAgentConfig,
    MyAgentInputSchema,
    MyAgentOutputSchema,
)


def _make_input(**overrides) -> MyAgentInputSchema:
    """Helper to create input schema with default placeholder values."""
    defaults = {
        "query": "Default test query",
        "data_path": "/path/to/data",
    }
    defaults.update(overrides)
    return MyAgentInputSchema(**defaults)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "First test query",
        "Second test query",
        "Third test query",
    ],
)
async def test_my_agent(query: str, reasoning_effort: str):
    """Test My Agent.

    Args:
        query: Test query
        reasoning_effort: CLI param --reasoning-effort (low/medium/high)
    """
    config = MyAgentConfig(reasoning_effort=reasoning_effort)
    agent = MyAgent(config=config, debug=True)
    result = await agent.arun(_make_input(query=query))

    assert isinstance(result, (MyAgentOutputSchema, TextOutput))
    if isinstance(result, MyAgentOutputSchema):
        assert result.report.strip(), "Report should not be empty"
```

For **hermetic unit tests on `PydanticAIBaseAgent`**, swap the real model for
`TestModel` and disable any MCP / network capabilities:

```python
from pydantic_ai.models.test import TestModel

async def test_my_agent_hermetic():
    agent = MyAgent(MyAgentConfig(capabilities=[]))   # no MCP in hermetic run
    with agent.override(model=TestModel()):
        result = await agent.arun(_make_input(query="x"))
    assert isinstance(result, (MyAgentOutputSchema, TextOutput))
```

Run tests with:

```bash
uv run pytest tests/agents/research_partner/test_my_agent.py -n=3
uv run pytest tests/agents/research_partner/test_my_agent.py --reasoning-effort=low -n=3
```

## Running the agent

```python
import asyncio
from akd_ext.agents.research_partner import MyAgent, MyAgentConfig, MyAgentInputSchema

async def main():
    agent = MyAgent(MyAgentConfig(debug=True))
    result = await agent.arun(MyAgentInputSchema(query="my question", data_path="/data"))
    print(result)

asyncio.run(main())
```

For streaming:

```python
async for event in agent.astream(MyAgentInputSchema(query="my question", data_path="/data")):
    print(event.event_type, event.data)
```

On `PydanticAIBaseAgent`, each `event.run_context` carries the live pai state;
feed it (or `agent.last_run_context`) into the next call for multi-turn
continuation as shown in *RunContext propagation and multi-turn runs* above.

## Linting

Always run before committing:

```bash
uv run pre-commit run --all-files
```

## Reference examples

| Pattern | Example file |
|---|---|
| Agent without tools (OpenAI) | `akd_ext/agents/research_partner/capability_feasibility_mapper.py` |
| Agent with MCP tools (OpenAI) | `akd_ext/agents/cmr_care.py` |
| Agent with MCP capability (Pydantic AI) | `examples/cmr_care_pydantic.py` |
| Multiple output fields | `akd_ext/agents/research_partner/workflow_spec_builder.py` |
| Single structured output (no union) | `akd_ext/agents/code_search_care.py` |
| Test with parametrize | `tests/agents/test_cmr_care.py` |
| Hermetic test with `TestModel` (Pydantic AI) | `tests/agents/test_base_pydantic.py` |
