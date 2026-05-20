"""Seed data for the first run — gives the UI something to render.

Only runs if the documents table is empty. Idempotent on subsequent launches.
"""

from __future__ import annotations

import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from docflow.application.interfaces import FileStorage
from docflow.domain.entities import (
    AuditAction,
    AuditLogEntry,
    Branch,
    Document,
    DocumentType,
    DocumentVersion,
    Tag,
)
from docflow.infrastructure.repositories.audit_repo import SqliteAuditRepository
from docflow.infrastructure.repositories.document_repo import SqliteDocumentRepository
from docflow.infrastructure.repositories.tag_repo import SqliteTagRepository
from docflow.infrastructure.repositories.version_repo import SqliteVersionRepository

def _default_description(name: str) -> str:
    """Lightweight stub-description so seeded cards aren't empty."""
    base = name.rsplit(".", 1)[0].replace("_", " ")
    return f"{base}. Сидоване значення для демонстрації картки документа."


DEFAULT_TAGS: list[tuple[str, str, str]] = [
    ("акт", "yellow", "Документи-акти будь-якого типу"),
    ("затверджено", "mint", "Документи з підписом і затвердженням"),
    ("draft", "gray", "Чернетки, ще не затверджені"),
    ("наказ", "pink", "Накази керівництва"),
    ("шаблон", "blue", "Шаблони для створення нових документів"),
    ("ОЗ", "purple", "Основні засоби"),
    ("2024", "orange", "Документи 2024 року"),
    ("Q4", "yellow", "Четвертий квартал"),
    ("МШП", "mint", "Малоцінні швидкозношувані предмети"),
]


def seed_if_empty(conn: sqlite3.Connection, storage: FileStorage, *, actor: str) -> None:
    row = conn.execute("SELECT COUNT(*) AS c FROM documents").fetchone()
    if row and row["c"] > 0:
        return

    docs = SqliteDocumentRepository(conn)
    versions = SqliteVersionRepository(conn)
    tags_repo = SqliteTagRepository(conn)
    audit = SqliteAuditRepository(conn)

    tag_ids: dict[str, int] = {}
    for name, color, description in DEFAULT_TAGS:
        tag = tags_repo.add(Tag(id=None, name=name, color=color, description=description))
        assert tag.id is not None
        tag_ids[name] = tag.id

    samples: list[tuple[str, list[str]]] = [
        ("Акт_списання_2024-Q4.docx", ["Q4", "акт", "затверджено"]),
        ("Інвентаризація_склад_А.xlsx", ["draft"]),
        ("Наказ_№142_про_комісію.pdf", ["наказ", "затверджено"]),
        ("Список_основних_засобів.xls", ["ОЗ"]),
        ("Протокол_засідання_05.docx", ["draft"]),
        ("Пояснювальна_до_акту.docx", ["акт"]),
        ("Розрахунок_зносу_2024.xlsx", ["2024"]),
        ("Звіт_по_МШП.pdf", ["МШП"]),
        ("Шаблон_акту_списання.docx", ["шаблон", "акт"]),
        ("Реєстр_договорів_2024.xlsx", ["2024"]),
    ]

    base_time = datetime.now() - timedelta(days=20)
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        for i, (name, tag_names) in enumerate(samples):
            doc_type = DocumentType.from_filename(name)
            created = base_time + timedelta(days=i, hours=i)
            doc = docs.add(
                Document(
                    id=None,
                    name=name,
                    doc_type=doc_type,
                    created_at=created,
                    updated_at=created + timedelta(hours=2),
                    created_by=actor,
                    description=_default_description(name),
                )
            )
            assert doc.id is not None
            for t in tag_names:
                tags_repo.attach(doc.id, tag_ids[t])

            branch = versions.add_branch(
                Branch(
                    id=None,
                    document_id=doc.id,
                    name="main",
                    created_at=created,
                    created_by=actor,
                    parent_version_id=None,
                    is_head=True,
                )
            )
            assert branch.id is not None

            # Dummy file in storage so size/sha1 are populated
            placeholder = tmp / name
            placeholder.write_bytes(b"DocFlow placeholder content\n")
            rel_path, size, sha1 = storage.save(placeholder, document_type=doc_type.value)

            version = versions.add_version(
                DocumentVersion(
                    id=None,
                    document_id=doc.id,
                    branch_id=branch.id,
                    label="v1.0",
                    message="Початкова версія",
                    parent_version_id=None,
                    file_path=rel_path,
                    file_size=size,
                    sha1=sha1,
                    created_at=created + timedelta(hours=1),
                    created_by=actor,
                )
            )
            assert version.id is not None
            versions.set_head(branch.id, version.id)

            audit.record(
                AuditLogEntry(
                    id=None,
                    occurred_at=created + timedelta(hours=1),
                    actor=actor,
                    action=AuditAction.DOCUMENT_IMPORTED,
                    document_id=doc.id,
                    details=f"{name} → v1.0",
                )
            )
