"""SQLite schema bootstrap + light migration from v1 to v2.

Schema v2 introduces the ``document_files`` table; ``versions`` references it
via ``file_id`` instead of carrying ``file_path/file_size/sha1`` inline.

Migration v1→v2 runs once on app start when an old DB is detected (the
``versions`` table still has the ``file_path`` column). It is content-aware:
versions that share the same sha1 collapse into a single document_files row,
so the storage layer can deduplicate blobs.
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

CREATE TABLE IF NOT EXISTS document_files (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id   INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    relative_path TEXT    NOT NULL,
    size_bytes    INTEGER NOT NULL,
    sha1          TEXT    NOT NULL,
    created_at    TEXT    NOT NULL
);

-- Deduplication index: per-document, one row per sha1.
CREATE UNIQUE INDEX IF NOT EXISTS idx_document_files_dedupe
    ON document_files (document_id, sha1);

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
    file_id           INTEGER NOT NULL REFERENCES document_files(id) ON DELETE RESTRICT,
    label             TEXT    NOT NULL,
    message           TEXT    NOT NULL DEFAULT '',
    parent_version_id INTEGER REFERENCES versions(id) ON DELETE SET NULL,
    created_at        TEXT    NOT NULL,
    created_by        TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_versions_document ON versions (document_id);
CREATE INDEX IF NOT EXISTS idx_versions_branch ON versions (branch_id);
CREATE INDEX IF NOT EXISTS idx_versions_parent ON versions (parent_version_id);
CREATE INDEX IF NOT EXISTS idx_versions_file ON versions (file_id);

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
    """Create tables. If an old (v1) versions table is found, migrate it first."""
    if _needs_v1_to_v2_migration(conn):
        _migrate_v1_to_v2(conn)
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def _needs_v1_to_v2_migration(conn: sqlite3.Connection) -> bool:
    """Old schema is detected by the ``file_path`` column on ``versions``."""
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='versions'"
    ).fetchone()
    if row is None:
        return False  # fresh DB
    cols = {r[1] for r in conn.execute("PRAGMA table_info(versions)").fetchall()}
    return "file_path" in cols and "file_id" not in cols


def _migrate_v1_to_v2(conn: sqlite3.Connection) -> None:
    """Move file_path/file_size/sha1 from versions into document_files; dedupe by sha1."""
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = OFF")
    cur.execute("BEGIN")
    try:
        # 1) Ensure document_files exists.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS document_files (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id   INTEGER NOT NULL,
                relative_path TEXT    NOT NULL,
                size_bytes    INTEGER NOT NULL,
                sha1          TEXT    NOT NULL,
                created_at    TEXT    NOT NULL
            )
            """
        )

        # 2) Build (document_id, sha1) -> file_id, inserting deduplicated rows.
        rows = cur.execute(
            """
            SELECT id, document_id, file_path, file_size, sha1, created_at
            FROM versions
            ORDER BY id
            """
        ).fetchall()
        file_id_by_key: dict[tuple[int, str], int] = {}
        version_to_file: dict[int, int] = {}
        for vid, doc_id, file_path, file_size, sha1, created_at in rows:
            key = (doc_id, sha1)
            if key not in file_id_by_key:
                cur.execute(
                    "INSERT INTO document_files "
                    "(document_id, relative_path, size_bytes, sha1, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (doc_id, file_path, file_size, sha1, created_at),
                )
                file_id_by_key[key] = int(cur.lastrowid or 0)
            version_to_file[vid] = file_id_by_key[key]

        # 3) Rebuild versions table with new shape.
        cur.execute(
            """
            CREATE TABLE versions_new (
                id                INTEGER PRIMARY KEY,
                document_id       INTEGER NOT NULL,
                branch_id         INTEGER NOT NULL,
                file_id           INTEGER NOT NULL,
                label             TEXT    NOT NULL,
                message           TEXT    NOT NULL DEFAULT '',
                parent_version_id INTEGER,
                created_at        TEXT    NOT NULL,
                created_by        TEXT    NOT NULL
            )
            """
        )
        for row in cur.execute(
            "SELECT id, document_id, branch_id, label, message, "
            "parent_version_id, created_at, created_by FROM versions"
        ).fetchall():
            (vid, doc_id, br_id, label, message,
             parent_vid, created_at, created_by) = row
            file_id = version_to_file.get(vid)
            if file_id is None:
                # Should not happen, but bail loudly rather than silently corrupt.
                raise RuntimeError(f"Migration failed: no file row for version {vid}")
            cur.execute(
                "INSERT INTO versions_new "
                "(id, document_id, branch_id, file_id, label, message, "
                "parent_version_id, created_at, created_by) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (vid, doc_id, br_id, file_id, label, message,
                 parent_vid, created_at, created_by),
            )

        cur.execute("DROP TABLE versions")
        cur.execute("ALTER TABLE versions_new RENAME TO versions")

        cur.execute("COMMIT")
    except Exception:
        cur.execute("ROLLBACK")
        raise
    finally:
        cur.execute("PRAGMA foreign_keys = ON")
