from __future__ import annotations

from pathlib import Path
from typing import Optional, Any, Tuple, List
import json
import random
import re
import copy

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem, QPixmap, QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QTextEdit,
    QMessageBox,
    QFileDialog,
    QLabel,
    QTabWidget,
    QComboBox,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QApplication,
    QGroupBox,
    QGridLayout,
    QScrollArea,
    QStackedWidget,
    QToolBar,
)


from app.config import CHARACTERS_DIR, DATA_DIR, project_root
from app.models import Character
from app.services.export_statblock_pdf import export_statblock_pdf
from app.services.export_ta_time_machine_pdf import export_ta_time_machine_pdf
from app.services import (
    list_character_files,
    load_character,
    save_character,
    delete_character_file,
)
from app.rules.armor import ARMOR_CATALOG, ARMOR_BY_NAME
from app.rules.gear import GEAR_CATALOG, GEAR_BY_NAME
from app.rules.random_names import ANIMAL_NAME_POOLS
from app.rules.shields import SHIELD_CATALOG, SHIELD_BY_NAME
from app.rules.skills import load_skill_rules
from app.rules.vehicles import (
    VEHICLES_AIRCRAFT,
    VEHICLES_LANDCRAFT,
    VEHICLES_LOOKUP,
    VEHICLES_WATERCRAFT,
)
from app.rules.weapons import WEAPONS_CATALOG, WEAPONS_BY_NAME
from app.rules.bioe_animals import BIOE_ANIMAL_DATA
from app.rules.bioe_lookup import BIOE_ANIMAL_ALIASES, BIOE_DEFAULT_ANIMAL, bioe_norm
from app.rules.physical_skill_effects import PHYSICAL_SKILL_EFFECTS
from app.rules.human_features import HUMAN_FEATURE_OPTIONS
from app.rules.psionic_powers import PSIONIC_POWER_OPTIONS
from app.rules.psionic_catalog import (
    PSIONIC_CATEGORY_MUTANT_ANIMAL,
    PSIONIC_CATEGORY_MUTANT_HOMINID,
    PSIONIC_CATEGORY_MUTANT_PROSTHETIC,
    PSIONIC_CATEGORY_MUTANT_HUMAN_ABILITIES,
    PSIONIC_CATEGORY_MUTANT_HOMINID_ABILITIES,
    get_psionic_catalog_options,
)
from app.rules.size_levels import SIZE_LEVEL_EFFECTS, SIZE_LEVEL_FORMULAS
from app.rules.combat import BASELINE_COMBAT, COMBAT_TRAINING_RULES
from app.rules.tmntos_animals import TMNTOS_ANIMAL_TYPE_RANGES, TMNTOS_ANIMALS_BY_TYPE
from app.rules.tmntta_animals import TMNTTA_ANIMAL_TYPE_RANGES, TMNTTA_ANIMALS_BY_TYPE
from app.rules.tmntos_backgrounds import (
    TMNTOS_MUTANT_ANIMAL_ORIGINS,
    TMNTOS_CREATOR_ORGANIZATIONS,
    TMNTOS_WILD_ANIMAL_EDUCATION,
)
from app.rules.tmntta_backgrounds import (
    TMNTTA_MUTANT_ANIMAL_ORIGINS,
    TMNTTA_CONTEMPORARY_ORIGINS,
    TMNTTA_TIME_TRAVEL_ORIGINS,
    TMNTTA_CROSS_DIMENSIONAL_ORIGINS,
    TMNTTA_EXPERIMENTAL_ANIMAL_BACKGROUNDS,
    TMNTTA_WILD_ANIMAL_BACKGROUNDS,
)
from app.rules.tmntta_time_devices import (
    TMNTTA_TIME_DEVICES,
    TMNTTA_TEMPORAL_SUPPORT_DEVICES,
    TMNTTA_TIME_DEVICE_INSTALL_COSTS,
    TMNTTA_TIME_DEVICES_BY_NAME,
    TMNTTA_TEMPORAL_SUPPORT_BY_NAME,
)
from app.utils.dice import eval_dice_expression, roll_dice, roll_d100
from app.generators.random_character import (
    pick_from_ranges,
    random_name_for_animal,
    roll_attribute_score,
    roll_size_choice,
)


def build_arrow_icons_qss(icons_dir: str) -> str:
    """
    Returns QSS to force Qt arrow indicators to use our SVG icons.
    Works for QSpinBox/QDoubleSpinBox (QAbstractSpinBox) + QComboBox arrows.
    """
    d = Path(icons_dir)

    up            = (d / "turtle-arrow-up.svg").as_posix()
    up_hover      = (d / "turtle-arrow-up-hover.svg").as_posix()
    up_pressed    = (d / "turtle-arrow-up-pressed.svg").as_posix()

    down          = (d / "turtle-arrow-down.svg").as_posix()
    down_hover    = (d / "turtle-arrow-down-hover.svg").as_posix()
    down_pressed  = (d / "turtle-arrow-down-pressed.svg").as_posix()

    return f"""
/* ---------- SPINBOX UP/DOWN BUTTONS ---------- */
QAbstractSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 20px;
    border: none;
}}
QAbstractSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 20px;
    border: none;
}}

QAbstractSpinBox::up-arrow {{
    image: url("{up}");
    width: 14px;
    height: 14px;
}}
QAbstractSpinBox::up-arrow:hover {{
    image: url("{up_hover}");
}}
QAbstractSpinBox::up-arrow:pressed {{
    image: url("{up_pressed}");
}}

QAbstractSpinBox::down-arrow {{
    image: url("{down}");
    width: 14px;
    height: 14px;
}}
QAbstractSpinBox::down-arrow:hover {{
    image: url("{down_hover}");
}}
QAbstractSpinBox::down-arrow:pressed {{
    image: url("{down_pressed}");
}}

/* ---------- COMBOBOX DROPDOWN ARROW ---------- */
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border: none;
}}
QComboBox::down-arrow {{
    image: url("{down}");
    width: 14px;
    height: 14px;
}}
QComboBox::down-arrow:hover {{
    image: url("{down_hover}");
}}
QComboBox::down-arrow:on {{
    image: url("{down_pressed}");
}}
"""
APP_NAME = "TurtleCom"
APP_VERSION = "v4.0"

# ---------------- Dark theme (no arrow images here) ----------------
DARK_QSS = """
QWidget {
    background-color: #1e1e1e;
    color: #e6e6e6;
    font-size: 12pt;
}

QLineEdit, QTextEdit, QPlainTextEdit, QListWidget, QComboBox {
    background-color: #2a2a2a;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    padding: 6px;
    selection-background-color: #3d6dcc;
}

QSpinBox, QDoubleSpinBox {
    background-color: #2a2a2a;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    padding: 6px;
    padding-right: 26px;
    selection-background-color: #3d6dcc;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    width: 22px;
    background: #2f2f2f;
    border-left: 1px solid #3a3a3a;
}

QSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    border-bottom: 1px solid #3a3a3a;
    border-top-right-radius: 6px;
}

QSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    border-bottom-right-radius: 6px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background: #3a3a3a;
}

QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed,
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {
    background: #444444;
}

QTabWidget::pane {
    border: 1px solid #3a3a3a;
    border-radius: 8px;
}

QTabBar::tab {
    background: #2a2a2a;
    border: 1px solid #3a3a3a;
    padding: 8px 12px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}

QTabBar::tab:selected {
    background: #333333;
    border-bottom-color: #333333;
}

QPushButton {
    background-color: #2f2f2f;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    padding: 8px 12px;
}

QPushButton:hover {
    background-color: #3a3a3a;
}

QPushButton:pressed {
    background-color: #444444;
}

QStatusBar {
    background-color: #1a1a1a;
    border-top: 1px solid #333333;
}

QMenuBar {
    background-color: #1e1e1e;
}

QMenuBar::item:selected {
    background-color: #333333;
}

QMenu {
    background-color: #1e1e1e;
    border: 1px solid #3a3a3a;
}

QMenu::item:selected {
    background-color: #333333;
}
"""


