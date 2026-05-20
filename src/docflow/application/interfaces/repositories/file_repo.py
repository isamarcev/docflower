"""DocumentFile repository interface."""

from __future__ import annotations

from typing import Protocol

from docflow.domain.entities import DocumentFile


class FileRepository(Protocol):
    def add(self, file: DocumentFile) -> DocumentFile: ...
    def get(self, file_id: int) -> DocumentFile: ...
    def find_by_sha1(self, document_id: int, sha1: str) -> DocumentFile | None:
        """Return an existing blob for this document with the same sha1, if any.

        Used by import/create-version to deduplicate: if the user re-imports
        an unchanged file, we reuse the existing DocumentFile instead of
        creating a new one.
        """
        ...

    def list_for_document(self, document_id: int) -> list[DocumentFile]: ...
    def count_versions_using(self, file_id: int) -> int:
        """How many DocumentVersion rows still point at this file.

        Used during delete to decide whether the blob on disk can be unlinked.
        """
        ...
