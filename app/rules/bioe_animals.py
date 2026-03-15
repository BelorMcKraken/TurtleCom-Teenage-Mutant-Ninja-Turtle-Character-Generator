from __future__ import annotations

from typing import Any

from app.rules.catalog_loader import load_json_file


def load_bioe_animal_data() -> dict[str, dict[str, Any]]:
    data = load_json_file("bioe_animals.json")
    if not isinstance(data, dict):
        raise ValueError("bioe_animals.json must contain an object")
    return data


BIOE_ANIMAL_DATA: dict[str, dict[str, Any]] = load_bioe_animal_data()