from __future__ import annotations

from typing import Any

from app.rules.catalog_loader import load_named_catalog

ARMOR_CATALOG: list[dict[str, Any]]
ARMOR_BY_NAME: dict[str, dict[str, Any]]

ARMOR_CATALOG, ARMOR_BY_NAME = load_named_catalog("armor.json")