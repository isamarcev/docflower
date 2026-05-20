"""SQLite-backed TagRepository."""

from __future__ import annotations

import sqlite3

from docflow.domain.entities import Tag
from docflow.domain.exceptions import DuplicateTagError, TagNotFoundError


class SqliteTagRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, tag: Tag) -> Tag:
        try:
            cur = self._conn.execute(
                "INSERT INTO tags (name, color, description) VALUES (?, ?, ?)",
                (tag.name, tag.color, tag.description),
            )
        except sqlite3.IntegrityError as e:
            raise DuplicateTagError(f"Тег '{tag.name}' вже існує") from e
        tag.id = int(cur.lastrowid or 0)
        return tag

    def get(self, tag_id: int) -> Tag:
        row = self._conn.execute("SELECT * FROM tags WHERE id = ?", (tag_id,)).fetchone()
        if row is None:
            raise TagNotFoundError(f"Тег id={tag_id} не знайдено")
        return _row_to_tag(row)

    def list_all(self) -> list[Tag]:
        rows = self._conn.execute("SELECT * FROM tags ORDER BY name").fetchall()
        return [_row_to_tag(r) for r in rows]

    def update(self, tag: Tag) -> None:
        if tag.id is None:
            raise ValueError("Cannot update tag without id")
        self._conn.execute(
            "UPDATE tags SET name = ?, color = ?, description = ? WHERE id = ?",
            (tag.name, tag.color, tag.description, tag.id),
        )

    def delete(self, tag_id: int) -> None:
        self._conn.execute("DELETE FROM tags WHERE id = ?", (tag_id,))

    def list_for_document(self, document_id: int) -> list[Tag]:
        rows = self._conn.execute(
            """
            SELECT t.* FROM tags t
            JOIN document_tags dt ON dt.tag_id = t.id
            WHERE dt.document_id = ?
            ORDER BY t.name
            """,
            (document_id,),
        ).fetchall()
        return [_row_to_tag(r) for r in rows]

    def attach(self, document_id: int, tag_id: int) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO document_tags (document_id, tag_id) VALUES (?, ?)",
            (document_id, tag_id),
        )

    def detach(self, document_id: int, tag_id: int) -> None:
        self._conn.execute(
            "DELETE FROM document_tags WHERE document_id = ? AND tag_id = ?",
            (document_id, tag_id),
        )

    def count_documents(self, tag_id: int) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS c FROM document_tags WHERE tag_id = ?", (tag_id,)
        ).fetchone()
        return int(row["c"]) if row else 0


def _row_to_tag(row: sqlite3.Row) -> Tag:
    return Tag(
        id=row["id"],
        name=row["name"],
        color=row["color"],
        description=row["description"],
    )
