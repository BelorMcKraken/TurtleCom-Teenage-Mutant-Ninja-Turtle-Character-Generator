from __future__ import annotations

import os
import sys
from pathlib import Path


def project_root() -> Path:
    # PyInstaller runtime
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)

    # Normal Python execution
    return Path(__file__).resolve().parents[1]


DATA_DIR = project_root() / "data"


def user_data_dir() -> Path:
    base = Path(os.getenv("APPDATA", Path.home()))
    path = base / "TurtleCom"
    path.mkdir(parents=True, exist_ok=True)
    return path


CHARACTERS_DIR = user_data_dir() / "characters"
CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)