from __future__ import annotations

from typing import Any

from app.rules.catalog_loader import load_json_file


def load_physical_skill_effects() -> dict[str, dict[str, Any]]:
    data = load_json_file("physical_skill_effects.json")
    if not isinstance(data, dict):
        raise ValueError("physical_skill_effects.json must contain an object")
    return data


PHYSICAL_SKILL_EFFECTS: dict[str, dict[str, Any]] = load_physical_skill_effects()