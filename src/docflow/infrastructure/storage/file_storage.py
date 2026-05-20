"""Local filesystem implementation of the FileStorage interface.

Files are stored under ``<root>/<doc_type>/<yyyy>/<mm>/<uuid>.<ext>``.
The relative path is what we persist in the DB; absolute paths are resolved on read.
"""

from __future__ import annotations

import hashlib
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from docflow.domain.exceptions import StorageError


class LocalFileStorage:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def save(self, source_path: Path, *, document_type: str) -> tuple[str, int, str]:
        if not source_path.exists() or not source_path.is_file():
            raise StorageError(f"Файл не знайдено: {source_path}")

        today = datetime.now()
        token = uuid.uuid4().hex[:12]
        rel = Path(document_type) / f"{today:%Y}" / f"{today:%m}" / f"{token}.{document_type}"
        dest = self._root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source_path, dest)

        size = dest.stat().st_size
        sha1 = _sha1_of(dest)
        return rel.as_posix(), size, sha1

    def resolve(self, relative_path: str) -> Path:
        return self._root / relative_path

    def delete(self, relative_path: str) -> None:
        path = self._root / relative_path
        try:
            path.unlink(missing_ok=True)
        except OSError as e:
            raise StorageError(f"Не вдалося видалити {relative_path}: {e}") from e


def _sha1_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha1(usedforsecurity=False)
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def sha1_of_file(path: Path) -> str:
    """Public helper for use-cases that need to peek at a file's hash before save."""
    return _sha1_of(path)
