"""Entry point — ``python -m docflow.main.app``.

Boots the DI container, seeds the DB on first run, opens the main window.
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from docflow.infrastructure.storage.file_storage import LocalFileStorage
from docflow.main.config import AppConfig
from docflow.main.container import build_container
from docflow.main.seed import seed_if_empty
from docflow.presentation.windows.main_window import MainWindow


def main() -> int:
    config = AppConfig.default()
    container = build_container(config)

    storage = LocalFileStorage(config.files_dir)
    seed_if_empty(container.conn, storage, actor=config.current_user)

    app = QApplication(sys.argv)
    app.setApplicationName("DocFlow")
    app.setOrganizationName("Служба списання")

    window = MainWindow(container.use_cases, current_user=config.current_user)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
