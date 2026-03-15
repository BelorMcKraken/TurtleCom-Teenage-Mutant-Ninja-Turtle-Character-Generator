# app/rules/psionic_powers.py

from __future__ import annotations
from pathlib import Path
from typing import List, Tuple
import json

from app.config import DATA_DIR


def _load_json() -> list[dict]:
    path = Path(DATA_DIR) / "rules" / "psionic_powers.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_psionic_power_options() -> List[Tuple[str, int]]:
    data = _load_json()
    return [(item["name"], int(item["bio_e"])) for item in data]


PSIONIC_POWER_OPTIONS: List[Tuple[str, int]] = load_psionic_power_options()