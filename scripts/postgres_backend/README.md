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

1. Opens a `psycopg` connection (DSN from `conninfo=`, env `CARE_POSTGRES_URL`,
   or the default `postgresql://postgres:postgres@localhost:5432/care_dev`).
2. Runs the bundled [`schema.sql`](./schema.sql) — `CREATE TABLE IF NOT EXISTS`,
   so it's safe on every start. No alembic, no separate migration step.
3. Returns a ready-to-use object that conforms to `BackendProtocol`, so anywhere
   `LocalBackend` works (e.g. `pydantic_ai_backends.ConsoleCapability`),
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

## Schema

Single table, multi-tenant via the `workspace` column. See [`schema.sql`](./schema.sql).

```sql
CREATE TABLE IF NOT EXISTS care_artifacts (
    workspace    TEXT        NOT NULL,
    path         TEXT        NOT NULL,           -- normalized "/scope.md"
    content      TEXT        NOT NULL,
    size_bytes   INTEGER     NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    modified_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace, path)
);
```

Directories are implicit — derived from path prefix grouping in `ls_info`.

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
    workspace: str,                # tenant key (= agent_name)
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
`"/contexts/x.md"`. `..` and `~` are rejected.

## Tests

`tests/test_postgres_backend.py` connects to a real Postgres pointed at by
`CARE_POSTGRES_TEST_URL`. The whole module is skipped when the env var is unset.

```bash
export CARE_POSTGRES_TEST_URL=postgresql://localhost/care_test
uv run pytest tests/test_postgres_backend.py -v
```
