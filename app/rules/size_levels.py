# app/rules/size_levels.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from app.config import DATA_DIR

SizeLevelEffects = Dict[int, Dict[str, int]]
SizeLevelFormulas = Dict[int, Dict[str, str]]


def _load_json(filename: str) -> dict:
    path = Path(DATA_DIR) / "rules" / filename
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _to_int_keyed_dict(data: dict) -> dict[int, dict]:
    return {int(key): value for key, value in data.items()}


def load_size_level_effects() -> SizeLevelEffects:
    data = _load_json("size_level_effects.json")
    return _to_int_keyed_dict(data)


def load_size_level_formulas() -> SizeLevelFormulas:
    data = _load_json("size_level_formulas.json")
    return _to_int_keyed_dict(data)


SIZE_LEVEL_EFFECTS: SizeLevelEffects = load_size_level_effects()
SIZE_LEVEL_FORMULAS: SizeLevelFormulas = load_size_level_formulas()