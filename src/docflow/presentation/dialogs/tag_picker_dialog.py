"""Pick a tag to attach to a document, or create a new one inline."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from docflow.application.dto import TagView


class TagPickerDialog(QDialog):
    def __init__(
        self,
        tags: list[TagView],
        parent: QWidget | None = None,
        *,
        exclude_tag_ids: list[int] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Додати тег")
        self.setMinimumSize(380, 420)
        self._chosen_id: int | None = None
        self._wants_create_new = False

        layout = QVBoxLayout(self)

        self._search = QLineEdit()
        self._search.setPlaceholderText("🔎  Шукати або створити новий…")
        self._search.textChanged.connect(self._on_filter)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._on_double)
        layout.addWidget(self._list, stretch=1)

        exclude = set(exclude_tag_ids or [])
        self._all_tags = [t for t in tags if t.id not in exclude]
        self._populate(self._all_tags)

        # Create-new button
        self._create_btn = QPushButton("+ Створити новий тег")
        self._create_btn.clicked.connect(self._on_create_new)
        layout.addWidget(self._create_btn)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Прикріпити")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate(self, tags: list[TagView]) -> None:
        self._list.clear()
        for t in tags:
            item = QListWidgetItem(f"●  {t.name}    ({t.document_count})")
            item.setData(Qt.ItemDataRole.UserRole, t.id)
            self._list.addItem(item)

    def _on_filter(self, text: str) -> None:
        text = text.strip().lower()
        if not text:
            self._populate(self._all_tags)
            return
        self._populate([t for t in self._all_tags if text in t.name.lower()])

    def _on_double(self, _item: QListWidgetItem) -> None:
        self._on_accept()

    def _on_create_new(self) -> None:
        self._wants_create_new = True
        self.accept()

    def _on_accept(self) -> None:
        item = self._list.currentItem()
        if item:
            self._chosen_id = int(item.data(Qt.ItemDataRole.UserRole))
        self.accept()

    # -- Public --

    def chosen_id(self) -> int | None:
        return self._chosen_id

    def wants_create_new(self) -> bool:
        return self._wants_create_new
