# PostgresBackend

Drop-in replacement for `pydantic_ai_backends.LocalBackend` that persists CARE v2
artifact workspaces to Postgres instead of the local filesystem.

Implements `pydantic_ai_backends.protocol.BackendProtocol`:
`ls_info`, `_read_bytes`, `read`, `write`, `edit`, `glob_info`, `grep_raw`.

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

## Usage

```python
from scripts.postgres_backend import PostgresBackend

backend = PostgresBackend(workspace="my_agent")
backend.write("/scope.md", "# Scope\n\n…")
print(backend.read("/scope.md"))
```

## Tests

`tests/test_postgres_backend.py` connects to a real Postgres pointed at by
`CARE_POSTGRES_TEST_URL`. The whole module is skipped when the env var is unset.

```bash
export CARE_POSTGRES_TEST_URL=postgresql://localhost/care_test
uv run pytest tests/test_postgres_backend.py -v
```
