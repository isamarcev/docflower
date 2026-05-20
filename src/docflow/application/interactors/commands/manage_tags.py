"""Tag CRUD and attach/detach commands.

Bundled here because they're tiny and always come together in the UI:
tag manager dialog uses Create/Update/Delete; document card uses Attach/Detach.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from docflow.application.interfaces.repositories import (
    AuditRepository,
    DocumentRepository,
    TagRepository,
)
from docflow.domain.entities import AuditAction, AuditLogEntry, Tag


@dataclass(slots=True)
class CreateTag:
    tags: TagRepository

    def __call__(self, *, name: str, color: str, description: str = "") -> Tag:
        return self.tags.add(Tag(id=None, name=name, color=color, description=description))


@dataclass(slots=True)
class UpdateTag:
    tags: TagRepository

    def __call__(self, *, tag_id: int, name: str, color: str, description: str) -> Tag:
        tag = self.tags.get(tag_id)
        tag.name = name
        tag.color = color
        tag.description = description
        self.tags.update(tag)
        return tag


@dataclass(slots=True)
class DeleteTag:
    tags: TagRepository

    def __call__(self, tag_id: int) -> None:
        self.tags.delete(tag_id)


@dataclass(slots=True)
class AttachTag:
    tags: TagRepository
    documents: DocumentRepository
    audit: AuditRepository

    def __call__(self, *, document_id: int, tag_id: int, actor: str) -> None:
        self.tags.attach(document_id, tag_id)
        doc = self.documents.get(document_id)
        tag = self.tags.get(tag_id)
        self.audit.record(
            AuditLogEntry(
                id=None,
                occurred_at=datetime.now(),
                actor=actor,
                action=AuditAction.TAG_ADDED,
                document_id=document_id,
                details=f"{doc.name}: +{tag.name}",
            )
        )


@dataclass(slots=True)
class DetachTag:
    tags: TagRepository
    documents: DocumentRepository
    audit: AuditRepository

    def __call__(self, *, document_id: int, tag_id: int, actor: str) -> None:
        self.tags.detach(document_id, tag_id)
        doc = self.documents.get(document_id)
        tag = self.tags.get(tag_id)
        self.audit.record(
            AuditLogEntry(
                id=None,
                occurred_at=datetime.now(),
                actor=actor,
                action=AuditAction.TAG_REMOVED,
                document_id=document_id,
                details=f"{doc.name}: −{tag.name}",
            )
        )
