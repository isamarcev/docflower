"""Create new version OR branch dialog.

Bound to either CreateVersion or CreateBranch + CreateVersion depending on which
radio is selected. Holds the chosen source file path which the main window picks
up after exec() returns Accepted.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from docflow.application.dto import DocumentDetails

Mode = Literal["version", "branch"]


class NewVersionDialog(QDialog):
    def __init__(
        self,
        details: DocumentDetails,
        *,
        parent: QWidget | None = None,
        mode: Mode = "version",
    ) -> None:
        super().__init__(parent)
        self._details = details
        self._source_path: Path | None = None
        self.setWindowTitle(
            "Створити нову версію" if mode == "version" else "Створити гілку"
        )
        self.setMinimumSize(560, 480)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("ВІД ЧОГО РОЗГАЛУЖУЄМОСЬ?"))
        from_label = QLabel(
            f"📄  {details.name}\n"
            f"обрана версія: {details.head_label} (HEAD · гілка {details.branch_name})"
        )
        from_label.setStyleSheet(
            "background:#FFFFFF; border:1px solid #C9C0A5; "
            "border-radius:6px; padding:8px;"
        )
        layout.addWidget(from_label)

        layout.addWidget(QLabel("ЩО ЗРОБИТИ?"))
        self.opt_version = QRadioButton(f"Нова версія в гілці {details.branch_name}")
        self.opt_branch = QRadioButton("Створити нову гілку")
        self._group = QButtonGroup(self)
        self._group.addButton(self.opt_version)
        self._group.addButton(self.opt_branch)
        if mode == "version":
            self.opt_version.setChecked(True)
        else:
            self.opt_branch.setChecked(True)
        row = QHBoxLayout()
        row.addWidget(self.opt_version)
        row.addWidget(self.opt_branch)
        layout.addLayout(row)

        form = QFormLayout()
        self.branch_name = QLineEdit()
        self.branch_name.setPlaceholderText("draft-Q1")
        form.addRow("Назва гілки:", self.branch_name)
        self.message = QTextEdit()
        self.message.setPlaceholderText("Опис змін…")
        self.message.setFixedHeight(80)
        form.addRow("Опис змін:", self.message)
        layout.addLayout(form)

        # Source file picker
        layout.addWidget(QLabel("ДЖЕРЕЛО"))
        src_row = QHBoxLayout()
        self._source_label = QLabel("Файл не обрано")
        self._source_label.setStyleSheet(
            "background:#FFFFFF; border:1px dashed #C9C0A5; "
            "border-radius:6px; padding:8px;"
        )
        src_row.addWidget(self._source_label, stretch=1)
        pick = QPushButton("📂  Огляд…")
        pick.clicked.connect(self._pick_source)
        src_row.addWidget(pick)
        layout.addLayout(src_row)
        hint = QLabel(
            "Файл стане новою версією. Тип має відповідати поточному "
            f"({details.doc_type.value})."
        )
        hint.setStyleSheet("color:#7A7257; font-size: 11px;")
        layout.addWidget(hint)

        layout.addStretch(1)

        # Wire opt -> enable/disable branch name
        self.opt_version.toggled.connect(self._refresh_enabled)
        self.opt_branch.toggled.connect(self._refresh_enabled)
        self._refresh_enabled()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("✓ Створити")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _refresh_enabled(self) -> None:
        self.branch_name.setEnabled(self.opt_branch.isChecked())

    def _pick_source(self) -> None:
        expected = self._details.doc_type.value
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Оберіть нову версію файлу",
            "",
            f"Документи (*.{expected})",
        )
        if path:
            self._source_path = Path(path)
            self._source_label.setText(f"📄  {self._source_path.name}\n{self._source_path.parent}")

    def _on_accept(self) -> None:
        if self._source_path is None:
            QMessageBox.warning(self, "Джерело не вибрано", "Будь ласка, виберіть файл-джерело.")
            return
        if self._source_path.suffix.lower().lstrip(".") != self._details.doc_type.value:
            QMessageBox.warning(
                self,
                "Невідповідний тип",
                f"Тип нового файлу має бути .{self._details.doc_type.value}",
            )
            return
        if self.opt_branch.isChecked() and not self.branch_name.text().strip():
            QMessageBox.warning(self, "Назва гілки", "Введіть назву нової гілки.")
            return
        self.accept()

    # ----- Public API -----

    def is_branch_mode(self) -> bool:
        return self.opt_branch.isChecked()

    def chosen_branch_name(self) -> str:
        return self.branch_name.text().strip()

    def chosen_message(self) -> str:
        return self.message.toPlainText().strip() or "Без опису"

    def chosen_source(self) -> Path:
        assert self._source_path is not None  # validated in _on_accept
        return self._source_path
