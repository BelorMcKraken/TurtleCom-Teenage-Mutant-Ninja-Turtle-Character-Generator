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

    armor_name: str = ""
    armor_ar: int = 0
    armor_sdc: int = 0
    armor_wt: str = ""
    armor_properties: str = ""

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
    # v0.1: fixed slots of dropdown selections (later: full skill objects w/ %)
    skills: Dict[str, List[str]] = field(default_factory=lambda: {
        "pro": [""] * 10,
        "amateur": [""] * 15,
    })

    # ---------- COMBAT ----------
    combat: Dict[str, Any] = field(default_factory=lambda: {
        "strike": 0,
        "parry": 0,
        "dodge": 0,
        "initiative": 0,
        "attacks_per_melee": 0,
        "weapons": []
    })

    # ---------- BIO-E ----------
    bio_e: Dict[str, Any] = field(default_factory=lambda: {
        "total": 0,
        "spent": 0,
        "traits": []
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

        # Defensive: if loading older files that used dict style
        # normalize to list slots so the UI won't crash.
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

            pro = (pro + [""] * 10)[:10]
            ama = (ama + [""] * 15)[:15]

            c.skills = {"pro": pro, "amateur": ama}

        return c

    def default_filename(self) -> str:
        base = safe_filename(self.name)
        if not base:
            base = "Unnamed"
        return f"{base}.json"