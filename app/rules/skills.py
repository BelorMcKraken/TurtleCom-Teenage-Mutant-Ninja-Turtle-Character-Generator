from __future__ import annotations

from typing import Any

from app.rules.catalog_loader import load_json_file


def load_skill_rules() -> dict[str, Any]:
    data = load_json_file("skills.json")
    if not isinstance(data, dict):
        raise ValueError("skills.json must contain a JSON object")
    return data