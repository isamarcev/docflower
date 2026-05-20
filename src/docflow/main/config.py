"""Application configuration — file paths and current user.

For now everything is filesystem-local. Later: add a pydantic-settings
based config that can be overridden by env / settings dialog.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _project_root() -> Path:
    """Return the docflow/ project root (two levels above this file)."""
    return Path(__file__).resolve().parents[3]


@dataclass(slots=True, frozen=True)
class AppConfig:
    data_dir: Path
    db_path: Path
    files_dir: Path
    current_user: str

    @classmethod
    def default(cls) -> "AppConfig":
        root = _project_root()
        data = root / "data"
        return cls(
            data_dir=data,
            db_path=data / "docflow.db",
            files_dir=data / "files",
            # Single-admin MVP: actor is always "Адмін" unless overridden via env.
            # Kept as a config value (not a constant) so we can switch to multi-user later
            # without touching call-sites.
            current_user=os.environ.get("DOCFLOW_USER", "Адмін"),
        )
