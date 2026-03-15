# app/rules/combat.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import DATA_DIR


def _load_json(filename: str) -> dict[str, Any]:
    path = Path(DATA_DIR) / "rules" / filename
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _normalize_critical_range(value: Any) -> tuple[int, int] | Any:
    if isinstance(value, list) and len(value) == 2:
        return int(value[0]), int(value[1])
    if isinstance(value, tuple) and len(value) == 2:
        return int(value[0]), int(value[1])
    return value


def load_baseline_combat() -> dict[str, Any]:
    data = _load_json("baseline_combat.json")
    data["critical_range"] = _normalize_critical_range(data.get("critical_range"))
    return data


def load_combat_training_rules() -> dict[str, dict[int, dict[str, Any]]]:
    raw = _load_json("combat_training_rules.json")
    normalized: dict[str, dict[int, dict[str, Any]]] = {}

    for training_name, levels in raw.items():
        normalized_levels: dict[int, dict[str, Any]] = {}

        for level_str, rule_data in levels.items():
            level = int(level_str)
            rule_copy = dict(rule_data)

            if "critical_range" in rule_copy:
                rule_copy["critical_range"] = _normalize_critical_range(rule_copy["critical_range"])

            normalized_levels[level] = rule_copy

        normalized[training_name] = normalized_levels

    return normalized


BASELINE_COMBAT = load_baseline_combat()
COMBAT_TRAINING_RULES = load_combat_training_rules()


def training_names() -> list[str]:
    return ["None"] + sorted(COMBAT_TRAINING_RULES.keys())


def combine_melee_damage(dmg_list: list[str]) -> str:
    if not dmg_list:
        return "—"
    return ", ".join(dmg_list)