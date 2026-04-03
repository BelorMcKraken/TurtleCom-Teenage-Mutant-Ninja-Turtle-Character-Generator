from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import DATA_DIR


def _load_json(filename: str) -> Any:
    path = Path(DATA_DIR) / "rules" / filename
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


TMNTTA_TIME_DEVICES = _load_json("tmntta_time_devices.json")
TMNTTA_TEMPORAL_SUPPORT_DEVICES = _load_json("tmntta_temporal_support_devices.json")
TMNTTA_TIME_DEVICE_INSTALL_COSTS = _load_json("tmntta_time_device_install_costs.json")


TMNTTA_TIME_DEVICES_BY_NAME = {
    item["name"]: item for item in TMNTTA_TIME_DEVICES
}

TMNTTA_TEMPORAL_SUPPORT_BY_NAME = {
    item["name"]: item for item in TMNTTA_TEMPORAL_SUPPORT_DEVICES
}