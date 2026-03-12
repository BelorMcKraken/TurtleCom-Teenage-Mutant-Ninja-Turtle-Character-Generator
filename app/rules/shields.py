from __future__ import annotations

from typing import Any

from app.rules.catalog_loader import load_named_catalog

SHIELD_CATALOG: list[dict[str, Any]]
SHIELD_BY_NAME: dict[str, dict[str, Any]]

SHIELD_CATALOG, SHIELD_BY_NAME = load_named_catalog("shields.json")