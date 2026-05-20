"""SQLite-backed DocumentRepository implementation."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from docflow.domain.entities import Document, DocumentType
from docflow.domain.exceptions import DocumentNotFoundError


class SqliteDocumentRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, document: Document) -> Document:
        cur = self._conn.execute(
            """
            INSERT INTO documents (name, doc_type, created_at, updated_at, created_by, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                document.name,
                document.doc_type.value,
                document.created_at.isoformat(),
                document.updated_at.isoformat(),
                document.created_by,
                document.description,
            ),
        )
        document.id = int(cur.lastrowid or 0)
        return document

    def get(self, document_id: int) -> Document:
        row = self._conn.execute(
            "SELECT * FROM documents WHERE id = ?", (document_id,)
        ).fetchone()
        if row is None:
            raise DocumentNotFoundError(f"Документ id={document_id} не знайдено")
        return _row_to_document(row)

    def list_all(self, *, name_query: str | None = None) -> list[Document]:
        if name_query:
            rows = self._conn.execute(
                "SELECT * FROM documents WHERE name LIKE ? COLLATE NOCASE ORDER BY updated_at DESC",
                (f"%{name_query}%",),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM documents ORDER BY updated_at DESC"
            ).fetchall()
        return [_row_to_document(r) for r in rows]

    def update(self, document: Document) -> None:
        if document.id is None:
            raise ValueError("Cannot update document without id")
        self._conn.execute(
            """
            UPDATE documents
               SET name = ?, description = ?, updated_at = ?
             WHERE id = ?
            """,
            (
                document.name,
                document.description,
                document.updated_at.isoformat(),
                document.id,
            ),
        )

    def delete(self, document_id: int) -> None:
        # FK cascades clean up versions, branches, document_tags.
        self._conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))


def _row_to_document(row: sqlite3.Row) -> Document:
    return Document(
        id=row["id"],
        name=row["name"],
        doc_type=DocumentType(row["doc_type"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        created_by=row["created_by"],
        description=row["description"],
    )
