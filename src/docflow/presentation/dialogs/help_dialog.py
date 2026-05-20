"""Help dialog — renders ``docs/help.md`` with a sidebar of section anchors.

The markdown file is searched in a few locations so the dialog works both in
dev mode (running from source) and when packaged as a frozen .exe.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

# Fallback shown if no help.md is found on disk. Keeps the dialog useful even
# when packaging strips the docs/ folder.
_FALLBACK_HELP = """# Довідка

Файл ``docs/help.md`` не знайдено. Перевірте, що папка `docs/` поряд із додатком.

## Основні дії

- **Ctrl+N** — додати документ
- Подвійний клік по рядку — відкрити картку
- `⨁ Нова версія` — наступний коміт у поточній гілці
- `⑂ Гілка` — нова гілка з копії або з нового файлу
- `🗑 Видалити` — каскадне видалення
"""


def _candidate_paths(file_name: str) -> list[Path]:
    """Locations to look for a doc file, in order of preference.

    1. Next to the running executable (frozen / installed app).
    2. Repo root: <project>/docs/.
    3. Source layout: src/../docs/.
    """
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).parent / "docs" / file_name)
    # Project root: assume this file is at src/docflow/presentation/dialogs/help_dialog.py
    here = Path(__file__).resolve()
    project_root = here.parents[4]
    candidates.append(project_root / "docs" / file_name)
    candidates.append(Path.cwd() / "docs" / file_name)
    return candidates


def load_doc(file_name: str, *, fallback: str = "") -> str:
    """Read a doc file from any of the candidate paths; return ``fallback`` if missing."""
    for p in _candidate_paths(file_name):
        if p.is_file():
            try:
                return p.read_text(encoding="utf-8")
            except OSError:
                continue
    return fallback


# Match ATX-style level-2 headings ("## Section name") so the sidebar can list them.
_H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


class HelpDialog(QDialog):
    """Reads docs/help.md, renders it with a left-side TOC of `##` headings."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Довідка — DocFlow")
        self.setMinimumSize(900, 640)

        md = load_doc("help.md", fallback=_FALLBACK_HELP)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter, stretch=1)

        # --- Sidebar TOC ---
        self._toc = QListWidget()
        self._toc.setFixedWidth(220)
        self._toc.setStyleSheet(
            "QListWidget { background: #E8E0C9; border: none; padding: 8px; }"
            "QListWidget::item { padding: 6px 10px; border-radius: 6px; }"
            "QListWidget::item:selected { background: #2C2C2C; color: white; }"
        )
        splitter.addWidget(self._toc)

        # --- Content viewer ---
        self._viewer = QTextBrowser()
        self._viewer.setOpenExternalLinks(True)
        # why: setMarkdown landed in Qt 5.14 and is in PyQt6. It supports headings,
        # lists, code, tables — enough for our help content.
        self._viewer.setMarkdown(md)
        self._viewer.setStyleSheet(
            "QTextBrowser { background: white; border: none; padding: 16px; font-size: 13px; }"
        )
        splitter.addWidget(self._viewer)
        splitter.setSizes([220, 680])

        # Populate TOC from ## headings
        self._sections = _H2_RE.findall(md)
        for title in self._sections:
            self._toc.addItem(QListWidgetItem(title))
        if self._sections:
            self._toc.setCurrentRow(0)
        self._toc.currentRowChanged.connect(self._scroll_to_section)

        # Buttons (Close)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.button(QDialogButtonBox.StandardButton.Close).setText("× Закрити")
        button_box.rejected.connect(self.reject)
        button_box.accepted.connect(self.accept)
        button_row = QWidget()
        br_layout = QHBoxLayout(button_row)
        br_layout.setContentsMargins(12, 8, 12, 12)
        br_layout.addStretch(1)
        br_layout.addWidget(button_box)
        layout.addWidget(button_row)

    def _scroll_to_section(self, index: int) -> None:
        """Use QTextBrowser's built-in `find` to jump to the matching heading."""
        if not 0 <= index < len(self._sections):
            return
        title = self._sections[index]
        # Move cursor to top first so find() starts from the document start.
        cursor = self._viewer.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        self._viewer.setTextCursor(cursor)
        self._viewer.find(title)


class AboutDialog(QDialog):
    """Tiny 'About DocFlow' dialog reading docs/about.md."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Про DocFlow")
        self.setMinimumSize(420, 320)

        md = load_doc("about.md", fallback="# DocFlow\n\nЛокальний документообіг.")

        layout = QVBoxLayout(self)
        viewer = QTextBrowser()
        viewer.setOpenExternalLinks(True)
        viewer.setMarkdown(md)
        viewer.setStyleSheet(
            "QTextBrowser { background: white; border: 1px solid #C9C0A5;"
            " border-radius: 6px; padding: 16px; }"
        )
        layout.addWidget(viewer, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("× Закрити")
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
