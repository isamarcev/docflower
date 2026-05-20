"""Audit-log repository interface."""

from __future__ import annotations

from typing import Protocol

from docflow.domain.entities import AuditAction, AuditLogEntry


class AuditRepository(Protocol):
    def record(self, entry: AuditLogEntry) -> None: ...
    def list_recent(
        self,
        *,
        limit: int = 200,
        actions: list[AuditAction] | None = None,
        document_id: int | None = None,
    ) -> list[AuditLogEntry]: ...
