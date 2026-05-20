"""Aggregate everything the document-card page renders, in one call."""

from __future__ import annotations

from dataclasses import dataclass

from docflow.application.dto import (
    AuditRow,
    DocumentDetails,
    TagView,
    VersionNode,
)
from docflow.application.interfaces.repositories import (
    AuditRepository,
    DocumentRepository,
    TagRepository,
    VersionRepository,
)


@dataclass(slots=True)
class GetDocumentDetails:
    documents: DocumentRepository
    versions: VersionRepository
    tags: TagRepository
    audit: AuditRepository

    def __call__(self, document_id: int) -> DocumentDetails:
        doc = self.documents.get(document_id)
        assert doc.id is not None

        branches = self.versions.list_branches(doc.id)
        head = self.versions.get_head(doc.id)
        all_versions = self.versions.list_versions(doc.id)

        # Build tag views
        tag_views = [
            TagView(id=t.id or 0, name=t.name, color=t.color, description=t.description)
            for t in self.tags.list_for_document(doc.id)
        ]

        # Recent versions: first 5
        recent_versions: list[VersionNode] = []
        branch_names = {b.id: b.name for b in branches}
        for v in all_versions[:5]:
            recent_versions.append(
                VersionNode(
                    version_id=v.id or 0,
                    label=v.label,
                    branch_id=v.branch_id,
                    branch_name=branch_names.get(v.branch_id, "?"),
                    parent_version_id=v.parent_version_id,
                    message=v.message,
                    created_at=v.created_at,
                    created_by=v.created_by,
                    is_head=(head is not None and head.id == v.id),
                )
            )

        # Recent audit: filter by document_id
        audit_entries = self.audit.list_recent(limit=5, document_id=doc.id)
        recent_audit = [
            AuditRow(
                occurred_at=e.occurred_at, actor=e.actor, action=e.action, details=e.details
            )
            for e in audit_entries
        ]

        return DocumentDetails(
            id=doc.id,
            name=doc.name,
            doc_type=doc.doc_type,
            description=doc.description,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            created_by=doc.created_by,
            size_bytes=head.file_size if head else 0,
            sha1=head.sha1 if head else "",
            head_label=head.label if head else "—",
            branch_name="main",
            versions_total=len(all_versions),
            branches_total=len(branches),
            file_path=head.file_path if head else "",
            tags=tag_views,
            recent_versions=recent_versions,
            recent_audit=recent_audit,
        )
