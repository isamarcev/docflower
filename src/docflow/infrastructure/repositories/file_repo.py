"""SQLite-backed FileRepository."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from docflow.domain.entities import DocumentFile


class SqliteFileRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, file: DocumentFile) -> DocumentFile:
        cur = self._conn.execute(
            """
            INSERT INTO document_files
              (document_id, relative_path, size_bytes, sha1, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                file.document_id,
                file.relative_path,
                file.size_bytes,
                file.sha1,
                file.created_at.isoformat(),
            ),
        )
        file.id = int(cur.lastrowid or 0)
        return file

    def get(self, file_id: int) -> DocumentFile:
        row = self._conn.execute(
            "SELECT * FROM document_files WHERE id = ?", (file_id,)
        ).fetchone()
        if row is None:
            raise LookupError(f"DocumentFile id={file_id} not found")
        return _row_to_file(row)

    def find_by_sha1(self, document_id: int, sha1: str) -> DocumentFile | None:
        row = self._conn.execute(
            "SELECT * FROM document_files WHERE document_id = ? AND sha1 = ?",
            (document_id, sha1),
        ).fetchone()
        return _row_to_file(row) if row else None

    def list_for_document(self, document_id: int) -> list[DocumentFile]:
        rows = self._conn.execute(
            "SELECT * FROM document_files WHERE document_id = ? ORDER BY id",
            (document_id,),
        ).fetchall()
        return [_row_to_file(r) for r in rows]

    def count_versions_using(self, file_id: int) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS c FROM versions WHERE file_id = ?", (file_id,)
        ).fetchone()
        return int(row["c"]) if row else 0


def _row_to_file(row: sqlite3.Row) -> DocumentFile:
    return DocumentFile(
        id=row["id"],
        document_id=row["document_id"],
        relative_path=row["relative_path"],
        size_bytes=row["size_bytes"],
        sha1=row["sha1"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )
