from __future__ import annotations

from typing import Any

from app.rules.catalog_loader import load_json_file


def _normalize_name_pools(data: Any) -> dict[str, list[str]]:
    if not isinstance(data, dict):
        raise ValueError("random_names.json must contain an object")

    pools: dict[str, list[str]] = {}

    for animal_name, names in data.items():
        key = str(animal_name).strip()
        if not key or not isinstance(names, list):
            continue

        cleaned = [str(name).strip() for name in names if str(name).strip()]
        pools[key] = cleaned

    return pools


ANIMAL_NAME_POOLS: dict[str, list[str]] = _normalize_name_pools(
    load_json_file("random_names.json")
)