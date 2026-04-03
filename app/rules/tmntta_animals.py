# app/rules/tmntta_animals.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import DATA_DIR


RangeTable = list[tuple[range, str]]
AnimalByTypeTable = dict[str, RangeTable]


def _load_json(filename: str) -> Any:
    path = Path(DATA_DIR) / "rules" / filename
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _to_range(start: int, end: int) -> range:
    return range(int(start), int(end) + 1)


def _load_range_table(filename: str) -> RangeTable:
    data = _load_json(filename)
    table: RangeTable = []

    for item in data:
        table.append((_to_range(item["start"], item["end"]), str(item["name"])))

    return table


def _load_animals_by_type(filename: str) -> AnimalByTypeTable:
    data = _load_json(filename)
    table: AnimalByTypeTable = {}

    for animal_type, rows in data.items():
        converted_rows: RangeTable = []
        for item in rows:
            converted_rows.append((_to_range(item["start"], item["end"]), str(item["name"])))
        table[str(animal_type)] = converted_rows

    return table


TMNTTA_ANIMAL_TYPE_RANGES: RangeTable = _load_range_table("tmntta_animal_type_ranges.json")
TMNTTA_ANIMALS_BY_TYPE: AnimalByTypeTable = _load_animals_by_type("tmntta_animals_by_type.json")