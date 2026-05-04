-- PostgresBackend schema for CARE v2 artifact workspace.
-- Mirrors StateBackend's flat-key model: paths are normalized absolute-style
-- ("/scope.md", "/contexts/index.md"); directories are implicit. The
-- FileInfo `size` field exposed by the backend is computed on the fly
-- (codepoint count of content excluding newlines) to match StateBackend
-- semantics, so no separate size column is needed.

CREATE TABLE IF NOT EXISTS care_artifacts (
    workspace    TEXT        NOT NULL,
    path         TEXT        NOT NULL,
    content      TEXT        NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    modified_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace, path)
);

CREATE INDEX IF NOT EXISTS care_artifacts_workspace_path_prefix
    ON care_artifacts (workspace, path text_pattern_ops);

-- Forward-compat: earlier dev iterations stored a NOT NULL `size_bytes`
-- column. Drop it idempotently so older tables converge with the current
-- schema without manual migration.
ALTER TABLE care_artifacts DROP COLUMN IF EXISTS size_bytes;
