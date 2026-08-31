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

## `min_score` and the SDE search backend

Both SDE-backed tools send `min_score` on every request — `sde_search_tool` on `/api/search`,
`repository_search_tool` on `/api/code/search`. It is a lower bound on the `_score` each document is
returned with, and the endpoint applies a server-side default of `0.55` when the field is omitted,
which is above the score most documents receive — so omitting it silently returns nothing. The tools
default to `min_score=0.0` and expose it as a config field.

Measured against the current endpoint, for `"UF universal format weather radar .uf reader python
reflectivity"`:

| `min_score` | results |
| --- | --- |
| omitted (server default `0.55`) | 0 |
| `0.0` | 385 |
