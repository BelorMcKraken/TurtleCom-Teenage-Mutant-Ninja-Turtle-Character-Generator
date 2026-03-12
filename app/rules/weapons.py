# app/rules/weapons.py

from __future__ import annotations

from typing import Any

from app.rules.catalog_loader import load_named_catalog


WEAPONS_CATALOG: list[dict[str, Any]]
WEAPONS_BY_NAME: dict[str, dict[str, Any]]

WEAPONS_CATALOG, WEAPONS_BY_NAME = load_named_catalog("weapons.json")