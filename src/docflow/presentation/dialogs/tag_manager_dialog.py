"""Tag manager — full CRUD over tags.

Loads tags via ``ListTags``, reflects changes via CreateTag/UpdateTag/DeleteTag.
Emits no signals; the caller refreshes its own data on close.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from docflow.application.dto import TagView
from docflow.application.interactors.commands.manage_tags import (
    CreateTag,
    DeleteTag,
    UpdateTag,
)
from docflow.application.interactors.queries.list_tags import ListTags
from docflow.presentation.dialogs.create_tag_dialog import CreateTagDialog, TagFormData
from docflow.presentation.styles.theme import tag_chip_style


class TagManagerDialog(QDialog):
    def __init__(
        self,
        *,
        list_tags: ListTags,
        create_tag: CreateTag,
        update_tag: UpdateTag,
        delete_tag: DeleteTag,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._list_tags = list_tags
        self._create_tag = create_tag
        self._update_tag = update_tag
        self._delete_tag = delete_tag

        self.setWindowTitle("Керування тегами")
        self.setMinimumSize(680, 480)

        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔎  пошук тегу…")
        self._search.textChanged.connect(self._refresh)
        top.addWidget(self._search, stretch=1)
        new_btn = QPushButton("+ Новий тег")
        new_btn.setObjectName("Primary")
        new_btn.clicked.connect(self._on_create)
        top.addWidget(new_btn)
        layout.addLayout(top)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            ["ТЕГ", "КОЛІР", "ДОКУМЕНТІВ", "ОПИС", ""]
        )
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setColumnWidth(0, 140)
        self._table.setColumnWidth(1, 80)
        self._table.setColumnWidth(2, 90)
        self._table.setColumnWidth(4, 90)
        layout.addWidget(self._table, stretch=1)

        hint = QLabel(
            "Видалення тегу не видаляє документи — лише знімає мітку."
        )
        hint.setStyleSheet("color: #7A7257;")
        layout.addWidget(hint)

        close_btn = QPushButton("× Закрити")
        close_btn.clicked.connect(self.accept)
        close_row = QHBoxLayout()
        close_row.addStretch(1)
        close_row.addWidget(close_btn)
        layout.addLayout(close_row)

        self._refresh()

    def _refresh(self) -> None:
        query = self._search.text().strip().lower()
        all_tags = self._list_tags()
        if query:
            all_tags = [t for t in all_tags if query in t.name.lower()]

        self._table.setRowCount(0)
        for t in all_tags:
            self._add_row(t)

    def _add_row(self, t: TagView) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setRowHeight(row, 36)

        # Name as a chip
        chip = QLabel(t.name)
        chip.setStyleSheet(tag_chip_style(t.color))
        chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wrap = QWidget()
        wlayout = QHBoxLayout(wrap)
        wlayout.setContentsMargins(6, 4, 6, 4)
        wlayout.addWidget(chip)
        wlayout.addStretch(1)
        self._table.setCellWidget(row, 0, wrap)

        self._table.setItem(row, 1, QTableWidgetItem(t.color))
        self._table.setItem(row, 2, QTableWidgetItem(str(t.document_count)))
        self._table.setItem(row, 3, QTableWidgetItem(t.description))

        actions = QWidget()
        a_layout = QHBoxLayout(actions)
        a_layout.setContentsMargins(0, 0, 0, 0)
        edit = QPushButton("✎")
        edit.setFixedWidth(32)
        edit.clicked.connect(lambda _checked, tag=t: self._on_edit(tag))
        delete = QPushButton("🗑")
        delete.setFixedWidth(32)
        delete.clicked.connect(lambda _checked, tag=t: self._on_delete(tag))
        a_layout.addWidget(edit)
        a_layout.addWidget(delete)
        a_layout.addStretch(1)
        self._table.setCellWidget(row, 4, actions)

    def _on_create(self) -> None:
        dlg = CreateTagDialog(self)
        if not dlg.exec():
            return
        data = dlg.data()
        try:
            self._create_tag(name=data.name, color=data.color, description=data.description)
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "Не вдалося створити тег", str(e))
            return
        self._refresh()

    def _on_edit(self, t: TagView) -> None:
        dlg = CreateTagDialog(
            self,
            initial=TagFormData(name=t.name, color=t.color, description=t.description),
        )
        if not dlg.exec():
            return
        data = dlg.data()
        self._update_tag(tag_id=t.id, name=data.name, color=data.color, description=data.description)
        self._refresh()

    def _on_delete(self, t: TagView) -> None:
        confirm = QMessageBox.question(
            self,
            "Видалити тег",
            f"Видалити тег «{t.name}»?\nДокументи залишаться, мітка зникне з {t.document_count} док.",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self._delete_tag(t.id)
        self._refresh()
