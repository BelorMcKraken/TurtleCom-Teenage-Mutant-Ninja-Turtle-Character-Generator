from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import DATA_DIR


PSIONIC_CATEGORY_MUTANT_ANIMAL = "mutant_animal_psionic_powers"
PSIONIC_CATEGORY_MUTANT_HOMINID = "mutant_hominid_psionic_powers"
PSIONIC_CATEGORY_MUTANT_PROSTHETIC = "mutant_prosthetic_psionic_powers"
PSIONIC_CATEGORY_MUTANT_HUMAN_ABILITIES = "mutant_human_abilities"
PSIONIC_CATEGORY_MUTANT_HOMINID_ABILITIES = "mutant_hominid_abilities"


def _load_json() -> dict[str, list[dict[str, Any]]]:
    path = Path(DATA_DIR) / "rules" / "psionic_catalog.json"
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("psionic_catalog.json must contain a top-level object")

    normalized: dict[str, list[dict[str, Any]]] = {}
    for category, items in data.items():
        if not isinstance(items, list):
            normalized[category] = []
            continue

        normalized_items: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            normalized_items.append(
                {
                    "name": str(item.get("name", "")).strip(),
                    "bio_e": int(item.get("bio_e", 0) or 0),
                }
            )
        normalized[category] = normalized_items

    return normalized


PSIONIC_CATALOG: dict[str, list[dict[str, Any]]] = _load_json()

MUTANT_ANIMAL_PSIONIC_POWERS = PSIONIC_CATALOG.get(PSIONIC_CATEGORY_MUTANT_ANIMAL, [])
MUTANT_HOMINID_PSIONIC_POWERS = PSIONIC_CATALOG.get(PSIONIC_CATEGORY_MUTANT_HOMINID, [])
MUTANT_PROSTHETIC_PSIONIC_POWERS = PSIONIC_CATALOG.get(PSIONIC_CATEGORY_MUTANT_PROSTHETIC, [])
MUTANT_HUMAN_ABILITIES = PSIONIC_CATALOG.get(PSIONIC_CATEGORY_MUTANT_HUMAN_ABILITIES, [])
MUTANT_HOMINID_ABILITIES = PSIONIC_CATALOG.get(PSIONIC_CATEGORY_MUTANT_HOMINID_ABILITIES, [])


def get_psionic_catalog_options(category: str) -> list[tuple[str, int]]:
    return [
        (str(item.get("name", "")).strip(), int(item.get("bio_e", 0) or 0))
        for item in PSIONIC_CATALOG.get(category, [])
        if str(item.get("name", "")).strip()
    ]


def get_all_psionic_categories() -> list[str]:
    return [
        PSIONIC_CATEGORY_MUTANT_ANIMAL,
        PSIONIC_CATEGORY_MUTANT_HOMINID,
        PSIONIC_CATEGORY_MUTANT_PROSTHETIC,
        PSIONIC_CATEGORY_MUTANT_HUMAN_ABILITIES,
        PSIONIC_CATEGORY_MUTANT_HOMINID_ABILITIES,
    ]