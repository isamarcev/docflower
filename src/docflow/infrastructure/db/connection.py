"""SQLite connection factory.

One ``sqlite3.Connection`` is shared per process. PyQt is single-threaded for UI;
all DB work happens on that same thread, so we don't need a pool.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from docflow.infrastructure.db.schema import initialize_schema


def open_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(
        str(db_path),
        detect_types=sqlite3.PARSE_DECLTYPES,
        isolation_level=None,  # autocommit; we manage transactions explicitly
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    initialize_schema(conn)
    return conn
