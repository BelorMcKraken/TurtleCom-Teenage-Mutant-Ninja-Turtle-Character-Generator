# app/rules/catalog_loader.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RULES_DATA_DIR = PROJECT_ROOT / "data" / "rules"


def load_json_file(filename: str) -> Any:
    path = RULES_DATA_DIR / filename
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_named_catalog(filename: str) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    data = load_json_file(filename)

    if not isinstance(data, list):
        raise ValueError(f"{filename} must contain a list of objects")

    catalog: list[dict[str, Any]] = []
    by_name: dict[str, dict[str, Any]] = {}

    for item in data:
        if not isinstance(item, dict):
            continue

        name = str(item.get("name", "")).strip()
        if not name:
            continue

        catalog.append(item)
        by_name[name] = item

    return catalog, by_name