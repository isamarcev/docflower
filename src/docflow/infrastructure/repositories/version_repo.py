"""SQLite-backed VersionRepository (branches + versions)."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from docflow.domain.entities import Branch, DocumentVersion
from docflow.domain.exceptions import BranchNotFoundError, VersionNotFoundError


class SqliteVersionRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # --- Branches ---

    def add_branch(self, branch: Branch) -> Branch:
        cur = self._conn.execute(
            """
            INSERT INTO branches
              (document_id, name, parent_version_id, created_at, created_by)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                branch.document_id,
                branch.name,
                branch.parent_version_id,
                branch.created_at.isoformat(),
                branch.created_by,
            ),
        )
        branch.id = int(cur.lastrowid or 0)
        return branch

    def list_branches(self, document_id: int) -> list[Branch]:
        rows = self._conn.execute(
            "SELECT * FROM branches WHERE document_id = ? ORDER BY id",
            (document_id,),
        ).fetchall()
        return [_row_to_branch(r) for r in rows]

    def get_branch(self, branch_id: int) -> Branch:
        row = self._conn.execute(
            "SELECT * FROM branches WHERE id = ?", (branch_id,)
        ).fetchone()
        if row is None:
            raise BranchNotFoundError(f"Гілка id={branch_id} не знайдена")
        return _row_to_branch(row)

    def set_head(self, branch_id: int, version_id: int) -> None:
        self._conn.execute(
            "UPDATE branches SET head_version_id = ? WHERE id = ?",
            (version_id, branch_id),
        )

    # --- Versions ---

    def add_version(self, version: DocumentVersion) -> DocumentVersion:
        cur = self._conn.execute(
            """
            INSERT INTO versions
              (document_id, branch_id, label, message, parent_version_id,
               file_path, file_size, sha1, created_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version.document_id,
                version.branch_id,
                version.label,
                version.message,
                version.parent_version_id,
                version.file_path,
                version.file_size,
                version.sha1,
                version.created_at.isoformat(),
                version.created_by,
            ),
        )
        version.id = int(cur.lastrowid or 0)
        return version

    def get_version(self, version_id: int) -> DocumentVersion:
        row = self._conn.execute(
            "SELECT * FROM versions WHERE id = ?", (version_id,)
        ).fetchone()
        if row is None:
            raise VersionNotFoundError(f"Версія id={version_id} не знайдена")
        return _row_to_version(row)

    def list_versions(self, document_id: int) -> list[DocumentVersion]:
        rows = self._conn.execute(
            "SELECT * FROM versions WHERE document_id = ? ORDER BY created_at DESC",
            (document_id,),
        ).fetchall()
        return [_row_to_version(r) for r in rows]

    def list_versions_in_branch(self, branch_id: int) -> list[DocumentVersion]:
        rows = self._conn.execute(
            "SELECT * FROM versions WHERE branch_id = ? ORDER BY created_at DESC",
            (branch_id,),
        ).fetchall()
        return [_row_to_version(r) for r in rows]

    def get_head(
        self, document_id: int, branch_name: str = "main"
    ) -> DocumentVersion | None:
        row = self._conn.execute(
            """
            SELECT v.* FROM versions v
            JOIN branches b ON b.head_version_id = v.id
            WHERE b.document_id = ? AND b.name = ?
            """,
            (document_id, branch_name),
        ).fetchone()
        return _row_to_version(row) if row else None


def _row_to_branch(row: sqlite3.Row) -> Branch:
    return Branch(
        id=row["id"],
        document_id=row["document_id"],
        name=row["name"],
        parent_version_id=row["parent_version_id"],
        created_at=datetime.fromisoformat(row["created_at"]),
        created_by=row["created_by"],
        is_head=row["head_version_id"] is not None,
    )


def _row_to_version(row: sqlite3.Row) -> DocumentVersion:
    return DocumentVersion(
        id=row["id"],
        document_id=row["document_id"],
        branch_id=row["branch_id"],
        label=row["label"],
        message=row["message"],
        parent_version_id=row["parent_version_id"],
        file_path=row["file_path"],
        file_size=row["file_size"],
        sha1=row["sha1"],
        created_at=datetime.fromisoformat(row["created_at"]),
        created_by=row["created_by"],
    )
