from __future__ import annotations

from typing import Any

from app.rules.catalog_loader import load_json_file


def _as_vehicle_list(data: Any) -> list[dict[str, str]]:
    if not isinstance(data, list):
        return []

    out: list[dict[str, str]] = []
    for item in data:
        if not isinstance(item, dict):
            continue

        name = str(item.get("name", "")).strip()
        if not name:
            continue

        out.append(
            {
                "name": name,
                "range": str(item.get("range", "")).strip(),
                "top_speed": str(item.get("top_speed", "")).strip(),
                "sdc": str(item.get("sdc", "")).strip(),
                "cost": str(item.get("cost", "")).strip(),
            }
        )
    return out


_VEHICLE_DATA = load_json_file("vehicles.json")

VEHICLES_LANDCRAFT: list[dict[str, str]] = _as_vehicle_list(_VEHICLE_DATA.get("landcraft", []))
VEHICLES_WATERCRAFT: list[dict[str, str]] = _as_vehicle_list(_VEHICLE_DATA.get("watercraft", []))
VEHICLES_AIRCRAFT: list[dict[str, str]] = _as_vehicle_list(_VEHICLE_DATA.get("aircraft", []))
VEHICLES_LOOKUP: dict[str, dict[str, str]] = {
    v["name"]: v
    for v in (VEHICLES_LANDCRAFT + VEHICLES_WATERCRAFT + VEHICLES_AIRCRAFT)
}