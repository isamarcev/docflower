"""List-documents query — feeds the main document table."""

from __future__ import annotations

from dataclasses import dataclass

from docflow.application.dto import DocumentListRow, TagView
from docflow.application.interfaces.repositories import (
    DocumentRepository,
    TagRepository,
    VersionRepository,
)


@dataclass(slots=True)
class ListDocuments:
    documents: DocumentRepository
    versions: VersionRepository
    tags: TagRepository

    def __call__(
        self,
        *,
        name_query: str | None = None,
        tag_id: int | None = None,
    ) -> list[DocumentListRow]:
        rows: list[DocumentListRow] = []
        for doc in self.documents.list_all(name_query=name_query):
            assert doc.id is not None  # repo guarantees this
            doc_tags = self.tags.list_for_document(doc.id)
            # Filter by tag if requested
            if tag_id is not None and not any(t.id == tag_id for t in doc_tags):
                continue
            branches = self.versions.list_branches(doc.id)
            head = self.versions.get_head(doc.id)
            tag_views = [
                TagView(id=t.id or 0, name=t.name, color=t.color, description=t.description)
                for t in doc_tags
            ]
            rows.append(
                DocumentListRow(
                    id=doc.id,
                    name=doc.name,
                    doc_type=doc.doc_type,
                    head_label=head.label if head else "—",
                    branches_count=len(branches),
                    tags=tag_views,
                    updated_at=doc.updated_at,
                    author=doc.created_by,
                )
            )
        return rows
