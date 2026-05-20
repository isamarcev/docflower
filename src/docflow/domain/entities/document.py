"""Document entity — top-level file unit (without versions/branches)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Supported document formats. Anything else is rejected at import."""

    DOCX = "docx"
    XLSX = "xlsx"
    XLS = "xls"
    PDF = "pdf"

    @classmethod
    def from_filename(cls, filename: str) -> "DocumentType":
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        try:
            return cls(ext)
        except ValueError as e:
            raise ValueError(f"Непідтримуваний тип файлу: .{ext}") from e


@dataclass(slots=True)
class Document:
    id: int | None
    name: str
    doc_type: DocumentType
    created_at: datetime
    updated_at: datetime
    created_by: str
    description: str = ""
    # IDs of tags attached. Names/colors resolved via TagRepository.
    tag_ids: list[int] = field(default_factory=list)
