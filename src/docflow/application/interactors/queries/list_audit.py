"""List recent audit-log entries for the audit-log screen."""

from __future__ import annotations

from dataclasses import dataclass

from docflow.application.dto import AuditRow
from docflow.application.interfaces.repositories import AuditRepository
from docflow.domain.entities import AuditAction


@dataclass(slots=True)
class ListAudit:
    audit: AuditRepository

    def __call__(
        self,
        *,
        limit: int = 200,
        actions: list[AuditAction] | None = None,
        document_id: int | None = None,
    ) -> list[AuditRow]:
        entries = self.audit.list_recent(limit=limit, actions=actions, document_id=document_id)
        return [
            AuditRow(
                occurred_at=e.occurred_at,
                actor=e.actor,
                action=e.action,
                details=e.details,
            )
            for e in entries
        ]