def _simple_attribute_mod(score: int) -> int:
    return max(0, (score - 10) // 2)


def _roll_d100() -> int:
    return random.randint(1, 100)


def _pick_from_ranges(table: list[tuple[range, str]], roll: int) -> str:
    for r, name in table:
        if roll in r:
            return name
    return ""

def _pick_payload_from_ranges(
    table: list[tuple[range, dict[str, str]]],
    roll: int,
) -> dict[str, str]:
    for value_range, payload in table:
        if roll in value_range:
            return payload
    return {"name": "", "details": ""}

def _cost_to_int(cost: str) -> int:
    if not cost:
        return 0
    s = cost.strip().lower()
    if s in {"—", "-", "n/a"}:
        return 0
    if "not" in s and "sold" in s:
        return 0

    s = s.replace(",", "")
    s = s.replace(" ", "")
    s = s.replace("usd", "")
    s = s.replace("+", "")

    for sep in ("–", "-"):
        if sep in s and "$" in s:
            left = s.split(sep, 1)[0]
            return _cost_to_int(left)

    s = s.replace("$", "")

    mult = 1
    if s.endswith("k"):
        mult = 1000
        s = s[:-1]
    if s.endswith("mil"):
        mult = 1_000_000
        s = s[:-3]

    m = re.search(r"(\d+)", s)
    if not m:
        return 0
    return int(m.group(1)) * mult



def _unique_items(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out


def _training_names() -> list[str]:
    return ["None"] + sorted(COMBAT_TRAINING_RULES.keys())


def _combine_melee_damage(dmg_list: list[str]) -> str:
    if not dmg_list:
        return "—"
    return ", ".join(dmg_list)






class AboutDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setModal(True)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        logo_path = project_root() / "assets" / "images" / "TurtleCom Logo.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path))
            if not pix.isNull():
                logo = QLabel()
                logo.setAlignment(Qt.AlignHCenter)
                logo.setPixmap(pix.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                layout.addWidget(logo)

        title = QLabel(f"<h2>{APP_NAME} <span style='font-weight:400'>({APP_VERSION})</span></h2>")
        title.setAlignment(Qt.AlignHCenter)
        layout.addWidget(title)

        credits = QLabel(
            "Offline TMNT & Other Strangeness Redux character tool.<br>"
            "Built with Python + PySide6 (Qt).<br><br>"
            "<b>Credits</b><br>"
            "Design & implementation: Belor Mck + ChatGPT via VIBE CODING!<br>"
            "Rules/content: TMNT & Other Strangeness Redux (Palladium Books)<br>"
        )
        credits.setAlignment(Qt.AlignHCenter)
        credits.setWordWrap(True)
        layout.addWidget(credits)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — Character Generator ({APP_VERSION})")
        self.resize(1100, 700)

        self.current_path: Optional[Path] = None
        self.current_character: Character = Character()

        self.dark_mode_enabled: bool = True

        self.skill_rules: dict[str, Any] = {}
        self.pro_skill_lookup: dict[str, dict[str, Any]] = {}
        self.amateur_skill_lookup: dict[str, dict[str, Any]] = {}
        self.pro_model: Optional[QStandardItemModel] = None
        self.amateur_model: Optional[QStandardItemModel] = None

        self.bio_weapon_cost_labels = []
        self.bio_ability_cost_labels = []


        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.welcome_page = QWidget()
        self.editor_page = QWidget()

        self.stack.addWidget(self.welcome_page)
        self.stack.addWidget(self.editor_page)

        self._build_menu()
        self._build_toolbar()

        self._build_welcome_page()
        self._build_editor_page()


        self.statusBar().showMessage("Ready")
        self.version_label = QLabel(APP_VERSION)
        self.statusBar().addPermanentWidget(self.version_label)

        self.refresh_list()
        self.refresh_welcome_list()
        self.on_toggle_dark_mode(True)

        self.stack.setCurrentWidget(self.welcome_page)


    def on_export_ta_pdf(self) -> None:
        c = self.editor_to_character()

        suggested_name = f"{c.default_filename().replace('.json', '')}.time-machine.pdf"
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Export Time Machine PDF",
            str(CHARACTERS_DIR / suggested_name),
            "PDF Files (*.pdf)",
        )
        if not path_str:
            return

        out_path = Path(path_str)
        if out_path.suffix.lower() != ".pdf":
            out_path = out_path.with_suffix(".pdf")

        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            export_ta_time_machine_pdf(c, out_path)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export failed",
                f"Could not export Time Machine PDF:\n{out_path}\n\n{e}",
            )
            return

        self.statusBar().showMessage(f"Exported Time Machine PDF: {out_path.name}", 4000)

    def on_export_statblock_pdf(self) -> None:
        c = self.editor_to_character()

        suggested_name = f"{c.default_filename().replace('.json', '')}.statblock.pdf"
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Export Statblock PDF",
            str(CHARACTERS_DIR / suggested_name),
            "PDF Files (*.pdf)",
        )
        if not path_str:
            return

        out_path = Path(path_str)
        if out_path.suffix.lower() != ".pdf":
            out_path = out_path.with_suffix(".pdf")

        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            export_statblock_pdf(c, out_path)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export failed",
                f"Could not export statblock PDF:\n{out_path}\n\n{e}",
            )
            return

        self.statusBar().showMessage(f"Exported statblock PDF: {out_path.name}", 4000)

    def build_foundry_export_payload(self) -> dict[str, Any]:
        c = self.editor_to_character()

        payload: dict[str, Any] = {
            "format": "tmntos-foundry-placeholder",
            "version": 1,
            "character": {
                "name": c.name,
                "animal": getattr(c, "animal", ""),
                "alignment": getattr(c, "alignment", ""),
                "age": getattr(c, "age", ""),
                "gender": getattr(c, "gender", ""),
                "weight": getattr(c, "weight", ""),
                "height": getattr(c, "height", ""),
                "size": getattr(c, "size", ""),
                "level": getattr(c, "level", 1),
                "xp": getattr(c, "xp", 0),
                "hit_points": getattr(c, "hit_points", 0),
                "sdc": getattr(c, "sdc", 0),
                "attributes": copy.deepcopy(getattr(c, "attributes", {})),
                "skills": copy.deepcopy(getattr(c, "skills", {})),
                "combat": copy.deepcopy(getattr(c, "combat", {})),
                "bio_e": copy.deepcopy(getattr(c, "bio_e", {})),
                "vehicles": copy.deepcopy(getattr(c, "vehicles", {})),
                "weapons_selected": copy.deepcopy(getattr(c, "weapons_selected", [])),
                "gear_selected": copy.deepcopy(getattr(c, "gear_selected", [])),
                "armor_name": getattr(c, "armor_name", ""),
                "armor_ar": getattr(c, "armor_ar", 0),
                "armor_sdc": getattr(c, "armor_sdc", 0),
                "armor_type": getattr(c, "armor_type", ""),
                "shield_type": getattr(c, "shield_type", ""),
                "shield_notes": getattr(c, "shield_notes", ""),
                "notes": getattr(c, "notes", ""),
            },
        }
        return payload
    


    def _find_payload_by_name(
        self,
        table: list[tuple[range, dict[str, str]]],
        name: str,
    ) -> dict[str, str]:
        for _, payload in table:
            if payload.get("name") == name:
                return payload
        return {"name": "", "details": ""}


    def _tmntta_origin_subtable(self, category_name: str) -> list[tuple[range, dict[str, str]]]:
        if category_name == "Contemporary Character":
            return TMNTTA_CONTEMPORARY_ORIGINS
        if category_name == "Time-Traveling Character":
            return TMNTTA_TIME_TRAVEL_ORIGINS
        if category_name == "Cross-Dimensional Character":
            return TMNTTA_CROSS_DIMENSIONAL_ORIGINS
        return []


    def _tmntta_background_table_for_origin(
        self,
        origin_name: str,
    ) -> list[tuple[range, dict[str, str]]]:
        if origin_name in {
            "Animal Sample from the Jurassic",
            "Animal Sample from the Cretaceous",
            "Animal Sample from the Cenozoic",
            "Animal Sample from the Far Future",
            "Cloned Prehistoric Animal",
            "Experimental Test Animal",
        }:
            return TMNTTA_EXPERIMENTAL_ANIMAL_BACKGROUNDS

        if origin_name in {
            "Accidental Cretaceous Hitchhiker",
            "Accidental Cenozoic Hitchhiker",
            "Ordinary Mutant Animal Mutated by Temporal Devices",
        }:
            return TMNTTA_WILD_ANIMAL_BACKGROUNDS

        if origin_name == "Standard TMNT & Other Strangeness Mutant Animal":
            return TMNTOS_WILD_ANIMAL_EDUCATION

        return []


    def _reload_origin_controls_for_source(self) -> None:
        source = str(self.cb_animal_source.currentData() or "")

        self.cb_mutant_origin.blockSignals(True)
        self.cb_background_education.blockSignals(True)
        self.cb_creator_organization.blockSignals(True)
        try:
            self.cb_mutant_origin.clear()
            self.cb_background_education.clear()
            self.cb_creator_organization.clear()

            self.cb_mutant_origin.addItem("Roll or select your origin", "")
            self.cb_background_education.addItem("Roll or select your background", "")
            self.cb_creator_organization.addItem("Not used for this source", "")

            if source == "tmntos":
                for _, payload in TMNTOS_MUTANT_ANIMAL_ORIGINS:
                    self.cb_mutant_origin.addItem(payload["name"], payload["name"])
                for _, payload in TMNTOS_WILD_ANIMAL_EDUCATION:
                    self.cb_background_education.addItem(payload["name"], payload["name"])
                for _, payload in TMNTOS_CREATOR_ORGANIZATIONS:
                    self.cb_creator_organization.addItem(payload["name"], payload["name"])
                self.cb_creator_organization.setEnabled(True)
                self.btn_roll_creator_organization.setEnabled(True)

            elif source == "tmntta":
                for _, payload in TMNTTA_MUTANT_ANIMAL_ORIGINS:
                    self.cb_mutant_origin.addItem(payload["name"], payload["name"])

                self.cb_creator_organization.setEnabled(False)
                self.btn_roll_creator_organization.setEnabled(False)

        finally:
            self.cb_mutant_origin.blockSignals(False)
            self.cb_background_education.blockSignals(False)
            self.cb_creator_organization.blockSignals(False)

        self.ed_mutant_origin_details.clear()
        self.ed_background_education_details.clear()
        self.ed_creator_organization_details.clear()
        
    def on_export_foundry_json(self) -> None:
        payload = self.build_foundry_export_payload()

        suggested_name = f"{self.editor_to_character().default_filename().replace('.json', '')}.foundry.json"
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Export JSON for Foundry VTT",
            str(CHARACTERS_DIR / suggested_name),
            "JSON Files (*.json)",
        )
        if not path_str:
            return

        path = Path(path_str)
        if path.suffix.lower() != ".json":
            path = path.with_suffix(".json")

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, "Export failed", f"Could not export Foundry JSON:\n{path}\n\n{e}")
            return

        self.statusBar().showMessage(f"Exported Foundry JSON: {path.name}", 4000)

    def on_mutant_origin_changed(self) -> None:
        selected = str(self.cb_mutant_origin.currentData() or "")
        source = str(self.cb_animal_source.currentData() or "")
        details = ""

        if source == "tmntos":
            for _, payload in TMNTOS_MUTANT_ANIMAL_ORIGINS:
                if payload["name"] == selected:
                    details = payload.get("details", "")
                    break
            self.ed_mutant_origin_details.setPlainText(details)
            self.update_creator_organization_enabled()
            if selected != "Deliberate Experimentation":
                self.cb_creator_organization.setCurrentIndex(0)
                self.ed_creator_organization_details.clear()
            return

        if source == "tmntta":
            category_payload = self._find_payload_by_name(TMNTTA_MUTANT_ANIMAL_ORIGINS, selected)
            details = category_payload.get("details", "")
            self.ed_mutant_origin_details.setPlainText(details)

            subtable = self._tmntta_origin_subtable(selected)

            self.cb_background_education.blockSignals(True)
            try:
                self.cb_background_education.clear()
                self.cb_background_education.addItem("Roll or select your background", "")
                for _, payload in subtable:
                    self.cb_background_education.addItem(payload["name"], payload["name"])
            finally:
                self.cb_background_education.blockSignals(False)

            self.ed_background_education_details.clear()
            self.cb_creator_organization.setCurrentIndex(0)
            self.ed_creator_organization_details.clear()
            self.cb_creator_organization.setEnabled(False)
            self.btn_roll_creator_organization.setEnabled(False)


    def on_background_education_changed(self) -> None:
        selected = str(self.cb_background_education.currentData() or "")
        source = str(self.cb_animal_source.currentData() or "")
        details = ""

        if source == "tmntos":
            for _, payload in TMNTOS_WILD_ANIMAL_EDUCATION:
                if payload["name"] == selected:
                    details = payload.get("details", "")
                    break
            self.ed_background_education_details.setPlainText(details)
            return

        if source == "tmntta":
            category_name = str(self.cb_mutant_origin.currentData() or "")
            table = self._tmntta_origin_subtable(category_name)
            for _, payload in table:
                if payload["name"] == selected:
                    details = payload.get("details", "")
                    break
            self.ed_background_education_details.setPlainText(details)


    def on_creator_organization_changed(self) -> None:
        selected = str(self.cb_creator_organization.currentData() or "")
        source = str(self.cb_animal_source.currentData() or "")
        details = ""

        if source == "tmntos":
            for _, payload in TMNTOS_CREATOR_ORGANIZATIONS:
                if payload["name"] == selected:
                    details = payload.get("details", "")
                    break

        self.ed_creator_organization_details.setPlainText(details)


    # app/ui/main_window.py

    def build_pdf_field_map(self) -> dict[str, str]:
        c = self.editor_to_character()

        attrs = getattr(c, "attributes", {}) or {}
        combat = getattr(c, "combat", {}) or {}
        bio_e = getattr(c, "bio_e", {}) or {}
        human_features = bio_e.get("human_features", {}) or {}
        original = bio_e.get("original", {}) or {}

        weapons_selected = list(getattr(c, "weapons_selected", []) or [])
        gear_selected = list(getattr(c, "gear_selected", []) or [])
        pro_skills = list(getattr(c, "skills", {}).get("pro", []) or [])
        amateur_skills = list(getattr(c, "skills", {}).get("amateur", []) or [])

        natural_weapons = list(bio_e.get("natural_weapons", []) or [])
        animal_abilities = list(bio_e.get("abilities", []) or [])

        mutant_animal_psionics = list(
            bio_e.get("mutant_animal_psionic_powers", []) or bio_e.get("psionics", []) or []
        )
        mutant_hominid_psionics = list(bio_e.get("mutant_hominid_psionic_powers", []) or [])
        mutant_prosthetic_psionics = list(bio_e.get("mutant_prosthetic_psionic_powers", []) or [])
        mutant_human_abilities = list(bio_e.get("mutant_human_abilities", []) or [])
        mutant_hominid_abilities = list(bio_e.get("mutant_hominid_abilities", []) or [])

        armor_type = str(getattr(c, "armor_type", "") or "")
        shield_type = str(getattr(c, "shield_type", "") or "")
        shield_notes = str(getattr(c, "shield_notes", "") or "")

        armor_lookup = ARMOR_BY_NAME.get(armor_type, {}) if armor_type else {}
        shield_lookup = resolve_shield_details(shield_type)

        def text(value: Any) -> str:
            if value is None:
                return ""
            return str(value)

        def non_empty(*values: Any) -> str:
            for value in values:
                s = text(value).strip()
                if s:
                    return s
            return ""

        def list_item_name(items: list[Any], index: int) -> str:
            if index >= len(items):
                return ""
            item = items[index]
            if isinstance(item, dict):
                return str(item.get("name", "") or "")
            return str(item or "")

        def list_item_cost(items: list[Any], index: int) -> str:
            if index >= len(items):
                return ""
            item = items[index]
            if isinstance(item, dict):
                return str(item.get("cost", "") or "")
            return ""

        def total_cost(items: list[Any]) -> int:
            total = 0
            for item in items:
                if isinstance(item, dict):
                    total += int(item.get("cost", 0) or 0)
            return total

        def skill_pct(name: str, lookup: dict[str, dict[str, Any]]) -> str:
            if not name:
                return ""
            pct = self._calc_skill_pct(name, lookup)
            return f"{pct}%" if pct is not None else ""

        field_map: dict[str, str] = {
            "Name": text(getattr(c, "name", "")),
            "Alignment": text(getattr(c, "alignment", "")),
            "Sex": text(getattr(c, "gender", "")),
            "Age": text(getattr(c, "age", "")),
            "Animal.Type": text(getattr(c, "animal", "")),
            "Character.Level": text(getattr(c, "level", "")),
            "XP": text(getattr(c, "xp", "")),
            "Height": text(getattr(c, "height", "")),
            "Weight": text(getattr(c, "weight", "")),
            "Hit.Points": text(getattr(c, "hit_points", "")),
            "SDC": text(getattr(c, "sdc", "")),
            "Origin.Animal.Size": text(original.get("size_level", "") or getattr(c, "size", "")),
            "Mutant.Form.Size": text(bio_e.get("mutant_size_label", "") or getattr(c, "size", "")),
            "Armor.Type": non_empty(getattr(c, "armor_name", ""), armor_type),
            "Armor.Rating": text(getattr(c, "armor_ar", "")),
            "Armor.SDC": text(getattr(c, "armor_sdc", "")),
            "Armor.Weight": non_empty(
                getattr(c, "armor_wt", ""),
                armor_lookup.get("weight"),
                armor_lookup.get("wt"),
            ),
            "Armor.Properties.0": non_empty(
                getattr(c, "armor_properties", ""),
                armor_lookup.get("properties"),
                armor_lookup.get("notes"),
            ),
            "Armor.Properties.1": non_empty(
                f"Shield: {shield_lookup['name']}" if shield_lookup["name"] else "",
                shield_notes,
                shield_lookup.get("notes", ""),
            ),
            "Combat.Style": text(combat.get("training", "")),
            "Actions": text(combat.get("actions_per_round", "")),
            "Initiative": text(combat.get("initiative", "")),
            "Melee.Strike": text(combat.get("strike", "")),
            "Melee.Parry": text(combat.get("parry", "")),
            "Dodge": text(combat.get("dodge", "")),
            "Roll": text(combat.get("roll_with_impact", "")),
            "Intelligence": text(attrs.get("IQ - Intelligence Quotient", "")),
            "Mental.Endurance": text(attrs.get("ME - Mental Endurance", "")),
            "Mental.Affinity": text(attrs.get("MA - Mental Affinity", "")),
            "Physical.Strength": text(attrs.get("PS - Physical Strength", "")),
            "Physical.Prowess": text(attrs.get("PP - Physical Prowess", "")),
            "Physical.Endurance": text(attrs.get("PE - Physical Endurance", "")),
            "Physical.Beauty": text(attrs.get("PB - Physical Beauty", "")),
            "Speed": text(attrs.get("Speed", "")),
            "Scholastic.Skills.0": text(pro_skills[0] if len(pro_skills) > 0 else ""),
            "Scholastic.Skills.1": text(pro_skills[1] if len(pro_skills) > 1 else ""),
            "Scholastic.Skills.2": text(pro_skills[2] if len(pro_skills) > 2 else ""),
            "Scholastic.Skills.3": text(pro_skills[3] if len(pro_skills) > 3 else ""),
            "Scholastic.Skills.4": text(pro_skills[4] if len(pro_skills) > 4 else ""),
            "Scholastic.Skills.5": text(pro_skills[5] if len(pro_skills) > 5 else ""),
            "Scholastic.Skills.6": text(pro_skills[6] if len(pro_skills) > 6 else ""),
            "Scholastic.Skills.7": text(pro_skills[7] if len(pro_skills) > 7 else ""),
            "Scholastic.Skills.8": text(pro_skills[8] if len(pro_skills) > 8 else ""),
            "Scholastic.Skills.9": text(pro_skills[9] if len(pro_skills) > 9 else ""),
            "Scholastic.Skills.10": text(pro_skills[10] if len(pro_skills) > 10 else ""),
            "Scholastic.Skills.11": text(pro_skills[11] if len(pro_skills) > 11 else ""),
            "Secondary.Skills.0": text(amateur_skills[0] if len(amateur_skills) > 0 else ""),
            "Secondary.Skills.1": text(amateur_skills[1] if len(amateur_skills) > 1 else ""),
            "Secondary.Skills.2": text(amateur_skills[2] if len(amateur_skills) > 2 else ""),
            "Secondary.Skills.3": text(amateur_skills[3] if len(amateur_skills) > 3 else ""),
            "Secondary.Skills.4": text(amateur_skills[4] if len(amateur_skills) > 4 else ""),
            "Secondary.Skills.5": text(amateur_skills[5] if len(amateur_skills) > 5 else ""),
            "Secondary.Skills.6": text(amateur_skills[6] if len(amateur_skills) > 6 else ""),
            "Secondary.Skills.7": text(amateur_skills[7] if len(amateur_skills) > 7 else ""),
            "Secondary.Skills.8": text(amateur_skills[8] if len(amateur_skills) > 8 else ""),
            "Secondary.Skills.9": text(amateur_skills[9] if len(amateur_skills) > 9 else ""),
            "Secondary.Skills.10": text(amateur_skills[10] if len(amateur_skills) > 10 else ""),
            "Secondary.Skills.11": text(amateur_skills[11] if len(amateur_skills) > 11 else ""),
            "Equipment.Valuables.1": text(getattr(c, "total_credits", "")),
            "Equipment.Valuables.2": text(getattr(c, "total_wealth", "")),
            "Equipment.Valuables.3": text(gear_selected[0] if len(gear_selected) > 0 else ""),
            "Equipment.Valuables.4": text(gear_selected[1] if len(gear_selected) > 1 else ""),
            "Ch.Notes.0": text(gear_selected[2] if len(gear_selected) > 2 else ""),
            "Ch.Notes.1": text(gear_selected[3] if len(gear_selected) > 3 else ""),
            "Ch.Notes.2": text(gear_selected[4] if len(gear_selected) > 4 else ""),
            "Ch.Notes.3": text(gear_selected[5] if len(gear_selected) > 5 else ""),
            "Ch.Notes.4": text(gear_selected[6] if len(gear_selected) > 6 else ""),
            "Ch.Notes.5": text(gear_selected[7] if len(gear_selected) > 7 else ""),
            "Ch.Notes.6": text(gear_selected[8] if len(gear_selected) > 8 else ""),
            "Ch.Notes.7": text(gear_selected[9] if len(gear_selected) > 9 else ""),
            "Origin.Mutant": text(bio_e.get("mutant_origin", {}).get("name", "")),
            "Build.Notes.0": text(bio_e.get("mutant_origin", {}).get("details", "")),
            "Build.Notes.1": text(bio_e.get("background_education", {}).get("name", "")),
            "Build.Notes.2": text(bio_e.get("creator_organization", {}).get("name", "")),
            "Build.Notes.3": text(bio_e.get("background_education", {}).get("details", "")),
            "Build.Notes.4": text(bio_e.get("creator_organization", {}).get("details", "")),
            "Build.Notes.5": text(getattr(c, "notes", "")),
            "Starting.BioE": text(bio_e.get("total", "")),
            "Final.BioE.Cost": text(bio_e.get("spent", "")),
            "BioE.Cost.Mutant.Form.Size": text(
                SIZE_LEVEL_EFFECTS.get(int(bio_e.get("mutant_size_level", 0) or 0), {}).get("bio_e", "")
            ),
            "Human.Features.Biped.0": text(human_features.get("biped_label", "")),
            "Human.Features.Hands.0": text(human_features.get("hands_label", "")),
            "Human.Features.Speech.0": text(human_features.get("speech_label", "")),
            "Human.Features.Looks.0": text(human_features.get("looks_label", "")),
            "BioE.Cost.Human.Features.Biped": text(human_features.get("biped_cost", "")),
            "BioE.Cost.Human.Features.Hands": text(human_features.get("hands_cost", "")),
            "BioE.Cost.Human.Features.Speech": text(human_features.get("speech_cost", "")),
            "BioE.Cost.Human.Features.Looks": text(human_features.get("looks_cost", "")),
            "BioE.Cost.Human.Features.Total": text(
                int(human_features.get("biped_cost", 0) or 0)
                + int(human_features.get("hands_cost", 0) or 0)
                + int(human_features.get("speech_cost", 0) or 0)
                + int(human_features.get("looks_cost", 0) or 0)
            ),
            "Abilities.Animal.Teeth": text(list_item_name(natural_weapons, 0)),
            "Abilities.Animal.Claws": text(list_item_name(natural_weapons, 1)),
            "Abilities.Animal.Horns": text(list_item_name(natural_weapons, 2)),
            "Abilities.Animal.Other.0": text(list_item_name(animal_abilities, 0)),
            "Abilities.Animal.Other.1": text(list_item_name(animal_abilities, 1)),
            "Abilities.Animal.Other.2": text(list_item_name(animal_abilities, 2)),
            "Abilities.Animal.Other.3": text(list_item_name(animal_abilities, 3)),
            "Abilities.Animal.Other.4": text(list_item_name(animal_abilities, 4)),
            "BioE.Cost.Teeth.Abilities": text(list_item_cost(natural_weapons, 0)),
            "BioE.Cost.Claws.Abilities": text(list_item_cost(natural_weapons, 1)),
            "BioE.Cost.Horns.Abilities": text(list_item_cost(natural_weapons, 2)),
            "BioE.Cost.Other.Abilities.0": text(list_item_cost(animal_abilities, 0)),
            "BioE.Cost.Other.Abilities.1": text(list_item_cost(animal_abilities, 1)),
            "BioE.Cost.Other.Abilities.2": text(list_item_cost(animal_abilities, 2)),
            "BioE.Cost.Other.Abilities.3": text(list_item_cost(animal_abilities, 3)),
            "BioE.Cost.Other.Abilities.4": text(list_item_cost(animal_abilities, 4)),
            "Psionic.Spell.Name.0": text(list_item_name(mutant_animal_psionics, 0)),
            "Psionic.Spell.Name.1": text(list_item_name(mutant_animal_psionics, 1)),
            "Psionic.Spell.Name.2": text(list_item_name(mutant_animal_psionics, 2)),
            "Psionic.Spell.Name.3": text(list_item_name(mutant_animal_psionics, 3)),
            "Psionic.Spell.Name.4": text(list_item_name(mutant_animal_psionics, 4)),
            "Psionic.Spell.Name.5": text(list_item_name(mutant_animal_psionics, 5)),
            "Psionic.Spell.Name.6": text(list_item_name(mutant_animal_psionics, 6)),
            "Psionic.Spell.Name.7": text(list_item_name(mutant_animal_psionics, 7)),
            "Ch.Notes.8": text(list_item_name(mutant_hominid_psionics, 0)),
            "Ch.Notes.9": text(list_item_name(mutant_hominid_psionics, 1)),
            "Ch.Notes.10": text(list_item_name(mutant_hominid_psionics, 2)),
            "Ch.Notes.11": text(list_item_name(mutant_prosthetic_psionics, 0)),
            "Ch.Notes.12": text(list_item_name(mutant_human_abilities, 0)),
            "Total.Cost.Mutant.Psionics": text(
                total_cost(mutant_animal_psionics)
                + total_cost(mutant_hominid_psionics)
                + total_cost(mutant_prosthetic_psionics)
            ),
            "Total.Cost.Mutant.Abilities": text(
                total_cost(animal_abilities)
                + total_cost(mutant_human_abilities)
                + total_cost(mutant_hominid_abilities)
            ),
        }

        for i in range(12):
            pro_name = pro_skills[i] if i < len(pro_skills) else ""
            pro_pct = skill_pct(pro_name, self.pro_skill_lookup)
            field_map[f"Scholastic.Skills.Pct.{i}"] = pro_pct
            field_map[f"Scholastic.Skills.Percent.{i}"] = pro_pct

            ama_name = amateur_skills[i] if i < len(amateur_skills) else ""
            ama_pct = skill_pct(ama_name, self.amateur_skill_lookup)
            field_map[f"Secondary.Skills.Pct.{i}"] = ama_pct
            field_map[f"Secondary.Skills.Percent.{i}"] = ama_pct

        weapon_names = [w for w in weapons_selected if str(w).strip()]
        for i, name in enumerate(weapon_names[:6]):
            details = resolve_weapon_details(str(name).strip())
            field_map[f"Weapon.Proficiency.{i}"] = details["name"]
            field_map[f"Type.Weapon.{i}"] = details["type"]
            field_map[f"W.Damage.{i}"] = details["damage"]
            field_map[f"Weapon.Damage.{i}"] = details["damage"]
            field_map[f"W.Range.{i}"] = details["range"]
            field_map[f"Weapon.Range.{i}"] = details["range"]
            field_map[f"W.Notes.{i}"] = details["notes"]
            field_map[f"Weapon.Notes.{i}"] = details["notes"]

        if shield_lookup["name"]:
            field_map["Shield.Type"] = shield_lookup["name"]
            field_map["Shield.SDC"] = shield_lookup["sdc"]
            field_map["Shield.Parry"] = shield_lookup["parry"]
            field_map["Shield.Notes"] = non_empty(shield_notes, shield_lookup["notes"])

        overflow_lines: list[str] = []

        if mutant_hominid_psionics:
            overflow_lines.append("Mutant Hominid Psionic Powers:")
            overflow_lines.extend(
                f"- {item.get('name', '')} ({item.get('cost', 0)} Bio-E)"
                for item in mutant_hominid_psionics
                if isinstance(item, dict)
            )

        if mutant_prosthetic_psionics:
            overflow_lines.append("Mutant Prosthetic Psionic Powers:")
            overflow_lines.extend(
                f"- {item.get('name', '')} ({item.get('cost', 0)} Bio-E)"
                for item in mutant_prosthetic_psionics
                if isinstance(item, dict)
            )

        if mutant_human_abilities:
            overflow_lines.append("Mutant Human Abilities:")
            overflow_lines.extend(
                f"- {item.get('name', '')} ({item.get('cost', 0)} Bio-E)"
                for item in mutant_human_abilities
                if isinstance(item, dict)
            )

        if mutant_hominid_abilities:
            overflow_lines.append("Mutant Hominid Abilities:")
            overflow_lines.extend(
                f"- {item.get('name', '')} ({item.get('cost', 0)} Bio-E)"
                for item in mutant_hominid_abilities
                if isinstance(item, dict)
            )

        extra_note_fields = [
            "Build.Notes.6",
            "Build.Notes.7",
            "Build.Notes.8",
            "Build.Notes.9",
            "Build.Notes.10",
            "Build.Notes.11",
            "Build.Notes.12",
        ]

        for i, line in enumerate(overflow_lines[: len(extra_note_fields)]):
            field_map[extra_note_fields[i]] = line

        selected_static_labels: list[str] = []

        def add_selected_names(items: list[Any]) -> None:
            for item in items:
                if isinstance(item, dict):
                    name = str(item.get("name", "") or "").strip()
                else:
                    name = str(item or "").strip()
                if name:
                    selected_static_labels.append(name)

        add_selected_names(natural_weapons)
        add_selected_names(animal_abilities)
        add_selected_names(mutant_animal_psionics)
        add_selected_names(mutant_hominid_psionics)
        add_selected_names(mutant_prosthetic_psionics)
        add_selected_names(mutant_human_abilities)
        add_selected_names(mutant_hominid_abilities)

        field_map["__SELECTED_STATIC_LABELS__"] = "\n".join(sorted(set(selected_static_labels), key=str.lower))
        return field_map

    def _save_vs_psionic_strangeness_from_me(self, me_value: int) -> int:
        """
        Central rule hook for Save vs Psionic & Strangeness.

        Current behavior:
        - below ME 16 => 0
        - 16+ => stepped bonus

        Edit this table if your house/system rule differs.
        """
        if me_value < 16:
            return 0
        if me_value <= 17:
            return 1
        if me_value <= 19:
            return 2
        if me_value <= 21:
            return 3
        if me_value <= 23:
            return 4
        return 5


    def _recalc_save_vs_psionic_strangeness(self) -> None:
        me_value = 0
        try:
            if hasattr(self, "sp_me"):
                me_value = int(self.sp_me.value() or 0)
            elif hasattr(self, "attr_spinners") and "ME - Mental Endurance" in self.attr_spinners:
                me_value = int(self.attr_spinners["ME - Mental Endurance"].value() or 0)
            elif hasattr(self, "attribute_fields") and "ME - Mental Endurance" in self.attribute_fields:
                me_value = int(self.attribute_fields["ME - Mental Endurance"].value() or 0)
        except Exception:
            me_value = 0

        value = self._save_vs_psionic_strangeness_from_me(me_value)

        if hasattr(self, "sp_save_vs_psionic_strangeness"):
            self.sp_save_vs_psionic_strangeness.blockSignals(True)
            try:
                self.sp_save_vs_psionic_strangeness.setValue(value)
            finally:
                self.sp_save_vs_psionic_strangeness.blockSignals(False)

    


    def on_roll_mutant_origin(self) -> None:
        source = str(self.cb_animal_source.currentData() or "")

        if source == "tmntos":
            roll = roll_d100()
            payload = _pick_payload_from_ranges(TMNTOS_MUTANT_ANIMAL_ORIGINS, roll)
            name = payload.get("name", "")

            idx = self.cb_mutant_origin.findData(name)
            self.cb_mutant_origin.setCurrentIndex(idx if idx != -1 else 0)
            self.ed_mutant_origin_details.setPlainText(payload.get("details", ""))
            self.update_creator_organization_enabled()

            if name == "Deliberate Experimentation":
                self.on_roll_creator_organization()

            self.statusBar().showMessage(f"Mutant Origin roll: {roll} -> {name}", 3000)
            return

        if source == "tmntta":
            roll = roll_d100()
            payload = _pick_payload_from_ranges(TMNTTA_MUTANT_ANIMAL_ORIGINS, roll)
            name = payload.get("name", "")

            idx = self.cb_mutant_origin.findData(name)
            self.cb_mutant_origin.setCurrentIndex(idx if idx != -1 else 0)
            self.ed_mutant_origin_details.setPlainText(payload.get("details", ""))

            self.statusBar().showMessage(f"TMNTTA Origin Category: {roll} -> {name}", 4000)


    def on_roll_background_education(self) -> None:
        source = str(self.cb_animal_source.currentData() or "")

        if source == "tmntos":
            roll = roll_d100()
            payload = _pick_payload_from_ranges(TMNTOS_WILD_ANIMAL_EDUCATION, roll)
            name = payload.get("name", "")

            idx = self.cb_background_education.findData(name)
            self.cb_background_education.setCurrentIndex(idx if idx != -1 else 0)
            self.ed_background_education_details.setPlainText(payload.get("details", ""))

            self.statusBar().showMessage(f"Education roll: {roll} -> {name}", 3000)
            return

        if source == "tmntta":
            category_name = str(self.cb_mutant_origin.currentData() or "")
            table = self._tmntta_origin_subtable(category_name)
            if not table:
                self.cb_background_education.setCurrentIndex(0)
                self.ed_background_education_details.clear()
                self.statusBar().showMessage("No TMNTTA subtable applies to this origin category.", 3000)
                return

            roll = roll_d100()
            payload = _pick_payload_from_ranges(table, roll)
            name = payload.get("name", "")

            idx = self.cb_background_education.findData(name)
            self.cb_background_education.setCurrentIndex(idx if idx != -1 else 0)
            self.ed_background_education_details.setPlainText(payload.get("details", ""))

            self.statusBar().showMessage(f"TMNTTA Sub-Origin: {roll} -> {name}", 3000)


    def on_roll_creator_organization(self) -> None:
        if str(self.cb_mutant_origin.currentData() or "") != "Deliberate Experimentation":
            self.cb_creator_organization.setCurrentIndex(0)
            self.ed_creator_organization_details.clear()
            return

        roll = roll_d100()
        payload = _pick_payload_from_ranges(TMNTOS_CREATOR_ORGANIZATIONS, roll)
        name = payload.get("name", "")

        idx = self.cb_creator_organization.findData(name)
        self.cb_creator_organization.setCurrentIndex(idx if idx != -1 else 0)
        self.ed_creator_organization_details.setPlainText(payload.get("details", ""))

        self.statusBar().showMessage(f"Creator Organization roll: {roll} -> {name}", 3000)


    # ----------- Scroll Bars --------
    def make_scrollable_tab(self, tab_widget: QWidget) -> QVBoxLayout:
        outer = QVBoxLayout(tab_widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)

        inner = QWidget()
        scroll.setWidget(inner)

        layout = QVBoxLayout(inner)
        return layout

    # ---------------- Menu / Toolbar ----------------
    def _build_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")

        self.action_new = QAction("&New", self)
        self.action_new.setShortcut("Ctrl+N")
        self.action_new.triggered.connect(self.on_new)
        file_menu.addAction(self.action_new)

        self.action_load = QAction("&Load...", self)
        self.action_load.setShortcut("Ctrl+O")
        self.action_load.triggered.connect(self.on_load_dialog)
        file_menu.addAction(self.action_load)

        file_menu.addSeparator()

        self.action_save = QAction("&Save", self)
        self.action_save.setShortcut("Ctrl+S")
        self.action_save.triggered.connect(self.on_save)
        file_menu.addAction(self.action_save)

        self.action_save_as = QAction("Save &As...", self)
        self.action_save_as.setShortcut("Ctrl+Shift+S")
        self.action_save_as.triggered.connect(self.on_save_as)
        file_menu.addAction(self.action_save_as)

        file_menu.addSeparator()

        self.action_export_foundry_json = QAction("Export JSON for &Foundry VTT...", self)
        self.action_export_foundry_json.triggered.connect(self.on_export_foundry_json)
        file_menu.addAction(self.action_export_foundry_json)

        self.action_export_statblock_pdf = QAction("Export &Statblock PDF...", self)
        self.action_export_statblock_pdf.triggered.connect(self.on_export_statblock_pdf)
        file_menu.addAction(self.action_export_statblock_pdf)

        

        self.action_export_ta_pdf = QAction("Export Time Machine PDF...", self)
        self.action_export_ta_pdf.triggered.connect(self.on_export_ta_pdf)
        file_menu.addAction(self.action_export_ta_pdf)

        file_menu.addSeparator()

        self.action_delete = QAction("&Delete", self)
        self.action_delete.triggered.connect(self.on_delete)
        file_menu.addAction(self.action_delete)

        file_menu.addSeparator()

        self.action_back_to_start = QAction("Back to Start Screen", self)
        self.action_back_to_start.triggered.connect(self.go_to_start_screen)
        file_menu.addAction(self.action_back_to_start)

        file_menu.addSeparator()

        self.action_exit = QAction("E&xit", self)
        self.action_exit.setShortcut("Alt+F4")
        self.action_exit.triggered.connect(self.close)
        file_menu.addAction(self.action_exit)

        settings_menu = menubar.addMenu("&Settings")

        self.action_dark_mode = QAction("Enable &Dark Mode", self)
        self.action_dark_mode.setCheckable(True)
        self.action_dark_mode.setChecked(True)
        self.action_dark_mode.toggled.connect(self.on_toggle_dark_mode)
        settings_menu.addAction(self.action_dark_mode)

        help_menu = menubar.addMenu("&Help")

        self.action_about = QAction("&About TurtleCom", self)
        self.action_about.triggered.connect(self.show_about)
        help_menu.addAction(self.action_about)

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main", self)
        tb.setMovable(False)
        self.addToolBar(tb)

        tb.addAction(self.action_new)
        tb.addAction(self.action_load)
        tb.addAction(self.action_save)
        tb.addSeparator()
        tb.addAction(self.action_back_to_start)

    def show_about(self) -> None:
        dlg = AboutDialog(self)
        dlg.exec()


    def _build_welcome_page(self) -> None:
        layout = QVBoxLayout(self.welcome_page)
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        layout.setSpacing(14)

        title = QLabel(
            "<h2 style='margin:0;'>TURTLE COM - A Teenage Mutant Ninja Turtle &amp; Other Strangeness generator.</h2>"
        )
        title.setAlignment(Qt.AlignHCenter)
        title.setWordWrap(True)
        layout.addWidget(title)

        logo_path = project_root() / "assets" / "images" / "TurtleCom Logo.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path))
            if not pix.isNull():
                logo = QLabel()
                logo.setAlignment(Qt.AlignHCenter)
                logo.setPixmap(pix.scaled(260, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                layout.addWidget(logo)

        btn_row = QHBoxLayout()

        self.btn_welcome_new = QPushButton("Create new character")
        self.btn_welcome_new.clicked.connect(self.on_welcome_new)
        btn_row.addWidget(self.btn_welcome_new)

        self.btn_welcome_random = QPushButton("Generate random level 1 character")
        self.btn_welcome_random.clicked.connect(self.on_welcome_random_level1)
        btn_row.addWidget(self.btn_welcome_random)

        layout.addLayout(btn_row)

        saved_box = QGroupBox("Saved Characters")
        saved_layout = QVBoxLayout(saved_box)

        self.welcome_list = QListWidget()
        self.welcome_list.itemDoubleClicked.connect(self.on_welcome_load_selected)
        saved_layout.addWidget(self.welcome_list, 1)

        load_row = QHBoxLayout()

        self.btn_welcome_load_selected = QPushButton("Load selected character")
        self.btn_welcome_load_selected.clicked.connect(self.on_welcome_load_selected)
        load_row.addWidget(self.btn_welcome_load_selected)

        self.btn_welcome_browse = QPushButton("Browse…")
        self.btn_welcome_browse.clicked.connect(self.on_welcome_browse_load)
        load_row.addWidget(self.btn_welcome_browse)

        saved_layout.addLayout(load_row)
        layout.addWidget(saved_box)





    # ---------------- Random Level 1 (implemented) ----------------
    def on_welcome_random_level1(self) -> None:
        self._enter_editor()
        self.load_into_editor(Character(), None)
        self.generate_random_level1_character()

    def generate_random_level1_character(self) -> None:
        # Level 1
        self.sp_level.setValue(1)

        # Attributes
        self.on_roll_all_attributes()

        # Animal (TMNTOS)
        self.cb_animal_source.setCurrentIndex(self.cb_animal_source.findData("tmntos"))
        self.on_roll_animal_type()
        self.on_roll_animal()
        self.on_roll_name_clicked()

        # Origin / Background / Creator Organization
        self.on_roll_mutant_origin()
        self.on_roll_background_education()

        if str(self.cb_mutant_origin.currentData() or "") == "Deliberate Experimentation":
            self.on_roll_creator_organization()
        else:
            if hasattr(self, "cb_creator_organization"):
                self.cb_creator_organization.setCurrentIndex(0)
            if hasattr(self, "ed_creator_organization_details"):
                self.ed_creator_organization_details.clear()

        # Alignment
        align_values = [
            "Principled (Good)",
            "Scrupulous (Good)",
            "Unprincipled (Selfish)",
            "Anarchist (Selfish)",
            "Miscreant (Evil)",
            "Aberrant (Evil)",
            "Diabolic (Evil)",
        ]
        chosen_align = random.choice(align_values)
        idx = self.cb_alignment.findData(chosen_align)
        self.cb_alignment.setCurrentIndex(idx if idx != -1 else 0)

        # Age/Gender
        self.ed_age.setText(str(random.randint(13, 60)))
        self.ed_gender.setText(random.choice(["Male", "Female", "Unknown"]))

        # Size
        # Do not random-roll mutant size during character generation.
        # Keep size/Bio-E based on the selected animal's baseline Bio-E data.
        self.cb_size_level.setCurrentIndex(0)
        self.cb_size_build.setCurrentIndex(1)  # Medium

        # Combat Training
        trainings = _training_names()[1:]  # exclude None
        training_name = random.choice(trainings) if trainings else "None"
        idx = self.cb_combat_training.findData(training_name)
        self.cb_combat_training.setCurrentIndex(idx if idx != -1 else 0)
        self.chk_combat_override.setChecked(False)
        self.recalc_combat_from_training()

        # Random Skills: 5 professional, 5 amateur
        pro_names = sorted([name for name in self.pro_skill_lookup.keys() if name])
        ama_names = sorted([name for name in self.amateur_skill_lookup.keys() if name])

        chosen_pro = random.sample(pro_names, k=min(5, len(pro_names))) if pro_names else []
        chosen_ama = random.sample(ama_names, k=min(5, len(ama_names))) if ama_names else []

        for i, cb in enumerate(self.pro_skill_boxes):
            desired = chosen_pro[i] if i < len(chosen_pro) else ""
            idx = cb.findData(desired, role=Qt.UserRole)
            cb.setCurrentIndex(idx if idx != -1 else 0)

        for i, cb in enumerate(self.amateur_skill_boxes):
            desired = chosen_ama[i] if i < len(chosen_ama) else ""
            idx = cb.findData(desired, role=Qt.UserRole)
            cb.setCurrentIndex(idx if idx != -1 else 0)

        self.on_skills_changed()

        # 1 weapon
        if self.weapon_combos:
            weapon_names = [w["name"] for w in WEAPONS_CATALOG]
            weapon_name = random.choice(weapon_names) if weapon_names else ""
            idx = self.weapon_combos[0].findData(weapon_name)
            self.weapon_combos[0].setCurrentIndex(idx if idx != -1 else 0)
            for i in range(1, len(self.weapon_combos)):
                self.weapon_combos[i].setCurrentIndex(0)

        # 1 vehicle
        sections = ["landcraft", "watercraft", "aircraft"]
        chosen_section = random.choice(sections)

        if chosen_section == "landcraft":
            pool = [v["name"] for v in VEHICLES_LANDCRAFT]
        elif chosen_section == "watercraft":
            pool = [v["name"] for v in VEHICLES_WATERCRAFT]
        else:
            pool = [v["name"] for v in VEHICLES_AIRCRAFT]

        vehicle_name = random.choice(pool) if pool else ""

        for key in ("landcraft", "watercraft", "aircraft"):
            section = self.vehicle_sections.get(key, {})
            combos: list[QComboBox] = section.get("combos", [])
            for i, cb in enumerate(combos):
                if key == chosen_section and i == 0 and vehicle_name:
                    idx = cb.findData(vehicle_name)
                    cb.setCurrentIndex(idx if idx != -1 else 0)
                else:
                    cb.setCurrentIndex(0)

        self.recalc_total_wealth()
        self.recalc_weight_breakdown()
        self.statusBar().showMessage("Generated random level 1 character")

    def update_creator_organization_enabled(self) -> None:
        source = str(self.cb_animal_source.currentData() or "")
        if source == "tmntta":
            self.cb_creator_organization.setEnabled(False)
            self.ed_creator_organization_details.setEnabled(False)
            self.btn_roll_creator_organization.setEnabled(False)
            self.cb_creator_organization.setCurrentIndex(0)
            self.ed_creator_organization_details.clear()
            return

        is_deliberate = str(self.cb_mutant_origin.currentData() or "") == "Deliberate Experimentation"
        self.cb_creator_organization.setEnabled(is_deliberate)
        self.ed_creator_organization_details.setEnabled(is_deliberate)
        self.btn_roll_creator_organization.setEnabled(is_deliberate)

        if not is_deliberate:
            self.cb_creator_organization.setCurrentIndex(0)
            self.ed_creator_organization_details.clear()

    def _ta_reset_builder(self) -> None:
        if hasattr(self, "cb_ta_device_category"):
            self.cb_ta_device_category.blockSignals(True)
            try:
                self.cb_ta_device_category.setCurrentIndex(0)
            finally:
                self.cb_ta_device_category.blockSignals(False)

        if hasattr(self, "cb_ta_device_name"):
            self.cb_ta_device_name.blockSignals(True)
            try:
                self.cb_ta_device_name.clear()
                self.cb_ta_device_name.addItem("Select device", "")
            finally:
                self.cb_ta_device_name.blockSignals(False)

        if hasattr(self, "cb_ta_mount_type"):
            self.cb_ta_mount_type.blockSignals(True)
            try:
                self.cb_ta_mount_type.setCurrentIndex(0)
            finally:
                self.cb_ta_mount_type.blockSignals(False)

        if hasattr(self, "cb_ta_vehicle_type"):
            self.cb_ta_vehicle_type.blockSignals(True)
            try:
                self.cb_ta_vehicle_type.setCurrentIndex(0)
                self.cb_ta_vehicle_type.setEnabled(False)
            finally:
                self.cb_ta_vehicle_type.blockSignals(False)

        if hasattr(self, "ed_ta_device_details"):
            self.ed_ta_device_details.clear()

        if hasattr(self, "ed_ta_mount_notes"):
            self.ed_ta_mount_notes.clear()

        for cb in getattr(self, "ta_support_device_combos", []):
            cb.blockSignals(True)
            try:
                cb.setCurrentIndex(0)
            finally:
                cb.blockSignals(False)

        for chk in getattr(self, "ta_support_portable_checks", []):
            chk.blockSignals(True)
            try:
                chk.setChecked(False)
            finally:
                chk.blockSignals(False)

        for sp_name in (
            "sp_ta_base_cost",
            "sp_ta_install_cost",
            "sp_ta_support_cost",
            "sp_ta_total_cost",
        ):
            if hasattr(self, sp_name):
                sp = getattr(self, sp_name)
                sp.blockSignals(True)
                try:
                    sp.setValue(0)
                finally:
                    sp.blockSignals(False)

        if hasattr(self, "ed_ta_summary_notes"):
            self.ed_ta_summary_notes.clear()

        self.ta_image_path = ""
        self._ta_set_image_preview("")

    def _ta_populate_device_names_for_category(self, category: str) -> None:
        if not hasattr(self, "cb_ta_device_name"):
            return

        self.cb_ta_device_name.blockSignals(True)
        try:
            self.cb_ta_device_name.clear()
            self.cb_ta_device_name.addItem("Select device", "")

            if category == "time_machine":
                for item in TMNTTA_TIME_DEVICES:
                    if str(item.get("category", "")) == "time_machine":
                        name = str(item.get("name", "") or "").strip()
                        if name:
                            self.cb_ta_device_name.addItem(name, name)

            elif category == "dimension_device":
                for item in TMNTTA_TIME_DEVICES:
                    if str(item.get("category", "")) == "dimension_device":
                        name = str(item.get("name", "") or "").strip()
                        if name:
                            self.cb_ta_device_name.addItem(name, name)

            elif category == "support_device":
                for item in TMNTTA_TEMPORAL_SUPPORT_DEVICES:
                    name = str(item.get("name", "") or "").strip()
                    if name:
                        self.cb_ta_device_name.addItem(name, name)
        finally:
            self.cb_ta_device_name.blockSignals(False)


    def _ta_populate_support_device_combos(self) -> None:
        combos = list(getattr(self, "ta_support_device_combos", []) or [])
        if not combos:
            return

        names = []
        for item in TMNTTA_TEMPORAL_SUPPORT_DEVICES:
            name = str(item.get("name", "") or "").strip()
            if name:
                names.append(name)

        for cb in combos:
            current_name = str(cb.currentData() or "").strip()

            cb.blockSignals(True)
            try:
                cb.clear()
                cb.addItem("None", "")
                for name in names:
                    cb.addItem(name, name)
            finally:
                cb.blockSignals(False)

            idx = cb.findData(current_name)
            cb.setCurrentIndex(idx if idx != -1 else 0)


    def _ta_get_selected_device_record(self) -> dict[str, Any]:
        category = str(self.cb_ta_device_category.currentData() or "").strip()
        name = str(self.cb_ta_device_name.currentData() or "").strip()

        if not name:
            return {}

        if category in {"time_machine", "dimension_device"}:
            return dict(TMNTTA_TIME_DEVICES_BY_NAME.get(name, {}) or {})

        if category == "support_device":
            return dict(TMNTTA_TEMPORAL_SUPPORT_BY_NAME.get(name, {}) or {})

        return {}


    def _ta_get_selected_support_records(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for cb in getattr(self, "ta_support_device_combos", []):
            name = str(cb.currentData() or "").strip()
            if not name:
                continue
            record = dict(TMNTTA_TEMPORAL_SUPPORT_BY_NAME.get(name, {}) or {})
            if record:
                records.append(record)
        return records


    def _ta_update_vehicle_type_enabled(self) -> None:
        if not hasattr(self, "cb_ta_vehicle_type"):
            return

        mount_type = str(self.cb_ta_mount_type.currentData() or "").strip()
        enabled = mount_type == "vehicle"

        self.cb_ta_vehicle_type.setEnabled(enabled)

        if not enabled:
            self.cb_ta_vehicle_type.blockSignals(True)
            try:
                self.cb_ta_vehicle_type.setCurrentIndex(0)
            finally:
                self.cb_ta_vehicle_type.blockSignals(False)


    def _ta_lookup_install_cost(self, device_name: str, vehicle_type: str) -> int:
        if not device_name or not vehicle_type:
            return 0

        vehicle_type_map = {
            "truck_van": "Truck or Van",
            "compact_sports_car": "Compact or Sports Car",
            "mid_size_larger_car": "Mid-Size or Larger Car",
            "motorcycle": "Motorcycle",
            "aircraft": "Aircraft",
            "watercraft": "Watercraft",
            "other_vehicle": "Other Vehicle",
        }

        expected_vehicle_type = vehicle_type_map.get(vehicle_type, vehicle_type)

        for row in TMNTTA_TIME_DEVICE_INSTALL_COSTS:
            row_device_name = str(row.get("device_name", "") or "").strip()
            row_vehicle_type = str(row.get("vehicle_type", "") or "").strip()

            if row_device_name != str(device_name).strip():
                continue
            if row_vehicle_type != expected_vehicle_type:
                continue

            value = row.get("install_cost", 0)
            if value is None:
                return 0

            try:
                return int(value or 0)
            except Exception:
                return 0

        return 0


    def _ta_calculate_base_cost(self) -> int:
        record = self._ta_get_selected_device_record()
        if not record:
            return 0

        mount_type = str(self.cb_ta_mount_type.currentData() or "").strip()

        if mount_type == "portable":
            portable_cost = record.get("portable_cost")
            if portable_cost is not None:
                try:
                    return int(portable_cost or 0)
                except Exception:
                    pass

        try:
            return int(record.get("base_cost", 0) or 0)
        except Exception:
            return 0


    def _ta_calculate_support_cost(self) -> int:
        total = 0
        combos = list(getattr(self, "ta_support_device_combos", []) or [])
        checks = list(getattr(self, "ta_support_portable_checks", []) or [])

        for i, cb in enumerate(combos):
            name = str(cb.currentData() or "").strip()
            if not name:
                continue

            record = dict(TMNTTA_TEMPORAL_SUPPORT_BY_NAME.get(name, {}) or {})
            if not record:
                continue

            portable_on = i < len(checks) and bool(checks[i].isChecked())

            value = record.get("portable_cost") if portable_on and record.get("portable_cost") is not None else record.get("base_cost", 0)
            try:
                total += int(value or 0)
            except Exception:
                continue

        return total


    def _ta_build_device_details_text(self, record: dict[str, Any]) -> str:
        if not record:
            return ""

        lines: list[str] = []

        name = str(record.get("name", "") or "").strip()
        category = str(record.get("category", "") or "").strip()
        base_cost = record.get("base_cost", 0)
        portable = record.get("portable", None)
        vehicle_mountable = record.get("vehicle_mountable", None)
        recharge_time = str(record.get("recharge_time", "") or "").strip()
        weight_lbs = record.get("weight_lbs", None)
        max_area = str(record.get("max_area_of_effect", "") or "").strip()
        bonus_text = str(record.get("bonus_text", "") or "").strip()
        malfunction_text = str(record.get("malfunction_text", "") or "").strip()
        details = str(record.get("details", "") or "").strip()

        if name:
            lines.append(name)
        if category:
            lines.append(f"Category: {category}")
        if base_cost:
            lines.append(f"Base Cost: ${int(base_cost):,}")
        if portable is not None:
            lines.append(f"Portable: {'Yes' if portable else 'No'}")
        if vehicle_mountable is not None:
            lines.append(f"Vehicle Mountable: {'Yes' if vehicle_mountable else 'No'}")
        if weight_lbs not in (None, ""):
            lines.append(f"Weight: {weight_lbs} lbs")
        if recharge_time:
            lines.append(f"Recharge: {recharge_time}")
        if max_area:
            lines.append(f"Area: {max_area}")
        if bonus_text:
            lines.append(f"Bonus: {bonus_text}")
        if malfunction_text:
            lines.append(f"Malfunction: {malfunction_text}")
        if details:
            lines.append("")
            lines.append(details)

        return "\n".join(lines)


    def _ta_build_mount_notes_text(self) -> str:
        lines: list[str] = []

        device_name = str(self.cb_ta_device_name.currentData() or "").strip()
        mount_type = str(self.cb_ta_mount_type.currentData() or "").strip()
        vehicle_type = str(self.cb_ta_vehicle_type.currentData() or "").strip()

        if device_name:
            lines.append(f"Device: {device_name}")

        if mount_type:
            lines.append(f"Mount Type: {mount_type}")

        if vehicle_type:
            lines.append(f"Vehicle Type: {vehicle_type}")

        if mount_type == "vehicle" and device_name and vehicle_type:
            install_cost = self._ta_lookup_install_cost(device_name, vehicle_type)
            if install_cost > 0:
                lines.append(f"Install Cost: ${install_cost:,}")
            else:
                lines.append("Install Cost: Not available / not supported")

        combos = list(getattr(self, "ta_support_device_combos", []) or [])
        checks = list(getattr(self, "ta_support_portable_checks", []) or [])
        chosen_supports: list[str] = []

        for i, cb in enumerate(combos):
            support_name = str(cb.currentData() or "").strip()
            if not support_name:
                continue
            portable_on = i < len(checks) and bool(checks[i].isChecked())
            chosen_supports.append(f"{support_name} (portable)" if portable_on else support_name)

        if chosen_supports:
            lines.append("")
            lines.append("Support Devices:")
            for entry in chosen_supports:
                lines.append(f"- {entry}")

        return "\n".join(lines)


    def _ta_set_image_preview(self, image_path: str) -> None:
        if not hasattr(self, "lbl_ta_image_preview"):
            return

        image_path = str(image_path or "").strip()
        if not image_path:
            self.lbl_ta_image_preview.setText("No time machine image loaded")
            self.lbl_ta_image_preview.setPixmap(QPixmap())
            return

        pix = QPixmap(image_path)
        if pix.isNull():
            self.lbl_ta_image_preview.setText("Could not load image")
            self.lbl_ta_image_preview.setPixmap(QPixmap())
            return

        self.lbl_ta_image_preview.setText("")
        self.lbl_ta_image_preview.setPixmap(
            pix.scaled(320, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )


    def on_ta_load_image(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Load Time Machine Image",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if not path_str:
            return

        if not hasattr(self, "ta_image_path"):
            self.ta_image_path = ""

        self.ta_image_path = str(path_str)
        self._ta_set_image_preview(self.ta_image_path)


    def on_ta_clear_image(self) -> None:
        self.ta_image_path = ""
        self._ta_set_image_preview("")

    def recalc_ta_time_devices(self) -> None:
        record = self._ta_get_selected_device_record()
        base_cost = self._ta_calculate_base_cost()

        mount_type = str(self.cb_ta_mount_type.currentData() or "").strip()
        vehicle_type = str(self.cb_ta_vehicle_type.currentData() or "").strip()
        device_name = str(self.cb_ta_device_name.currentData() or "").strip()

        install_cost = 0
        if mount_type == "vehicle" and device_name and vehicle_type:
            install_cost = self._ta_lookup_install_cost(device_name, vehicle_type)

        support_cost = self._ta_calculate_support_cost()
        total_cost = base_cost + install_cost + support_cost

        for sp_name, value in (
            ("sp_ta_base_cost", base_cost),
            ("sp_ta_install_cost", install_cost),
            ("sp_ta_support_cost", support_cost),
            ("sp_ta_total_cost", total_cost),
        ):
            if hasattr(self, sp_name):
                sp = getattr(self, sp_name)
                sp.blockSignals(True)
                try:
                    sp.setValue(value)
                finally:
                    sp.blockSignals(False)

        if hasattr(self, "ed_ta_device_details"):
            self.ed_ta_device_details.setPlainText(self._ta_build_device_details_text(record))

        if hasattr(self, "ed_ta_mount_notes"):
            self.ed_ta_mount_notes.setPlainText(self._ta_build_mount_notes_text())


    def on_ta_device_category_changed(self) -> None:
        category = str(self.cb_ta_device_category.currentData() or "").strip()

        self._ta_populate_device_names_for_category(category)

        if hasattr(self, "cb_ta_mount_type"):
            self.cb_ta_mount_type.blockSignals(True)
            try:
                self.cb_ta_mount_type.setCurrentIndex(0)
            finally:
                self.cb_ta_mount_type.blockSignals(False)

        self._ta_update_vehicle_type_enabled()
        self.recalc_ta_time_devices()


    def on_ta_device_name_changed(self) -> None:
        self._ta_update_vehicle_type_enabled()
        self.recalc_ta_time_devices()


    def on_ta_mount_type_changed(self) -> None:
        self._ta_update_vehicle_type_enabled()
        self.recalc_ta_time_devices()


    def on_ta_vehicle_type_changed(self) -> None:
        self.recalc_ta_time_devices()


    def on_ta_support_devices_changed(self) -> None:
        self.recalc_ta_time_devices()

    def refresh_welcome_list(self) -> None:
        if not hasattr(self, "welcome_list"):
            return

        self.welcome_list.blockSignals(True)
        self.welcome_list.clear()

        for p in list_character_files():
            item = QListWidgetItem(p.name)
            item.setData(Qt.UserRole, p)
            self.welcome_list.addItem(item)

        self.welcome_list.blockSignals(False)


    def _enter_editor(self) -> None:
        self.stack.setCurrentWidget(self.editor_page)
        self.refresh_list()
        self.statusBar().showMessage("Editor ready")


    def go_to_start_screen(self) -> None:
        self.refresh_welcome_list()
        self.stack.setCurrentWidget(self.welcome_page)
        self.statusBar().showMessage("Start screen")


    def on_welcome_new(self) -> None:
        self._enter_editor()
        self.load_into_editor(Character(), None)


    def on_welcome_load_selected(self, _item: QListWidgetItem | None = None) -> None:
        item = self.welcome_list.currentItem()
        if item is None:
            QMessageBox.information(self, "Load", "Select a character from the list first.")
            return

        p = item.data(Qt.UserRole)
        if not isinstance(p, Path):
            p = CHARACTERS_DIR / str(item.text())

        try:
            c = load_character(p)
        except Exception as e:
            QMessageBox.critical(self, "Load failed", f"Could not load:\n{p}\n\n{e}")
            return

        self._enter_editor()
        self.load_into_editor(c, p)
        self.refresh_list()


    def on_welcome_browse_load(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Load Character JSON",
            str(CHARACTERS_DIR),
            "JSON Files (*.json)",
        )
        if not path_str:
            return

        p = Path(path_str)
        try:
            c = load_character(p)
        except Exception as e:
            QMessageBox.critical(self, "Load failed", f"Could not load:\n{p}\n\n{e}")
            return

        self._enter_editor()
        self.load_into_editor(c, p)
        self.refresh_list()
        self.refresh_welcome_list()

    # ---------------- Helpers ----------------
    def refresh_list(self) -> None:
        if not hasattr(self, "list_widget"):
            return
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for p in list_character_files():
            self.list_widget.addItem(p.name)
        self.list_widget.blockSignals(False)

    def confirm(self, title: str, text: str) -> bool:
        return QMessageBox.question(self, title, text) == QMessageBox.Yes
    

    def sync_defense_summary_fields(self) -> None:
        base_sdc = int(self.sp_sdc.value()) if hasattr(self, "sp_sdc") else 0
        armor_ar = int(self.sp_armor_ar.value()) if hasattr(self, "sp_armor_ar") else 0
        armor_sdc = int(self.sp_armor_sdc.value()) if hasattr(self, "sp_armor_sdc") else 0

        shield_sdc = 0
        if hasattr(self, "lbl_shield_sdc"):
            text = self.lbl_shield_sdc.text().strip()
            match = re.search(r"(\d+)", text)
            if match:
                shield_sdc = int(match.group(1))

        if hasattr(self, "ed_basic_armor_ar"):
            self.ed_basic_armor_ar.setText(str(armor_ar))

        if hasattr(self, "ed_basic_armor_sdc"):
            self.ed_basic_armor_sdc.setText(str(armor_sdc))

        if hasattr(self, "ed_basic_shield_sdc"):
            self.ed_basic_shield_sdc.setText(str(shield_sdc))

        if hasattr(self, "ed_basic_total_sdc"):
            self.ed_basic_total_sdc.setText(str(base_sdc + armor_sdc + shield_sdc))


    
    # ---------------- Actions ----------------
    def on_new(self) -> None:
        if self.confirm("New Character", "Discard current edits and start a new character?"):
            if hasattr(self, "skill_effect_rolls"):
                self.skill_effect_rolls.clear()
            self.load_into_editor(Character(), None)

    def on_select_character(self) -> None:
        items = self.list_widget.selectedItems()
        if not items:
            return

        filename = items[0].text()
        path = CHARACTERS_DIR / filename
        try:
            c = load_character(path)
        except Exception as e:
            QMessageBox.critical(self, "Load failed", f"Could not load {filename}\n\n{e}")
            return

        self.load_into_editor(c, path)

    def on_load_dialog(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Load Character JSON",
            str(CHARACTERS_DIR),
            "JSON Files (*.json)",
        )
        if not path_str:
            return

        path = Path(path_str)
        try:
            c = load_character(path)
        except Exception as e:
            QMessageBox.critical(self, "Load failed", f"Could not load:\n{path}\n\n{e}")
            return

        if hasattr(self, "skill_effect_rolls"):
            self.skill_effect_rolls.clear()

        self.load_into_editor(c, path)
        self.refresh_list()
        self.refresh_welcome_list()

    def on_save(self) -> None:
        c = self.editor_to_character()

        if self.current_path is None:
            filename = c.default_filename()
            path = CHARACTERS_DIR / filename
        else:
            path = self.current_path

        if not c.name.strip():
            if not self.confirm("No Name", "Character has no name. Save anyway?"):
                return

        try:
            save_character(c, path)
        except Exception as e:
            QMessageBox.critical(self, "Save failed", f"Could not save:\n{path}\n\n{e}")
            return

        self.load_into_editor(c, path)
        self.refresh_list()
        self.refresh_welcome_list()

    def on_save_as(self) -> None:
        c = self.editor_to_character()

        suggested = str(CHARACTERS_DIR / c.default_filename())
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Save Character As",
            suggested,
            "JSON Files (*.json)",
        )
        if not path_str:
            return

        path = Path(path_str)
        if path.suffix.lower() != ".json":
            path = path.with_suffix(".json")

        try:
            save_character(c, path)
        except Exception as e:
            QMessageBox.critical(self, "Save failed", f"Could not save:\n{path}\n\n{e}")
            return

        self.load_into_editor(c, path)
        self.refresh_list()
        self.refresh_welcome_list()

    def on_delete(self) -> None:
        if self.current_path is None:
            QMessageBox.information(self, "Delete", "This character isn’t saved yet.")
            return

        if not self.confirm("Delete Character", f"Delete file?\n\n{self.current_path.name}"):
            return

        try:
            delete_character_file(self.current_path)
        except Exception as e:
            QMessageBox.critical(self, "Delete failed", f"Could not delete:\n{self.current_path}\n\n{e}")
            return

        if hasattr(self, "skill_effect_rolls"):
            self.skill_effect_rolls.clear()

        self.load_into_editor(Character(), None)
        self.refresh_list()
        self.refresh_welcome_list()

    def on_load_character_art(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Character Image",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if not path:
            return

        pix = QPixmap(path)
        if pix.isNull():
            return

        scaled = pix.scaled(240, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.lbl_character_art.setPixmap(scaled)
        self.current_character.image_path = path

    def on_clear_character_art(self) -> None:
        self.lbl_character_art.clear()
        self.lbl_character_art.setText("Character Art\n240x240")
        self.current_character.image_path = None


    def _all_selected_skill_names(self) -> list[str]:
        names: list[str] = []

        for cb in getattr(self, "pro_skill_boxes", []):
            name = self._selected_skill_name(cb)
            if name:
                names.append(name)

        for cb in getattr(self, "amateur_skill_boxes", []):
            name = self._selected_skill_name(cb)
            if name:
                names.append(name)

        return names


    def _roll_skill_effect_expr(self, expr: str) -> int:
        total, detail = self.eval_dice_expression(expr)
        self.log_roll(f"[Skill Bonus] {expr} -> {detail} Total = {total}")
        return total


    def _ensure_skill_effect_rolls(self) -> None:
        if not hasattr(self, "skill_effect_rolls"):
            self.skill_effect_rolls: dict[str, dict[str, int]] = {}


    def _refresh_skill_effect_roll_cache(self) -> None:
        self._ensure_skill_effect_rolls()

        selected = set(self._all_selected_skill_names())
        effects = globals().get("PHYSICAL_SKILL_EFFECTS", {})

        for skill_name in list(self.skill_effect_rolls.keys()):
            if skill_name not in selected:
                del self.skill_effect_rolls[skill_name]

        for skill_name in selected:
            effect = effects.get(skill_name)
            if not effect:
                continue

            if skill_name not in self.skill_effect_rolls:
                self.skill_effect_rolls[skill_name] = {}

            cache = self.skill_effect_rolls[skill_name]

            for key, expr_key in (
                ("sdc_roll", "sdc_roll"),
                ("speed_roll", "speed_roll"),
                ("swim_speed_roll", "swim_speed_roll"),
            ):
                expr = effect.get(expr_key)
                if isinstance(expr, str) and key not in cache:
                    cache[key] = self._roll_skill_effect_expr(expr)

            attr_rolls = effect.get("attribute_rolls", {})
            if isinstance(attr_rolls, dict):
                for attr_name, expr in attr_rolls.items():
                    cache_key = f"attr_{attr_name}"
                    if isinstance(expr, str) and cache_key not in cache:
                        cache[cache_key] = self._roll_skill_effect_expr(expr)


    def _get_physical_skill_totals(self) -> dict[str, Any]:
        self._refresh_skill_effect_roll_cache()
        effects = globals().get("PHYSICAL_SKILL_EFFECTS", {})

        totals: dict[str, Any] = {
            "attributes": {"IQ - Intelligence Quotient": 0, "ME - Mental Endurance": 0, "MA - Mental Affinity": 0, "PS - Physical Strength": 0, "PP - Physical Prowess": 0, "PE - Physical Endurance": 0, "PB - Physical Beauty": 0, "Speed": 0},
            "combat": {
                "strike": 0,
                "parry": 0,
                "dodge": 0,
                "initiative": 0,
                "actions_per_round": 0,
                "roll_with_impact": 0,
                "pull_punch": 0,
                "strike_swords": 0,
                "parry_swords": 0,
                "damage_swords": 0,
            },
            "sdc_bonus": 0,
            "speed_bonus": 0,
            "swim_speed_bonus": 0,
            "skill_pct_bonus": {},
            "extra_attacks": [],
            "notes": [],
        }

        for skill_name in self._all_selected_skill_names():
            effect = effects.get(skill_name)
            if not effect:
                continue

            for attr_name, amount in effect.get("attribute_bonus", {}).items():
                key = "Speed" if attr_name == "Speed" else attr_name
                if key in totals["attributes"] and isinstance(amount, int):
                    totals["attributes"][key] += amount

            for attr_name in effect.get("attribute_rolls", {}):
                cache_key = f"attr_{attr_name}"
                rolled = self.skill_effect_rolls.get(skill_name, {}).get(cache_key, 0)
                key = "Speed" if attr_name == "Speed" else attr_name
                if key in totals["attributes"]:
                    totals["attributes"][key] += int(rolled)

            for combat_key, amount in effect.get("combat_bonus", {}).items():
                if combat_key in totals["combat"] and isinstance(amount, int):
                    totals["combat"][combat_key] += amount

            totals["sdc_bonus"] += int(effect.get("sdc_flat", 0) or 0)
            totals["sdc_bonus"] += int(self.skill_effect_rolls.get(skill_name, {}).get("sdc_roll", 0) or 0)
            totals["speed_bonus"] += int(self.skill_effect_rolls.get(skill_name, {}).get("speed_roll", 0) or 0)
            totals["swim_speed_bonus"] += int(self.skill_effect_rolls.get(skill_name, {}).get("swim_speed_roll", 0) or 0)

            for skill_key, pct_bonus in effect.get("skill_bonus_pct", {}).items():
                totals["skill_pct_bonus"][skill_key] = totals["skill_pct_bonus"].get(skill_key, 0) + int(pct_bonus)

            for attack_name in effect.get("extra_attacks", []):
                if attack_name not in totals["extra_attacks"]:
                    totals["extra_attacks"].append(attack_name)

            for note in effect.get("notes", []):
                if note not in totals["notes"]:
                    totals["notes"].append(f"{skill_name}: {note}")

        return totals


    def get_effective_attribute(self, attr_name: str) -> int:
        base = 0
        if attr_name in self.attribute_fields:
            base = int(self.attribute_fields[attr_name].value())

        totals = self._get_physical_skill_totals()
        bonus = int(totals["attributes"].get(attr_name, 0))
        return base + bonus
    
    def _normalize_animal_for_names(self, animal_label: str) -> str:
        from app.generators.random_character import normalize_animal_for_names
        return normalize_animal_for_names(animal_label)

    def on_roll_name_clicked(self) -> None:
        animal_label = self.cb_animal.currentText() if hasattr(self, "cb_animal") and self.cb_animal is not None else ""
        name = random_name_for_animal(animal_label)

        if not name:
            if not self.ed_name.text().strip():
                self.ed_name.setText("—")
            return

        self.ed_name.setText(name)  

    def on_roll_size_clicked(self) -> None:
        size_level, size_build = roll_size_choice()

        idx = self.cb_size_level.findData(size_level)
        if idx != -1:
            self.cb_size_level.setCurrentIndex(idx)

        idx = self.cb_size_build.findData(size_build)
        if idx != -1:
            self.cb_size_build.setCurrentIndex(idx)

        self.statusBar().showMessage(
            f"Rolled size: Level {size_level}, {size_build.title()}",
            3000,
        )


    def _make_bio_catalog_combo(
        self,
        options: list[tuple[str, int]],
        none_label: str = "None (0 Bio-E)",
    ) -> QComboBox:
        cb = QComboBox()
        cb.addItem(none_label, 0)
        for name, cost in options:
            cb.addItem(f"{name} ({cost} Bio-E)", cost)
        cb.setCurrentIndex(0)
        cb.currentIndexChanged.connect(self.recalc_bioe_spent)
        return cb        

    # ---------------- Editor page ----------------
    def _build_editor_page(self) -> None:
        layout = QHBoxLayout(self.editor_page)

        # ---------------- Left: dice tools + notes ----------------
        left = QVBoxLayout()
        layout.addLayout(left, 1)

        dice_box = QGroupBox("Dice Tools")
        dice_layout = QVBoxLayout(dice_box)

        self.roll_log = QTextEdit()
        self.roll_log.setReadOnly(True)
        self.roll_log.setPlaceholderText("Roll log…")
        self.roll_log.setMinimumHeight(140)
        dice_layout.addWidget(self.roll_log)

        grid = QGridLayout()
        dice_layout.addLayout(grid)

        self.dice_counts: dict[int, QSpinBox] = {}
        die_faces = [2, 4, 6, 8, 10, 12, 20, 100]

        for idx, faces in enumerate(die_faces):
            r = idx // 4
            c = (idx % 4) * 2

            sp = QSpinBox()
            sp.setRange(0, 200)
            sp.setValue(0)
            sp.setToolTip(f"How many d{faces} to roll")
            self.dice_counts[faces] = sp

            btn = QPushButton(f"Roll d{faces}")
            btn.clicked.connect(lambda _=False, f=faces: self.on_roll_generic_die(f))

            grid.addWidget(sp, r, c)
            grid.addWidget(btn, r, c + 1)

        btn_row = QHBoxLayout()
        self.btn_clear_log = QPushButton("Clear Log")
        self.btn_clear_log.clicked.connect(self.roll_log.clear)
        btn_row.addWidget(self.btn_clear_log)
        dice_layout.addLayout(btn_row)
        left.addWidget(dice_box)

        # ---------------- Left bottom: Notes ----------------
        notes_box = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_box)

        self.ed_notes = QTextEdit()
        self.ed_notes.setPlaceholderText("Notes…")
        notes_layout.addWidget(self.ed_notes, 1)

        left.addWidget(notes_box, 1)

        # ---------------- Right: tabbed editor ----------------
        right = QVBoxLayout()
        layout.addLayout(right, 2)

        self.tabs = QTabWidget()
        right.addWidget(self.tabs, 1)

        self.tab_basics = QWidget()
        self.tab_attributes = QWidget()
        self.tab_skills = QWidget()
        self.tab_combat = QWidget()
        self.tab_bioe = QWidget()
        self.tab_equipment = QWidget()
        self.tab_vehicles = QWidget()
        self.tab_time_machines = QWidget()
        self.tab_custom_vehicles = QWidget()
        self.tab_custom_air_ships = QWidget()

        self.tabs.addTab(self.tab_basics, "Basics")
        self.tabs.addTab(self.tab_attributes, "Attributes")
        self.tabs.addTab(self.tab_skills, "Skills")
        self.tabs.addTab(self.tab_combat, "Combat")
        self.tabs.addTab(self.tab_bioe, "Bio-E / Mutant")
        self.tabs.addTab(self.tab_equipment, "Equipment")
        self.tabs.addTab(self.tab_vehicles, "Basic Vehicles")
        self.tabs.addTab(self.tab_time_machines, "Time Machines & Dimension Devices (TA)")
        self.tabs.addTab(self.tab_custom_vehicles, "Custom Vehicles (RH)")
        self.tabs.addTab(self.tab_custom_air_ships, "Custom Air Ships (MDU)")

        # ===================== Basics tab =====================
        self.basics_layout = self.make_scrollable_tab(self.tab_basics)
        basics_form = QFormLayout()
        self.basics_layout.addLayout(basics_form)

        # ---- Character Art ----
        art_row = QWidget()
        art_layout = QVBoxLayout()
        art_layout.setContentsMargins(0, 0, 0, 0)
        art_row.setLayout(art_layout)

        self.lbl_character_art = QLabel()
        self.lbl_character_art.setFixedSize(240, 240)
        self.lbl_character_art.setAlignment(Qt.AlignCenter)
        self.lbl_character_art.setStyleSheet(
            "border: 1px solid #444; background-color: #222;"
        )
        self.lbl_character_art.setText("Character Art\n240x240")

        btn_row = QWidget()
        btn_row_l = QHBoxLayout()
        btn_row_l.setContentsMargins(0, 0, 0, 0)
        btn_row.setLayout(btn_row_l)

        self.btn_load_art = QPushButton("Load Image")
        self.btn_clear_art = QPushButton("Clear")

        self.btn_load_art.clicked.connect(self.on_load_character_art)
        self.btn_clear_art.clicked.connect(self.on_clear_character_art)

        btn_row_l.addWidget(self.btn_load_art)
        btn_row_l.addWidget(self.btn_clear_art)

        art_layout.addWidget(self.lbl_character_art, 0, Qt.AlignCenter)
        art_layout.addWidget(btn_row)

        basics_form.addRow("Character Art", art_row)

        name_row = QWidget()
        name_l = QHBoxLayout()
        name_l.setContentsMargins(0, 0, 0, 0)
        name_row.setLayout(name_l)

        self.ed_name = QLineEdit()
        self.btn_roll_name = QPushButton("Roll")
        self.btn_roll_name.clicked.connect(self.on_roll_name_clicked)

        name_l.addWidget(self.ed_name, 1)
        name_l.addWidget(self.btn_roll_name, 0)

        basics_form.addRow("Name", name_row)

        self.cb_animal_source = QComboBox()
        self.cb_animal_source.addItem("Select your source", "")
        self.cb_animal_source.addItem("Teenage Mutant Ninja Turtles & Other Strangeness", "tmntos")
        self.cb_animal_source.addItem("Teenage Mutant Ninja Turtles Transdimensional Adventures", "tmntta")
        self.cb_animal_source.currentIndexChanged.connect(self.on_animal_source_changed)
        basics_form.addRow("Animal Source", self.cb_animal_source)

        animal_type_row = QWidget()
        animal_type_l = QHBoxLayout()
        animal_type_l.setContentsMargins(0, 0, 0, 0)
        animal_type_row.setLayout(animal_type_l)

        self.cb_animal_type = QComboBox()
        self.cb_animal_type.addItem("Roll or select your animal type", "")
        self.cb_animal_type.currentIndexChanged.connect(self.on_animal_type_changed)

        self.btn_roll_animal_type = QPushButton("Roll")
        self.btn_roll_animal_type.clicked.connect(self.on_roll_animal_type)

        animal_type_l.addWidget(self.cb_animal_type, 1)
        animal_type_l.addWidget(self.btn_roll_animal_type, 0)
        basics_form.addRow("Animal Type", animal_type_row)

        animal_row = QWidget()
        animal_l = QHBoxLayout()
        animal_l.setContentsMargins(0, 0, 0, 0)
        animal_row.setLayout(animal_l)

        self.cb_animal = QComboBox()
        self.cb_animal.addItem("Roll or select your animal", "")
        self.cb_animal.currentIndexChanged.connect(self.on_bioe_animal_selected)

        self.btn_roll_animal = QPushButton("Roll")
        self.btn_roll_animal.clicked.connect(self.on_roll_animal)

        animal_l.addWidget(self.cb_animal, 1)
        animal_l.addWidget(self.btn_roll_animal, 0)
        basics_form.addRow("Animal", animal_row)

        self.cb_alignment = QComboBox()
        self.cb_alignment.addItem("Select alignment", "")
        self.cb_alignment.addItem("Principled (Good)", "Principled (Good)")
        self.cb_alignment.addItem("Scrupulous (Good)", "Scrupulous (Good)")
        self.cb_alignment.addItem("Unprincipled (Selfish)", "Unprincipled (Selfish)")
        self.cb_alignment.addItem("Anarchist (Selfish)", "Anarchist (Selfish)")
        self.cb_alignment.addItem("Miscreant (Evil)", "Miscreant (Evil)")
        self.cb_alignment.addItem("Aberrant (Evil)", "Aberrant (Evil)")
        self.cb_alignment.addItem("Diabolic (Evil)", "Diabolic (Evil)")
        basics_form.addRow("Alignment", self.cb_alignment)

        self.ed_age = QLineEdit()
        basics_form.addRow("Age", self.ed_age)

        self.ed_gender = QLineEdit()
        basics_form.addRow("Gender", self.ed_gender)

        origin_row = QWidget()
        origin_top_l = QHBoxLayout()
        origin_top_l.setContentsMargins(0, 0, 0, 0)
        origin_row.setLayout(origin_top_l)

        self.cb_mutant_origin = QComboBox()
        self.cb_mutant_origin.addItem("Select or roll origin", "")
        for _, payload in TMNTOS_MUTANT_ANIMAL_ORIGINS:
            self.cb_mutant_origin.addItem(payload["name"], payload["name"])
        self.cb_mutant_origin.currentIndexChanged.connect(self.on_mutant_origin_changed)

        self.btn_roll_mutant_origin = QPushButton("Roll")
        self.btn_roll_mutant_origin.clicked.connect(self.on_roll_mutant_origin)

        origin_top_l.addWidget(self.cb_mutant_origin, 1)
        origin_top_l.addWidget(self.btn_roll_mutant_origin, 0)

        self.ed_mutant_origin_details = QTextEdit()
        self.ed_mutant_origin_details.setReadOnly(True)
        self.ed_mutant_origin_details.setMinimumHeight(90)

        origin_container = QWidget()
        origin_container_l = QVBoxLayout()
        origin_container_l.setContentsMargins(0, 0, 0, 0)
        origin_container.setLayout(origin_container_l)
        origin_container_l.addWidget(origin_row)
        origin_container_l.addWidget(self.ed_mutant_origin_details)

        basics_form.addRow("Mutant Animal Origin", origin_container)

        education_row = QWidget()
        education_top_l = QHBoxLayout()
        education_top_l.setContentsMargins(0, 0, 0, 0)
        education_row.setLayout(education_top_l)

        self.cb_background_education = QComboBox()
        self.cb_background_education.addItem("Select or roll education", "")
        for _, payload in TMNTOS_WILD_ANIMAL_EDUCATION:
            self.cb_background_education.addItem(payload["name"], payload["name"])
        self.cb_background_education.currentIndexChanged.connect(self.on_background_education_changed)

        self.btn_roll_background_education = QPushButton("Roll")
        self.btn_roll_background_education.clicked.connect(self.on_roll_background_education)

        education_top_l.addWidget(self.cb_background_education, 1)
        education_top_l.addWidget(self.btn_roll_background_education, 0)

        self.ed_background_education_details = QTextEdit()
        self.ed_background_education_details.setReadOnly(True)
        self.ed_background_education_details.setMinimumHeight(110)

        education_container = QWidget()
        education_container_l = QVBoxLayout()
        education_container_l.setContentsMargins(0, 0, 0, 0)
        education_container.setLayout(education_container_l)
        education_container_l.addWidget(education_row)
        education_container_l.addWidget(self.ed_background_education_details)

        basics_form.addRow("Background / Education", education_container)

        creator_row = QWidget()
        creator_top_l = QHBoxLayout()
        creator_top_l.setContentsMargins(0, 0, 0, 0)
        creator_row.setLayout(creator_top_l)

        self.cb_creator_organization = QComboBox()
        self.cb_creator_organization.addItem("Select or roll creator organization", "")
        for _, payload in TMNTOS_CREATOR_ORGANIZATIONS:
            self.cb_creator_organization.addItem(payload["name"], payload["name"])
        self.cb_creator_organization.currentIndexChanged.connect(self.on_creator_organization_changed)

        self.btn_roll_creator_organization = QPushButton("Roll")
        self.btn_roll_creator_organization.clicked.connect(self.on_roll_creator_organization)

        creator_top_l.addWidget(self.cb_creator_organization, 1)
        creator_top_l.addWidget(self.btn_roll_creator_organization, 0)

        self.ed_creator_organization_details = QTextEdit()
        self.ed_creator_organization_details.setReadOnly(True)
        self.ed_creator_organization_details.setMinimumHeight(70)

        creator_container = QWidget()
        creator_container_l = QVBoxLayout()
        creator_container_l.setContentsMargins(0, 0, 0, 0)
        creator_container.setLayout(creator_container_l)
        creator_container_l.addWidget(creator_row)
        creator_container_l.addWidget(self.ed_creator_organization_details)

        basics_form.addRow("Creator Organization", creator_container)

        size_row = QWidget()
        size_row_layout = QHBoxLayout()
        size_row_layout.setContentsMargins(0, 0, 0, 0)
        size_row.setLayout(size_row_layout)

        self.cb_size_level = QComboBox()
        for lvl in range(1, 26):
            self.cb_size_level.addItem(str(lvl), lvl)

        self.cb_size_build = QComboBox()
        self.cb_size_build.addItem("Short", "short")
        self.cb_size_build.addItem("Medium", "medium")
        self.cb_size_build.addItem("Long", "long")

        self.btn_roll_size = QPushButton("Roll")
        self.btn_roll_size.clicked.connect(self.on_roll_size_clicked)

        size_row_layout.addWidget(QLabel("Level"))
        size_row_layout.addWidget(self.cb_size_level)
        size_row_layout.addSpacing(8)
        size_row_layout.addWidget(QLabel("Build"))
        size_row_layout.addWidget(self.cb_size_build)
        size_row_layout.addStretch(1)
        size_row_layout.addWidget(self.btn_roll_size)

        basics_form.addRow("Size", size_row)

        self.ed_weight = QLineEdit()
        basics_form.addRow("Weight", self.ed_weight)

        self.ed_height = QLineEdit()
        basics_form.addRow("Height", self.ed_height)

        self.sp_total_credits = QSpinBox()
        self.sp_total_credits.setRange(0, 2_000_000_000)
        self.sp_total_credits.valueChanged.connect(self.recalc_total_wealth)
        basics_form.addRow("Total Credits", self.sp_total_credits)

        self.ed_total_wealth = QLineEdit()
        self.ed_total_wealth.setReadOnly(True)
        basics_form.addRow("Total Wealth", self.ed_total_wealth)

        self.sp_xp = QSpinBox()
        self.sp_xp.setRange(0, 10_000_000)
        basics_form.addRow("XP", self.sp_xp)

        self.sp_level = QSpinBox()
        self.sp_level.setRange(1, 99)
        self.sp_level.valueChanged.connect(self.recalc_skill_displays)
        self.sp_level.valueChanged.connect(self.recalc_combat_from_training)
        basics_form.addRow("Level", self.sp_level)

        hp_row = QWidget()
        hp_row_l = QHBoxLayout()
        hp_row_l.setContentsMargins(0, 0, 0, 0)
        hp_row.setLayout(hp_row_l)

        self.sp_hp = QSpinBox()
        self.sp_hp.setRange(0, 100_000)

        self.btn_roll_hp = QPushButton("Roll")
        self.btn_roll_hp.setToolTip("Roll 1d6 and add to PE to determine HP")
        self.btn_roll_hp.clicked.connect(self.on_roll_hp_clicked)

        hp_row_l.addWidget(self.sp_hp, 1)
        hp_row_l.addWidget(self.btn_roll_hp, 0)

        basics_form.addRow("Hit Points", hp_row)

        self.sp_sdc = QSpinBox()
        self.sp_sdc.setRange(0, 100_000)
        self.sp_sdc.valueChanged.connect(self.sync_defense_summary_fields)
        basics_form.addRow("Base SDC", self.sp_sdc)

        self.ed_basic_armor_ar = QLineEdit()
        self.ed_basic_armor_ar.setReadOnly(True)
        basics_form.addRow("Armor AR", self.ed_basic_armor_ar)

        self.ed_basic_armor_sdc = QLineEdit()
        self.ed_basic_armor_sdc.setReadOnly(True)
        basics_form.addRow("Armor SDC", self.ed_basic_armor_sdc)

        self.ed_basic_shield_sdc = QLineEdit()
        self.ed_basic_shield_sdc.setReadOnly(True)
        basics_form.addRow("Shield SDC", self.ed_basic_shield_sdc)

        self.ed_basic_total_sdc = QLineEdit()
        self.ed_basic_total_sdc.setReadOnly(True)
        basics_form.addRow("Total SDC", self.ed_basic_total_sdc)

        self.basics_layout.addStretch(1)

        # ===================== Attributes tab =====================
        self.attributes_layout = self.make_scrollable_tab(self.tab_attributes)
        attr_form = QFormLayout()
        self.attributes_layout.addLayout(attr_form)
        self.attribute_fields: dict[str, QSpinBox] = {}

        for attr in ["IQ - Intelligence Quotient", "ME - Mental Endurance", "MA - Mental Affinity", "PS - Physical Strength", "PP - Physical Prowess", "PE - Physical Endurance", "PB - Physical Beauty", "Speed"]:
            sp = QSpinBox()
            sp.setRange(0, 100)
            sp.valueChanged.connect(self.recalc_skill_displays)

            row = QWidget()
            row_l = QHBoxLayout()
            row_l.setContentsMargins(0, 0, 0, 0)
            row.setLayout(row_l)

            btn = QPushButton("Roll")
            btn.setToolTip("Roll attribute (3d6; if 16–18 add +1d6)")
            btn.clicked.connect(lambda _=False, a=attr: self.on_roll_single_attribute(a))

            row_l.addWidget(sp, 1)
            row_l.addWidget(btn, 0)

            attr_form.addRow(attr, row)
            self.attribute_fields[attr] = sp

        self.btn_roll_all_attributes = QPushButton("Roll All")
        self.btn_roll_all_attributes.setToolTip("Roll all attributes (3d6; if 16–18 add +1d6).")
        self.btn_roll_all_attributes.clicked.connect(self.on_roll_all_attributes)
        attr_form.addRow("", self.btn_roll_all_attributes)
        self.attributes_layout.addStretch(1)

        # ===================== Skills tab =====================
        self.skills_layout = self.make_scrollable_tab(self.tab_skills)
        skills_layout = self.skills_layout

        self._load_skill_rules()
        self._build_skill_models()

        skills_layout.addWidget(QLabel("Professional Skills (10)"))
        pro_form = QFormLayout()
        self.pro_skill_boxes = []
        self.pro_skill_pct_labels = []

        for i in range(10):
            cb = QComboBox()
            cb.setModel(self.pro_model)
            cb.currentIndexChanged.connect(self.on_skills_changed)

            pct = QLabel("—")
            pct.setMinimumWidth(70)

            btn_roll = QPushButton("Roll")
            btn_roll.setMaximumWidth(70)
            btn_roll.clicked.connect(
                lambda _=False, c=cb: self.on_roll_skill_check(c, self.pro_skill_lookup)
            )

            row = QWidget()
            row_l = QHBoxLayout(row)
            row_l.setContentsMargins(0, 0, 0, 0)
            row_l.addWidget(cb, 1)
            row_l.addWidget(pct, 0)
            row_l.addWidget(btn_roll, 0)

            self.pro_skill_boxes.append(cb)
            self.pro_skill_pct_labels.append(pct)
            pro_form.addRow(f"Pro {i+1}", row)

        skills_layout.addLayout(pro_form)
        skills_layout.addWidget(QLabel(""))

        skills_layout.addWidget(QLabel("Amateur Skills (15)"))
        ama_form = QFormLayout()
        self.amateur_skill_boxes = []
        self.amateur_skill_pct_labels = []

        for i in range(15):
            cb = QComboBox()
            cb.setModel(self.amateur_model)
            cb.currentIndexChanged.connect(self.on_skills_changed)

            pct = QLabel("—")
            pct.setMinimumWidth(70)

            btn_roll = QPushButton("Roll")
            btn_roll.setMaximumWidth(70)
            btn_roll.clicked.connect(
                lambda _=False, c=cb: self.on_roll_skill_check(c, self.amateur_skill_lookup)
            )

            row = QWidget()
            row_l = QHBoxLayout(row)
            row_l.setContentsMargins(0, 0, 0, 0)
            row_l.addWidget(cb, 1)
            row_l.addWidget(pct, 0)
            row_l.addWidget(btn_roll, 0)

            self.amateur_skill_boxes.append(cb)
            self.amateur_skill_pct_labels.append(pct)
            ama_form.addRow(f"Amateur {i+1}", row)

        skills_layout.addLayout(ama_form)
        skills_layout.addStretch(1)

        # ===================== Combat tab =====================
        self.combat_layout = self.make_scrollable_tab(self.tab_combat)
        combat_form = QFormLayout()
        self.combat_layout.addLayout(combat_form)

        self.cb_combat_training = QComboBox()
        for name in _training_names():
            self.cb_combat_training.addItem(name, name)

        self.ed_combat_training_details = QTextEdit()
        self.ed_combat_training_details.setReadOnly(False)
        self.ed_combat_training_details.setMinimumHeight(180)

        combat_form.addRow("Combat Training", self.cb_combat_training)
        combat_form.addRow("Training Details", self.ed_combat_training_details)

        self.chk_combat_auto_details = QCheckBox("Auto-generate Training Details")
        self.chk_combat_auto_details.setChecked(True)
        self.chk_combat_auto_details.toggled.connect(lambda _=False: self.recalc_combat_from_training())
        combat_form.addRow("", self.chk_combat_auto_details)

        self.chk_combat_override = QCheckBox("Override derived combat values (manual edit)")
        self.chk_combat_override.setChecked(False)
        self.chk_combat_override.toggled.connect(self.on_toggle_combat_override)
        combat_form.addRow("", self.chk_combat_override)

        self.cb_combat_training.currentIndexChanged.connect(self.recalc_combat_from_training)

        self.sp_strike = QSpinBox()
        self.sp_parry = QSpinBox()
        self.sp_dodge = QSpinBox()
        self.sp_save_vs_psionic_strangeness = QSpinBox()
        self.sp_initiative = QSpinBox()
        self.sp_actions = QSpinBox()
        self.sp_roll_with_impact = QSpinBox()
        self.ed_critical_range = QLineEdit()

        for sp in (
            self.sp_strike,
            self.sp_parry,
            self.sp_dodge,
            self.sp_save_vs_psionic_strangeness,
            self.sp_initiative,
            self.sp_actions,
            self.sp_roll_with_impact,
        ):
            sp.setRange(-50, 50)

        self.sp_save_vs_psionic_strangeness.setReadOnly(True)
        self.sp_roll_with_impact.setReadOnly(True)
        self.ed_critical_range.setReadOnly(True)

        combat_form.addRow("Strike", self.sp_strike)
        combat_form.addRow("Parry", self.sp_parry)
        combat_form.addRow("Dodge", self.sp_dodge)
        combat_form.addRow("Saves VS Psionic & Strangeness", self.sp_save_vs_psionic_strangeness)
        combat_form.addRow("Initiative", self.sp_initiative)
        combat_form.addRow("Actions per Round", self.sp_actions)
        combat_form.addRow("Roll with Impact", self.sp_roll_with_impact)
        combat_form.addRow("Critical Range", self.ed_critical_range)

        techniques_box = QGroupBox("Combat Techniques / Special Attacks")
        techniques_layout = QVBoxLayout(techniques_box)

        self.lw_combat_techniques = QListWidget()
        techniques_layout.addWidget(self.lw_combat_techniques)

        combat_form.addRow("", techniques_box)
        self._set_combat_spinboxes_editable(False)
        self.combat_layout.addStretch(1)

        if hasattr(self, "attr_spinners") and "ME - Mental Endurance" in self.attr_spinners:
            self.attr_spinners["ME - Mental Endurance"].valueChanged.connect(self._recalc_save_vs_psionic_strangeness)
        
        if hasattr(self, "attribute_fields") and "ME - Mental Endurance" in self.attribute_fields:
            self.attribute_fields["ME - Mental Endurance"].valueChanged.connect(self._recalc_save_vs_psionic_strangeness)

        self._recalc_save_vs_psionic_strangeness()

        # ===================== Bio-E / Mutant tab =====================
        self.bioe_layout = self.make_scrollable_tab(self.tab_bioe)

        bio_top = QFormLayout()
        self.bioe_layout.addLayout(bio_top)

        self.sp_bio_total = QSpinBox()
        self.sp_bio_total.setRange(0, 999)
        self.sp_bio_total.valueChanged.connect(self.recalc_bioe_spent)
        bio_top.addRow("Starting Bio-E", self.sp_bio_total)

        self.sp_bio_spent = QSpinBox()
        self.sp_bio_spent.setRange(-999, 999)
        self.sp_bio_spent.setReadOnly(True)
        bio_top.addRow("Spent Bio-E", self.sp_bio_spent)

        orig_box = QGroupBox("Original Animal")
        orig_form = QFormLayout(orig_box)

        self.ed_bio_orig_size_level = QLineEdit()
        self.ed_bio_orig_size_level.setReadOnly(True)
        orig_form.addRow("Size Level", self.ed_bio_orig_size_level)

        self.ed_bio_orig_length = QLineEdit()
        self.ed_bio_orig_length.setReadOnly(True)
        orig_form.addRow("Length", self.ed_bio_orig_length)

        self.ed_bio_orig_weight = QLineEdit()
        self.ed_bio_orig_weight.setReadOnly(True)
        orig_form.addRow("Weight", self.ed_bio_orig_weight)

        self.ed_bio_orig_build = QLineEdit()
        self.ed_bio_orig_build.setReadOnly(True)
        orig_form.addRow("Build", self.ed_bio_orig_build)

        self.bioe_layout.addWidget(orig_box)

        mutant_box = QGroupBox("Mutant Form / Human Features")
        mutant_form = QFormLayout(mutant_box)

        self.cb_bio_mutant_size_level = QComboBox()
        self.cb_bio_mutant_size_level.addItem("Select size level", 0)
        for lvl in range(1, 26):
            self.cb_bio_mutant_size_level.addItem(str(lvl), lvl)
        self.cb_bio_mutant_size_level.currentIndexChanged.connect(self.recalc_bioe_spent)
        mutant_form.addRow("Mutant Size Level", self.cb_bio_mutant_size_level)

        self.cb_human_biped = QComboBox()
        for label, cost in HUMAN_FEATURE_OPTIONS:
            self.cb_human_biped.addItem(label, cost)
        self.cb_human_biped.currentIndexChanged.connect(self.recalc_bioe_spent)
        mutant_form.addRow("Biped", self.cb_human_biped)

        self.cb_human_hands = QComboBox()
        for label, cost in HUMAN_FEATURE_OPTIONS:
            self.cb_human_hands.addItem(label, cost)
        self.cb_human_hands.currentIndexChanged.connect(self.recalc_bioe_spent)
        mutant_form.addRow("Hands", self.cb_human_hands)

        self.cb_human_speech = QComboBox()
        for label, cost in HUMAN_FEATURE_OPTIONS:
            self.cb_human_speech.addItem(label, cost)
        self.cb_human_speech.currentIndexChanged.connect(self.recalc_bioe_spent)
        mutant_form.addRow("Speech", self.cb_human_speech)

        self.cb_human_looks = QComboBox()
        for label, cost in HUMAN_FEATURE_OPTIONS:
            self.cb_human_looks.addItem(label, cost)
        self.cb_human_looks.currentIndexChanged.connect(self.recalc_bioe_spent)
        mutant_form.addRow("Looks", self.cb_human_looks)

        self.bioe_layout.addWidget(mutant_box)

        nw_box = QGroupBox("Natural Weapons")
        nw_layout = QFormLayout(nw_box)
        self.bio_weapon_combos: list[QComboBox] = []

        for i in range(5):
            cb = QComboBox()
            cb.addItem("None", {})
            self.bio_weapon_combos.append(cb)
            cb.currentIndexChanged.connect(self.recalc_bioe_spent)
            nw_layout.addRow(f"Weapon {i + 1}", cb)

        self.bioe_layout.addWidget(nw_box)

        ability_box = QGroupBox("Animal Abilities")
        ability_layout = QFormLayout(ability_box)
        self.bio_ability_combos: list[QComboBox] = []

        for i in range(8):
            cb = QComboBox()
            cb.addItem("None", {})
            self.bio_ability_combos.append(cb)
            cb.currentIndexChanged.connect(self.recalc_bioe_spent)
            ability_layout.addRow(f"Ability {i + 1}", cb)

        self.bioe_layout.addWidget(ability_box)

        animal_psionic_box = QGroupBox("Mutant Animal Psionic Powers")
        animal_psionic_layout = QFormLayout(animal_psionic_box)
        self.bio_mutant_animal_psionic_combos: list[QComboBox] = []

        for i in range(6):
            cb = self._make_bio_catalog_combo(
                get_psionic_catalog_options(PSIONIC_CATEGORY_MUTANT_ANIMAL)
            )
            self.bio_mutant_animal_psionic_combos.append(cb)
            animal_psionic_layout.addRow(f"Animal Psionic {i + 1}", cb)

        self.bioe_layout.addWidget(animal_psionic_box)

        hominid_psionic_box = QGroupBox("Mutant Hominid Psionic Powers")
        hominid_psionic_layout = QFormLayout(hominid_psionic_box)
        self.bio_mutant_hominid_psionic_combos: list[QComboBox] = []

        for i in range(6):
            cb = self._make_bio_catalog_combo(
                get_psionic_catalog_options(PSIONIC_CATEGORY_MUTANT_HOMINID)
            )
            self.bio_mutant_hominid_psionic_combos.append(cb)
            hominid_psionic_layout.addRow(f"Hominid Psionic {i + 1}", cb)

        self.bioe_layout.addWidget(hominid_psionic_box)

        prosthetic_psionic_box = QGroupBox("Mutant Prosthetic Psionic Powers")
        prosthetic_psionic_layout = QFormLayout(prosthetic_psionic_box)
        self.bio_mutant_prosthetic_psionic_combos: list[QComboBox] = []

        for i in range(3):
            cb = self._make_bio_catalog_combo(
                get_psionic_catalog_options(PSIONIC_CATEGORY_MUTANT_PROSTHETIC)
            )
            self.bio_mutant_prosthetic_psionic_combos.append(cb)
            prosthetic_psionic_layout.addRow(f"Prosthetic Psionic {i + 1}", cb)

        self.bioe_layout.addWidget(prosthetic_psionic_box)

        human_ability_box = QGroupBox("Mutant Human Abilities")
        human_ability_layout = QFormLayout(human_ability_box)
        self.bio_mutant_human_ability_combos: list[QComboBox] = []

        for i in range(8):
            cb = self._make_bio_catalog_combo(
                get_psionic_catalog_options(PSIONIC_CATEGORY_MUTANT_HUMAN_ABILITIES)
            )
            self.bio_mutant_human_ability_combos.append(cb)
            human_ability_layout.addRow(f"Human Ability {i + 1}", cb)

        self.bioe_layout.addWidget(human_ability_box)

        hominid_ability_box = QGroupBox("Mutant Hominid Abilities")
        hominid_ability_layout = QFormLayout(hominid_ability_box)
        self.bio_mutant_hominid_ability_combos: list[QComboBox] = []

        for i in range(8):
            cb = self._make_bio_catalog_combo(
                get_psionic_catalog_options(PSIONIC_CATEGORY_MUTANT_HOMINID_ABILITIES)
            )
            self.bio_mutant_hominid_ability_combos.append(cb)
            hominid_ability_layout.addRow(f"Hominid Ability {i + 1}", cb)

        self.bioe_layout.addWidget(hominid_ability_box)

        traits_box = QGroupBox("Traits / Notes")
        traits_layout = QVBoxLayout(traits_box)

        self.ed_traits = QTextEdit()
        self.ed_traits.setPlaceholderText("One trait per line")
        traits_layout.addWidget(self.ed_traits)

        self.bioe_layout.addWidget(traits_box)
        self.bioe_layout.addStretch(1)

        # ===================== Equipment tab =====================
        self.equipment_layout = self.make_scrollable_tab(self.tab_equipment)
        equip_layout = self.equipment_layout

        weapons_box = QGroupBox("Weapons")
        weapons_form = QFormLayout(weapons_box)
        self.weapon_combos = []
        self.weapon_cost_labels = []
        self.weapon_detail_boxes = []
        self.weapon_attack_buttons = []
        self.weapon_damage_buttons = []

        for i in range(5):
            row = QWidget()
            row_l = QVBoxLayout()
            row_l.setContentsMargins(0, 0, 0, 0)
            row.setLayout(row_l)

            top = QWidget()
            top_l = QHBoxLayout()
            top_l.setContentsMargins(0, 0, 0, 0)
            top.setLayout(top_l)

            cb = QComboBox()
            cb.addItem("Select a weapon", "")
            for w in sorted(WEAPONS_CATALOG, key=lambda x: x["name"]):
                cb.addItem(w["name"], w["name"])

            btn_attack = QPushButton("Roll To Hit")
            btn_attack.setEnabled(False)
            btn_attack.clicked.connect(lambda _=False, idx=i: self.on_weapon_roll_to_hit(idx))

            btn_dmg = QPushButton("Roll Damage")
            btn_dmg.setEnabled(False)
            btn_dmg.clicked.connect(lambda _=False, idx=i: self.on_weapon_roll_damage(idx))

            cost_lbl = QLabel("$0")
            cost_lbl.setMinimumWidth(90)

            top_l.addWidget(cb, 1)
            top_l.addWidget(btn_attack, 0)
            top_l.addWidget(btn_dmg, 0)
            top_l.addWidget(cost_lbl, 0)

            details = QTextEdit()
            details.setReadOnly(True)
            details.setMinimumHeight(55)

            row_l.addWidget(top)
            row_l.addWidget(details)

            cb.currentIndexChanged.connect(lambda _=False, idx=i: self.on_weapon_changed(idx))

            self.weapon_combos.append(cb)
            self.weapon_cost_labels.append(cost_lbl)
            self.weapon_detail_boxes.append(details)
            self.weapon_attack_buttons.append(btn_attack)
            self.weapon_damage_buttons.append(btn_dmg)

            weapons_form.addRow(f"Weapon {i+1}", row)

        equip_layout.addWidget(weapons_box)

        armor_box = QGroupBox("Armor")
        armor_form = QFormLayout(armor_box)

        armor_row = QWidget()
        armor_row_l = QHBoxLayout()
        armor_row_l.setContentsMargins(0, 0, 0, 0)
        armor_row.setLayout(armor_row_l)

        self.cb_armor = QComboBox()
        self.cb_armor.addItem("Select armor", "")
        for a in sorted(ARMOR_CATALOG, key=lambda x: x["name"]):
            self.cb_armor.addItem(a["name"], a["name"])
        self.cb_armor.currentIndexChanged.connect(self.on_armor_changed)

        self.lbl_armor_cost = QLabel("$0")
        self.lbl_armor_cost.setMinimumWidth(90)
        armor_row_l.addWidget(self.cb_armor, 1)
        armor_row_l.addWidget(self.lbl_armor_cost, 0)

        self.ed_armor_name = QLineEdit()
        self.sp_armor_ar = QSpinBox()
        self.sp_armor_ar.setRange(0, 99)
        self.sp_armor_sdc = QSpinBox()
        self.sp_armor_sdc.setRange(0, 100_000)

        armor_form.addRow("Armor Type", armor_row)
        armor_form.addRow("Armor (custom name)", self.ed_armor_name)
        armor_form.addRow("AR", self.sp_armor_ar)
        armor_form.addRow("Armor SDC", self.sp_armor_sdc)

        equip_layout.addWidget(armor_box)

        shield_box = QGroupBox("Shields")
        shield_form = QFormLayout(shield_box)

        shield_row = QWidget()
        shield_row_l = QHBoxLayout()
        shield_row_l.setContentsMargins(0, 0, 0, 0)
        shield_row.setLayout(shield_row_l)

        self.cb_shield = QComboBox()
        self.cb_shield.addItem("Select shield", "")
        for s in sorted(SHIELD_CATALOG, key=lambda x: x["name"]):
            self.cb_shield.addItem(s["name"], s["name"])
        self.cb_shield.currentIndexChanged.connect(self.on_shield_changed)

        self.lbl_shield_cost = QLabel("$0")
        self.lbl_shield_cost.setMinimumWidth(90)

        shield_row_l.addWidget(self.cb_shield, 1)
        shield_row_l.addWidget(self.lbl_shield_cost, 0)

        self.lbl_shield_parry = QLabel("Parry Bonus: —")
        self.lbl_shield_sdc = QLabel("SDC: —")
        self.ed_shield_notes = QLineEdit()
        self.ed_shield_notes.setPlaceholderText("Notes (optional)")

        shield_form.addRow("Shield Type", shield_row)
        shield_form.addRow("", self.lbl_shield_parry)
        shield_form.addRow("", self.lbl_shield_sdc)
        shield_form.addRow("Notes", self.ed_shield_notes)

        equip_layout.addWidget(shield_box)

        gear_box = QGroupBox("Gear")
        gear_form = QFormLayout(gear_box)
        self.gear_combos = []
        self.gear_cost_labels = []

        gear_sorted = sorted(GEAR_CATALOG, key=lambda x: x["name"])
        for i in range(30):
            row = QWidget()
            row_l = QHBoxLayout()
            row_l.setContentsMargins(0, 0, 0, 0)
            row.setLayout(row_l)

            cb = QComboBox()
            cb.addItem("Select gear item", "")
            for g in gear_sorted:
                cb.addItem(g["name"], g["name"])

            cost_lbl = QLabel("$0")
            cost_lbl.setMinimumWidth(90)

            row_l.addWidget(cb, 1)
            row_l.addWidget(cost_lbl, 0)

            cb.currentIndexChanged.connect(lambda _=False, idx=i: self.on_gear_changed(idx))

            self.gear_combos.append(cb)
            self.gear_cost_labels.append(cost_lbl)

            gear_form.addRow(f"Gear {i+1}", row)

        equip_layout.addWidget(gear_box)
        equip_layout.addStretch(1)

        # ===================== Basic Vehicles tab =====================
        self.vehicles_layout = self.make_scrollable_tab(self.tab_vehicles)
        vehicles_layout = self.vehicles_layout
        self.vehicle_sections: dict[str, dict[str, Any]] = {}
        self._build_vehicle_section(vehicles_layout, "Landcraft", VEHICLES_LANDCRAFT, key="landcraft")
        self._build_vehicle_section(vehicles_layout, "Watercraft", VEHICLES_WATERCRAFT, key="watercraft")
        self._build_vehicle_section(vehicles_layout, "Aircraft", VEHICLES_AIRCRAFT, key="aircraft")
        vehicles_layout.addStretch(1)

        # Initialize dependent UI state
        self.on_animal_source_changed()
        self.recalc_combat_from_training()
        self.recalc_total_wealth()

        # ===================== Time Machines & Dimension Devices (TA) tab =====================
        self.ta_time_devices_layout = self.make_scrollable_tab(self.tab_time_machines)

        # ---- Section 1: Device selection ----
        ta_device_box = QGroupBox("Time Machines & Dimension Devices (TA)")
        ta_device_form = QFormLayout(ta_device_box)

        self.cb_ta_device_category = QComboBox()
        self.cb_ta_device_category.addItem("Select device category", "")
        self.cb_ta_device_category.addItem("Time Machine", "time_machine")
        self.cb_ta_device_category.addItem("Dimension Device", "dimension_device")
        self.cb_ta_device_category.addItem("Support Device", "support_device")

        self.cb_ta_device_name = QComboBox()
        self.cb_ta_device_name.addItem("Select device", "")

        self.ed_ta_device_details = QTextEdit()
        self.ed_ta_device_details.setReadOnly(True)
        self.ed_ta_device_details.setMinimumHeight(140)
        self.ed_ta_device_details.setPlaceholderText("Selected device details will appear here...")

        ta_device_form.addRow("Device Category", self.cb_ta_device_category)
        ta_device_form.addRow("Device Name", self.cb_ta_device_name)
        ta_device_form.addRow("Device Details", self.ed_ta_device_details)

        self.ta_time_devices_layout.addWidget(ta_device_box)

        # ---- Section 2: Mount / install ----
        ta_mount_box = QGroupBox("Mount / Installation")
        ta_mount_form = QFormLayout(ta_mount_box)

        self.cb_ta_mount_type = QComboBox()
        self.cb_ta_mount_type.addItem("Select mount type", "")
        self.cb_ta_mount_type.addItem("Standalone", "standalone")
        self.cb_ta_mount_type.addItem("Portable", "portable")
        self.cb_ta_mount_type.addItem("Installed in Vehicle", "vehicle")

        self.cb_ta_vehicle_type = QComboBox()
        self.cb_ta_vehicle_type.addItem("Select vehicle type", "")
        self.cb_ta_vehicle_type.addItem("Truck or Van", "truck_van")
        self.cb_ta_vehicle_type.addItem("Compact or Sports Car", "compact_sports_car")
        self.cb_ta_vehicle_type.addItem("Mid-Size or Larger Car", "mid_size_larger_car")
        self.cb_ta_vehicle_type.addItem("Motorcycle", "motorcycle")
        self.cb_ta_vehicle_type.addItem("Aircraft", "aircraft")
        self.cb_ta_vehicle_type.addItem("Watercraft", "watercraft")
        self.cb_ta_vehicle_type.addItem("Other Vehicle", "other_vehicle")
        self.cb_ta_vehicle_type.setEnabled(False)

        self.ed_ta_mount_notes = QTextEdit()
        self.ed_ta_mount_notes.setReadOnly(True)
        self.ed_ta_mount_notes.setMinimumHeight(100)
        self.ed_ta_mount_notes.setPlaceholderText("Mount and installation notes will appear here...")

        ta_mount_form.addRow("Mount Type", self.cb_ta_mount_type)
        ta_mount_form.addRow("Vehicle Type", self.cb_ta_vehicle_type)
        ta_mount_form.addRow("Installation Notes", self.ed_ta_mount_notes)

        self.ta_time_devices_layout.addWidget(ta_mount_box)

        # ---- Section 3: Support devices ----
        ta_support_box = QGroupBox("Support Devices / Sensors")
        ta_support_layout = QVBoxLayout(ta_support_box)

        self.ta_support_device_combos: list[QComboBox] = []
        self.ta_support_portable_checks: list[QCheckBox] = []

        for i in range(6):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)

            cb = QComboBox()
            cb.addItem("None", "")
            cb.setMinimumWidth(360)

            chk = QCheckBox("Portable version")

            row_layout.addWidget(QLabel(f"Support Device {i + 1}"))
            row_layout.addWidget(cb, 1)
            row_layout.addWidget(chk)

            self.ta_support_device_combos.append(cb)
            self.ta_support_portable_checks.append(chk)
            ta_support_layout.addWidget(row)

        self.ta_time_devices_layout.addWidget(ta_support_box)

        # ---- Section 4: Cost summary ----
        ta_cost_box = QGroupBox("Cost Summary")
        ta_cost_form = QFormLayout(ta_cost_box)

        self.sp_ta_base_cost = QSpinBox()
        self.sp_ta_base_cost.setRange(0, 999_999_999)
        self.sp_ta_base_cost.setReadOnly(True)
        self.sp_ta_base_cost.setButtonSymbols(QSpinBox.NoButtons)

        self.sp_ta_install_cost = QSpinBox()
        self.sp_ta_install_cost.setRange(0, 999_999_999)
        self.sp_ta_install_cost.setReadOnly(True)
        self.sp_ta_install_cost.setButtonSymbols(QSpinBox.NoButtons)

        self.sp_ta_support_cost = QSpinBox()
        self.sp_ta_support_cost.setRange(0, 999_999_999)
        self.sp_ta_support_cost.setReadOnly(True)
        self.sp_ta_support_cost.setButtonSymbols(QSpinBox.NoButtons)

        self.sp_ta_total_cost = QSpinBox()
        self.sp_ta_total_cost.setRange(0, 999_999_999)
        self.sp_ta_total_cost.setReadOnly(True)
        self.sp_ta_total_cost.setButtonSymbols(QSpinBox.NoButtons)

        ta_cost_form.addRow("Base Cost", self.sp_ta_base_cost)
        ta_cost_form.addRow("Installation Cost", self.sp_ta_install_cost)
        ta_cost_form.addRow("Support Device Cost", self.sp_ta_support_cost)
        ta_cost_form.addRow("Total Cost", self.sp_ta_total_cost)

        self.ta_time_devices_layout.addWidget(ta_cost_box)

        # ---- Section 5: Builder notes ----
        ta_notes_box = QGroupBox("Builder Notes")
        ta_notes_layout = QVBoxLayout(ta_notes_box)

        self.ed_ta_summary_notes = QTextEdit()
        self.ed_ta_summary_notes.setPlaceholderText("Additional TA builder notes...")
        self.ed_ta_summary_notes.setMinimumHeight(140)

        ta_notes_layout.addWidget(self.ed_ta_summary_notes)
        self.ta_time_devices_layout.addWidget(ta_notes_box)

        # ---- Section 6: Time machine image ----
        ta_image_box = QGroupBox("Time Machine Image")
        ta_image_layout = QVBoxLayout(ta_image_box)

        self.lbl_ta_image_preview = QLabel("No time machine image loaded")
        self.lbl_ta_image_preview.setAlignment(Qt.AlignCenter)
        self.lbl_ta_image_preview.setMinimumHeight(220)
        self.lbl_ta_image_preview.setStyleSheet("border: 1px solid #3a3a3a; border-radius: 8px;")

        ta_image_btn_row = QHBoxLayout()

        self.btn_ta_load_image = QPushButton("Load Time Machine Image")
        self.btn_ta_clear_image = QPushButton("Clear Image")

        self.btn_ta_load_image.clicked.connect(self.on_ta_load_image)
        self.btn_ta_clear_image.clicked.connect(self.on_ta_clear_image)

        ta_image_btn_row.addWidget(self.btn_ta_load_image)
        ta_image_btn_row.addWidget(self.btn_ta_clear_image)

        ta_image_layout.addWidget(self.lbl_ta_image_preview)
        ta_image_layout.addLayout(ta_image_btn_row)

        self.ta_time_devices_layout.addWidget(ta_image_box)
        self.ta_time_devices_layout.addStretch(1)

        # ===================== TA SIGNAL CONNECTIONS =====================
        self.cb_ta_device_category.currentIndexChanged.connect(self.on_ta_device_category_changed)
        self.cb_ta_device_name.currentIndexChanged.connect(self.on_ta_device_name_changed)
        self.cb_ta_mount_type.currentIndexChanged.connect(self.on_ta_mount_type_changed)
        self.cb_ta_vehicle_type.currentIndexChanged.connect(self.on_ta_vehicle_type_changed)

        for cb in self.ta_support_device_combos:
            cb.currentIndexChanged.connect(self.on_ta_support_devices_changed)

        for chk in self.ta_support_portable_checks:
            chk.toggled.connect(self.on_ta_support_devices_changed)

        self._ta_populate_support_device_combos()
        self._ta_reset_builder()

        # ===================== Custom Vehicles (RH) tab =====================
        self.custom_vehicles_layout = self.make_scrollable_tab(self.tab_custom_vehicles)
        cv_box = QGroupBox("Custom Vehicles (RH)")
        cv_layout = QVBoxLayout(cv_box)

        self.ed_custom_vehicles_placeholder = QTextEdit()
        self.ed_custom_vehicles_placeholder.setPlaceholderText("Future RH custom vehicle controls go here…")
        cv_layout.addWidget(self.ed_custom_vehicles_placeholder)

        self.custom_vehicles_layout.addWidget(cv_box)
        self.custom_vehicles_layout.addStretch(1)

        # ===================== Custom Air Ships (MDU) tab =====================
        self.custom_air_ships_layout = self.make_scrollable_tab(self.tab_custom_air_ships)
        ca_box = QGroupBox("Custom Air Ships (MDU)")
        ca_layout = QVBoxLayout(ca_box)

        self.ed_custom_air_ships_placeholder = QTextEdit()
        self.ed_custom_air_ships_placeholder.setPlaceholderText("Future MDU custom air ship controls go here…")
        ca_layout.addWidget(self.ed_custom_air_ships_placeholder)

        self.custom_air_ships_layout.addWidget(ca_box)
        self.custom_air_ships_layout.addStretch(1)



    # ---------- Dice logging ----------

    def log_roll(self, text: str) -> None:
        self.roll_log.append(text)
        sb = self.roll_log.verticalScrollBar()
        if sb is not None:
            sb.setValue(sb.maximum())

    def roll_dice(self, count: int, sides: int) -> Tuple[List[int], int]:
        return roll_dice(count, sides)

    def eval_dice_expression(self, expr: str) -> Tuple[int, str]:
        return eval_dice_expression(expr)

    def log_roll_expression(self, expr: str) -> int:
        total, detail = self.eval_dice_expression(expr)
        self.log_roll(f"{detail} Total = {total}")
        return total

    def on_roll_generic_die(self, faces: int) -> None:
        count = int(self.dice_counts[faces].value())
        if count <= 0:
            self.log_roll(f"(skipped) rolling {count}d{faces}")
            return
        rolls, total = self.roll_dice(count, faces)
        self.log_roll(f"rolling {count}d{faces}... {rolls} Total = {total}")
    
    def on_roll_hp_clicked(self) -> None:
        pe_val = self.get_effective_attribute("PE - Physical Endurance")
        roll = random.randint(1, 6)
        hp = pe_val + roll
        self.sp_hp.setValue(hp)
        self.log_roll(f"HP roll: effective PE({pe_val}) + 1d6({roll}) = {hp}")

    def on_skills_changed(self) -> None:
        self.recalc_skill_displays()
        self.recalc_combat_from_training()
        self.update_psionic_availability()
        self.recalc_bioe_spent()

    def on_roll_skill_check(self, cb: QComboBox, lookup: dict[str, dict[str, Any]]) -> None:
        """Roll 1d100 vs the current displayed/derived skill % (success = roll <= %)."""
        skill_name = self._selected_skill_name(cb)
        if not skill_name:
            self.log_roll("Skill roll: (no skill selected)")
            return

        pct = self._calc_skill_pct(skill_name, lookup)
        if pct is None:
            self.log_roll(f"Skill roll: {skill_name} (no % found) -> skipped")
            return

        roll = random.randint(1, 100)
        success = roll <= int(pct)

        self.log_roll(
            f"Skill roll: {skill_name} ({pct}%) 1d100={roll} -> {'SUCCESS' if success else 'FAIL'}"
        )



    # ---------- Settings ----------
    def on_toggle_dark_mode(self, enabled: bool) -> None:
        self.dark_mode_enabled = enabled

        app = QApplication.instance()
        if app is None:
            return

        icons_dir = r"C:\Users\ianrw\Desktop\TurtleCom\assets\icons"
        arrow_qss = build_arrow_icons_qss(icons_dir)

        # If you have a LIGHT_QSS, use it here. If not, just use "" for light mode.
        base_qss = DARK_QSS if enabled else ""

        app.setStyleSheet(base_qss + "\n" + arrow_qss)
    # ---------- Skill rules ----------
    def _load_skill_rules(self) -> None:
        try:
            self.skill_rules = load_skill_rules()
        except Exception as e:
            rules_path = DATA_DIR / "rules" / "skills.json"
            QMessageBox.warning(
                self,
                "Skills Load Error",
                f"Could not read skills.json:\n\n{rules_path}\n\n{e}",
            )
            self.skill_rules = {"professional": {}, "amateur": {}}

    def _build_skill_models(self) -> None:
        self.pro_model, self.pro_skill_lookup = self._make_grouped_model(self.skill_rules.get("professional", {}))
        self.amateur_model, self.amateur_skill_lookup = self._make_grouped_model(self.skill_rules.get("amateur", {}))

    def _make_grouped_model(self, grouped: dict[str, list[Any]]) -> tuple[QStandardItemModel, dict[str, dict[str, Any]]]:
        model = QStandardItemModel()
        lookup: dict[str, dict[str, Any]] = {}

        blank = QStandardItem("")
        blank.setData("", Qt.UserRole)
        model.appendRow(blank)

        for category, skills in grouped.items():
            header = QStandardItem(category)
            header.setFlags(Qt.ItemIsEnabled)
            header.setData(None, Qt.UserRole)
            model.appendRow(header)

            for s in skills:
                if not isinstance(s, dict):
                    continue
                name = s.get("name", "")
                if not isinstance(name, str) or not name.strip():
                    continue
                name = name.strip()

                item = QStandardItem(f"  {name}")
                item.setData(name, Qt.UserRole)
                model.appendRow(item)
                lookup[name] = s

            sep = QStandardItem("──────────")
            sep.setFlags(Qt.ItemIsEnabled)
            sep.setData(None, Qt.UserRole)
            model.appendRow(sep)

        return model, lookup

    def _selected_skill_name(self, cb: QComboBox) -> str:
        name = cb.currentData(Qt.UserRole)
        return name if isinstance(name, str) else ""

    def _calc_skill_pct(self, skill_name: str, lookup: dict[str, dict[str, Any]]) -> Optional[int]:
        if not skill_name:
            return None

        rule = lookup.get(skill_name)
        if not isinstance(rule, dict):
            return None

        base = rule.get("base_pct")
        if isinstance(base, list) and base:
            base_val = base[0]
        elif isinstance(base, int):
            base_val = base
        else:
            return None

        default_per_level = int(self.skill_rules.get("meta", {}).get("default_per_level", 5))
        per_level = rule.get("per_level", None)
        if not isinstance(per_level, int) or per_level <= 0:
            per_level = default_per_level

        level = int(self.sp_level.value())

        attrib_name = rule.get("attribute")
        attrib_score = self.get_effective_attribute(attrib_name) if attrib_name in self.attribute_fields else 0

        mode = self.skill_rules.get("attribute_bonus_mode", "simple")
        attrib_mod = _simple_attribute_mod(attrib_score) if mode == "simple" and attrib_score > 0 else 0

        physical_totals = self._get_physical_skill_totals()
        extra_pct = int(physical_totals["skill_pct_bonus"].get(skill_name, 0))

        return base_val + per_level * max(0, (level - 1)) + attrib_mod + extra_pct

    def recalc_skill_displays(self) -> None:
        for cb, lbl in zip(self.pro_skill_boxes, self.pro_skill_pct_labels):
            name = self._selected_skill_name(cb)
            pct = self._calc_skill_pct(name, self.pro_skill_lookup)
            lbl.setText(f"{pct}%" if pct is not None else "—")

        for cb, lbl in zip(self.amateur_skill_boxes, self.amateur_skill_pct_labels):
            name = self._selected_skill_name(cb)
            pct = self._calc_skill_pct(name, self.amateur_skill_lookup)
            lbl.setText(f"{pct}%" if pct is not None else "—")

    # ---------- Attributes rolling ----------
    def roll_attribute_score(self) -> tuple[int, list[int]]:
        return roll_attribute_score()

    def on_roll_single_attribute(self, attr_name: str) -> None:
        sp = self.attribute_fields.get(attr_name)
        if sp is None:
            return
        total, rolls = self.roll_attribute_score()
        sp.setValue(total)
        self.log_roll(f"Attribute {attr_name}: rolled {rolls} => {total}")

    def on_roll_all_attributes(self) -> None:
        for attr_name in ("IQ - Intelligence Quotient", "ME - Mental Endurance", "MA - Mental Affinity", "PS - Physical Strength", "PP - Physical Prowess", "PE - Physical Endurance", "PB - Physical Beauty", "Speed"):
            self.on_roll_single_attribute(attr_name)
        self.statusBar().showMessage("Rolled all attributes")

    # ---------- Animal Source / Type / Animal ----------
    def on_animal_source_changed(self) -> None:
        source = str(self.cb_animal_source.currentData() or "")

        self.cb_animal_type.blockSignals(True)
        self.cb_animal.blockSignals(True)
        try:
            self.cb_animal_type.clear()
            self.cb_animal.clear()

            self.cb_animal_type.addItem("Roll or select your animal type", "")
            self.cb_animal.addItem("Roll or select your animal", "")

            if source == "tmntos":
                for _, tname in TMNTOS_ANIMAL_TYPE_RANGES:
                    self.cb_animal_type.addItem(tname, tname)
                self.btn_roll_animal_type.setEnabled(True)
                self.btn_roll_animal.setEnabled(True)

            elif source == "tmntta":
                for _, tname in TMNTTA_ANIMAL_TYPE_RANGES:
                    self.cb_animal_type.addItem(tname, tname)
                self.btn_roll_animal_type.setEnabled(True)
                self.btn_roll_animal.setEnabled(True)

            else:
                self.btn_roll_animal_type.setEnabled(False)
                self.btn_roll_animal.setEnabled(False)
        finally:
            self.cb_animal_type.blockSignals(False)
            self.cb_animal.blockSignals(False)

        self._reload_origin_controls_for_source()

    def on_animal_type_changed(self) -> None:
        source = str(self.cb_animal_source.currentData() or "")
        animal_type = str(self.cb_animal_type.currentData() or "")

        self.cb_animal.blockSignals(True)
        try:
            self.cb_animal.clear()
            self.cb_animal.addItem("Roll or select your animal", "")

            if source == "tmntos":
                table = TMNTOS_ANIMALS_BY_TYPE.get(animal_type, [])

            elif source == "tmntta":
                table = TMNTTA_ANIMALS_BY_TYPE.get(animal_type, [])

            else:
                table = []

            for _, aname in table:
                self.cb_animal.addItem(aname, aname)
        finally:
            self.cb_animal.blockSignals(False)

    def on_roll_animal_type(self) -> None:
        source = str(self.cb_animal_source.currentData() or "")

        if source == "tmntos":
            table = TMNTOS_ANIMAL_TYPE_RANGES
            source_label = "TMNTOS"
        elif source == "tmntta":
            table = TMNTTA_ANIMAL_TYPE_RANGES
            source_label = "TMNTTA"
        else:
            return

        roll = roll_d100()
        chosen = pick_from_ranges(table, roll)
        if not chosen:
            return

        idx = self.cb_animal_type.findData(chosen)
        self.cb_animal_type.setCurrentIndex(idx if idx != -1 else 0)
        self.log_roll(f"Animal Type ({source_label}): rolled d100={roll} => {chosen}")

    def on_roll_animal(self) -> None:
        source = str(self.cb_animal_source.currentData() or "")
        animal_type = str(self.cb_animal_type.currentData() or "")

        if source == "tmntos":
            table = TMNTOS_ANIMALS_BY_TYPE.get(animal_type, [])
            source_label = "TMNTOS"
        elif source == "tmntta":
            table = TMNTTA_ANIMALS_BY_TYPE.get(animal_type, [])
            source_label = "TMNTTA"
        else:
            return

        if not table:
            return

        roll = roll_d100()
        chosen = pick_from_ranges(table, roll)
        if not chosen:
            return

        idx = self.cb_animal.findData(chosen)
        self.cb_animal.setCurrentIndex(idx if idx != -1 else 0)
        self.log_roll(f"Animal ({source_label}): rolled d100={roll} => {chosen}")






    # ---------- Combat training ----------
    def on_toggle_combat_override(self, enabled: bool) -> None:
        self._set_combat_spinboxes_editable(bool(enabled))
        self.recalc_combat_from_training()

    def _set_combat_spinboxes_editable(self, editable: bool) -> None:
        for sp in (
            self.sp_strike,
            self.sp_parry,
            self.sp_dodge,
            self.sp_save_vs_psionic_strangeness,
            self.sp_initiative,
            self.sp_actions,
            self.sp_roll_with_impact,
        ):
            sp.setReadOnly(not editable)
            sp.setButtonSymbols(
                QSpinBox.ButtonSymbols.UpDownArrows if editable else QSpinBox.ButtonSymbols.NoButtons
            )

        if hasattr(self, "ed_critical_range"):
            self.ed_critical_range.setReadOnly(True)
            

    def _calc_training_summary(self, training_name: str, level: int) -> dict[str, Any]:
        out: dict[str, Any] = {
            "strike": 0,
            "parry": 0,
            "dodge": 0,
            "initiative": 0,
            "actions_per_round": int(BASELINE_COMBAT["actions_per_round"]),
            "unarmed_damage": str(BASELINE_COMBAT["unarmed_damage"]),
            "known_actions": list(BASELINE_COMBAT["known_actions"]),
            "known_reactions": list(BASELINE_COMBAT["known_reactions"]),
            "critical_range": tuple(BASELINE_COMBAT["critical_range"]),
            "roll_with_impact": 0,
            "melee_damage_list": [],
            "melee_damage": "—",
            "specials": [],
            "notes": list(BASELINE_COMBAT.get("notes", [])),
        }

        if training_name == "None":
            return out

        table = COMBAT_TRAINING_RULES.get(training_name, {})
        for lvl in sorted(table.keys()):
            if lvl > level:
                break
            delta = table[lvl]

            for k in ("strike", "parry", "dodge", "initiative", "actions_per_round"):
                if k in delta and isinstance(delta[k], int):
                    out[k] += int(delta[k])

            if "roll_with_impact" in delta and isinstance(delta["roll_with_impact"], int):
                out["roll_with_impact"] += int(delta["roll_with_impact"])

            if "melee_damage" in delta and isinstance(delta["melee_damage"], str):
                out["melee_damage_list"].append(delta["melee_damage"])

            if "unlock_actions" in delta and isinstance(delta["unlock_actions"], list):
                for a in delta["unlock_actions"]:
                    if isinstance(a, str) and a and a not in out["known_actions"]:
                        out["known_actions"].append(a)

            if "unlock_reactions" in delta and isinstance(delta["unlock_reactions"], list):
                for r in delta["unlock_reactions"]:
                    if isinstance(r, str) and r and r not in out["known_reactions"]:
                        out["known_reactions"].append(r)

            if "critical_range" in delta and isinstance(delta["critical_range"], tuple) and len(delta["critical_range"]) == 2:
                out["critical_range"] = delta["critical_range"]

            if "specials" in delta and isinstance(delta["specials"], list):
                for s in delta["specials"]:
                    if isinstance(s, str) and s:
                        out["specials"].append(s)

        out["melee_damage"] = _combine_melee_damage(out["melee_damage_list"])
        return out

    def recalc_combat_from_training(self) -> None:
        training = self.cb_combat_training.currentData()
        training_name = str(training) if isinstance(training, str) and training else "None"
        level = int(self.sp_level.value())

        summary = self._calc_training_summary(training_name, level)
        physical = self._get_physical_skill_totals()
        override_on = bool(self.chk_combat_override.isChecked())

        derived_strike = int(summary["strike"]) + int(physical["combat"].get("strike", 0))
        derived_parry = int(summary["parry"]) + int(physical["combat"].get("parry", 0))
        derived_dodge = int(summary["dodge"]) + int(physical["combat"].get("dodge", 0))
        derived_initiative = int(summary["initiative"]) + int(physical["combat"].get("initiative", 0))
        derived_actions = int(summary["actions_per_round"]) + int(physical["combat"].get("actions_per_round", 0))
        derived_roll_with_impact = int(summary.get("roll_with_impact", 0)) + int(physical["combat"].get("roll_with_impact", 0))

        extra_attacks = list(summary.get("known_actions", []))
        for attack_name in physical.get("extra_attacks", []):
            if attack_name not in extra_attacks:
                extra_attacks.append(attack_name)

        if hasattr(self, "lw_combat_techniques"):
            self.lw_combat_techniques.clear()
            for attack_name in extra_attacks:
                self.lw_combat_techniques.addItem(attack_name)

        if not override_on:
            self.sp_strike.blockSignals(True)
            self.sp_parry.blockSignals(True)
            self.sp_dodge.blockSignals(True)
            self.sp_initiative.blockSignals(True)
            self.sp_actions.blockSignals(True)
            self.sp_roll_with_impact.blockSignals(True)
            try:
                self.sp_strike.setValue(derived_strike)
                self.sp_parry.setValue(derived_parry)
                self.sp_dodge.setValue(derived_dodge)
                self.sp_initiative.setValue(derived_initiative)
                self.sp_actions.setValue(derived_actions)
                self.sp_roll_with_impact.setValue(derived_roll_with_impact)
            finally:
                self.sp_strike.blockSignals(False)
                self.sp_parry.blockSignals(False)
                self.sp_dodge.blockSignals(False)
                self.sp_initiative.blockSignals(False)
                self.sp_actions.blockSignals(False)
                self.sp_roll_with_impact.blockSignals(False)

        crit_min, crit_max = summary["critical_range"]
        crit_text = f"{crit_min}" if crit_min == crit_max else f"{crit_min}–{crit_max}"

        if hasattr(self, "ed_critical_range"):
            self.ed_critical_range.setText(crit_text)

        self._recalc_save_vs_psionic_strangeness()

        if not self.chk_combat_auto_details.isChecked():
            return

        crit_min, crit_max = summary["critical_range"]
        crit_text = f"{crit_min}" if crit_min == crit_max else f"{crit_min}–{crit_max}"

        lines: list[str] = []
        lines.append(f"Training: {training_name}")
        lines.append(f"Level: {level}")
        if override_on:
            lines.append("NOTE: Override enabled — numeric fields are manual.")
        lines.append("")
        lines.append("Derived (training + physical skills):")
        lines.append(f"• Strike: {derived_strike:+d}")
        lines.append(f"• Parry: {derived_parry:+d}")
        lines.append(f"• Dodge: {derived_dodge:+d}")
        lines.append(f"• Initiative: {derived_initiative:+d}")
        lines.append(f"• Actions/round: {derived_actions}")
        lines.append(f"• Roll with Impact bonus: +{derived_roll_with_impact}")
        lines.append(f"• Critical range: {crit_text}")

        sword_strike = int(physical["combat"].get("strike_swords", 0))
        sword_parry = int(physical["combat"].get("parry_swords", 0))
        sword_damage = int(physical["combat"].get("damage_swords", 0))
        pull_punch = int(physical["combat"].get("pull_punch", 0))

        if sword_strike or sword_parry or sword_damage:
            lines.append("")
            lines.append("Weapon-specific bonuses:")
            lines.append(f"• Sword Strike bonus: {sword_strike:+d}")
            lines.append(f"• Sword Parry bonus: {sword_parry:+d}")
            lines.append(f"• Sword Damage bonus: {sword_damage:+d}")

        if pull_punch:
            lines.append(f"• Pull Punch bonus: {pull_punch:+d}")

        if summary.get("melee_damage", "—") != "—":
            lines.append(f"• Melee damage bonus: {summary['melee_damage']}")

        if physical.get("notes"):
            lines.append("")
            lines.append("Physical skill notes:")
            for note in physical["notes"]:
                lines.append(f"• {note}")

        self.ed_combat_training_details.setPlainText("\n".join(lines))
    # ---------------- Size Roll + Apply ----------------
    def on_roll_size_clicked(self) -> None:
        try:
            size_level = int(self.cb_size_level.currentData())
            build_key = str(self.cb_size_build.currentData())
            if size_level not in SIZE_LEVEL_FORMULAS:
                QMessageBox.warning(self, "Size", "Invalid size selection.")
                return

            formulas = SIZE_LEVEL_FORMULAS[size_level]
            weight_expr = formulas["weight"]
            height_expr = formulas[build_key]

            weight_total = self.log_roll_expression(weight_expr.replace("D%", "D%"))
            height_total = self.log_roll_expression(height_expr.replace("D%", "D%"))

            if "ounce" in weight_expr.lower():
                self.ed_weight.setText(f"{weight_total} oz")
            else:
                self.ed_weight.setText(f"{weight_total} lbs")

            self.ed_height.setText(self.format_inches(height_total))

            effects = SIZE_LEVEL_EFFECTS.get(size_level, {})
            self.apply_size_effects(effects)

            self.statusBar().showMessage(f"Rolled size {size_level} ({build_key.title()})")
        except Exception as e:
            QMessageBox.critical(self, "Roll failed", f"Could not roll/apply size.\n\n{e}")

    def format_inches(self, total_inches: int) -> str:
        if total_inches < 12:
            return f'{total_inches}"'
        feet = total_inches // 12
        inches = total_inches % 12
        return f"{feet}' {inches}\""

    def apply_size_effects(self, effects: dict[str, int]) -> None:
        for attr in ["IQ - Intelligence Quotient", "PS - Physical Strength", "PE - Physical Endurance", "Speed"]:
            if attr in effects and attr in self.attribute_fields:
                base = int(self.attribute_fields[attr].value())
                self.attribute_fields[attr].setValue(max(0, base + int(effects[attr])))

        if "SDC" in effects:
            self.sp_sdc.setValue(max(0, int(effects["SDC"])))

        if "bio_e" in effects:
            self.sp_bio_total.setValue(max(0, int(self.sp_bio_total.value()) + int(effects["bio_e"])))

        parts = []
        for k, v in effects.items():
            sign = "+" if v >= 0 else ""
            parts.append(f"{k} {sign}{v}")
        self.log_roll("Applied size effects: " + ", ".join(parts))

    # ---------- Weapon rolling ----------
    def _weapon_damage_expr(self, weapon_name: str) -> Optional[str]:
        w = WEAPONS_BY_NAME.get(weapon_name)
        if not w:
            return None
        details = str(w.get("details", ""))

        m = re.search(r"Damage\s+([0-9Dd%+\-– ]+)", details)
        if not m:
            return None

        raw = m.group(1).strip()
        raw = raw.replace(" ", "")
        raw = raw.replace("D", "d").replace("d%", "d%")

        # Prefer the first entry in ranges like 2D6–3D6 or "2D6–3D6"
        raw = raw.replace("–", "-")
        if "-" in raw and "d" in raw:
            left = raw.split("-", 1)[0]
            if re.fullmatch(r"\d+d\d+(?:\+\d+)?", left):
                return left

        # Simple "1d8+2" etc
        if re.fullmatch(r"\d+d\d+(?:\+\d+)?", raw):
            return raw

        # Sometimes "6D6–7D6" already handled above, or "6D6to12D6"
        m2 = re.search(r"(\d+d\d+(?:\+\d+)?)", raw)
        return m2.group(1) if m2 else None

    def _melee_damage_bonus_int(self) -> int:
        training = str(self.cb_combat_training.currentData() or "None")
        level = int(self.sp_level.value())
        summary = self._calc_training_summary(training, level)
        bonus = 0
        for s in summary.get("melee_damage_list", []) or []:
            if isinstance(s, str):
                m = re.search(r"([+-]\d+)", s.replace(" ", ""))
                if m:
                    bonus += int(m.group(1))
        return bonus

    def on_weapon_roll_to_hit(self, idx: int) -> None:
        if idx >= len(self.weapon_combos):
            return
        weapon = str(self.weapon_combos[idx].currentData() or "")
        if not weapon:
            return
        d20 = random.randint(1, 20)
        bonus = int(self.sp_strike.value())
        total = d20 + bonus
        self.log_roll(f"[To Hit] {weapon}: d20={d20} + Strike({bonus:+d}) => {total}")

    def on_weapon_roll_damage(self, idx: int) -> None:
        if idx >= len(self.weapon_combos):
            return
        weapon = str(self.weapon_combos[idx].currentData() or "")
        if not weapon:
            return

        expr = self._weapon_damage_expr(weapon)
        if not expr:
            self.log_roll(f"[Damage] {weapon}: (no damage expression found)")
            return

        base_total, detail = self.eval_dice_expression(expr)
        dmg_bonus = self._melee_damage_bonus_int()
        total = base_total + dmg_bonus
        self.log_roll(f"[Damage] {weapon}: {detail} Base={base_total} + MeleeBonus({dmg_bonus:+d}) => {total}")


    # ---------- Equipment handlers ----------
    def on_weapon_changed(self, idx: int) -> None:
        if idx >= len(self.weapon_combos):
            return
        name = str(self.weapon_combos[idx].currentData() or "")
        if not name:
            self.weapon_cost_labels[idx].setText("$0")
            self.weapon_detail_boxes[idx].setPlainText("")
            self.weapon_attack_buttons[idx].setEnabled(False)
            self.weapon_damage_buttons[idx].setEnabled(False)
            self.recalc_total_wealth()
            self.recalc_weight_breakdown()
            return
        w = WEAPONS_BY_NAME.get(name, {})
        self.weapon_cost_labels[idx].setText(str(w.get("cost", "$0")))
        self.weapon_detail_boxes[idx].setPlainText(str(w.get("details", "")))
        self.weapon_attack_buttons[idx].setEnabled(True)
        self.weapon_damage_buttons[idx].setEnabled(True)
        self.recalc_total_wealth()
        self.recalc_weight_breakdown()

    def on_armor_changed(self) -> None:
        name = str(self.cb_armor.currentData() or self.cb_armor.currentText() or "").strip()

        if not name:
            self.lbl_armor_cost.setText("$0")
            self.sp_armor_ar.setValue(0)
            self.sp_armor_sdc.setValue(0)
            self.recalc_total_wealth()
            self.recalc_weight_breakdown()
            return

        armor = ARMOR_BY_NAME.get(name, {})
        self.lbl_armor_cost.setText(str(armor.get("cost", "$0")))

        ar = armor.get("ar")
        sdc = armor.get("sdc")

        self.sp_armor_ar.setValue(int(ar) if isinstance(ar, int) else 0)
        self.sp_armor_sdc.setValue(int(sdc) if isinstance(sdc, int) else 0)

        self.sync_defense_summary_fields()
        self.recalc_total_wealth()
        self.recalc_weight_breakdown()

    def on_shield_changed(self) -> None:
        name = str(self.cb_shield.currentData() or self.cb_shield.currentText() or "").strip()

        if not name:
            self.lbl_shield_cost.setText("$0")
            self.lbl_shield_parry.setText("Parry Bonus: —")
            self.lbl_shield_sdc.setText("SDC: —")
            self.sync_defense_summary_fields()
            self.recalc_total_wealth()
            self.recalc_weight_breakdown()
            return

        shield = SHIELD_BY_NAME.get(name, {})

        self.lbl_shield_cost.setText(str(shield.get("cost", "$0")))

        parry = shield.get("parry")
        sdc = shield.get("sdc")

        self.lbl_shield_parry.setText(
            f"Parry Bonus: {parry:+d}" if isinstance(parry, int) else "Parry Bonus: —"
        )
        self.lbl_shield_sdc.setText(
            f"SDC: {sdc}" if isinstance(sdc, int) else "SDC: —"
        )

        self.sync_defense_summary_fields()
        self.recalc_total_wealth()
        self.recalc_weight_breakdown()

    def on_gear_changed(self, idx: int) -> None:
        if idx >= len(self.gear_combos):
            return
        name = str(self.gear_combos[idx].currentData() or "")
        if not name:
            self.gear_cost_labels[idx].setText("$0")
            self.recalc_total_wealth()
            self.recalc_weight_breakdown()
            return
        g = GEAR_BY_NAME.get(name, {})
        self.gear_cost_labels[idx].setText(str(g.get("cost", "$0")))
        self.recalc_total_wealth()
        self.recalc_weight_breakdown()

# ---------- Bio-E helpers ----------

    
    def _bioe_resolve_key(self, animal_label_or_key: str) -> str:
        """
        Takes whatever your UI has (e.g. 'Dog', 'Black Bear', or already a BIOE key)
        and returns a valid BIOE_ANIMAL_DATA key when possible.
        """
        if not animal_label_or_key:
            return ""

        # If it already matches a BIOE key, keep it
        if animal_label_or_key in BIOE_ANIMAL_DATA:
            return animal_label_or_key

        norm = bioe_norm(animal_label_or_key)
        key = BIOE_ANIMAL_ALIASES.get(norm, "")

        # Some UI strings are descriptive like "Crocodile (or Alligator)" – try substring matching
        if not key:
            for alias_norm, bioe_key in BIOE_ANIMAL_ALIASES.items():
                if alias_norm and alias_norm in norm:
                    key = bioe_key
                    break

        return key

    def _bioe_get_animal_rule(self, animal: str) -> dict[str, Any]:
        """
        Takes whatever the UI selected (e.g. 'Dog', 'Black Bear', etc.)
        and resolves it to a valid BIOE_ANIMAL_DATA key.
        """

        if not animal:
            return dict(BIOE_DEFAULT_ANIMAL)

        # If it's already a real key, use it directly
        if animal in BIOE_ANIMAL_DATA:
            return dict(BIOE_ANIMAL_DATA[animal])

        norm = animal.strip().upper()

        # Try alias lookup
        key = BIOE_ANIMAL_ALIASES.get(norm)

        if key and key in BIOE_ANIMAL_DATA:
            return dict(BIOE_ANIMAL_DATA[key])

        # Try partial match fallback
        for alias, bioe_key in BIOE_ANIMAL_ALIASES.items():
            if alias in norm and bioe_key in BIOE_ANIMAL_DATA:
                return dict(BIOE_ANIMAL_DATA[bioe_key])

        # Nothing matched
        return dict(BIOE_DEFAULT_ANIMAL)

    def _bioe_combo_cost(self, cb: QComboBox) -> int:
        val = cb.currentData()
        return int(val) if isinstance(val, int) else 0

    def _bioe_set_original_fields(self, original: dict[str, Any]) -> None:
        size_level = original.get("size_level", "")
        length_in = original.get("length_in", "")
        weight_lbs = original.get("weight_lbs", "")
        build = original.get("build", "")

        self.ed_bio_orig_size_level.setText(str(size_level) if size_level != "" else "")
        self.ed_bio_orig_length.setText(self.format_inches(int(length_in)) if isinstance(length_in, int) else str(length_in))
        self.ed_bio_orig_weight.setText(f"{weight_lbs} lbs" if isinstance(weight_lbs, int) else str(weight_lbs))
        self.ed_bio_orig_build.setText(str(build))

        # Set mutant size selector to original by default (if possible)
        if isinstance(size_level, int) and 1 <= size_level <= 25:
            idx = self.cb_bio_mutant_size_level.findData(size_level)
            self.cb_bio_mutant_size_level.setCurrentIndex(idx if idx != -1 else 0)

    def _bioe_populate_natural_weapons(self, options: list[dict[str, Any] | str]) -> None:
        combos = list(getattr(self, "bio_weapon_combos", []) or [])
        cost_labels = list(getattr(self, "bio_weapon_cost_labels", []) or [])

        normalized: list[tuple[str, int]] = [("None", 0)]

        for item in options or []:
            if isinstance(item, dict):
                name = str(item.get("name", "") or "").strip()
                cost = int(item.get("cost", 0) or 0)
            else:
                name = str(item or "").strip()
                cost = 0

            if not name:
                continue

            normalized.append((name, cost))

        for i, cb in enumerate(combos):
            previous_data = cb.currentData()
            previous_name = ""
            if isinstance(previous_data, dict):
                previous_name = str(previous_data.get("name", "") or "").strip()
            if not previous_name:
                previous_name = str(cb.currentText() or "").strip()

            previous_key = self._bioe_normalize_option_name(previous_name)

            cb.blockSignals(True)
            try:
                cb.clear()
                for name, cost in normalized:
                    label = f"{name} ({cost} Bio-E)" if name != "None" and cost > 0 else name
                    cb.addItem(label, {"name": name, "cost": cost})
            finally:
                cb.blockSignals(False)

            restored_index = -1
            if previous_key:
                for idx in range(cb.count()):
                    data = cb.itemData(idx)
                    if isinstance(data, dict):
                        item_name = str(data.get("name", "") or "").strip()
                    else:
                        item_name = str(cb.itemText(idx) or "").strip()

                    if self._bioe_normalize_option_name(item_name) == previous_key:
                        restored_index = idx
                        break

            if restored_index >= 0:
                cb.setCurrentIndex(restored_index)
            else:
                cb.setCurrentIndex(0)

            if i < len(cost_labels):
                data = cb.currentData() or {}
                cost = int(data.get("cost", 0) or 0) if isinstance(data, dict) else 0
                cost_labels[i].setText(str(cost))

    def _bioe_populate_abilities(self, options: list[dict[str, Any] | str]) -> None:
        combos = list(getattr(self, "bio_ability_combos", []) or [])
        cost_labels = list(getattr(self, "bio_ability_cost_labels", []) or [])

        normalized: list[tuple[str, int]] = [("None", 0)]

        for item in options or []:
            if isinstance(item, dict):
                name = str(item.get("name", "") or "").strip()
                cost = int(item.get("cost", 0) or 0)
            else:
                name = str(item or "").strip()
                cost = 0

            if not name:
                continue

            normalized.append((name, cost))

        for i, cb in enumerate(combos):
            previous_data = cb.currentData()
            previous_name = ""
            if isinstance(previous_data, dict):
                previous_name = str(previous_data.get("name", "") or "").strip()
            if not previous_name:
                previous_name = str(cb.currentText() or "").strip()

            previous_key = self._bioe_normalize_option_name(previous_name)

            cb.blockSignals(True)
            try:
                cb.clear()
                for name, cost in normalized:
                    label = f"{name} ({cost} Bio-E)" if name != "None" and cost > 0 else name
                    cb.addItem(label, {"name": name, "cost": cost})
            finally:
                cb.blockSignals(False)

            restored_index = -1
            if previous_key:
                for idx in range(cb.count()):
                    data = cb.itemData(idx)
                    if isinstance(data, dict):
                        item_name = str(data.get("name", "") or "").strip()
                    else:
                        item_name = str(cb.itemText(idx) or "").strip()

                    if self._bioe_normalize_option_name(item_name) == previous_key:
                        restored_index = idx
                        break

            if restored_index >= 0:
                cb.setCurrentIndex(restored_index)
            else:
                cb.setCurrentIndex(0)

            if i < len(cost_labels):
                data = cb.currentData() or {}
                cost = int(data.get("cost", 0) or 0) if isinstance(data, dict) else 0
                cost_labels[i].setText(str(cost))

    def _bioe_normalize_option_name(self, value: str) -> str:
        text = str(value or "").strip().casefold()
        text = re.sub(r"\s+", " ", text)
        text = text.replace(" (", "(")
        text = text.replace(") ", ")")
        return text

    def update_psionic_availability(self) -> None:
        for cb in getattr(self, "bio_psionic_combos", []):
            cb.setEnabled(True)

        if hasattr(self, "lbl_bio_remaining"):
            self.lbl_bio_remaining.setToolTip("")

        self.recalc_bioe_spent()

    def on_bioe_animal_selected(self) -> None:
        raw_data = str(self.cb_animal.currentData() or "").strip()
        raw_text = str(self.cb_animal.currentText() or "").strip()
        animal = raw_data or raw_text

        if not hasattr(self, "bio_weapon_cost_labels"):
            self.bio_weapon_cost_labels = []
        if not hasattr(self, "bio_ability_cost_labels"):
            self.bio_ability_cost_labels = []

        if not animal:
            if hasattr(self, "sp_bio_total"):
                self.sp_bio_total.setValue(0)

            if hasattr(self, "ed_bio_orig_size_level"):
                self.ed_bio_orig_size_level.clear()
            if hasattr(self, "ed_bio_orig_length"):
                self.ed_bio_orig_length.clear()
            if hasattr(self, "ed_bio_orig_weight"):
                self.ed_bio_orig_weight.clear()
            if hasattr(self, "ed_bio_orig_build"):
                self.ed_bio_orig_build.clear()

            if hasattr(self, "cb_bio_mutant_size_level"):
                self.cb_bio_mutant_size_level.blockSignals(True)
                try:
                    self.cb_bio_mutant_size_level.setCurrentIndex(0)
                finally:
                    self.cb_bio_mutant_size_level.blockSignals(False)

            self._bioe_populate_natural_weapons([])
            self._bioe_populate_abilities([])
            self.recalc_bioe_spent()
            return

        bioe_key = self._bioe_resolve_key(animal)
        if bioe_key and bioe_key in BIOE_ANIMAL_DATA:
            rule = dict(BIOE_ANIMAL_DATA[bioe_key])
        else:
            rule = self._bioe_get_animal_rule(animal)

        if not isinstance(rule, dict):
            rule = dict(BIOE_DEFAULT_ANIMAL)

        original = rule.get("original", {}) or {}

        if hasattr(self, "sp_bio_total"):
            self.sp_bio_total.setValue(int(rule.get("bio_e", 0) or 0))

        self._bioe_set_original_fields(original)

        natural_weapon_options = (
            rule.get("natural_weapons")
            or rule.get("animal_natural_weapons")
            or rule.get("weapons")
            or []
        )
        if not isinstance(natural_weapon_options, list):
            natural_weapon_options = []

        animal_ability_options = (
            rule.get("abilities")
            or rule.get("animal_abilities")
            or []
        )
        if not isinstance(animal_ability_options, list):
            animal_ability_options = []

        self._bioe_populate_natural_weapons(natural_weapon_options)
        self._bioe_populate_abilities(animal_ability_options)

        self.recalc_bioe_spent()
    

    def _resolve_bioe_original_size_level(self, rule: dict[str, Any]) -> int:
        original = rule.get("original", {}) or {}

        candidates = [
            original.get("size_level"),
            rule.get("size_level"),
            rule.get("mutant_size_level"),
        ]

        for value in candidates:
            try:
                size_level = int(value or 0)
            except Exception:
                size_level = 0
            if 1 <= size_level <= 25:
                return size_level

        return 0


    def _bioe_size_level_cost(self) -> int:
        try:
            orig = int(self.ed_bio_orig_size_level.text().strip() or "0")
        except Exception:
            orig = 0

        try:
            chosen = int(self.cb_bio_mutant_size_level.currentData() or 0)
        except Exception:
            chosen = 0

        if orig <= 0 or chosen <= 0:
            return 0

        orig_cost = int(SIZE_LEVEL_EFFECTS.get(orig, {}).get("bio_e", 0) or 0)
        chosen_cost = int(SIZE_LEVEL_EFFECTS.get(chosen, {}).get("bio_e", 0) or 0)

        steps_delta = chosen - orig
        if steps_delta < 0:
            return steps_delta * 5

        return chosen_cost - orig_cost

    def recalc_bioe_spent(self) -> None:
        total_spent = 0

        def combo_cost(cb: QComboBox) -> int:
            data = cb.currentData()
            if isinstance(data, dict):
                return int(data.get("cost", 0) or 0)
            try:
                return int(data or 0)
            except Exception:
                return 0

        def selected_catalog_entries(combo_attr_name: str) -> list[dict[str, int | str]]:
            entries: list[dict[str, int | str]] = []
            for cb in getattr(self, combo_attr_name, []):
                label = str(cb.currentText() or "").strip()
                cost = combo_cost(cb) if cb.isEnabled() else 0
                if label and "None" not in label and cost > 0:
                    entries.append({"name": label.split(" (", 1)[0], "cost": cost})
            return entries

        for cb in (
            getattr(self, "cb_human_hands", None),
            getattr(self, "cb_human_biped", None),
            getattr(self, "cb_human_speech", None),
            getattr(self, "cb_human_looks", None),
        ):
            if cb is not None:
                total_spent += combo_cost(cb)

        total_spent += self._bioe_size_level_cost()

        for cb in getattr(self, "bio_weapon_combos", []):
            total_spent += combo_cost(cb)

        for cb in getattr(self, "bio_ability_combos", []):
            total_spent += combo_cost(cb)

        mutant_animal_psionics = selected_catalog_entries("bio_mutant_animal_psionic_combos")
        mutant_hominid_psionics = selected_catalog_entries("bio_mutant_hominid_psionic_combos")
        mutant_prosthetic_psionics = selected_catalog_entries("bio_mutant_prosthetic_psionic_combos")
        mutant_human_abilities = selected_catalog_entries("bio_mutant_human_ability_combos")
        mutant_hominid_abilities = selected_catalog_entries("bio_mutant_hominid_ability_combos")

        for entries in (
            mutant_animal_psionics,
            mutant_hominid_psionics,
            mutant_prosthetic_psionics,
            mutant_human_abilities,
            mutant_hominid_abilities,
        ):
            total_spent += sum(int(entry.get("cost", 0) or 0) for entry in entries)

        self.sp_bio_spent.setValue(total_spent)

        if hasattr(self, "lbl_bio_remaining"):
            total = int(self.sp_bio_total.value() or 0)
            remaining = total - total_spent
            self.lbl_bio_remaining.setText(f"Remaining Bio-E: {remaining}")



    # ---------- Total Wealth ----------
    def recalc_total_wealth(self) -> None:
        credits = int(self.sp_total_credits.value())
        equip_cost = 0

        for cb in getattr(self, "weapon_combos", []):
            name = str(cb.currentData() or "")
            if name:
                equip_cost += _cost_to_int(str(WEAPONS_BY_NAME.get(name, {}).get("cost", "")))

        armor_type = str(getattr(self, "cb_armor", QComboBox()).currentData() or "")
        if armor_type:
            equip_cost += _cost_to_int(str(ARMOR_BY_NAME.get(armor_type, {}).get("cost", "")))

        shield_type = str(getattr(self, "cb_shield", QComboBox()).currentData() or "")
        if shield_type:
            equip_cost += _cost_to_int(str(SHIELD_BY_NAME.get(shield_type, {}).get("cost", "")))

        for cb in getattr(self, "gear_combos", []):
            name = str(cb.currentData() or "")
            if name:
                equip_cost += _cost_to_int(str(GEAR_BY_NAME.get(name, {}).get("cost", "")))

        vehicle_cost = 0
        for key in ("landcraft", "watercraft", "aircraft"):
            section = getattr(self, "vehicle_sections", {}).get(key, {})
            combos: list[QComboBox] = section.get("combos", [])
            for cb in combos:
                name = str(cb.currentData() or "")
                if name:
                    vehicle_cost += _cost_to_int(str(VEHICLES_LOOKUP.get(name, {}).get("cost", "")))

        total = credits + equip_cost + vehicle_cost
        self.ed_total_wealth.setText(f"{total}")
        
    # ---------- Vehicles UI ----------
    def _build_vehicle_section(self, parent_layout: QVBoxLayout, title: str, vehicles: list[dict[str, str]], key: str) -> None:
        box = QGroupBox(title)
        form = QFormLayout(box)

        combos: list[QComboBox] = []
        descs: list[QTextEdit] = []

        for idx in range(2):
            cb = QComboBox()
            cb.addItem("Select a vehicle", "")
            for v in vehicles:
                cb.addItem(v["name"], v["name"])

            desc = QTextEdit()
            desc.setReadOnly(True)
            desc.setMinimumHeight(70)

            cb.currentIndexChanged.connect(lambda _=False, k=key, i=idx: self.on_vehicle_changed(k, i))

            combos.append(cb)
            descs.append(desc)

            form.addRow(f"{title} {idx+1}", cb)
            form.addRow("Details", desc)

        parent_layout.addWidget(box)
        self.vehicle_sections[key] = {"combos": combos, "descs": descs}

    def on_vehicle_changed(self, section_key: str, idx: int) -> None:
        section = self.vehicle_sections.get(section_key, {})
        combos: list[QComboBox] = section.get("combos", [])
        descs: list[QTextEdit] = section.get("descs", [])
        if idx >= len(combos) or idx >= len(descs):
            return

        name = str(combos[idx].currentData() or "")
        if not name:
            descs[idx].setPlainText("")
            self.recalc_total_wealth()
            return

        v = VEHICLES_LOOKUP.get(name)
        if not v:
            descs[idx].setPlainText("")
            self.recalc_total_wealth()
            return

        text = (
            f"{v['name']}\n"
            f"Range: {v['range']}\n"
            f"Top Speed: {v['top_speed']}\n"
            f"SDC: {v['sdc']}\n"
            f"Cost: {v['cost']}\n"
        )
        descs[idx].setPlainText(text)
        self.recalc_total_wealth()


    def _parse_weight_lbs_from_text(self, text: str) -> float:
        """
        Extracts weights from text like:
        - "...; 2.0kg"
        - "10 lbs"
        Sums all found weights. Ignores dice-formulas like "300+6D10 lbs".
        """
        if not text:
            return 0.0

        total_lbs = 0.0

        # --- kg like "2.0kg" or "2 kg"
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*kg\b", text, flags=re.IGNORECASE):
            kg = float(m.group(1))
            total_lbs += kg * 2.2046226218

        # --- lbs like "10 lbs" or "10 lb"
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*lb(?:s)?\b", text, flags=re.IGNORECASE):
            lbs = float(m.group(1))
            total_lbs += lbs

        return total_lbs


    def _get_body_weight_lbs(self) -> float:
        """
        Reads body weight from self.ed_weight.
        Accepts:
        - "180" (assumed lbs)
        - "180 lbs"
        - "82 kg"
        """
        if not hasattr(self, "ed_weight"):
            return 0.0

        raw = (self.ed_weight.text() or "").strip()
        if not raw:
            return 0.0

        # pull first number
        m = re.search(r"(\d+(?:\.\d+)?)", raw)
        if not m:
            return 0.0

        val = float(m.group(1))
        if re.search(r"\bkg\b", raw, flags=re.IGNORECASE):
            return val * 2.2046226218

        # default lbs
        return val




    def _get_equipment_weight_lbs(self) -> float:
        """
        Sums weights we can detect from selected equipment:
        - weapons: WEAPONS_BY_NAME[name]['details'] contains 'kg'
        - shield: SHIELD_BY_NAME[name]['details'] contains 'lbs'
        - gear: currently most entries are not weighted (will count if details include kg/lbs)
        - armor: no weight in catalog currently (ignored unless you add it)
        """
        total = 0.0

        # weapons
        if hasattr(self, "weapon_combos"):
            for cb in self.weapon_combos:
                name = str(cb.currentData() or "")
                if not name:
                    continue
                w = WEAPONS_BY_NAME.get(name)
                if w:
                    total += self._parse_weight_lbs_from_text(str(w.get("details", "")))

        # shield
        if hasattr(self, "cb_shield"):
            sname = str(self.cb_shield.currentData() or "")
            if sname:
                s = SHIELD_BY_NAME.get(sname)
                if s:
                    total += self._parse_weight_lbs_from_text(str(s.get("details", "")))

        # gear (only counts if your details strings include kg/lbs)
        if hasattr(self, "gear_combos"):
            for cb in self.gear_combos:
                gname = str(cb.currentData() or "")
                if not gname:
                    continue
                g = GEAR_BY_NAME.get(gname)
                if g:
                    total += self._parse_weight_lbs_from_text(str(g.get("details", "")))

        # armor (ignored unless you later add weight data to ARMOR_CATALOG)
        return total

    def get_vehicle(name: str) -> dict[str, str]:
        return VEHICLES_LOOKUP.get(name, {})

    def _get_vehicles_weight_lbs(self) -> float:
        """
        Vehicles catalog currently doesn't include weight in the text you print,
        so this will be 0 unless you add:
        v['weight'] = "2500 lbs" or "1200kg"
        """
        total = 0.0
        if not hasattr(self, "vehicle_sections"):
            return 0.0

        for key in ("landcraft", "watercraft", "aircraft"):
            section = self.vehicle_sections.get(key, {})
            combos = section.get("combos", [])
            for cb in combos:
                name = str(cb.currentData() or "")
                if not name:
                    continue
                v = VEHICLES_LOOKUP.get(name)
                if not v:
                    continue

                # Option A: you add v["weight"] later
                if "weight" in v and v["weight"]:
                    total += self._parse_weight_lbs_from_text(str(v["weight"]))
                    continue

                # Option B: if you later include "Weight: ..." in the desc text and want to parse it
                # (not used right now)
        return total


    def recalc_weight_breakdown(self) -> None:
        """
        Updates the read-only 'body + gear' weight field.
        """
        if not hasattr(self, "ed_weight_with_gear"):
            return

        body = self._get_body_weight_lbs()
        gear = self._get_equipment_weight_lbs()

        self.ed_weight_with_gear.setText(f"{body + gear:,.1f} lbs")

   

    # ---------------- Character IO ----------------
    def editor_to_character(self) -> Character:
        c = self.current_character

        if not isinstance(getattr(c, "bio_e", None), dict):
            c.bio_e = {}
        if not isinstance(getattr(c, "attributes", None), dict):
            c.attributes = {}
        if not isinstance(getattr(c, "skills", None), dict):
            c.skills = {"pro": [], "amateur": []}
        if not isinstance(getattr(c, "combat", None), dict):
            c.combat = {}

        def combo_value(cb: QComboBox) -> str:
            data = cb.currentData()
            if data not in (None, ""):
                return str(data).strip()
            return str(cb.currentText() or "").strip()

        def collect_catalog_entries(combo_attr_name: str) -> list[dict[str, Any]]:
            entries: list[dict[str, Any]] = []
            for cb in getattr(self, combo_attr_name, []):
                label = str(cb.currentText() or "").strip()
                cost = int(cb.currentData() or 0) if cb.isEnabled() else 0
                if label and "None" not in label and cost > 0:
                    entries.append({"name": label.split(" (", 1)[0], "cost": cost})
            return entries

        image_path = ""
        if hasattr(self, "current_image_path") and self.current_image_path:
            image_path = str(self.current_image_path).strip()
        elif getattr(c, "image_path", None):
            image_path = str(c.image_path).strip()
        elif getattr(c, "bio_e", {}).get("image_path"):
            image_path = str(c.bio_e.get("image_path", "")).strip()

        self.current_image_path = image_path

        try:
            c.image_path = image_path
        except Exception:
            pass

        c.bio_e["image_path"] = image_path

        c.name = self.ed_name.text().strip()

        animal_source = combo_value(self.cb_animal_source)
        animal_type = combo_value(self.cb_animal_type)
        animal = combo_value(self.cb_animal)

        c.animal = animal
        c.bio_e["animal_source"] = animal_source
        c.bio_e["animal_type"] = animal_type
        c.bio_e["animal"] = animal

        c.bio_e["mutant_origin"] = {
            "name": combo_value(self.cb_mutant_origin),
            "details": self.ed_mutant_origin_details.toPlainText().strip(),
        }

        c.bio_e["background_education"] = {
            "name": combo_value(self.cb_background_education),
            "details": self.ed_background_education_details.toPlainText().strip(),
        }

        c.bio_e["creator_organization"] = {
            "name": combo_value(self.cb_creator_organization),
            "details": self.ed_creator_organization_details.toPlainText().strip(),
        }

        c.alignment = combo_value(self.cb_alignment)

        c.age = self.ed_age.text().strip()
        c.gender = self.ed_gender.text().strip()

        c.weight = self.ed_weight.text().strip()
        c.height = self.ed_height.text().strip()
        c.size = f"{self.cb_size_level.currentData()} ({self.cb_size_build.currentText()})"

        try:
            setattr(c, "total_credits", int(self.sp_total_credits.value()))
            setattr(c, "total_wealth", int(self.ed_total_wealth.text() or "0"))
        except Exception:
            pass

        c.xp = int(self.sp_xp.value())
        c.level = int(self.sp_level.value())
        c.hit_points = int(self.sp_hp.value())
        c.sdc = int(self.sp_sdc.value())

        try:
            setattr(c, "weapons_selected", [combo_value(cb) for cb in self.weapon_combos])
            setattr(c, "armor_type", combo_value(self.cb_armor))
            setattr(c, "shield_type", combo_value(self.cb_shield))
            setattr(c, "shield_notes", self.ed_shield_notes.text().strip())
            setattr(c, "gear_selected", [combo_value(cb) for cb in self.gear_combos])
        except Exception:
            pass

        c.armor_name = self.ed_armor_name.text().strip()
        c.armor_ar = int(self.sp_armor_ar.value())
        c.armor_sdc = int(self.sp_armor_sdc.value())

        c.notes = self.ed_notes.toPlainText()

        for key, sp in self.attribute_fields.items():
            c.attributes[key] = int(sp.value())

        c.skills["pro"] = [self._selected_skill_name(cb) for cb in self.pro_skill_boxes]
        c.skills["amateur"] = [self._selected_skill_name(cb) for cb in self.amateur_skill_boxes]

        c.combat["training"] = combo_value(self.cb_combat_training) or "None"
        c.combat["override"] = bool(self.chk_combat_override.isChecked())
        c.combat["auto_details"] = bool(self.chk_combat_auto_details.isChecked())
        c.combat["training_details_text"] = self.ed_combat_training_details.toPlainText()
        c.combat["strike"] = int(self.sp_strike.value())
        c.combat["parry"] = int(self.sp_parry.value())
        c.combat["dodge"] = int(self.sp_dodge.value())
        c.combat["save_vs_psionic_strangeness"] = int(self.sp_save_vs_psionic_strangeness.value() or 0)
        c.combat["initiative"] = int(self.sp_initiative.value())
        c.combat["actions_per_round"] = int(self.sp_actions.value())
        c.combat["roll_with_impact"] = int(self.sp_roll_with_impact.value() or 0)
        c.combat["critical_range"] = str(self.ed_critical_range.text() or "").strip()

        vehicles: dict[str, list[str]] = {"landcraft": [], "watercraft": [], "aircraft": []}
        for key in ("landcraft", "watercraft", "aircraft"):
            section = self.vehicle_sections.get(key, {})
            combos: list[QComboBox] = section.get("combos", [])
            picked: list[str] = []
            for cb in combos:
                name = combo_value(cb)
                if name:
                    picked.append(name)
            vehicles[key] = picked
        try:
            setattr(c, "vehicles", vehicles)
        except Exception:
            pass


        ta_support_devices: list[dict[str, Any]] = []
        combos = list(getattr(self, "ta_support_device_combos", []) or [])
        checks = list(getattr(self, "ta_support_portable_checks", []) or [])

        for i, cb in enumerate(combos):
            support_name = str(cb.currentData() or "").strip()
            if not support_name:
                continue

            portable_on = i < len(checks) and bool(checks[i].isChecked())
            ta_support_devices.append(
                {
                    "name": support_name,
                    "portable": portable_on,
                }
            )

        
        c.ta_time_devices = {
            "device_category": str(getattr(self, "cb_ta_device_category").currentData() or "").strip() if hasattr(self, "cb_ta_device_category") else "",
            "device_name": str(getattr(self, "cb_ta_device_name").currentData() or "").strip() if hasattr(self, "cb_ta_device_name") else "",
            "mount_type": str(getattr(self, "cb_ta_mount_type").currentData() or "").strip() if hasattr(self, "cb_ta_mount_type") else "",
            "vehicle_type": str(getattr(self, "cb_ta_vehicle_type").currentData() or "").strip() if hasattr(self, "cb_ta_vehicle_type") else "",
            "base_cost": int(getattr(self, "sp_ta_base_cost").value() or 0) if hasattr(self, "sp_ta_base_cost") else 0,
            "install_cost": int(getattr(self, "sp_ta_install_cost").value() or 0) if hasattr(self, "sp_ta_install_cost") else 0,
            "support_cost": int(getattr(self, "sp_ta_support_cost").value() or 0) if hasattr(self, "sp_ta_support_cost") else 0,
            "total_cost": int(getattr(self, "sp_ta_total_cost").value() or 0) if hasattr(self, "sp_ta_total_cost") else 0,
            "selected_support_devices": ta_support_devices,
            "notes": str(getattr(self, "ed_ta_summary_notes").toPlainText() or "").strip() if hasattr(self, "ed_ta_summary_notes") else "",
            "image_path": str(getattr(self, "ta_image_path", "") or "").strip(),
            "device_record": self._ta_get_selected_device_record(),
        }

        c.bio_e["total"] = int(self.sp_bio_total.value())
        c.bio_e["spent"] = int(self.sp_bio_spent.value())

        c.bio_e["original"] = {
            "size_level": self.ed_bio_orig_size_level.text().strip(),
            "length": self.ed_bio_orig_length.text().strip(),
            "weight": self.ed_bio_orig_weight.text().strip(),
            "build": self.ed_bio_orig_build.text().strip(),
        }

        c.bio_e["mutant_size_level"] = int(self.cb_bio_mutant_size_level.currentData() or 0)
        c.bio_e["mutant_size_label"] = self.cb_bio_mutant_size_level.currentText().strip()

        c.bio_e["human_features"] = {
            "hands_cost": int(self.cb_human_hands.currentData() or 0),
            "biped_cost": int(self.cb_human_biped.currentData() or 0),
            "speech_cost": int(self.cb_human_speech.currentData() or 0),
            "looks_cost": int(self.cb_human_looks.currentData() or 0),
            "hands_label": self.cb_human_hands.currentText().strip(),
            "biped_label": self.cb_human_biped.currentText().strip(),
            "speech_label": self.cb_human_speech.currentText().strip(),
            "looks_label": self.cb_human_looks.currentText().strip(),
        }

        nw: list[dict[str, Any]] = []
        for cb in getattr(self, "bio_weapon_combos", []):
            data = cb.currentData()
            if not isinstance(data, dict):
                continue

            name = str(data.get("name", "") or "").strip()
            cost = int(data.get("cost", 0) or 0)

            if not name or self._bioe_normalize_option_name(name) == "none":
                continue

            nw.append({"name": name, "cost": cost})

        c.bio_e["natural_weapons"] = nw

        ab: list[dict[str, Any]] = []
        for cb in getattr(self, "bio_ability_combos", []):
            data = cb.currentData()
            if not isinstance(data, dict):
                continue

            name = str(data.get("name", "") or "").strip()
            cost = int(data.get("cost", 0) or 0)

            if not name or self._bioe_normalize_option_name(name) == "none":
                continue

            ab.append({"name": name, "cost": cost})

        c.bio_e["abilities"] = ab

        mutant_animal_psionics = collect_catalog_entries("bio_mutant_animal_psionic_combos")
        mutant_hominid_psionics = collect_catalog_entries("bio_mutant_hominid_psionic_combos")
        mutant_prosthetic_psionics = collect_catalog_entries("bio_mutant_prosthetic_psionic_combos")
        mutant_human_abilities = collect_catalog_entries("bio_mutant_human_ability_combos")
        mutant_hominid_abilities = collect_catalog_entries("bio_mutant_hominid_ability_combos")

        c.bio_e["mutant_animal_psionic_powers"] = mutant_animal_psionics
        c.bio_e["mutant_hominid_psionic_powers"] = mutant_hominid_psionics
        c.bio_e["mutant_prosthetic_psionic_powers"] = mutant_prosthetic_psionics
        c.bio_e["mutant_human_abilities"] = mutant_human_abilities
        c.bio_e["mutant_hominid_abilities"] = mutant_hominid_abilities

        # Backward compatibility with old single psionics bucket
        c.bio_e["psionics"] = list(mutant_animal_psionics)

        traits = [line.strip() for line in self.ed_traits.toPlainText().splitlines() if line.strip()]
        c.bio_e["traits"] = traits

        if image_path:
            pix = QPixmap(image_path)
            if not pix.isNull():
                self.lbl_character_art.setPixmap(
                    pix.scaled(240, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )

        return c
    
        


    def load_into_editor(self, c: Character, path: Optional[Path]) -> None:
        self.current_character = c
        self.current_path = path

        image_path = getattr(c, "image_path", None) or getattr(c, "bio_e", {}).get("image_path") or ""
        self.current_image_path = str(image_path).strip()

        self.ed_name.setText(c.name)

        animal_source = (
            getattr(c, "animal_source", None)
            or getattr(c, "bio_e", {}).get("animal_source", None)
        )

        animal_type = (
            getattr(c, "animal_type", None)
            or getattr(c, "bio_e", {}).get("animal_type", None)
        )

        animal = (
            getattr(c, "animal", "")
            or getattr(c, "bio_e", {}).get("animal", "")
            or ""
        )

        if isinstance(animal_source, str) and animal_source:
            idx = self.cb_animal_source.findData(animal_source)
            self.cb_animal_source.setCurrentIndex(idx if idx != -1 else 0)
        else:
            self.cb_animal_source.setCurrentIndex(0)

        self.on_animal_source_changed()

        if isinstance(animal_type, str) and animal_type:
            idx = self.cb_animal_type.findData(animal_type)
            self.cb_animal_type.setCurrentIndex(idx if idx != -1 else 0)
        else:
            self.cb_animal_type.setCurrentIndex(0)

        self.on_animal_type_changed()

        if isinstance(animal, str) and animal:
            idx = self.cb_animal.findData(animal)
            self.cb_animal.setCurrentIndex(idx if idx != -1 else 0)
        else:
            self.cb_animal.setCurrentIndex(0)

        if isinstance(getattr(c, "alignment", ""), str) and c.alignment:
            idx = self.cb_alignment.findData(c.alignment)
            self.cb_alignment.setCurrentIndex(idx if idx != -1 else 0)
        else:
            self.cb_alignment.setCurrentIndex(0)

        origin_data = getattr(c, "bio_e", {}).get("mutant_origin", {}) or {}
        origin_name = str(origin_data.get("name", "") or "")
        origin_details = str(origin_data.get("details", "") or "")
        idx = self.cb_mutant_origin.findData(origin_name)
        if idx == -1 and origin_name:
            idx = self.cb_mutant_origin.findText(origin_name)
        self.cb_mutant_origin.setCurrentIndex(idx if idx != -1 else 0)
        self.ed_mutant_origin_details.setPlainText(origin_details)

        education_data = getattr(c, "bio_e", {}).get("background_education", {}) or {}
        education_name = str(education_data.get("name", "") or "")
        education_details = str(education_data.get("details", "") or "")
        idx = self.cb_background_education.findData(education_name)
        if idx == -1 and education_name:
            idx = self.cb_background_education.findText(education_name)
        self.cb_background_education.setCurrentIndex(idx if idx != -1 else 0)
        self.ed_background_education_details.setPlainText(education_details)

        creator_data = getattr(c, "bio_e", {}).get("creator_organization", {}) or {}
        creator_name = str(creator_data.get("name", "") or "")
        creator_details = str(creator_data.get("details", "") or "")
        idx = self.cb_creator_organization.findData(creator_name)
        if idx == -1 and creator_name:
            idx = self.cb_creator_organization.findText(creator_name)
        self.cb_creator_organization.setCurrentIndex(idx if idx != -1 else 0)
        self.ed_creator_organization_details.setPlainText(creator_details)

        self.update_creator_organization_enabled()

        self.ed_age.setText(getattr(c, "age", "") or "")
        self.ed_gender.setText(getattr(c, "gender", "") or "")

        self.ed_weight.setText(getattr(c, "weight", "") or "")
        self.ed_height.setText(getattr(c, "height", "") or "")

        size_value = str(getattr(c, "size", "") or "").strip()
        size_level = 1
        size_build = "medium"

        if size_value:
            match = re.match(r"^\s*(\d+)\s*\((.*?)\)\s*$", size_value)
            if match:
                size_level = int(match.group(1))
                parsed_build = match.group(2).strip().lower()
                if parsed_build in {"short", "medium", "long"}:
                    size_build = parsed_build

        idx = self.cb_size_level.findData(size_level)
        self.cb_size_level.setCurrentIndex(idx if idx != -1 else 0)

        idx = self.cb_size_build.findData(size_build)
        self.cb_size_build.setCurrentIndex(idx if idx != -1 else 1)

        self.sp_total_credits.setValue(int(getattr(c, "total_credits", 0) or 0))
        self.ed_total_wealth.setText(str(getattr(c, "total_wealth", 0) or 0))

        self.sp_xp.setValue(int(getattr(c, "xp", 0) or 0))
        self.sp_level.setValue(int(getattr(c, "level", 1) or 1))
        self.sp_hp.setValue(int(getattr(c, "hit_points", 0) or 0))
        self.sp_sdc.setValue(int(getattr(c, "sdc", 0) or 0))

        weapons_selected = getattr(c, "weapons_selected", []) or []
        for i, cb in enumerate(self.weapon_combos):
            desired = str(weapons_selected[i]).strip() if i < len(weapons_selected) else ""
            idx = cb.findData(desired)
            if idx == -1 and desired:
                idx = cb.findText(desired)
            cb.setCurrentIndex(idx if idx != -1 else 0)
            self.on_weapon_changed(i)

        armor_type = str(getattr(c, "armor_type", "") or "").strip()
        idx = self.cb_armor.findData(armor_type)
        if idx == -1 and armor_type:
            idx = self.cb_armor.findText(armor_type)
        self.cb_armor.setCurrentIndex(idx if idx != -1 else 0)

        self.ed_armor_name.setText(getattr(c, "armor_name", "") or "")
        if armor_type and armor_type in ARMOR_BY_NAME:
            self.on_armor_changed()
        else:
            self.sp_armor_ar.setValue(int(getattr(c, "armor_ar", 0) or 0))
            self.sp_armor_sdc.setValue(int(getattr(c, "armor_sdc", 0) or 0))

        shield_type = str(getattr(c, "shield_type", "") or "").strip()
        idx = self.cb_shield.findData(shield_type)
        if idx == -1 and shield_type:
            idx = self.cb_shield.findText(shield_type)
        self.cb_shield.setCurrentIndex(idx if idx != -1 else 0)
        self.ed_shield_notes.setText(str(getattr(c, "shield_notes", "") or ""))
        self.on_shield_changed()

        gear_selected = getattr(c, "gear_selected", []) or []
        for i, cb in enumerate(self.gear_combos):
            desired = str(gear_selected[i]).strip() if i < len(gear_selected) else ""
            idx = cb.findData(desired)
            if idx == -1 and desired:
                idx = cb.findText(desired)
            cb.setCurrentIndex(idx if idx != -1 else 0)
            self.on_gear_changed(i)

        self.ed_notes.setPlainText(getattr(c, "notes", "") or "")

        for key, sp in self.attribute_fields.items():
            sp.setValue(int(getattr(c, "attributes", {}).get(key, 0)))

        pro_list = getattr(c, "skills", {}).get("pro", [""] * 10)
        ama_list = getattr(c, "skills", {}).get("amateur", [""] * 15)
        pro_list = (pro_list + [""] * 10)[:10]
        ama_list = (ama_list + [""] * 15)[:15]

        for i, cb in enumerate(self.pro_skill_boxes):
            desired = pro_list[i] or ""
            idx = cb.findData(desired, role=Qt.UserRole)
            if idx == -1 and desired:
                idx = cb.findText(desired)
            cb.setCurrentIndex(idx if idx != -1 else 0)

        for i, cb in enumerate(self.amateur_skill_boxes):
            desired = ama_list[i] or ""
            idx = cb.findData(desired, role=Qt.UserRole)
            if idx == -1 and desired:
                idx = cb.findText(desired)
            cb.setCurrentIndex(idx if idx != -1 else 0)

        training_name = str(getattr(c, "combat", {}).get("training", "None") or "None")
        idx = self.cb_combat_training.findData(training_name)
        if idx == -1 and training_name:
            idx = self.cb_combat_training.findText(training_name)
        self.cb_combat_training.setCurrentIndex(idx if idx != -1 else 0)

        auto_details = bool(getattr(c, "combat", {}).get("auto_details", True))
        self.chk_combat_auto_details.setChecked(auto_details)

        override = bool(getattr(c, "combat", {}).get("override", False))
        self.chk_combat_override.setChecked(override)
        self._set_combat_spinboxes_editable(override)

        if override:
            self.sp_strike.setValue(int(getattr(c, "combat", {}).get("strike", 0)))
            self.sp_parry.setValue(int(getattr(c, "combat", {}).get("parry", 0)))
            self.sp_dodge.setValue(int(getattr(c, "combat", {}).get("dodge", 0)))
            self.sp_save_vs_psionic_strangeness.setValue(
                int(getattr(c, "combat", {}).get("save_vs_psionic_strangeness", 0) or 0)
            )
            self.sp_initiative.setValue(int(getattr(c, "combat", {}).get("initiative", 0)))
            self.sp_actions.setValue(int(getattr(c, "combat", {}).get("actions_per_round", 2)))
            self.sp_roll_with_impact.setValue(
                int(getattr(c, "combat", {}).get("roll_with_impact", 0) or 0)
            )
            self.ed_critical_range.setText(
                str(getattr(c, "combat", {}).get("critical_range", "") or "")
            )

        if not auto_details:
            self.ed_combat_training_details.setPlainText(
                str(getattr(c, "combat", {}).get("training_details_text", ""))
            )

        vehicles = getattr(c, "vehicles", {}) or {}
        for section_key in ("landcraft", "watercraft", "aircraft"):
            picked = vehicles.get(section_key, []) if isinstance(vehicles, dict) else []
            section = self.vehicle_sections.get(section_key, {})
            combos: list[QComboBox] = section.get("combos", [])
            for i, cb in enumerate(combos):
                desired = str(picked[i]).strip() if i < len(picked) else ""
                idx = cb.findData(desired)
                if idx == -1 and desired:
                    idx = cb.findText(desired)
                cb.setCurrentIndex(idx if idx != -1 else 0)
                self.on_vehicle_changed(section_key, i)

        self.sp_bio_total.setValue(int(getattr(c, "bio_e", {}).get("total", 0)))
        self.sp_bio_spent.setValue(int(getattr(c, "bio_e", {}).get("spent", 0)))

        original = getattr(c, "bio_e", {}).get("original", {}) or {}
        if isinstance(original, dict):
            self.ed_bio_orig_size_level.setText(str(original.get("size_level", "") or ""))
            self.ed_bio_orig_length.setText(str(original.get("length", "") or ""))
            self.ed_bio_orig_weight.setText(str(original.get("weight", "") or ""))
            self.ed_bio_orig_build.setText(str(original.get("build", "") or ""))

        if self.current_image_path:
            pix = QPixmap(self.current_image_path)
            if not pix.isNull():
                self.lbl_character_art.setPixmap(
                    pix.scaled(240, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                self.lbl_character_art.clear()
                self.lbl_character_art.setText("No Image")
        else:
            self.lbl_character_art.clear()
            self.lbl_character_art.setText("No Image")

        self.on_bioe_animal_selected()

        saved_natural_weapons = list(getattr(c, "bio_e", {}).get("natural_weapons", []) or [])
        saved_abilities = list(getattr(c, "bio_e", {}).get("abilities", []) or [])

        for i, cb in enumerate(getattr(self, "bio_weapon_combos", [])):
            desired_name = ""
            if i < len(saved_natural_weapons) and isinstance(saved_natural_weapons[i], dict):
                desired_name = str(saved_natural_weapons[i].get("name", "") or "").strip()

            desired_key = self._bioe_normalize_option_name(desired_name)
            found_index = -1

            if desired_key:
                for idx in range(cb.count()):
                    data = cb.itemData(idx)
                    item_name = (
                        str(data.get("name", "") or "").strip()
                        if isinstance(data, dict)
                        else str(cb.itemText(idx) or "").strip()
                    )
                    if self._bioe_normalize_option_name(item_name) == desired_key:
                        found_index = idx
                        break

            cb.setCurrentIndex(found_index if found_index >= 0 else 0)

        for i, cb in enumerate(getattr(self, "bio_ability_combos", [])):
            desired_name = ""
            if i < len(saved_abilities) and isinstance(saved_abilities[i], dict):
                desired_name = str(saved_abilities[i].get("name", "") or "").strip()

            desired_key = self._bioe_normalize_option_name(desired_name)
            found_index = -1

            if desired_key:
                for idx in range(cb.count()):
                    data = cb.itemData(idx)
                    item_name = (
                        str(data.get("name", "") or "").strip()
                        if isinstance(data, dict)
                        else str(cb.itemText(idx) or "").strip()
                    )
                    if self._bioe_normalize_option_name(item_name) == desired_key:
                        found_index = idx
                        break

            cb.setCurrentIndex(found_index if found_index >= 0 else 0)

        self.recalc_bioe_spent()

        mutant_size = int(getattr(c, "bio_e", {}).get("mutant_size_level", 0) or 0)
        mutant_size_label = str(getattr(c, "bio_e", {}).get("mutant_size_label", "") or "")

        idx = self.cb_bio_mutant_size_level.findData(mutant_size)
        if idx == -1 and mutant_size_label:
            idx = self.cb_bio_mutant_size_level.findText(mutant_size_label)
        self.cb_bio_mutant_size_level.setCurrentIndex(idx if idx != -1 else 0)

        hf = getattr(c, "bio_e", {}).get("human_features", {}) or {}
        if isinstance(hf, dict):
            for cb, cost_key, label_key in (
                (self.cb_human_hands, "hands_cost", "hands_label"),
                (self.cb_human_biped, "biped_cost", "biped_label"),
                (self.cb_human_speech, "speech_cost", "speech_label"),
                (self.cb_human_looks, "looks_cost", "looks_label"),
            ):
                cost = int(hf.get(cost_key, 0) or 0)
                label = str(hf.get(label_key, "") or "")

                idx = cb.findData(cost)
                if idx == -1 and label:
                    idx = cb.findText(label)
                cb.setCurrentIndex(idx if idx != -1 else 0)

        

        saved_animal_ps = getattr(c, "bio_e", {}).get("mutant_animal_psionic_powers", []) or getattr(c, "bio_e", {}).get("psionics", []) or []
        if isinstance(saved_animal_ps, list):
            for i, cb in enumerate(getattr(self, "bio_mutant_animal_psionic_combos", [])):
                desired = saved_animal_ps[i].get("name") if i < len(saved_animal_ps) and isinstance(saved_animal_ps[i], dict) else ""
                if desired and cb.isEnabled():
                    found = 0
                    for j in range(cb.count()):
                        if cb.itemText(j).startswith(desired):
                            found = j
                            break
                    cb.setCurrentIndex(found)
                else:
                    cb.setCurrentIndex(0)

        saved_hominid_ps = getattr(c, "bio_e", {}).get("mutant_hominid_psionic_powers", []) or []
        if isinstance(saved_hominid_ps, list):
            for i, cb in enumerate(getattr(self, "bio_mutant_hominid_psionic_combos", [])):
                desired = saved_hominid_ps[i].get("name") if i < len(saved_hominid_ps) and isinstance(saved_hominid_ps[i], dict) else ""
                if desired and cb.isEnabled():
                    found = 0
                    for j in range(cb.count()):
                        if cb.itemText(j).startswith(desired):
                            found = j
                            break
                    cb.setCurrentIndex(found)
                else:
                    cb.setCurrentIndex(0)

        saved_prosthetic_ps = getattr(c, "bio_e", {}).get("mutant_prosthetic_psionic_powers", []) or []
        if isinstance(saved_prosthetic_ps, list):
            for i, cb in enumerate(getattr(self, "bio_mutant_prosthetic_psionic_combos", [])):
                desired = saved_prosthetic_ps[i].get("name") if i < len(saved_prosthetic_ps) and isinstance(saved_prosthetic_ps[i], dict) else ""
                if desired and cb.isEnabled():
                    found = 0
                    for j in range(cb.count()):
                        if cb.itemText(j).startswith(desired):
                            found = j
                            break
                    cb.setCurrentIndex(found)
                else:
                    cb.setCurrentIndex(0)

        saved_human_ab = getattr(c, "bio_e", {}).get("mutant_human_abilities", []) or []
        if isinstance(saved_human_ab, list):
            for i, cb in enumerate(getattr(self, "bio_mutant_human_ability_combos", [])):
                desired = saved_human_ab[i].get("name") if i < len(saved_human_ab) and isinstance(saved_human_ab[i], dict) else ""
                if desired and cb.isEnabled():
                    found = 0
                    for j in range(cb.count()):
                        if cb.itemText(j).startswith(desired):
                            found = j
                            break
                    cb.setCurrentIndex(found)
                else:
                    cb.setCurrentIndex(0)

        saved_hominid_ab = getattr(c, "bio_e", {}).get("mutant_hominid_abilities", []) or []
        if isinstance(saved_hominid_ab, list):
            for i, cb in enumerate(getattr(self, "bio_mutant_hominid_ability_combos", [])):
                desired = saved_hominid_ab[i].get("name") if i < len(saved_hominid_ab) and isinstance(saved_hominid_ab[i], dict) else ""
                if desired and cb.isEnabled():
                    found = 0
                    for j in range(cb.count()):
                        if cb.itemText(j).startswith(desired):
                            found = j
                            break
                    cb.setCurrentIndex(found)
                else:
                    cb.setCurrentIndex(0)

        self.recalc_bioe_spent()
        traits = getattr(c, "bio_e", {}).get("traits", []) or []
        self.ed_traits.setPlainText("\n".join(str(t) for t in traits))

        self.recalc_skill_displays()
        self.recalc_combat_from_training()
        self.recalc_total_wealth()
        self.recalc_weight_breakdown()
        self.sync_defense_summary_fields()

        if path:
            self.statusBar().showMessage(f"Loaded: {path.name}")
        else:
            self.statusBar().showMessage("New (unsaved) character")

        self.on_skills_changed()

        ta_data = getattr(c, "ta_time_devices", {}) or {}
        if not isinstance(ta_data, dict):
            ta_data = {}

        if hasattr(self, "cb_ta_device_category"):
            idx = self.cb_ta_device_category.findData(str(ta_data.get("device_category", "") or "").strip())
            self.cb_ta_device_category.setCurrentIndex(idx if idx != -1 else 0)
            self.on_ta_device_category_changed()

        if hasattr(self, "cb_ta_device_name"):
            idx = self.cb_ta_device_name.findData(str(ta_data.get("device_name", "") or "").strip())
            self.cb_ta_device_name.setCurrentIndex(idx if idx != -1 else 0)

        if hasattr(self, "cb_ta_mount_type"):
            idx = self.cb_ta_mount_type.findData(str(ta_data.get("mount_type", "") or "").strip())
            self.cb_ta_mount_type.setCurrentIndex(idx if idx != -1 else 0)

        self._ta_update_vehicle_type_enabled()

        if hasattr(self, "cb_ta_vehicle_type"):
            idx = self.cb_ta_vehicle_type.findData(str(ta_data.get("vehicle_type", "") or "").strip())
            self.cb_ta_vehicle_type.setCurrentIndex(idx if idx != -1 else 0)

        saved_supports = list(ta_data.get("selected_support_devices", []) or [])

        combos = list(getattr(self, "ta_support_device_combos", []) or [])
        checks = list(getattr(self, "ta_support_portable_checks", []) or [])

        for i, cb in enumerate(combos):
            support_name = ""
            portable_on = False

            if i < len(saved_supports) and isinstance(saved_supports[i], dict):
                support_name = str(saved_supports[i].get("name", "") or "").strip()
                portable_on = bool(saved_supports[i].get("portable", False))

            idx = cb.findData(support_name)
            cb.setCurrentIndex(idx if idx != -1 else 0)

            if i < len(checks):
                checks[i].setChecked(portable_on)

        if hasattr(self, "ed_ta_summary_notes"):
            self.ed_ta_summary_notes.setPlainText(str(ta_data.get("notes", "") or "").strip())

        self.ta_image_path = str(ta_data.get("image_path", "") or "").strip()
        self._ta_set_image_preview(self.ta_image_path)

        self.recalc_ta_time_devices()

        # Only set default notes for NEW characters
        if not getattr(c, "notes", "").strip():
            if hasattr(self, "ed_notes"):
                self.ed_notes.setPlainText(
                    "Cowabunga dudes!\n\n"
                    "TurtleCom is a fan-built character management and content tool for Teenage Mutant Ninja Turtles & Other Strangeness (TMNTOS), designed to streamline character creation, organization, and gameplay for players and GMs.\n\n"
                    "Created by Belor McKraken, a tabletop gaming enthusiast and developer focused on accessible tools for the TTRPG community.\n\n"
                    "Contact:\n"
                    "Email: your-email@example.com\n"
                    "Discord: Belor McKraken\n\n"
                    "Disclaimer:\n"
                    "This is an unofficial fan project and is not affiliated with or endorsed by Palladium Books.\n"
                    "All related names, logos, and trademarks are the property of their respective owners.\n"
                    "For personal, non-commercial use only.\n\n"
                    "(TA) = Transdimensional Adventures REDUX\n"
                    "(RH) = Road Hogs\n"
                    "(MDU) = Mutants Down Under"
                )