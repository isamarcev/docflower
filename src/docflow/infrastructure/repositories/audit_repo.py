"""SQLite-backed AuditRepository."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from docflow.domain.entities import AuditAction, AuditLogEntry


class SqliteAuditRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def record(self, entry: AuditLogEntry) -> None:
        self._conn.execute(
            """
            INSERT INTO audit_log (occurred_at, actor, action, document_id, details)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                entry.occurred_at.isoformat(),
                entry.actor,
                entry.action.value,
                entry.document_id,
                entry.details,
            ),
        )

    def list_recent(
        self,
        *,
        limit: int = 200,
        actions: list[AuditAction] | None = None,
        document_id: int | None = None,
    ) -> list[AuditLogEntry]:
        where: list[str] = []
        params: list[object] = []
        if actions:
            placeholders = ",".join("?" * len(actions))
            where.append(f"action IN ({placeholders})")
            params.extend(a.value for a in actions)
        if document_id is not None:
            where.append("document_id = ?")
            params.append(document_id)

        sql = "SELECT * FROM audit_log"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY occurred_at DESC LIMIT ?"
        params.append(limit)

        rows = self._conn.execute(sql, params).fetchall()
        return [
            AuditLogEntry(
                id=r["id"],
                occurred_at=datetime.fromisoformat(r["occurred_at"]),
                actor=r["actor"],
                action=AuditAction(r["action"]),
                document_id=r["document_id"],
                details=r["details"],
            )
            for r in rows
        ]
