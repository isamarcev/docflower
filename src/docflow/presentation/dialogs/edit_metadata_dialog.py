"""Edit document name + description."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class EditMetadataDialog(QDialog):
    def __init__(
        self,
        *,
        name: str,
        description: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Редагувати картку документа")
        self.setMinimumSize(480, 320)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._name = QLineEdit(name)
        form.addRow("Назва:", self._name)

        self._description = QTextEdit(description)
        self._description.setMinimumHeight(150)
        form.addRow("Опис:", self._description)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("✓ Зберегти")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        if not self._name.text().strip():
            QMessageBox.warning(self, "Назва", "Назва не може бути порожньою.")
            return
        self.accept()

    def chosen_name(self) -> str:
        return self._name.text().strip()

    def chosen_description(self) -> str:
        return self._description.toPlainText().strip()
