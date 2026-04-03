from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Any, List
import re


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def safe_filename(name: str) -> str:
    name = name.strip()
    if not name:
        return "Unnamed"
    name = re.sub(r"[^\w\s\-]", "", name)
    name = re.sub(r"\s+", "_", name)
    return name[:80]


@dataclass
class Character:
    # ---------- BASICS ----------
    name: str = ""
    animal: str = ""
    alignment: str = ""
    disposition: str = ""

    age: str = ""
    gender: str = ""
    weight: str = ""
    height: str = ""
    size: str = ""

    xp: int = 0
    level: int = 1
    hit_points: int = 0
    sdc: int = 0

    total_credits: int = 0
    total_wealth: int = 0

    image_path: str = ""

    # ---------- EQUIPMENT ----------
    weapons_selected: List[str] = field(default_factory=list)
    gear_selected: List[str] = field(default_factory=list)

    armor_type: str = ""
    armor_name: str = ""
    armor_ar: int = 0
    armor_sdc: int = 0
    armor_wt: str = ""
    armor_properties: str = ""

    shield_type: str = ""
    shield_notes: str = ""

    notes: str = ""

    # ---------- ATTRIBUTES ----------
    attributes: Dict[str, int] = field(default_factory=lambda: {
        "IQ": 0,
        "ME": 0,
        "MA": 0,
        "PS": 0,
        "PP": 0,
        "PE": 0,
        "PB": 0,
        "Speed": 0,
    })

    # ---------- SKILLS ----------
    skills: Dict[str, List[str]] = field(default_factory=lambda: {
        "pro": [""] * 10,
        "amateur": [""] * 15,
    })

    # ---------- COMBAT ----------
    combat: Dict[str, Any] = field(default_factory=lambda: {
        "training": "None",
        "override": False,
        "auto_details": True,
        "training_details_text": "",
        "strike": 0,
        "parry": 0,
        "dodge": 0,
        "initiative": 0,
        "actions_per_round": 2,
        "weapons": [],
    })

    # ---------- VEHICLES ----------
    vehicles: Dict[str, List[str]] = field(default_factory=lambda: {
        "landcraft": [],
        "watercraft": [],
        "aircraft": [],
    })

    # ---------- TIME MACHINES (TA) ----------
    ta_time_devices: Dict[str, Any] = field(default_factory=dict)

    # ---------- BIO-E ----------
    bio_e: Dict[str, Any] = field(default_factory=lambda: {
        "total": 0,
        "spent": 0,
        "traits": [],
    })

    uid: str = field(default_factory=_now_iso)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def touch(self) -> None:
        self.updated_at = _now_iso()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Character":
        c = Character()

        for key, value in data.items():
            if hasattr(c, key):
                setattr(c, key, value)

        if not isinstance(c.weapons_selected, list):
            c.weapons_selected = []
        else:
            c.weapons_selected = [str(x) for x in c.weapons_selected]

        if not isinstance(c.gear_selected, list):
            c.gear_selected = []
        else:
            c.gear_selected = [str(x) for x in c.gear_selected]

        if not isinstance(c.vehicles, dict):
            c.vehicles = {"landcraft": [], "watercraft": [], "aircraft": []}
        else:
            c.vehicles = {
                "landcraft": [str(x) for x in c.vehicles.get("landcraft", []) if str(x)],
                "watercraft": [str(x) for x in c.vehicles.get("watercraft", []) if str(x)],
                "aircraft": [str(x) for x in c.vehicles.get("aircraft", []) if str(x)],
            }

        if not isinstance(c.attributes, dict):
            c.attributes = {
                "IQ": 0,
                "ME": 0,
                "MA": 0,
                "PS": 0,
                "PP": 0,
                "PE": 0,
                "PB": 0,
                "Speed": 0,
            }
        else:
            defaults = {
                "IQ": 0,
                "ME": 0,
                "MA": 0,
                "PS": 0,
                "PP": 0,
                "PE": 0,
                "PB": 0,
                "Speed": 0,
            }
            for key, default_value in defaults.items():
                c.attributes[key] = int(c.attributes.get(key, default_value) or 0)

        if isinstance(c.skills, dict):
            pro = c.skills.get("pro", [""] * 10)
            ama = c.skills.get("amateur", [""] * 15)

            if isinstance(pro, dict) and "selected" in pro:
                pro = [pro.get("selected", "")] + [""] * 9
            if isinstance(ama, dict) and "selected" in ama:
                ama = [ama.get("selected", "")] + [""] * 14

            if not isinstance(pro, list):
                pro = [""] * 10
            if not isinstance(ama, list):
                ama = [""] * 15

            pro = [str(x) for x in (pro + [""] * 10)[:10]]
            ama = [str(x) for x in (ama + [""] * 15)[:15]]

            c.skills = {"pro": pro, "amateur": ama}
        else:
            c.skills = {"pro": [""] * 10, "amateur": [""] * 15}

        if not isinstance(c.combat, dict):
            c.combat = {
                "training": "None",
                "override": False,
                "auto_details": True,
                "training_details_text": "",
                "strike": 0,
                "parry": 0,
                "dodge": 0,
                "initiative": 0,
                "actions_per_round": 2,
                "weapons": [],
            }
        else:
            c.combat.setdefault("training", "None")
            c.combat.setdefault("override", False)
            c.combat.setdefault("auto_details", True)
            c.combat.setdefault("training_details_text", "")
            c.combat.setdefault("strike", 0)
            c.combat.setdefault("parry", 0)
            c.combat.setdefault("dodge", 0)
            c.combat.setdefault("initiative", 0)
            c.combat.setdefault("actions_per_round", 2)
            c.combat.setdefault("weapons", [])

        if not isinstance(c.bio_e, dict):
            c.bio_e = {"total": 0, "spent": 0, "traits": []}
        else:
            c.bio_e.setdefault("total", 0)
            c.bio_e.setdefault("spent", 0)
            c.bio_e.setdefault("traits", [])

        if not isinstance(c.ta_time_devices, dict):
            c.ta_time_devices = {}

        c.image_path = str(c.image_path or "")
        c.armor_type = str(c.armor_type or "")
        c.armor_name = str(c.armor_name or "")
        c.armor_wt = str(c.armor_wt or "")
        c.armor_properties = str(c.armor_properties or "")
        c.shield_type = str(c.shield_type or "")
        c.shield_notes = str(c.shield_notes or "")

        c.total_credits = int(c.total_credits or 0)
        c.total_wealth = int(c.total_wealth or 0)
        c.armor_ar = int(c.armor_ar or 0)
        c.armor_sdc = int(c.armor_sdc or 0)
        c.hit_points = int(c.hit_points or 0)
        c.sdc = int(c.sdc or 0)
        c.xp = int(c.xp or 0)
        c.level = int(c.level or 1)

        return c

    def default_filename(self) -> str:
        base = safe_filename(self.name)
        if not base:
            base = "Unnamed"
        return f"{base}.json"