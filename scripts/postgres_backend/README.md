# PostgresBackend

Drop-in replacement for `pydantic_ai_backends.LocalBackend` that persists CARE v2
artifact workspaces to Postgres instead of the local filesystem.

Implements `pydantic_ai_backends.protocol.BackendProtocol`:
`ls_info`, `_read_bytes`, `read`, `write`, `edit`, `glob_info`, `grep_raw`.

## Self-contained — drop in and go

You don't need to manage a schema file in your own project; you don't need
migrations; you don't need any Python boilerplate. Just import the class:

```python
from postgres_backend import PostgresBackend

be = PostgresBackend(workspace="my_agent")     # connects + creates table on first run
be.write("/scope.md", "# Scope\n\nhello")
print(be.read("/scope.md"))
```

What happens on construction:

1. Acquires (or creates) a process-wide `psycopg_pool.ConnectionPool` for
   the DSN (from `conninfo=`, env `CARE_POSTGRES_URL`, or the default
   `postgresql://postgres:postgres@localhost:5432/care_dev`).
2. Runs the bundled [`schema.sql`](./schema.sql) — `CREATE TABLE IF NOT EXISTS`
   plus an idempotent `ALTER TABLE ... DROP COLUMN IF EXISTS size_bytes`
   migration — at most **once per DSN per process**, regardless of how
   many `PostgresBackend` instances are constructed.
3. Returns a ready-to-use object that conforms to `BackendProtocol`, so
   anywhere `LocalBackend` works (e.g. `pydantic_ai_backends.ConsoleCapability`),
   `PostgresBackend` works too.

To use it from another Python program in this repo, the package directory
(`scripts/postgres_backend/`) needs to be importable. Either:

```python
# Option A — add scripts/ to sys.path
import sys, pathlib
sys.path.insert(0, str(pathlib.Path("/path/to/akd-ext/scripts")))
from postgres_backend import PostgresBackend

# Option B — copy the postgres_backend/ folder into your project, then
from postgres_backend import PostgresBackend
```

Disable auto-init (e.g. in tests where the schema is bootstrapped once at
session level) with `PostgresBackend(workspace="x", auto_init=False)`.

## Concurrency

Every operation grabs a connection out of the shared pool, runs its query,
and returns the connection — so multiple threads (e.g. concurrent uvicorn
requests against the same agent workspace) and multiple `PostgresBackend`
instances can coexist safely against the same DSN.

Pool sizing is configurable via env:

| Var | Default | Purpose |
|---|---|---|
| `CARE_POSTGRES_POOL_MIN` | `1` | Minimum idle pool connections |
| `CARE_POSTGRES_POOL_MAX` | `10` | Maximum pool size |

Tests that need to release pool resources between runs can call
`postgres_backend.close_all_pools()` (production code does not need to).

## Schema

Single table, multi-tenant via the `workspace` column. See [`schema.sql`](./schema.sql).

```sql
CREATE TABLE IF NOT EXISTS care_artifacts (
    workspace    TEXT        NOT NULL,
    path         TEXT        NOT NULL,           -- normalized "/scope.md"
    content      TEXT        NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    modified_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace, path)
);
```

Directories are implicit — derived from path prefix grouping in `ls_info`.
The `size` field on `FileInfo` is computed from `content` (codepoint count
excluding `\n`) to match StateBackend semantics, so no separate column is
stored.

## Connection

Default DSN is `postgresql://postgres:postgres@localhost:5432/care_dev` —
matches the `akd-labs` docker-compose Postgres so it works out of the box.

Override via:

- `CARE_POSTGRES_URL` env var, or
- explicit `conninfo=` ctor kwarg.

One-time setup against the docker-compose DB:

```bash
PGPASSWORD=postgres psql -h localhost -U postgres -d postgres -c "CREATE DATABASE care_dev;"
# tests use a separate DB:
PGPASSWORD=postgres psql -h localhost -U postgres -d postgres -c "CREATE DATABASE care_test;"
export CARE_POSTGRES_TEST_URL=postgresql://postgres:postgres@localhost:5432/care_test
```

