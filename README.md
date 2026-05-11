# akd-ext

Misc extension to [akd-core](https://github.com/NASA-IMPACT/accelerated-discovery/).

## Documentation

- [Creating Agents](docs/development/creating_agents.md) — guide for building new agents on `OpenAIBaseAgent` or `PydanticAIBaseAgent`, including config, schemas, tools, capabilities, tests, and reference examples.

## Installation

### Using uv (recommended)

```bash
uv pip install git+https://github.com/NASA-IMPACT/akd-ext.git@develop
```

### For development

```bash
git clone https://github.com/NASA-IMPACT/akd-ext.git
cd akd-ext
git checkout develop
uv venv --python 3.12
uv sync  # preferred
source .venv/bin/activate
```

### Running scripts

The best way to execute scripts is with `uv run`:

```bash
uv run python your_script.py
```
