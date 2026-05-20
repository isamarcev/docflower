"""Import a brand-new document with its initial version (v1.0) in branch ``main``."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from docflow.application.dto import ImportDocumentInput
from docflow.application.interfaces import FileStorage
from docflow.application.interfaces.repositories import (
    AuditRepository,
    DocumentRepository,
    TagRepository,
    VersionRepository,
)
from docflow.domain.entities import (
    AuditAction,
    AuditLogEntry,
    Branch,
    Document,
    DocumentType,
    DocumentVersion,
)


@dataclass(slots=True)
class ImportDocument:
    documents: DocumentRepository
    versions: VersionRepository
    tags: TagRepository
    audit: AuditRepository
    storage: FileStorage

    def __call__(self, cmd: ImportDocumentInput) -> Document:
        doc_type = DocumentType.from_filename(cmd.name)
        now = datetime.now()

        doc = self.documents.add(
            Document(
                id=None,
                name=cmd.name,
                doc_type=doc_type,
                created_at=now,
                updated_at=now,
                created_by=cmd.actor,
                description=cmd.description,
            )
        )
        assert doc.id is not None
        for tag_id in cmd.tag_ids:
            self.tags.attach(doc.id, tag_id)

        main = self.versions.add_branch(
            Branch(
                id=None,
                document_id=doc.id,
                name="main",
                created_at=now,
                created_by=cmd.actor,
                parent_version_id=None,
                is_head=True,
            )
        )
        assert main.id is not None

        rel_path, size, sha1 = self.storage.save(cmd.source_path, document_type=doc_type.value)
        version = self.versions.add_version(
            DocumentVersion(
                id=None,
                document_id=doc.id,
                branch_id=main.id,
                label="v1.0",
                message="Початкова версія",
                parent_version_id=None,
                file_path=rel_path,
                file_size=size,
                sha1=sha1,
                created_at=now,
                created_by=cmd.actor,
            )
        )
        assert version.id is not None
        self.versions.set_head(main.id, version.id)

        self.audit.record(
            AuditLogEntry(
                id=None,
                occurred_at=now,
                actor=cmd.actor,
                action=AuditAction.DOCUMENT_IMPORTED,
                document_id=doc.id,
                details=f"{cmd.name} → v1.0",
            )
        )
        return doc
