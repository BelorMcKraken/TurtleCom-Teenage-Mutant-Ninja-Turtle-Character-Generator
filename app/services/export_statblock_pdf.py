from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, StyleSheet1, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.character import Character


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _clean_list(values: Iterable[Any]) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        text = _clean_text(value)
        if not text:
            continue
        if text.lower().startswith("select "):
            continue
        cleaned.append(text)
    return cleaned


def _clean_named_entries(values: Iterable[Any]) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        if isinstance(value, dict):
            text = _clean_text(value.get("name", ""))
        else:
            text = _clean_text(value)
        if not text:
            continue
        cleaned.append(text)
    return cleaned


def _styles() -> StyleSheet1:
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="TC_Title",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            spaceAfter=8,
            alignment=TA_CENTER,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TC_Subtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=12,
            textColor=colors.HexColor("#444444"),
            alignment=TA_CENTER,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TC_Section",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13,
            textColor=colors.white,
            spaceAfter=0,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TC_Label",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=12,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TC_Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=12,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TC_List",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.25,
            leading=11.5,
            leftIndent=8,
            bulletIndent=0,
            spaceAfter=1,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TC_Small",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#555555"),
        )
    )
    return styles


def _label_value(label: str, value: Any, styles: StyleSheet1) -> Paragraph:
    return Paragraph(
        f"<b>{label}:</b> {_clean_text(value)}",
        styles["TC_Label"],
    )


def _paragraph(text: str, styles: StyleSheet1) -> Paragraph:
    return Paragraph(text, styles["TC_Body"])


def _bullet_items(title: str, items: list[str], styles: StyleSheet1) -> list:
    if not items:
        return []

    story: list = [
        Paragraph(f"<b>{title}</b>", styles["TC_Body"]),
        Spacer(1, 2),
    ]
    for item in items:
        story.append(Paragraph(f"• {item}", styles["TC_List"]))
    story.append(Spacer(1, 6))
    return story


def _section(title: str, body_flowables: list, styles: StyleSheet1) -> KeepTogether:
    header = Table(
        [[Paragraph(title, styles["TC_Section"])]],
        colWidths=[7.1 * inch],
    )
    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#2F4F4F")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    body = Table(
        [[body_flowables]],
        colWidths=[7.1 * inch],
    )
    body.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#C8C8C8")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    return KeepTogether([header, body, Spacer(1, 8)])


