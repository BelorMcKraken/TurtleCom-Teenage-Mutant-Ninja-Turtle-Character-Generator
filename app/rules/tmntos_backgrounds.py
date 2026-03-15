# app/rules/tmntos_backgrounds.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


from app.config import DATA_DIR


RangeTextTable = list[tuple[range, dict[str, str]]]


def _load_json(filename: str) -> Any:
    path = Path(DATA_DIR) / "rules" / filename
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _to_range(start: int, end: int) -> range:
    return range(int(start), int(end) + 1)


def _load_range_text_table(filename: str) -> RangeTextTable:
    rows = _load_json(filename)
    table: RangeTextTable = []

    for row in rows:
        table.append(
            (
                _to_range(row["start"], row["end"]),
                {
                    "name": str(row["name"]),
                    "details": str(row.get("details", "")),
                },
            )
        )

    return table


TMNTOS_MUTANT_ANIMAL_ORIGINS: RangeTextTable = _load_range_text_table(
    "tmntos_mutant_animal_origins.json"
)

TMNTOS_CREATOR_ORGANIZATIONS: RangeTextTable = _load_range_text_table(
    "tmntos_creator_organizations.json"
)

TMNTOS_WILD_ANIMAL_EDUCATION: RangeTextTable = _load_range_text_table(
    "tmntos_wild_animal_education.json"
)