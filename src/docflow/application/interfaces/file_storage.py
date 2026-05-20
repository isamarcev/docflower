"""File storage interface — abstracts the filesystem from use-cases."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class FileStorage(Protocol):
    def save(self, source_path: Path, *, document_type: str) -> tuple[str, int, str]:
        """Copy ``source_path`` into managed storage.

        Returns ``(relative_path, size_bytes, sha1_hex)`` so the caller can persist
        these attributes on the DocumentVersion.
        """
        ...

    def resolve(self, relative_path: str) -> Path:
        """Translate a stored relative_path back to an absolute filesystem path."""
        ...

    def delete(self, relative_path: str) -> None: ...
