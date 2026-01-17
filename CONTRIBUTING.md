# Contributing to akd-ext

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/NASA-IMPACT/akd-ext.git
   cd akd-ext
   ```

2. **Install uv** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install dependencies**
   ```bash
   uv sync --extra dev
   ```

4. **Install pre-commit hooks**
   ```bash
   uv run pre-commit install
   ```

## Development Workflow

### Running Tests
```bash
uv run pytest
```

### Running Linters
```bash
uv run pre-commit run --all-files
```

### Adding a New Tool

Tools follow the akd-core pattern. See `akd_ext/tools/dummy.py` as a reference:

```python
from akd._base import InputSchema, OutputSchema
from akd.tools import BaseTool
from pydantic import Field


class MyInputSchema(InputSchema):
    """Input schema for MyTool."""

    query: str = Field(..., description="Description of the input")


class MyOutputSchema(OutputSchema):
    """Output schema for MyTool."""

    result: str = Field(..., description="Description of the output")


class MyTool(BaseTool[MyInputSchema, MyOutputSchema]):
    """Description of what this tool does."""

    input_schema = MyInputSchema
    output_schema = MyOutputSchema

    async def _arun(self, params: MyInputSchema) -> MyOutputSchema:
        # Implementation here
        return MyOutputSchema(result=params.query)
```

### Tool Attributes (Auto-generated)

Each tool has these auto-generated attributes:
- `.name` - Derived from class name (e.g., `"MyTool"`)
- `.description` - Generated from class docstring + input/output schema field names and descriptions

### Tool Configuration

Customize tools via `BaseToolConfig`:

```python
from akd.tools import BaseToolConfig

# Override name
tool = MyTool(config=BaseToolConfig(name="custom_name"))

# Create custom config class for additional options
class MyToolConfig(BaseToolConfig):
    custom_option: str = "default_value"

tool = MyTool(config=MyToolConfig(name="custom", custom_option="foo"))
```

See `akd_ext/tools/dummy.py` for a complete reference implementation.

## Code Style

- **Python 3.12+ is strictly required**
- We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting
- Line length: 120 characters
- Pre-commit hooks will auto-fix most issues

### Type Hints

Use modern Python 3.12+ type hint syntax:

```python
# Good
def foo(x: int | None = None) -> list[str]:
    ...

# Bad (old style)
from typing import Optional, Union, List
def foo(x: Optional[int] = None) -> List[str]:
    ...
```

| Old Style | Modern Style |
|-----------|--------------|
| `Optional[X]` | `X \| None` |
| `Union[X, Y]` | `X \| Y` |
| `List[X]` | `list[X]` |
| `Dict[K, V]` | `dict[K, V]` |
| `Tuple[X, Y]` | `tuple[X, Y]` |
| `Set[X]` | `set[X]` |

## Pull Requests

1. Create a feature branch from `develop`
2. Make your changes
3. Ensure tests pass: `uv run pytest`
4. Ensure linting passes: `uv run pre-commit run --all-files`
5. Submit a PR against `develop`
