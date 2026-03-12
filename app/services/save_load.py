from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from app.config import CHARACTERS_DIR
from app.models.character import Character


def list_character_files() -> List[Path]:
    CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(CHARACTERS_DIR.glob("*.json"), key=lambda p: p.name.lower())


def load_character(path: Path) -> Character:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return Character.from_dict(data)


def save_character(character: Character, path: Path) -> None:
    character.touch()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(character.to_dict(), f, indent=2, ensure_ascii=False)


def delete_character_file(path: Path) -> None:
    if path.exists() and path.is_file():
        path.unlink()