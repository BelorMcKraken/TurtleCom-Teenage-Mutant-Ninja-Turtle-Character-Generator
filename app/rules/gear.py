from __future__ import annotations

from typing import Any

from app.rules.catalog_loader import load_named_catalog

GEAR_CATALOG: list[dict[str, Any]]
GEAR_BY_NAME: dict[str, dict[str, Any]]

GEAR_CATALOG, GEAR_BY_NAME = load_named_catalog("gear.json")