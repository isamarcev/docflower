"""Create new version OR branch dialog.

For "version" mode a source file is mandatory.
For "branch" mode the default is to copy the parent version into the new branch
(no new file required); the user can opt to upload a new file as the branch's
first commit instead.
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
    QFrame,
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
        self.setMinimumSize(580, 540)

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
        default_name = f"draft-{max(1, details.branches_total)}"
        self.branch_name.setText(default_name)
        self.branch_name.setPlaceholderText("draft-Q1")
        form.addRow("Назва гілки:", self.branch_name)
        self.message = QTextEdit()
        self.message.setPlaceholderText("Опис змін…")
        self.message.setFixedHeight(80)
        form.addRow("Опис змін:", self.message)
        layout.addLayout(form)

        # --- Source section (file vs copy-from-parent) ---
        layout.addWidget(QLabel("ДЖЕРЕЛО"))
        self._source_frame = QFrame()
        sf_layout = QVBoxLayout(self._source_frame)
        sf_layout.setContentsMargins(0, 0, 0, 0)

        # Two-radio choice. "Copy" is only meaningful in branch mode; we hide
        # it in version mode by disabling the radio buttons there.
        self.opt_copy = QRadioButton(
            f"Скопіювати поточну версію ({details.head_label}) в нову гілку"
        )
        self.opt_new_file = QRadioButton("Завантажити новий файл")
        self._source_group = QButtonGroup(self)
        self._source_group.addButton(self.opt_copy)
        self._source_group.addButton(self.opt_new_file)
        sf_layout.addWidget(self.opt_copy)
        sf_layout.addWidget(self.opt_new_file)

        # File picker row (only enabled when "new file" is chosen)
        src_row = QHBoxLayout()
        src_row.setContentsMargins(20, 0, 0, 0)
        self._source_label = QLabel("Файл не обрано")
        self._source_label.setStyleSheet(
            "background:#FFFFFF; border:1px dashed #C9C0A5; "
            "border-radius:6px; padding:8px;"
        )
        src_row.addWidget(self._source_label, stretch=1)
        self._pick_btn = QPushButton("📂  Огляд…")
        self._pick_btn.clicked.connect(self._pick_source)
        src_row.addWidget(self._pick_btn)
        sf_layout.addLayout(src_row)

        self._hint = QLabel(
            "Файл стане новою версією. Тип має відповідати поточному "
            f"({details.doc_type.value})."
        )
        self._hint.setStyleSheet("color:#7A7257; font-size: 11px;")
        sf_layout.addWidget(self._hint)
        layout.addWidget(self._source_frame)

        layout.addStretch(1)

        # Wire mode + source toggles
        self.opt_version.toggled.connect(self._refresh_mode)
        self.opt_branch.toggled.connect(self._refresh_mode)
        self.opt_copy.toggled.connect(self._refresh_source)
        self.opt_new_file.toggled.connect(self._refresh_source)
        # Default source for branch mode: copy; for version mode: new file (forced).
        if mode == "branch":
            self.opt_copy.setChecked(True)
        else:
            self.opt_new_file.setChecked(True)
        self._refresh_mode()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("✓ Створити")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ----- UI state helpers -----

    def _refresh_mode(self) -> None:
        is_branch = self.opt_branch.isChecked()
        self.branch_name.setEnabled(is_branch)
        # Copy-from-parent only makes sense for a NEW branch; for a new version
        # there's no "copy" — new versions always need new content. So we force
        # new-file mode and lock the radios in version mode.
        self.opt_copy.setEnabled(is_branch)
        if not is_branch and not self.opt_new_file.isChecked():
            self.opt_new_file.setChecked(True)
        self._refresh_source()

    def _refresh_source(self) -> None:
        wants_new_file = self.opt_new_file.isChecked()
        self._source_label.setEnabled(wants_new_file)
        self._pick_btn.setEnabled(wants_new_file)
        self._hint.setVisible(wants_new_file)

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
        if self.opt_branch.isChecked() and not self.branch_name.text().strip():
            QMessageBox.warning(self, "Назва гілки", "Введіть назву нової гілки.")
            return
        if self.opt_new_file.isChecked():
            if self._source_path is None:
                QMessageBox.warning(
                    self, "Джерело не вибрано", "Будь ласка, виберіть файл-джерело."
                )
                return
            if self._source_path.suffix.lower().lstrip(".") != self._details.doc_type.value:
                QMessageBox.warning(
                    self,
                    "Невідповідний тип",
                    f"Тип нового файлу має бути .{self._details.doc_type.value}",
                )
                return
        self.accept()

    # ----- Public API -----

    def is_branch_mode(self) -> bool:
        return self.opt_branch.isChecked()

    def is_copy_from_parent(self) -> bool:
        """True iff the user wants to reuse the parent version's blob."""
        return self.opt_copy.isChecked()

    def chosen_branch_name(self) -> str:
        return self.branch_name.text().strip()

    def chosen_message(self) -> str:
        return self.message.toPlainText().strip() or "Без опису"

    def chosen_source(self) -> Path | None:
        return self._source_path