def _attribute_table(c: Character, styles: StyleSheet1) -> Table:
    attrs = getattr(c, "attributes", {}) or {}
    data = [
        [
            Paragraph("<b>IQ</b>", styles["TC_Body"]),
            Paragraph(str(attrs.get("IQ", 0)), styles["TC_Body"]),
            Paragraph("<b>ME</b>", styles["TC_Body"]),
            Paragraph(str(attrs.get("ME", 0)), styles["TC_Body"]),
            Paragraph("<b>MA</b>", styles["TC_Body"]),
            Paragraph(str(attrs.get("MA", 0)), styles["TC_Body"]),
            Paragraph("<b>PS</b>", styles["TC_Body"]),
            Paragraph(str(attrs.get("PS", 0)), styles["TC_Body"]),
        ],
        [
            Paragraph("<b>PP</b>", styles["TC_Body"]),
            Paragraph(str(attrs.get("PP", 0)), styles["TC_Body"]),
            Paragraph("<b>PE</b>", styles["TC_Body"]),
            Paragraph(str(attrs.get("PE", 0)), styles["TC_Body"]),
            Paragraph("<b>PB</b>", styles["TC_Body"]),
            Paragraph(str(attrs.get("PB", 0)), styles["TC_Body"]),
            Paragraph("<b>Speed</b>", styles["TC_Body"]),
            Paragraph(str(attrs.get("Speed", 0)), styles["TC_Body"]),
        ],
    ]

    table = Table(
        data,
        colWidths=[0.55 * inch, 0.35 * inch] * 4,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.35, colors.HexColor("#D0D0D0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E0E0E0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _summary_table(rows: list[tuple[str, Any]], styles: StyleSheet1) -> Table:
    data = []
    for label, value in rows:
        value_text = _clean_text(value)
        if not value_text:
            continue
        data.append(
            [
                Paragraph(f"<b>{label}</b>", styles["TC_Body"]),
                Paragraph(value_text, styles["TC_Body"]),
            ]
        )

    if not data:
        data = [[Paragraph("<i>No data</i>", styles["TC_Body"]), Paragraph("", styles["TC_Body"])]]

    table = Table(data, colWidths=[1.6 * inch, 5.3 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.35, colors.HexColor("#D0D0D0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E0E0E0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _image_flowable(image_path: str) -> list:
    if not image_path:
        return []

    path = Path(image_path)
    if not path.exists():
        return []

    try:
        img = Image(str(path))
        img._restrictSize(1.6 * inch, 1.6 * inch)
        return [img]
    except Exception:
        return []


def export_statblock_pdf(character: Character, output_path: str | Path) -> None:
    c = character
    bio = getattr(c, "bio_e", {}) or {}
    styles = _styles()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.4 * inch,
        leftMargin=0.4 * inch,
        topMargin=0.45 * inch,
        bottomMargin=0.45 * inch,
    )

    story: list = []

    title = f"{_clean_text(c.name) or 'Unnamed Character'} — Level {getattr(c, 'level', 1)} {_clean_text(c.animal) or 'Mutant'}"
    subtitle_parts = [
        _clean_text(getattr(c, "alignment", "")),
        _clean_text(getattr(c, "gender", "")),
        f"Age {_clean_text(getattr(c, 'age', ''))}" if _clean_text(getattr(c, "age", "")) else "",
    ]
    subtitle = " | ".join(part for part in subtitle_parts if part)

    story.append(Paragraph(title, styles["TC_Title"]))
    if subtitle:
        story.append(Paragraph(subtitle, styles["TC_Subtitle"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#A0A0A0")))
    story.append(Spacer(1, 8))

    image_block = _image_flowable(_clean_text(getattr(c, "image_path", "")))

    basics_rows = [
        ("Animal", getattr(c, "animal", "")),
        ("Height", getattr(c, "height", "")),
        ("Weight", getattr(c, "weight", "")),
        ("Size", getattr(c, "size", "")),
        ("XP", getattr(c, "xp", "")),
        ("Credits", getattr(c, "total_credits", "")),
        ("Wealth", f"${getattr(c, 'total_wealth', 0):,}" if getattr(c, "total_wealth", 0) else ""),
    ]

    basic_table = _summary_table(basics_rows, styles)

    if image_block:
        top_table = Table(
            [[image_block[0], basic_table]],
            colWidths=[1.8 * inch, 5.1 * inch],
        )
        top_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story.append(top_table)
        story.append(Spacer(1, 10))
    else:
        story.append(basic_table)
        story.append(Spacer(1, 10))

    story.append(_section("Attributes", [_attribute_table(c, styles)], styles))

    combat = getattr(c, "combat", {}) or {}
    combat_rows = [
        ("HP", getattr(c, "hit_points", "")),
        ("SDC", getattr(c, "sdc", "")),
        ("Training", combat.get("training", "")),
        ("Actions / Round", combat.get("actions_per_round", "")),
        ("Initiative", combat.get("initiative", "")),
        ("Strike", combat.get("strike", "")),
        ("Parry", combat.get("parry", "")),
        ("Dodge", combat.get("dodge", "")),
        (
            "Armor",
            (
                f"{_clean_text(getattr(c, 'armor_type', ''))} "
                f"(AR {getattr(c, 'armor_ar', 0)}, SDC {getattr(c, 'armor_sdc', 0)})"
                if _clean_text(getattr(c, "armor_type", ""))
                else ""
            ),
        ),
        ("Shield", getattr(c, "shield_type", "")),
    ]
    story.append(_section("Combat", [_summary_table(combat_rows, styles)], styles))

    story.append(
        _section(
            "Skills",
            _bullet_items("Professional", _clean_list(getattr(c, "skills", {}).get("pro", [])), styles)
            + _bullet_items("Amateur", _clean_list(getattr(c, "skills", {}).get("amateur", [])), styles),
            styles,
        )
    )

    equipment_flowables: list = []
    equipment_flowables += _bullet_items("Weapons", _clean_list(getattr(c, "weapons_selected", [])), styles)
    equipment_flowables += _bullet_items("Gear", _clean_list(getattr(c, "gear_selected", [])), styles)

    vehicles = getattr(c, "vehicles", {}) or {}
    vehicle_lines = []
    land = _clean_list(vehicles.get("landcraft", []))
    water = _clean_list(vehicles.get("watercraft", []))
    air = _clean_list(vehicles.get("aircraft", []))
    if land:
        vehicle_lines.append(f"Land: {', '.join(land)}")
    if water:
        vehicle_lines.append(f"Water: {', '.join(water)}")
    if air:
        vehicle_lines.append(f"Air: {', '.join(air)}")
    equipment_flowables += _bullet_items("Vehicles", vehicle_lines, styles)

    if _clean_text(getattr(c, "shield_notes", "")):
        equipment_flowables.append(_label_value("Shield Notes", getattr(c, "shield_notes", ""), styles))

    story.append(_section("Equipment", equipment_flowables or [_paragraph("No equipment listed.", styles)], styles))

    original = bio.get("original", {}) or {}
    human_features = bio.get("human_features", {}) or {}

    mutant_rows = [
        ("Origin", bio.get("mutant_origin", {}).get("name", "")),
        ("Background", bio.get("background_education", {}).get("name", "")),
        ("Creator", bio.get("creator_organization", {}).get("name", "")),
        ("Original Animal Size", original.get("size_level", "")),
        ("Original Length", original.get("length", "") or original.get("length_in", "")),
        ("Original Weight", original.get("weight", "") or original.get("weight_lbs", "")),
        ("Original Build", original.get("build", "")),
        ("Starting Bio-E", bio.get("total", "")),
        ("Spent Bio-E", bio.get("spent", "")),
        ("Mutant Size", bio.get("mutant_size_label", "")),
        ("Hands", human_features.get("hands_label", "")),
        ("Biped", human_features.get("biped_label", "")),
        ("Speech", human_features.get("speech_label", "")),
        ("Looks", human_features.get("looks_label", "")),
    ]

    mutant_flowables: list = [_summary_table(mutant_rows, styles)]

    if _clean_text(bio.get("mutant_origin", {}).get("details", "")):
        mutant_flowables.append(Spacer(1, 6))
        mutant_flowables.append(_label_value("Origin Details", bio.get("mutant_origin", {}).get("details", ""), styles))

    if _clean_text(bio.get("background_education", {}).get("details", "")):
        mutant_flowables.append(_label_value("Background Details", bio.get("background_education", {}).get("details", ""), styles))

    if _clean_text(bio.get("creator_organization", {}).get("details", "")):
        mutant_flowables.append(_label_value("Creator Details", bio.get("creator_organization", {}).get("details", ""), styles))

    mutant_flowables += _bullet_items("Natural Weapons", _clean_named_entries(bio.get("natural_weapons", [])), styles)
    mutant_flowables += _bullet_items("Animal Abilities", _clean_named_entries(bio.get("abilities", [])), styles)
    mutant_flowables += _bullet_items("Animal Psionics", _clean_named_entries(bio.get("mutant_animal_psionic_powers", [])), styles)
    mutant_flowables += _bullet_items("Hominid Psionics", _clean_named_entries(bio.get("mutant_hominid_psionic_powers", [])), styles)
    mutant_flowables += _bullet_items("Prosthetic Psionics", _clean_named_entries(bio.get("mutant_prosthetic_psionic_powers", [])), styles)
    mutant_flowables += _bullet_items("Human Abilities", _clean_named_entries(bio.get("mutant_human_abilities", [])), styles)
    mutant_flowables += _bullet_items("Hominid Abilities", _clean_named_entries(bio.get("mutant_hominid_abilities", [])), styles)
    mutant_flowables += _bullet_items("Traits", _clean_list(bio.get("traits", [])), styles)

    story.append(_section("Bio-E / Mutant", mutant_flowables, styles))

    if _clean_text(getattr(c, "notes", "")) or _clean_text(combat.get("training_details_text", "")):
        notes_flowables: list = []
        if _clean_text(getattr(c, "notes", "")):
            notes_flowables.append(_label_value("Notes", getattr(c, "notes", ""), styles))
        if _clean_text(combat.get("training_details_text", "")):
            notes_flowables.append(_label_value("Combat Details", combat.get("training_details_text", ""), styles))
        story.append(_section("Notes", notes_flowables, styles))

    story.append(Spacer(1, 4))
    story.append(Paragraph("Generated by TurtleCom", styles["TC_Small"]))

    doc.build(story)