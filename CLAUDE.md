# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## akd-core Design Principles

This project extends [akd-core](https://github.com/NASA-IMPACT/accelerated-discovery/) which defines the foundational patterns for tools and agents.

### Schema-First Design

All tools and agents require typed input/output schemas extending `InputSchema` and `OutputSchema` from `akd._base`:

```python
from akd._base import InputSchema, OutputSchema
from pydantic import Field

class MyInputSchema(InputSchema):
    """Docstring is required."""
    query: str = Field(..., description="Description required for all fields")

class MyOutputSchema(OutputSchema):
    """Docstring is required."""
    result: str = Field(..., description="Description required for all fields")
```

### Execution Interface

The public-facing interface is always `arun()` (async):
- `arun(params)` - Public async method that handles IO validation via schemas
- `_arun(params)` - Internal method subclasses implement for actual execution
- `run(params)` - Sync wrapper available for convenience

```python
# Usage
result = await my_tool.arun(MyInputSchema(query="test"))
# or sync
result = my_tool.run(MyInputSchema(query="test"))
```

### Configuration Objects

Tools and agents use config classes extending `BaseToolConfig` or `BaseAgentConfig`:
- Config validated at instantiation
- Properties auto-exposed: `agent.model_name` maps to `agent.config.model_name`
- Override defaults via config classes, not constructor params

### Agent Hierarchy

```
BaseAgent (akd-core)
├── LiteLLMInstructorBaseAgent (akd-core) - Structured generation via instructor + LiteLLM
└── OpenAIBaseAgent (akd_ext) - OpenAI Agents SDK based agents
    └── FreeFormOpenAIBaseAgent (akd_ext) - Free-form text output variant
```

## Commands

All Python commands use `uv run`:

```bash
# Run tests (with parallelization)
uv run pytest -n=3

# Run a single test file
uv run pytest tests/agents/test_cmr_care.py -n=3

# Run a single test function
uv run pytest tests/agents/test_cmr_care.py::test_cmr_care_agent -n=3

# Run with specific reasoning effort
uv run pytest --reasoning-effort=low -n=3

# Lint
uv run pre-commit run --all-files

# Run a script
uv run python your_script.py
```

## Architecture

### Creating a Tool

Tools inherit from `BaseTool[InputSchema, OutputSchema]`:

```python
from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool
from pydantic import Field

class MyInputSchema(InputSchema):
    """Input schema for MyTool."""
    query: str = Field(..., description="The input query")

class MyOutputSchema(OutputSchema):
    """Output schema for MyTool."""
    result: str = Field(..., description="The output result")

class MyTool(BaseTool[MyInputSchema, MyOutputSchema]):
    """Tool description goes here."""
    input_schema = MyInputSchema
    output_schema = MyOutputSchema

    async def _arun(self, params: MyInputSchema) -> MyOutputSchema:
        """Internal execution - implement your logic here."""
        return MyOutputSchema(result=params.query)
```

Register in `akd_ext/tools/__init__.py`:
```python
from .my_tool import MyTool, MyInputSchema, MyOutputSchema
__all__ = [..., "MyTool", "MyInputSchema", "MyOutputSchema"]
```

Reference implementation: `akd_ext/tools/dummy.py`

### Creating an OpenAI Agents SDK Based Agent

Agents in akd_ext use the OpenAI Agents SDK via base classes in `akd_ext/agents/_base.py`.

**For structured output:**
```python
from akd._base import InputSchema, OutputSchema
from akd_ext.agents._base import OpenAIBaseAgent, OpenAIBaseAgentConfig
from pydantic import Field

class MyAgentInput(InputSchema):
    """Input schema."""
    query: str = Field(..., description="User query")

class MyAgentOutput(OutputSchema):
    """Output schema."""
    answer: str = Field(..., description="Agent answer")

class MyAgentConfig(OpenAIBaseAgentConfig):
    """Config with defaults."""
    system_prompt: str = Field(default="You are a helpful assistant.")
    model_name: str = Field(default="gpt-4o")

class MyAgent(OpenAIBaseAgent[MyAgentInput, MyAgentOutput]):
    """Agent description."""
    input_schema = MyAgentInput
    output_schema = MyAgentOutput
    config_schema = MyAgentConfig
```

**For free-form text output:**
```python
from akd_ext.agents._base import FreeFormOpenAIBaseAgent

class MyFreeFormAgent(FreeFormOpenAIBaseAgent[MyAgentInput]):
    """Returns unstructured text wrapped in FreeFormOutput."""
    input_schema = MyAgentInput
    config_schema = MyAgentConfig
```

**Multi-agent orchestration** - override `_arun()` only when custom logic is needed (see `akd_ext/agents/cmr_care.py`):
- Compose agents by creating internal agent instances in `__init__`
- Override `_arun()` to orchestrate the pipeline
- Pass conversation history between agents via `memory` property

Register in `akd_ext/agents/__init__.py`.

### Key Base Classes

| Class | Location | Purpose |
|-------|----------|---------|
| `BaseAgent[In, Out]` | akd-core | Abstract base for all agents |
| `LiteLLMInstructorBaseAgent[In, Out]` | akd-core | Structured generation via instructor + LiteLLM |
| `OpenAIBaseAgent[In, Out]` | akd_ext | OpenAI Agents SDK based agent |
| `FreeFormOpenAIBaseAgent[In]` | akd_ext | Free-form text output variant |
| `BaseTool[In, Out]` | akd-core | Tool base class |

### OpenAIBaseAgentConfig Properties

- `model_name`, `temperature`, `max_tokens` - Model settings
- `reasoning_effort` - For reasoning models (o1, o3, gpt-5.2): "low", "medium", "high"
- `tools` - List of tools (FunctionTool, HostedMCPTool, etc.)
- `stateless` - False (default) maintains conversation history
- `model_settings` property - Builds ModelSettings, handles reasoning models specially

## Code Style

- Python 3.12+ required
- Use modern type hints: `X | None` not `Optional[X]`, `list[X]` not `List[X]`
- Line length: 120 characters
- Ruff for linting/formatting
