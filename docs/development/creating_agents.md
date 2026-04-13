# Creating Agents in akd-ext

This guide walks through creating a new agent using the OpenAI Agents SDK base classes provided by akd-ext.

## Overview

Agents in akd-ext follow a **schema-first** pattern built on top of the OpenAI Agents SDK. Every agent requires:

- **Input schema** — typed parameters the agent receives
- **Output schema** — typed structured output the agent returns
- **Config** — model settings, system prompt, tools
- **Agent class** — ties everything together

### Class Hierarchy

```
BaseAgent (akd-core)
└── OpenAIBaseAgent (akd_ext/agents/_base.py)
    └── Your agent
```

## Step-by-step Guide

### 1. Define the Input Schema

Extend `InputSchema` from akd-core. Every field needs a `Field(...)` with a description.

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
- Docstring is **required**
- All fields must have `description` in `Field()`
- Use modern type hints: `str | None` not `Optional[str]`, `list[str]` not `List[str]`

### 2. Define the Output Schema

Extend `OutputSchema`. Set `__response_field__` to indicate which field contains the primary text response.

```python
from akd._base import OutputSchema
from pydantic import Field

class MyAgentOutputSchema(OutputSchema):
    """Use this schema to return the analysis report.
    Use TextOutput for clarification questions."""

    __response_field__ = "report"
    report: str = Field(default="", description="The full analysis report")
```

For multiple output fields:

```python
class MyAgentOutputSchema(OutputSchema):
    """Output with separate spec and reasoning."""

    __response_field__ = "spec"
    spec: str = Field(default="", description="The specification document")
    reasoning: str = Field(default="", description="Reasoning behind design choices")
```

The `__response_field__` tells the framework which field contains the main text content for streaming.

### 3. Write the System Prompt

Define the system prompt as a module-level constant. This is the core of your agent's behavior.

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

### 4. Define the Config

Extend `OpenAIBaseAgentConfig` with your defaults.

```python
from typing import Literal
from akd_ext.agents._base import OpenAIBaseAgentConfig
from pydantic import Field

class MyAgentConfig(OpenAIBaseAgentConfig):
    """Configuration for My Agent."""

    system_prompt: str = Field(default=MY_AGENT_SYSTEM_PROMPT)
    model_name: str = Field(default="gpt-5.2")
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(default="medium")
```

Key config properties:
- `model_name` — model to use (e.g., `"gpt-5.2"`, `"gpt-4o"`, `"gpt-5-nano"`)
- `reasoning_effort` — for reasoning models: `"low"`, `"medium"`, `"high"`, or `None`
- `tools` — list of tools (see [Adding Tools](#adding-tools))
- `stateless` — `False` (default) keeps conversation history, `True` for single-turn
- `temperature`, `max_tokens`, `top_p` — sampling parameters

### 5. Create the Agent Class

```python
from akd._base import TextOutput
from akd_ext.agents._base import OpenAIBaseAgent

class MyAgent(OpenAIBaseAgent[MyAgentInputSchema, MyAgentOutputSchema]):
    """My Agent description."""

    input_schema = MyAgentInputSchema
    output_schema = MyAgentOutputSchema | TextOutput  # union output
    config_schema = MyAgentConfig

    def check_output(self, output) -> str | None:
        if isinstance(output, MyAgentOutputSchema) and not output.report.strip():
            return "Report is empty. Provide a complete analysis."
        return super().check_output(output)
```

#### Union Output with TextOutput

Setting `output_schema = MyAgentOutputSchema | TextOutput` allows the agent to return either:
- **Structured output** (`MyAgentOutputSchema`) — when it has results
- **Free-form text** (`TextOutput`) — for clarification questions or when inputs are insufficient

If you don't need this flexibility, use a single schema: `output_schema = MyAgentOutputSchema`.

#### `check_output()` Override

Override `check_output()` to validate the agent's output before returning it. Return `None` if valid, or an error message string to reject and retry.

### 6. Adding Tools

#### MCP Tools (Hosted)

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
            }
        ),
    ]

class MyAgentConfig(OpenAIBaseAgentConfig):
    tools: list[Any] = Field(default_factory=get_default_tools)
```

#### Web Search

```python
from agents import WebSearchTool

class MyAgentConfig(OpenAIBaseAgentConfig):
    tools: list[Any] = Field(default_factory=lambda: [WebSearchTool()])
```

#### AKD Tools

AKD `BaseTool` instances are auto-converted to OpenAI `FunctionTool` via the config validator.

## File Structure

Place your agent in the appropriate directory:

```
akd_ext/agents/
├── _base.py                              # Base classes (don't modify)
├── __init__.py                           # Top-level exports
├── cmr_care.py                           # Standalone agent example
└── research_partner/                     # Agent group
    ├── __init__.py                       # Group exports
    ├── capability_feasibility_mapper.py
    ├── workflow_spec_builder.py
    ├── experiment_implementation.py
    └── interpretation_paper_assembly.py
```

Each agent file follows this internal layout:
1. Module docstring
2. Imports
3. System prompt constant
4. Tool factory function (if applicable)
5. Config class
6. Input/Output schema classes
7. Agent class

## Registration

### In the agent group `__init__.py`

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

### In the top-level `akd_ext/agents/__init__.py`

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

## Writing Tests

Tests live in `tests/agents/` mirroring the source structure. Use the `reasoning_effort` fixture from `tests/conftest.py`.

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

Run tests with:

```bash
uv run pytest tests/agents/research_partner/test_my_agent.py -n=3
uv run pytest tests/agents/research_partner/test_my_agent.py --reasoning-effort=low -n=3
```

## Running the Agent

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

## Linting

Always run before committing:

```bash
uv run pre-commit run --all-files
```

## Reference Examples

| Pattern | Example File |
|---------|-------------|
| Agent without tools | `akd_ext/agents/research_partner/capability_feasibility_mapper.py` |
| Agent with MCP tools | `akd_ext/agents/cmr_care.py` |
| Multiple output fields | `akd_ext/agents/research_partner/workflow_spec_builder.py` |
| Single structured output (no union) | `akd_ext/agents/code_search_care.py` |
| Test with parametrize | `tests/agents/test_cmr_care.py` |
