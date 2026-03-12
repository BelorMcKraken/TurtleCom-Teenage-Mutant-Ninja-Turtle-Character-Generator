from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    # app/config.py -> app -> TurtleCom root
    return Path(__file__).resolve().parents[1]


DATA_DIR = project_root() / "data"
CHARACTERS_DIR = DATA_DIR / "characters"
CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)