"""SQLite schema bootstrap.

Lightweight: no migrations framework yet. Tables are created with IF NOT EXISTS
on every app start; future schema changes will go through a numbered-migration
script (see §8 of CLAUDE.md).
"""

from __future__ import annotations

import sqlite3

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS documents (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL,
    doc_type     TEXT    NOT NULL CHECK (doc_type IN ('docx', 'xlsx', 'xls', 'pdf')),
    created_at   TEXT    NOT NULL,
    updated_at   TEXT    NOT NULL,
    created_by   TEXT    NOT NULL,
    description  TEXT    NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_documents_name ON documents (name COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS branches (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id       INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    name              TEXT    NOT NULL,
    parent_version_id INTEGER REFERENCES versions(id) ON DELETE SET NULL,
    created_at        TEXT    NOT NULL,
    created_by        TEXT    NOT NULL,
    head_version_id   INTEGER REFERENCES versions(id) ON DELETE SET NULL,
    UNIQUE (document_id, name)
);

CREATE INDEX IF NOT EXISTS idx_branches_document ON branches (document_id);

CREATE TABLE IF NOT EXISTS versions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id       INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    branch_id         INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    label             TEXT    NOT NULL,
    message           TEXT    NOT NULL DEFAULT '',
    parent_version_id INTEGER REFERENCES versions(id) ON DELETE SET NULL,
    file_path         TEXT    NOT NULL,
    file_size         INTEGER NOT NULL,
    sha1              TEXT    NOT NULL,
    created_at        TEXT    NOT NULL,
    created_by        TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_versions_document ON versions (document_id);
CREATE INDEX IF NOT EXISTS idx_versions_branch ON versions (branch_id);
CREATE INDEX IF NOT EXISTS idx_versions_parent ON versions (parent_version_id);

CREATE TABLE IF NOT EXISTS tags (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    color       TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS document_tags (
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tag_id      INTEGER NOT NULL REFERENCES tags(id)      ON DELETE CASCADE,
    PRIMARY KEY (document_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_document_tags_tag ON document_tags (tag_id);

CREATE TABLE IF NOT EXISTS audit_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at  TEXT    NOT NULL,
    actor        TEXT    NOT NULL,
    action       TEXT    NOT NULL,
    document_id  INTEGER REFERENCES documents(id) ON DELETE SET NULL,
    details      TEXT    NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_audit_log_occurred ON audit_log (occurred_at DESC);
"""


def initialize_schema(conn: sqlite3.Connection) -> None:
    """Create all tables/indexes if they don't already exist."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()
