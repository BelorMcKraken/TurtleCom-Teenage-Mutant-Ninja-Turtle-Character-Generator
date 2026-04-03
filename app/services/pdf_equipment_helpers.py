# app/services/pdf_equipment_helpers.py

from __future__ import annotations

from typing import Any

from app.rules.shields import SHIELD_BY_NAME
from app.rules.weapons import WEAPONS_BY_NAME


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _first_non_empty(*values: Any) -> str:
    for value in values:
        text = _text(value)
        if text:
            return text
    return ""


def resolve_weapon_details(name: str) -> dict[str, str]:
    cleaned_name = _text(name)
    raw = WEAPONS_BY_NAME.get(cleaned_name, {}) if cleaned_name else {}
    if not isinstance(raw, dict):
        raw = {}

    weapon_type = _first_non_empty(
        raw.get("type"),
        raw.get("weapon_type"),
        raw.get("category"),
        raw.get("class"),
        raw.get("group"),
        raw.get("kind"),
        raw.get("weaponClass"),
    )
    if not weapon_type:
        for key, value in raw.items():
            key_text = str(key).casefold()
            if "type" in key_text or "category" in key_text or "class" in key_text:
                weapon_type = _text(value)
                if weapon_type:
                    break

    damage = _first_non_empty(
        raw.get("damage"),
        raw.get("dmg"),
        raw.get("md"),
        raw.get("sdc_damage"),
        raw.get("damage_sdc"),
        raw.get("damage_dice"),
        raw.get("primary_damage"),
        raw.get("damageRoll"),
    )
    if not damage:
        dice = _first_non_empty(raw.get("dice"), raw.get("damage_dice_count"))
        sides = _first_non_empty(raw.get("sides"), raw.get("damage_dice_sides"))
        bonus = _first_non_empty(raw.get("bonus"), raw.get("damage_bonus"))
        if dice and sides:
            bonus_text = f"+{bonus}" if bonus and not str(bonus).startswith("-") else str(bonus or "")
            damage = f"{dice}D{sides}{bonus_text}"

    if not damage:
        for key, value in raw.items():
            key_text = str(key).casefold()
            if "damage" in key_text or key_text in {"dmg", "md"}:
                damage = _text(value)
                if damage:
                    break

    range_text = _first_non_empty(
        raw.get("range"),
        raw.get("effective_range"),
        raw.get("distance"),
        raw.get("max_range"),
    )
    notes = _first_non_empty(
        raw.get("notes"),
        raw.get("special"),
        raw.get("description"),
        raw.get("ammo"),
    )

    return {
        "name": cleaned_name,
        "type": weapon_type,
        "damage": damage,
        "range": range_text,
        "notes": notes,
    }


def resolve_shield_details(name: str) -> dict[str, str]:
    cleaned_name = _text(name)
    raw = SHIELD_BY_NAME.get(cleaned_name, {}) if cleaned_name else {}
    if not isinstance(raw, dict):
        raw = {}

    sdc = _first_non_empty(
        raw.get("sdc"),
        raw.get("SDC"),
        raw.get("hit_points"),
        raw.get("hp"),
        raw.get("value"),
    )
    if not sdc:
        for key, value in raw.items():
            key_text = str(key).casefold()
            if "sdc" in key_text or "hit" in key_text or key_text == "hp":
                sdc = _text(value)
                if sdc:
                    break

    parry = _first_non_empty(
        raw.get("parry"),
        raw.get("parry_bonus"),
        raw.get("bonus_parry"),
        raw.get("defense_bonus"),
    )
    if not parry:
        for key, value in raw.items():
            key_text = str(key).casefold()
            if "parry" in key_text:
                parry = _text(value)
                if parry:
                    break

    notes = _first_non_empty(
        raw.get("notes"),
        raw.get("special"),
        raw.get("description"),
        raw.get("properties"),
    )

    return {
        "name": cleaned_name,
        "parry": parry,
        "sdc": sdc,
        "notes": notes,
    }