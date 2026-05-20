"""+ Додати документ — drag&drop area + file picker + bulk-tag editor (stub)."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

SUPPORTED_EXT = {".docx", ".xlsx", ".xls", ".pdf"}


class AddDocumentDialog(QDialog):
    def __init__(self, parent: object | None = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self.setWindowTitle("Додати документ")
        self.setMinimumSize(620, 460)
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)

        # Drop zone
        drop_zone = QLabel("⬇  Перетягніть файли сюди\nабо натисніть «Обрати файли…»")
        drop_zone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_zone.setStyleSheet(
            "border: 2px dashed #C9C0A5; border-radius: 8px; padding: 40px;"
            "color: #7A7257; font-size: 14px;"
        )
        drop_zone.setMinimumHeight(160)
        layout.addWidget(drop_zone)

        pick_row = QHBoxLayout()
        pick_btn = QPushButton("📂  Обрати файли…")
        pick_btn.clicked.connect(self._pick_files)
        pick_row.addWidget(pick_btn)
        pick_row.addStretch(1)
        pick_row.addWidget(QLabel("Підтримуються: docx · xlsx · xls · pdf"))
        layout.addLayout(pick_row)

        # Queue
        layout.addWidget(QLabel("ДО ЗАВАНТАЖЕННЯ:"))
        self._queue = QListWidget()
        layout.addWidget(self._queue, stretch=1)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("✓ Додати")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # -- drag & drop --

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802 — Qt API
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802 — Qt API
        for url in event.mimeData().urls():
            p = Path(url.toLocalFile())
            if p.suffix.lower() in SUPPORTED_EXT:
                self._add_to_queue(p)

    # -- helpers --

    def _pick_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Оберіть документи",
            "",
            "Документи (*.docx *.xlsx *.xls *.pdf)",
        )
        for p in paths:
            self._add_to_queue(Path(p))

    def _add_to_queue(self, path: Path) -> None:
        item = QListWidgetItem(f"📄  {path.name}    ·    {path.parent}")
        item.setData(Qt.ItemDataRole.UserRole, str(path))
        self._queue.addItem(item)

    def selected_files(self) -> list[str]:
        return [
            self._queue.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self._queue.count())
        ]
