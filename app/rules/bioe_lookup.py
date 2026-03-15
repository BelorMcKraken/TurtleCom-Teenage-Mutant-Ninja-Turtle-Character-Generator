# app/rules/bioe_lookup.py

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.config import DATA_DIR
from app.rules.bioe_animals import BIOE_ANIMAL_DATA


def _load_json(filename: str) -> Any:
    path = Path(DATA_DIR) / "rules" / filename
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def bioe_norm(value: str) -> str:
    value = (value or "").strip().upper()
    value = value.replace("&", "AND")
    value = re.sub(r"[—–-]", " ", value)
    value = re.sub(r"[^A-Z0-9 ]+", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _build_exact_aliases(data: dict[str, dict[str, Any]]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for key in data.keys():
        aliases[bioe_norm(key)] = key
    return aliases


def load_manual_bioe_animal_aliases() -> dict[str, str]:
    data = _load_json("bioe_animal_aliases.json")
    return {bioe_norm(str(key)): str(value) for key, value in data.items()}


def load_bioe_default_animal() -> dict[str, Any]:
    data = _load_json("bioe_default_animal.json")
    return dict(data)


BIOE_DEFAULT_ANIMAL: dict[str, Any] = load_bioe_default_animal()

BIOE_ANIMAL_ALIASES: dict[str, str] = {
    **_build_exact_aliases(BIOE_ANIMAL_DATA),
    **load_manual_bioe_animal_aliases(),
}