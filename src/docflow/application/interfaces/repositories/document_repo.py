"""Document repository interface.

Implementations live in ``infrastructure/repositories``. Application code depends
only on this Protocol — that is the Dependency Inversion boundary.
"""

from __future__ import annotations

from typing import Protocol

from docflow.domain.entities import Document


class DocumentRepository(Protocol):
    def add(self, document: Document) -> Document:
        """Persist a new document. Returns the document with ``id`` populated."""
        ...

    def get(self, document_id: int) -> Document:
        """Fetch a document by id or raise DocumentNotFoundError."""
        ...

    def list_all(self, *, name_query: str | None = None) -> list[Document]:
        """Return all documents, optionally filtered by case-insensitive name substring."""
        ...

    def update(self, document: Document) -> None:
        """Update mutable fields (name, description, tags, updated_at)."""
        ...

    def delete(self, document_id: int) -> None:
        """Remove the document and cascade (versions, branches, tag-links)."""
        ...