`auto_init=True` (default) runs `schema.sql` at construction — no manual setup.

## Constructor

```python
PostgresBackend(
    workspace: str,                # tenant key (= agent_name); non-empty, no NUL
    *,
    conninfo: str | None = None,   # libpq DSN; falls back to CARE_POSTGRES_URL or default
    auto_init: bool = True,        # CREATE TABLE IF NOT EXISTS at construction
)
```

## Methods (BackendProtocol)

```
ls_info(path)                   → list[FileInfo]
read(path, offset=0, limit=2000) → str          # line-numbered or "Error: …"
_read_bytes(path)               → bytes
write(path, content)            → WriteResult
edit(path, old, new, replace_all=False) → EditResult
glob_info(pattern, path="/")    → list[FileInfo]
grep_raw(pattern, path=None, glob=None, ignore_hidden=True) → list[GrepMatch] | str
```

Path semantics: absolute-style normalized internally — `"."`, `"./"`, `""` all
mean root (`"/"`); `"contexts/x.md"` and `"./contexts/x.md"` both become
`"/contexts/x.md"`. `..`, `~`, and embedded NUL bytes are rejected.

## Tests

`tests/test_postgres_backend.py` connects to a real Postgres pointed at by
`CARE_POSTGRES_TEST_URL`. The whole module is skipped when the env var is unset.

```bash
export CARE_POSTGRES_TEST_URL=postgresql://localhost/care_test
uv run pytest tests/test_postgres_backend.py -v
```

## Running `serve_care.py` against this backend

If you're a tester picking up the `care-v2-script-postgres-backend` branch,
here's the minimum you need to configure.

### Prerequisites

1. **Clone the CARE v2 prompts repo** on the `Care_version2` branch:
   ```bash
   git clone git@github.com:NASA-IMPACT/AKD-CARE.git
   cd AKD-CARE && git checkout Care_version2
   ```
2. **Have a Postgres reachable.** Easiest: the akd-labs docker-compose
   (`postgres:postgres@localhost:5432`) — the default DSN already targets it.
   Otherwise spin up your own and set `CARE_POSTGRES_URL`.
3. **Create the dev DB once** (the table inside it is auto-created):
   ```bash
   PGPASSWORD=postgres psql -h localhost -U postgres -d postgres \
     -c "CREATE DATABASE care_dev;"
   ```
4. **OpenAI key** for the default `openai:gpt-5.2` model (or override the
   model with `--model`/`CARE_MODEL`).

### Environment variables

| Var | Required? | Purpose |
|---|---|---|
| `CARE_REPO_PATH` | **yes** — no default | absolute path to your `AKD-CARE` clone |
| `OPENAI_API_KEY` | yes (unless you override the model) | model auth |
| `CARE_POSTGRES_URL` | only if NOT using the akd-labs docker-compose default | libpq DSN |
| `CARE_POSTGRES_POOL_MIN` | optional | min idle pool connections (default `1`) |
| `CARE_POSTGRES_POOL_MAX` | optional | max pool connections (default `10`) |
| `CARE_MODEL` | optional | model id override |
| `CARE_THINKING` | optional | `none\|low\|medium\|high` (default `medium`) |
| `CARE_STORAGE` | optional | `postgres` (default) or `local` |
| `CARE_AGENT_NAME` | optional | sets `--agent-name` default |

### Minimum command sequence

```bash
uv sync
export CARE_REPO_PATH=/path/to/your/AKD-CARE
export OPENAI_API_KEY=sk-...
PGPASSWORD=postgres psql -h localhost -U postgres -d postgres \
  -c "CREATE DATABASE care_dev;"

uv run python3 scripts/serve_care.py --phase 1 --agent-name pg_smoke --port 7932
```

Open `http://127.0.0.1:7932` and start the interview.

### Verify artifacts land in Postgres

```bash
PGPASSWORD=postgres psql -h localhost -U postgres -d care_dev \
  -c "SELECT path, length(content), modified_at
      FROM care_artifacts WHERE workspace='pg_smoke' ORDER BY path;"
```
