"""List-tags query — feeds the sidebar tag panel and the tag-management dialog."""

from __future__ import annotations

from dataclasses import dataclass

from docflow.application.dto import TagView
from docflow.application.interfaces.repositories import TagRepository


@dataclass(slots=True)
class ListTags:
    tags: TagRepository

    def __call__(self) -> list[TagView]:
        out: list[TagView] = []
        for t in self.tags.list_all():
            assert t.id is not None
            out.append(
                TagView(
                    id=t.id,
                    name=t.name,
                    color=t.color,
                    description=t.description,
                    document_count=self.tags.count_documents(t.id),
                )
            )
        return out
