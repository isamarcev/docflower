"""Document card page — metadata, tags, recent versions, recent activity.

Matches the wireframe at "Картка документа (метадані)". The page is read-only;
edits go through dialogs (NewVersion, AddTag, EditMetadata).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from docflow.application.dto import DocumentDetails
from docflow.presentation.styles.theme import doc_type_badge_style
from docflow.presentation.widgets.tag_chip import TagChip


def _human_size(size_bytes: int) -> str:
    for unit in ["Б", "КБ", "МБ", "ГБ"]:
        if size_bytes < 1024:
            return f"{size_bytes:.0f} {unit}" if unit == "Б" else f"{size_bytes:.1f} {unit}"
        size_bytes //= 1024
    return f"{size_bytes} ТБ"


class DocumentCardPage(QWidget):
    open_externally_requested = pyqtSignal(int)            # document_id
    new_version_requested = pyqtSignal(int)
    new_branch_requested = pyqtSignal(int)
    edit_metadata_requested = pyqtSignal(int)
    add_tag_requested = pyqtSignal(int)
    detach_tag_requested = pyqtSignal(int, int)            # (document_id, tag_id)
    show_tree_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)
    export_requested = pyqtSignal(int)
    back_requested = pyqtSignal()

    def __init__(self, parent: object | None = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self._doc_id: int | None = None
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(10)

        # Toolbar
        toolbar = QHBoxLayout()
        self._back_btn = QPushButton("← До списку")
        self._back_btn.clicked.connect(self.back_requested)
        toolbar.addWidget(self._back_btn)
        self._open_btn = QPushButton("▶  Відкрити в редакторі")
        self._open_btn.setObjectName("Primary")
        self._open_btn.clicked.connect(self._emit_open)
        toolbar.addWidget(self._open_btn)
        self._edit_btn = QPushButton("✎  Редагувати картку")
        self._edit_btn.clicked.connect(self._emit_edit)
        toolbar.addWidget(self._edit_btn)
        self._new_ver_btn = QPushButton("⨁  Нова версія")
        self._new_ver_btn.clicked.connect(self._emit_new_version)
        toolbar.addWidget(self._new_ver_btn)
        self._branch_btn = QPushButton("⑂  Гілка")
        self._branch_btn.clicked.connect(self._emit_new_branch)
        toolbar.addWidget(self._branch_btn)
        self._tree_btn = QPushButton("🌲  Дерево версій")
        self._tree_btn.clicked.connect(self._emit_show_tree)
        toolbar.addWidget(self._tree_btn)
        self._export_btn = QPushButton("⬇  Експорт")
        self._export_btn.clicked.connect(self._emit_export)
        toolbar.addWidget(self._export_btn)
        toolbar.addStretch(1)
        self._delete_btn = QPushButton("🗑  Видалити")
        self._delete_btn.setObjectName("Danger")
        self._delete_btn.clicked.connect(self._emit_delete)
        toolbar.addWidget(self._delete_btn)
        outer.addLayout(toolbar)

        # Header
        self._badge = QLabel("docx")
        self._badge.setStyleSheet(doc_type_badge_style("docx"))
        self._title = QLabel("—")
        self._title.setStyleSheet("font-size: 18px; font-weight: 700;")
        self._subtitle = QLabel("")
        self._subtitle.setStyleSheet("color: #7A7257;")
        head_row = QHBoxLayout()
        head_row.addWidget(self._badge)
        head_row.addWidget(self._title)
        head_row.addStretch(1)
        outer.addLayout(head_row)
        outer.addWidget(self._subtitle)

        # Body: two columns
        body = QHBoxLayout()
        outer.addLayout(body, stretch=1)

        # --- LEFT: metadata + description ---
        left = QVBoxLayout()
        body.addLayout(left, stretch=3)

        self._meta_box = QGroupBox("Метадані")
        meta_layout = QFormLayout(self._meta_box)
        meta_layout.setHorizontalSpacing(20)
        self._meta_type = QLabel("—")
        self._meta_path = QLabel("—")
        self._meta_path.setWordWrap(True)
        self._meta_created = QLabel("—")
        self._meta_updated = QLabel("—")
        self._meta_size = QLabel("—")
        self._meta_current_ver = QLabel("—")
        self._meta_total_ver = QLabel("—")
        self._meta_branches = QLabel("—")
        self._meta_sha1 = QLabel("—")
        self._meta_sha1.setStyleSheet("font-family: monospace; color: #7A7257;")
        meta_layout.addRow("Тип файлу:", self._meta_type)
        meta_layout.addRow("Шлях:", self._meta_path)
        meta_layout.addRow("Створено:", self._meta_created)
        meta_layout.addRow("Останнє оновл.:", self._meta_updated)
        meta_layout.addRow("Розмір:", self._meta_size)
        meta_layout.addRow("Поточна версія:", self._meta_current_ver)
        meta_layout.addRow("Усього версій:", self._meta_total_ver)
        meta_layout.addRow("Гілок:", self._meta_branches)
        meta_layout.addRow("Контрольна сума:", self._meta_sha1)
        left.addWidget(self._meta_box)

        # Tags
        self._tags_box = QGroupBox("Теги")
        tags_layout = QVBoxLayout(self._tags_box)
        self._tags_row_widget = QFrame()
        self._tags_row = QHBoxLayout(self._tags_row_widget)
        self._tags_row.setContentsMargins(0, 0, 0, 0)
        self._tags_row.setSpacing(4)
        tags_layout.addWidget(self._tags_row_widget)
        self._add_tag_btn = QPushButton("+ додати тег")
        self._add_tag_btn.setStyleSheet("text-align: left;")
        self._add_tag_btn.clicked.connect(self._emit_add_tag)
        tags_layout.addWidget(self._add_tag_btn)
        left.addWidget(self._tags_box)

        # Description
        self._desc_box = QGroupBox("Опис")
        desc_layout = QVBoxLayout(self._desc_box)
        self._desc_label = QLabel("—")
        self._desc_label.setWordWrap(True)
        self._desc_label.setStyleSheet("color: #2C2C2C;")
        desc_layout.addWidget(self._desc_label)
        left.addWidget(self._desc_box)
        left.addStretch(1)

        # --- RIGHT: recent versions + recent activity ---
        right = QVBoxLayout()
        body.addLayout(right, stretch=2)

        self._ver_box = QGroupBox("Останні версії")
        ver_layout = QVBoxLayout(self._ver_box)
        self._ver_table = QTableWidget(0, 3)
        self._ver_table.setHorizontalHeaderLabels(["ВЕР.", "ОПИС", "КОЛИ"])
        self._ver_table.verticalHeader().setVisible(False)
        self._ver_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._ver_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._ver_table.setShowGrid(False)
        self._ver_table.setAlternatingRowColors(True)
        self._ver_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._ver_table.setColumnWidth(0, 60)
        self._ver_table.setColumnWidth(2, 100)
        ver_layout.addWidget(self._ver_table)
        self._show_tree_link = QPushButton("△  Усе дерево версій →")
        self._show_tree_link.setStyleSheet("text-align: left;")
        self._show_tree_link.clicked.connect(self._emit_show_tree)
        ver_layout.addWidget(self._show_tree_link)
        right.addWidget(self._ver_box)

        self._audit_box = QGroupBox("Останні дії")
        audit_layout = QVBoxLayout(self._audit_box)
        self._audit_list_widget = QFrame()
        self._audit_list = QVBoxLayout(self._audit_list_widget)
        self._audit_list.setContentsMargins(0, 0, 0, 0)
        self._audit_list.setSpacing(4)
        audit_layout.addWidget(self._audit_list_widget)
        right.addWidget(self._audit_box)
        right.addStretch(1)

    # ---------- Public API ----------

    def set_document(self, d: DocumentDetails) -> None:
        self._doc_id = d.id

        # Header
        self._badge.setText(d.doc_type.value)
        self._badge.setStyleSheet(doc_type_badge_style(d.doc_type.value))
        self._title.setText(d.name)
        self._subtitle.setText(
            f"{d.head_label} · гілка {d.branch_name} · HEAD · {_human_size(d.size_bytes)}"
        )

        # Metadata
        type_long = {"docx": "docx · Microsoft Word", "xlsx": "xlsx · Microsoft Excel",
                     "xls":  "xls · Microsoft Excel", "pdf":  "pdf · Adobe PDF"}
        self._meta_type.setText(type_long.get(d.doc_type.value, d.doc_type.value))
        self._meta_path.setText(d.file_path or "—")
        self._meta_created.setText(
            f"{d.created_at.strftime('%d.%m.%Y %H:%M')} · {d.created_by}"
        )
        self._meta_updated.setText(d.updated_at.strftime("%d.%m.%Y %H:%M"))
        self._meta_size.setText(_human_size(d.size_bytes))
        self._meta_current_ver.setText(d.head_label)
        self._meta_total_ver.setText(str(d.versions_total))
        self._meta_branches.setText(str(d.branches_total))
        self._meta_sha1.setText(f"sha1: {d.sha1[:8]}…{d.sha1[-4:]}" if d.sha1 else "—")

        # Description
        self._desc_label.setText(d.description or "Без опису")

        # Tags
        self._clear_layout(self._tags_row)
        for t in d.tags:
            chip = _RemovableTagChip(t.id, t.name, t.color)
            chip.removed.connect(lambda tid, did=d.id: self.detach_tag_requested.emit(did, tid))
            self._tags_row.addWidget(chip)
        self._tags_row.addStretch(1)

        # Recent versions
        self._ver_table.setRowCount(0)
        for v in d.recent_versions:
            i = self._ver_table.rowCount()
            self._ver_table.insertRow(i)
            label = QTableWidgetItem(("★ " if v.is_head else "") + v.label)
            self._ver_table.setItem(i, 0, label)
            self._ver_table.setItem(i, 1, QTableWidgetItem(v.message))
            self._ver_table.setItem(i, 2, QTableWidgetItem(v.created_at.strftime("%d.%m %H:%M")))

        # Recent audit
        self._clear_layout(self._audit_list)
        if not d.recent_audit:
            self._audit_list.addWidget(QLabel("Дій ще немає."))
        else:
            for a in d.recent_audit:
                lbl = QLabel(
                    f"<span style='color:#7A7257'>{a.occurred_at.strftime('%d.%m %H:%M')}</span> · "
                    f"<b>{a.actor}</b>: {a.details}"
                )
                lbl.setWordWrap(True)
                self._audit_list.addWidget(lbl)

    # ---------- Internal ----------

    def _clear_layout(self, layout: QVBoxLayout | QHBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _emit_open(self) -> None:
        if self._doc_id is not None:
            self.open_externally_requested.emit(self._doc_id)

    def _emit_edit(self) -> None:
        if self._doc_id is not None:
            self.edit_metadata_requested.emit(self._doc_id)

    def _emit_new_version(self) -> None:
        if self._doc_id is not None:
            self.new_version_requested.emit(self._doc_id)

    def _emit_new_branch(self) -> None:
        if self._doc_id is not None:
            self.new_branch_requested.emit(self._doc_id)

    def _emit_show_tree(self) -> None:
        if self._doc_id is not None:
            self.show_tree_requested.emit(self._doc_id)

    def _emit_delete(self) -> None:
        if self._doc_id is not None:
            self.delete_requested.emit(self._doc_id)

    def _emit_export(self) -> None:
        if self._doc_id is not None:
            self.export_requested.emit(self._doc_id)

    def _emit_add_tag(self) -> None:
        if self._doc_id is not None:
            self.add_tag_requested.emit(self._doc_id)


class _RemovableTagChip(QFrame):
    """Tag chip with an inline ✕ button that detaches it from the document."""

    removed = pyqtSignal(int)  # tag_id

    def __init__(self, tag_id: int, name: str, color: str) -> None:
        super().__init__()
        self._tag_id = tag_id
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        chip = TagChip(name, color)
        layout.addWidget(chip)

        close = QPushButton("×")
        close.setFixedSize(16, 16)
        close.setStyleSheet(
            "QPushButton { border: none; background: transparent;"
            " color: #7A7257; font-weight: bold; }"
            "QPushButton:hover { color: #2C2C2C; }"
        )
        close.clicked.connect(lambda: self.removed.emit(self._tag_id))
        layout.addWidget(close)
