"""Generic destructive confirmation dialog (matches the wireframe)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)


class ConfirmDeleteDialog(QDialog):
    def __init__(self, parent: object | None = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self.setWindowTitle("Підтвердження видалення")
        self.setMinimumSize(440, 280)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        warn = QLabel("⚠")
        warn.setStyleSheet("font-size: 32px;")
        warn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(warn)

        title = QLabel("Видалити документ?")
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("Операцію не можна буде скасувати без архіву.\n"
                    "Буде видалено: поточну версію, всю історію, усі гілки, зв'язки.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #7A7257;")
        layout.addWidget(sub)

        layout.addStretch(1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setText("🗑  Видалити")
        ok_btn.setObjectName("Danger")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
