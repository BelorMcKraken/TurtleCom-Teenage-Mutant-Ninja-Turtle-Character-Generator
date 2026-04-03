# app/services/export_statblock_pdf.py

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    FrameBreak,
    Image,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.config import project_root
from app.rules.skills import load_skill_rules
from app.rules.weapons import WEAPONS_BY_NAME

try:
    from app.rules.armor import SHIELD_BY_NAME
except Exception:
    SHIELD_BY_NAME = {}

COMIC_RED = colors.HexColor("#B80F0A")
COMIC_RED_DARK = colors.HexColor("#7F0906")
INK = colors.HexColor("#161616")
STEEL = colors.HexColor("#24374F")
GOLD = colors.HexColor("#B8A16C")
TABLE_HEADER = colors.HexColor("#E3E6EA")
TABLE_ALT = colors.HexColor("#F1F3F5")


@dataclass(slots=True)
class ExportFonts:
    regular: str
    bold: str
    italic: str
    bold_italic: str
    display: str


@dataclass(slots=True)
class SkillContext:
    rules: dict[str, Any]
    lookup: dict[str, dict[str, Any]]
    level: int
    attributes: dict[str, Any]


def _find_footer_logo() -> Path | None:
    candidates = [
        project_root() / "assets" / "turtlecom_logo.png",
        project_root() / "assets" / "turtlecom_logo.jpg",
        project_root() / "assets" / "turtlecom_logo.jpeg",
        project_root() / "assets" / "images" / "turtlecom_logo.png",
        project_root() / "assets" / "images" / "turtlecom_logo.jpg",
        project_root() / "assets" / "images" / "turtlecom_logo.jpeg",
        project_root() / "assets" / "logo.png",
        project_root() / "assets" / "images" / "logo.png",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _find_background_asset() -> Path | None:
    candidates = [
        project_root() / "assets" / "pdf_bg_shell_bw.png",
        project_root() / "assets" / "images" / "pdf_bg_shell_bw.png",
        project_root() / "assets" / "pdf_bg_shell_bw.jpg",
        project_root() / "assets" / "images" / "pdf_bg_shell_bw.jpg",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def export_statblock_pdf(character: Any, out_path: str | Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fonts = _register_fonts()
    styles = _build_styles(fonts)
    doc = _build_doc(out_path, fonts)
    story = _build_story(character, styles)
    doc.build(story)


def _build_doc(out_path: Path, fonts: ExportFonts) -> BaseDocTemplate:
    page_width, page_height = LETTER

    margin = 0.50 * inch
    gutter = 0.26 * inch
    top = 0.58 * inch

    footer_strip_y = 0.12 * inch
    footer_strip_h = 0.78 * inch
    footer_safe_top = footer_strip_y + footer_strip_h + 0.05 * inch
    bottom = footer_safe_top + 0.06 * inch

    first_header_height = 1.68 * inch
    first_header_gap = 0.00 * inch

    usable_width = page_width - (margin * 2) - gutter
    col_width = usable_width / 2

    first_header_y = page_height - top - first_header_height
    first_body_top_y = first_header_y - first_header_gap
    first_body_height = first_body_top_y - bottom

    continuation_top = 0.58 * inch
    continuation_body_height = page_height - continuation_top - bottom

    header = Frame(
        margin,
        first_header_y,
        page_width - (margin * 2),
        first_header_height,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="header",
    )

    first_left = Frame(
        margin,
        bottom,
        col_width,
        first_body_height,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="first_left",
    )

    first_right = Frame(
        margin + col_width + gutter,
        bottom,
        col_width,
        first_body_height,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="first_right",
    )

    later_left = Frame(
        margin,
        bottom,
        col_width,
        continuation_body_height,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="later_left",
    )

    later_right = Frame(
        margin + col_width + gutter,
        bottom,
        col_width,
        continuation_body_height,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="later_right",
    )

    doc = BaseDocTemplate(
        str(out_path),
        pagesize=LETTER,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=top,
        bottomMargin=bottom,
        title="TurtleCom Statblock",
        author="TurtleCom",
    )

    doc.addPageTemplates(
        [
            PageTemplate(
                id="FirstPage",
                frames=[header, first_left, first_right],
                onPage=_make_page_decor(fonts),
                autoNextPageTemplate="LaterPages",
            ),
            PageTemplate(
                id="LaterPages",
                frames=[later_left, later_right],
                onPage=_make_page_decor(fonts),
            ),
        ]
    )
    return doc

def _register_fonts() -> ExportFonts:
    fonts_dir = project_root() / "assets" / "fonts"

    serif_regular_candidates = [
        fonts_dir / "NotoSerif-Regular.ttf",
        fonts_dir / "CormorantGaramond-Regular.ttf",
        fonts_dir / "EBGaramond-Regular.ttf",
        fonts_dir / "LibreBaskerville-Regular.ttf",
    ]
    serif_bold_candidates = [
        fonts_dir / "NotoSerif-Bold.ttf",
        fonts_dir / "CormorantGaramond-Bold.ttf",
        fonts_dir / "EBGaramond-Bold.ttf",
        fonts_dir / "LibreBaskerville-Bold.ttf",
    ]
    serif_italic_candidates = [
        fonts_dir / "NotoSerif-Italic.ttf",
        fonts_dir / "CormorantGaramond-Italic.ttf",
        fonts_dir / "EBGaramond-Italic.ttf",
        fonts_dir / "LibreBaskerville-Italic.ttf",
    ]
    serif_bold_italic_candidates = [
        fonts_dir / "NotoSerif-BoldItalic.ttf",
        fonts_dir / "CormorantGaramond-BoldItalic.ttf",
        fonts_dir / "EBGaramond-BoldItalic.ttf",
        fonts_dir / "LibreBaskerville-BoldItalic.ttf",
    ]
    display_candidates = [
        fonts_dir / "Cinzel-Bold.ttf",
        fonts_dir / "IMFellEnglishSC-Regular.ttf",
        fonts_dir / "UncialAntiqua-Regular.ttf",
        fonts_dir / "NotoSerif-Bold.ttf",
    ]

    regular = _register_first_available("TCSerif", serif_regular_candidates, fallback="Times-Roman")
    bold = _register_first_available("TCSerifBold", serif_bold_candidates, fallback="Times-Bold")
    italic = _register_first_available("TCSerifItalic", serif_italic_candidates, fallback="Times-Italic")
    bold_italic = _register_first_available(
        "TCSerifBoldItalic",
        serif_bold_italic_candidates,
        fallback="Times-BoldItalic",
    )
    display = _register_first_available("TCDisplay", display_candidates, fallback=bold)

    return ExportFonts(
        regular=regular,
        bold=bold,
        italic=italic,
        bold_italic=bold_italic,
        display=display,
    )


def _register_first_available(alias: str, candidates: list[Path], fallback: str) -> str:
    for candidate in candidates:
        if candidate.exists():
            try:
                pdfmetrics.registerFont(TTFont(alias, str(candidate)))
                return alias
            except Exception:
                continue
    return fallback


def _build_styles(fonts: ExportFonts) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()

    body = ParagraphStyle(
        "TCBody",
        parent=base["BodyText"],
        fontName=fonts.regular,
        fontSize=12,
        leading=14,
        textColor=INK,
        spaceAfter=4,
    )
    small = ParagraphStyle(
        "TCSmall",
        parent=body,
        fontSize=12,
        leading=14,
        spaceAfter=3,
    )
    note_body = ParagraphStyle(
        "TCNoteBody",
        parent=body,
        fontSize=12,
        leading=14,
        spaceAfter=2,
    )
    title = ParagraphStyle(
        "TCTitle",
        parent=body,
        fontName=fonts.display,
        fontSize=14,
        leading=16,
        alignment=TA_CENTER,
        textColor=COMIC_RED,
        spaceAfter=4,
    )
    subtitle = ParagraphStyle(
        "TCSubtitle",
        parent=body,
        fontName=fonts.bold,
        fontSize=14,
        leading=16,
        alignment=TA_CENTER,
        textColor=INK,
        spaceAfter=8,
    )
    section = ParagraphStyle(
        "TCSection",
        parent=body,
        fontName=fonts.bold,
        fontSize=12,
        leading=14,
        textColor=colors.white,
        spaceBefore=6,
        spaceAfter=6,
        alignment=TA_LEFT,
    )
    label = ParagraphStyle(
        "TCLabel",
        parent=body,
        fontName=fonts.bold,
        fontSize=12,
        leading=14,
        textColor=INK,
    )
    table_body = ParagraphStyle(
        "TCTableBody",
        parent=body,
        fontSize=12,
        leading=14,
        spaceAfter=0,
    )

    return {
        "body": body,
        "small": small,
        "note_body": note_body,
        "title": title,
        "subtitle": subtitle,
        "section": section,
        "label": label,
        "table_body": table_body,
    }

def _find_section_bars_asset() -> Path | None:
    candidates = [
        project_root() / "assets" / "turtlecom_bars.png",
        project_root() / "assets" / "images" / "turtlecom_bars.png",
        project_root() / "assets" / "turtlecom_bars.jpg",
        project_root() / "assets" / "images" / "turtlecom_bars.jpg",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _app_version_string() -> str:
    try:
        from importlib.metadata import PackageNotFoundError, version
    except Exception:
        PackageNotFoundError = Exception
        version = None

    candidates = [
        "TurtleCom",
        "turtlecom",
        "tmnt-character-generator",
    ]

    if version is not None:
        for name in candidates:
            try:
                found = str(version(name)).strip()
                if found:
                    return found
            except PackageNotFoundError:
                continue
            except Exception:
                continue

    try:
        from app import __version__ as app_version

        found = str(app_version).strip()
        if found:
            return found
    except Exception:
        pass

    return "dev"


def _make_page_decor(fonts: ExportFonts):
    logo_path = _find_footer_logo()
    bg_path = _find_background_asset()
    app_version = _app_version_string()

    def _draw(canvas, doc) -> None:
        w, h = LETTER
        template_id = getattr(getattr(doc, "pageTemplate", None), "id", "")

        footer_strip_y = 0.12 * inch
        footer_strip_h = 0.78 * inch
        footer_safe_top = footer_strip_y + footer_strip_h + 0.05 * inch

        canvas.saveState()

        if bg_path is not None:
            try:
                canvas.drawImage(
                    str(bg_path),
                    0,
                    footer_safe_top,
                    width=w,
                    height=h - footer_safe_top,
                    preserveAspectRatio=False,
                    mask="auto",
                )
            except Exception:
                pass

        content_x = doc.leftMargin - 0.02 * inch
        content_w = w - (doc.leftMargin + doc.rightMargin) + 0.04 * inch

        if template_id == "FirstPage":
            header_box_h = 1.64 * inch
            header_box_y = h - doc.topMargin - header_box_h

            canvas.setFillColorRGB(1, 1, 1)
            canvas.rect(
                content_x,
                header_box_y,
                content_w,
                header_box_h,
                fill=1,
                stroke=0,
            )

            body_top = header_box_y - 0.00 * inch
        else:
            body_top = h - 0.58 * inch

        body_y = doc.bottomMargin
        body_h = body_top - body_y

        canvas.setFillColorRGB(1, 1, 1)
        canvas.rect(
            content_x,
            body_y,
            content_w,
            body_h,
            fill=1,
            stroke=0,
        )

        canvas.setFillColorRGB(1, 1, 1)
        canvas.rect(
            doc.leftMargin,
            footer_strip_y,
            w - doc.leftMargin - doc.rightMargin,
            footer_strip_h,
            fill=1,
            stroke=0,
        )

        canvas.setStrokeColor(STEEL)
        canvas.setLineWidth(1.1)
        canvas.line(doc.leftMargin, h - 0.42 * inch, w - doc.rightMargin, h - 0.42 * inch)

        footer_message = (
            "This character sheet was created using the TurtleCom "
            "Teenage Mutant Ninja Turtle & Other Strangeness Character Generator."
        )
        page_label = f"Page {canvas.getPageNumber()}"

        logo_x = doc.leftMargin
        logo_w = 0.80 * inch
        logo_h = 0.80 * inch

        text_font_size = 10
        text_leading = 11
        page_label_font_size = 11
        page_label_x = w - doc.rightMargin

        text_left = logo_x + logo_w + 0.12 * inch
        max_text_width = max(1.0, page_label_x - text_left - 0.90 * inch)

        canvas.setFont(fonts.regular, text_font_size)

        words = footer_message.split()
        lines: list[str] = []
        current = ""

        for word in words:
            trial = f"{current} {word}".strip()
            if canvas.stringWidth(trial, fonts.regular, text_font_size) <= max_text_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        lines = lines[:2] or [footer_message]
        line_count = len(lines)
        text_block_h = line_count * text_leading

        footer_center_y = footer_strip_y + (footer_strip_h / 2.0)
        logo_y = footer_center_y - (logo_h / 2.0)
        text_top_y = footer_center_y + (text_block_h / 2.0) - text_leading + 1
        page_label_y = footer_center_y - (page_label_font_size * 0.35)

        if logo_path is not None:
            try:
                canvas.drawImage(
                    str(logo_path),
                    logo_x,
                    logo_y,
                    width=logo_w,
                    height=logo_h,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            except Exception:
                pass

        footer_text = canvas.beginText()
        footer_text.setTextOrigin(text_left, text_top_y)
        footer_text.setFont(fonts.regular, text_font_size)
        footer_text.setFillColor(STEEL)
        footer_text.setLeading(text_leading)

        for line in lines:
            footer_text.textLine(line)

        canvas.drawText(footer_text)

        canvas.setFillColor(STEEL)
        canvas.setFont(fonts.bold, page_label_font_size)
        canvas.drawRightString(page_label_x, page_label_y, page_label)

        canvas.restoreState()

    return _draw

def _build_story(character: Any, styles: dict[str, ParagraphStyle]) -> list[Any]:
    story: list[Any] = []

    story.extend(_build_header(character, styles))

    # Leave the page-1 header frame so body sections always start in the columns.
    story.append(FrameBreak())

    sections = [
        _section_identity(character, styles),
        _section_attributes(character, styles),
        _section_combat(character, styles),
        _section_equipment(character, styles),
        _section_skills(character, styles),
        _section_bioe(character, styles),
        _section_mutations_and_psionics(character, styles),
        _section_notes(character, styles),
    ]

    for section in sections:
        if section:
            story.extend(section)

    return story

def _build_header(character: Any, styles: dict[str, ParagraphStyle]) -> list[Any]:
    items: list[Any] = []

    image_path = str(
        getattr(character, "image_path", "")
        or getattr(getattr(character, "bio_e", {}), "image_path", "")
        or ""
    ).strip()
    art = _safe_image(image_path, width=1.05 * inch, height=1.05 * inch)

    name = _esc(_text(getattr(character, "name", "Unnamed Character"), "Unnamed Character"))
    animal = _esc(_text(getattr(character, "animal", "Unknown Animal"), "Unknown Animal"))
    level = _esc(_text(getattr(character, "level", "1"), "1"))
    alignment = _esc(_text(getattr(character, "alignment", "—"), "—"))
    gender = _esc(_text(getattr(character, "gender", "—"), "—"))
    age = _esc(_text(getattr(character, "age", "—"), "—"))
    size = _esc(_text(getattr(character, "size", "—"), "—"))
    height = _esc(_text(getattr(character, "height", "—"), "—"))
    weight = _esc(_text(getattr(character, "weight", "—"), "—"))
    wealth = _esc(_currency(getattr(character, "total_wealth", "")))
    credits = _esc(_text(getattr(character, "total_credits", "0"), "0"))

    heading = [
        Paragraph(name, styles["title"]),
        Paragraph(
            f"Level {level} {animal} &nbsp;•&nbsp; {alignment} &nbsp;•&nbsp; {gender} &nbsp;•&nbsp; Age {age}",
            styles["subtitle"],
        ),
        Paragraph(
            f"Size {size} &nbsp;•&nbsp; Height {height} &nbsp;•&nbsp; Weight {weight} &nbsp;•&nbsp; Wealth {wealth} &nbsp;•&nbsp; Credits {credits}",
            styles["small"],
        ),
    ]

    content = [[art if art is not None else "", heading]]
    table = Table(content, colWidths=[1.15 * inch, 5.80 * inch], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("LINEBELOW", (0, 0), (-1, -1), 0.6, GOLD),
            ]
        )
    )
    items.append(table)
    return items


def _section_identity(character: Any, styles: dict[str, ParagraphStyle]) -> list[Any]:
    bio_e = _as_dict(getattr(character, "bio_e", {}))
    original = _as_dict(bio_e.get("original"))
    rows = [
        ("Origin Animal", _text(getattr(character, "animal", ""))),
        ("Mutant Origin", _nested_name(bio_e.get("mutant_origin"))),
        ("Background", _nested_name(bio_e.get("background_education"))),
        ("Creator", _nested_name(bio_e.get("creator_organization"))),
        ("Original Build", _text(original.get("size_level", ""))),
        ("Mutant Size", _text(bio_e.get("mutant_size_label", "") or getattr(character, "size", ""))),
        ("XP", _text(getattr(character, "xp", "0"), "0")),
        ("Level", _text(getattr(character, "level", "1"), "1")),
    ]
    return _section_box("Identity", rows, styles, columns=1, col_widths=[1.10 * inch, 2.00 * inch])


def _section_attributes(character: Any, styles: dict[str, ParagraphStyle]) -> list[Any]:
    attrs = _as_dict(getattr(character, "attributes", {}))
    rows = [
        ("IQ - Intelligence Quotient", _attribute_value(attrs, "IQ", "IQ - Intelligence Quotient")),
        ("ME - Mental Endurance", _attribute_value(attrs, "ME", "ME - Mental Endurance")),
        ("MA - Mental Affinity", _attribute_value(attrs, "MA", "MA - Mental Affinity")),
        ("PS - Physical Strength", _attribute_value(attrs, "PS", "PS - Physical Strength")),
        ("PP - Physical Prowess", _attribute_value(attrs, "PP", "PP - Physical Prowess")),
        ("PE - Physical Endurance", _attribute_value(attrs, "PE", "PE - Physical Endurance")),
        ("PB - Physical Beauty", _attribute_value(attrs, "PB", "PB - Physical Beauty")),
        ("Speed", attrs.get("Speed", "—")),
    ]
    return _section_box("Attributes", rows, styles, columns=1)


def _section_combat(character: Any, styles: dict[str, ParagraphStyle]) -> list[Any]:
    combat = _as_dict(getattr(character, "combat", {}))
    rows = [
        ("HP", _text(getattr(character, "hit_points", "—"))),
        ("SDC", _text(getattr(character, "sdc", "—"))),
        ("Training", _text(combat.get("training", "—"))),
        ("Actions", _text(combat.get("actions_per_round", "—"))),
        ("Initiative", _signed_text(combat.get("initiative", "—"))),
        ("Strike", _signed_text(combat.get("strike", "—"))),
        ("Parry", _signed_text(combat.get("parry", "—"))),
        ("Dodge", _signed_text(combat.get("dodge", "—"))),
        ("Save vs Psionic / Strangeness", _signed_text(combat.get("save_vs_psionic_strangeness", "—"))),
        ("Roll w/ Impact", _signed_text(combat.get("roll_with_impact", "—"))),
    ]

    armor_name = _clean_placeholder(
        _text(getattr(character, "armor_name", "") or getattr(character, "armor_type", ""))
    )
    shield_name = _clean_placeholder(_text(getattr(character, "shield_type", "")))
    shield_sdc = _shield_sdc(character, shield_name)

    if armor_name:
        rows.append(
            (
                "Armor",
                f"{armor_name} (AR {_text(getattr(character, 'armor_ar', '—'))}, SDC {_text(getattr(character, 'armor_sdc', '—'))})",
            )
        )

    if shield_name:
        shield_text = f"{shield_name} (SDC {shield_sdc})" if shield_sdc else shield_name
        rows.append(("Shield", shield_text))

    return _section_box("Combat", rows, styles)


def _section_equipment(character: Any, styles: dict[str, ParagraphStyle]) -> list[Any]:
    bar_width = 3.30 * inch
    parts: list[Any] = [_section_banner("Equipment", styles, width=bar_width)]

    weapon_rows = _weapon_rows(getattr(character, "weapons_selected", []))
    if weapon_rows:
        parts.append(
            _mini_table(
                ["Weapon", "Range", "Damage"],
                weapon_rows,
                styles,
                [1.95 * inch, 0.55 * inch, 0.80 * inch],
            )
        )

    gear = _string_list(getattr(character, "gear_selected", []))
    vehicles = _flatten_vehicle_lines(_as_dict(getattr(character, "vehicles", {})))

    parts.extend(_bullet_block("Gear", gear, styles))
    parts.extend(_bullet_block("Vehicles", vehicles, styles))
    return parts




def _section_skills(character: Any, styles: dict[str, ParagraphStyle]) -> list[Any]:
    bar_width = 3.30 * inch
    parts: list[Any] = [_section_banner("Skills", styles, width=bar_width)]

    pro_rows = _skill_rows(character, "pro")
    amateur_rows = _skill_rows(character, "amateur")

    if pro_rows:
        parts.append(
            _mini_table(
                ["Professional", "%"],
                pro_rows,
                styles,
                [2.55 * inch, 0.75 * inch],
            )
        )
        parts.append(Spacer(1, 0.04 * inch))

    if amateur_rows:
        parts.append(
            _mini_table(
                ["Amateur", "%"],
                amateur_rows,
                styles,
                [2.55 * inch, 0.75 * inch],
            )
        )

    if not pro_rows and not amateur_rows:
        parts.append(Paragraph("—", styles["body"]))

    return parts


def _section_bioe(character: Any, styles: dict[str, ParagraphStyle]) -> list[Any]:
    bio_e = _as_dict(getattr(character, "bio_e", {}))
    human_features = _as_dict(bio_e.get("human_features"))
    rows = [
        ("Starting Bio-E", _text(bio_e.get("total", "—"))),
        ("Spent Bio-E", _text(bio_e.get("spent", "—"))),
        ("Hands", _feature_line(human_features, "hands")),
        ("Biped", _feature_line(human_features, "biped")),
        ("Speech", _feature_line(human_features, "speech")),
        ("Looks", _feature_line(human_features, "looks")),
    ]
    return _section_box("Bio-E / Mutant", rows, styles)


def _section_mutations_and_psionics(character: Any, styles: dict[str, ParagraphStyle]) -> list[Any]:
    bio_e = _as_dict(getattr(character, "bio_e", {}))

    natural_weapons = _selected_bioe_name_list(bio_e.get("natural_weapons", []))
    animal_abilities = _selected_bioe_name_list(bio_e.get("abilities", []))
    animal_psionics = _entry_name_list(
        bio_e.get("mutant_animal_psionic_powers", []) or bio_e.get("psionics", [])
    )
    hominid_psionics = _entry_name_list(bio_e.get("mutant_hominid_psionic_powers", []))
    prosthetic_psionics = _entry_name_list(bio_e.get("mutant_prosthetic_psionic_powers", []))
    human_abilities = _entry_name_list(bio_e.get("mutant_human_abilities", []))
    hominid_abilities = _entry_name_list(bio_e.get("mutant_hominid_abilities", []))

    parts: list[Any] = [_section_banner("Mutations / Psionics", styles)]
    parts.extend(_bullet_block("Natural Weapons", natural_weapons, styles))
    parts.extend(_bullet_block("Animal Abilities", animal_abilities, styles))
    parts.extend(_bullet_block("Animal Psionics", animal_psionics, styles))
    parts.extend(_bullet_block("Hominid Psionics", hominid_psionics, styles))
    parts.extend(_bullet_block("Prosthetic Psionics", prosthetic_psionics, styles))
    parts.extend(_bullet_block("Human Abilities", human_abilities, styles))
    parts.extend(_bullet_block("Hominid Abilities", hominid_abilities, styles))
    return parts


def _section_notes(character: Any, styles: dict[str, ParagraphStyle]) -> list[Any]:
    bio_e = _as_dict(getattr(character, "bio_e", {}))
    mutant_origin = _as_dict(bio_e.get("mutant_origin"))
    background = _as_dict(bio_e.get("background_education"))
    creator = _as_dict(bio_e.get("creator_organization"))
    combat = _as_dict(getattr(character, "combat", {}))

    note_lines = [
        ("Origin Details", _text(mutant_origin.get("details", ""))),
        ("Background Details", _text(background.get("details", ""))),
        ("Creator Details", _text(creator.get("details", ""))),
        ("Combat Details", _combat_summary(combat)),
        ("Notes", _text(getattr(character, "notes", ""))),
    ]

    parts: list[Any] = [_section_banner("Notes", styles)]
    for label, value in note_lines:
        if not value.strip():
            continue
        parts.append(Paragraph(f"<b>{_esc(label)}:</b> {_esc(value)}", styles["note_body"]))
        parts.append(Spacer(1, 0.025 * inch))

    return parts


def _section_box(
    title: str,
    rows: list[tuple[str, Any]],
    styles: dict[str, ParagraphStyle],
    columns: int = 1,
    col_widths: list[float] | None = None,
) -> list[Any]:
    parts: list[Any] = [_section_banner(title, styles)]

    clean_rows = [(str(k), _text(v, "—")) for k, v in rows if _text(v).strip()]
    if not clean_rows:
        parts.append(Paragraph("—", styles["body"]))
        return parts

    if columns <= 1:
        data = [
            [Paragraph(f"<b>{_esc(k)}:</b>", styles["label"]), Paragraph(_esc(v), styles["body"])]
            for k, v in clean_rows
        ]
        table = Table(
            data,
            colWidths=col_widths if col_widths is not None else [2.15 * inch, 0.95 * inch],
            hAlign="LEFT",
        )
    else:
        pairs: list[list[Any]] = []
        chunked = [clean_rows[i:i + columns] for i in range(0, len(clean_rows), columns)]
        for group in chunked:
            row: list[Any] = []
            for k, v in group:
                row.append(Paragraph(f"<b>{_esc(k)}:</b>", styles["label"]))
                row.append(Paragraph(_esc(v), styles["body"]))
            while len(row) < columns * 2:
                row.extend(["", ""])
            pairs.append(row)

        table = Table(
            pairs,
            colWidths=[0.58 * inch, 0.97 * inch, 0.58 * inch, 0.97 * inch][: columns * 2],
            hAlign="LEFT",
        )

    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )
    parts.append(table)
    parts.append(Spacer(1, 0.06 * inch))
    return parts

class SectionBar(Flowable):
    def __init__(self, title: str, style: ParagraphStyle, width: float, image_path: Path | None) -> None:
        super().__init__()
        self.title = title
        self.style = style
        self.width = width
        self.height = 0.34 * inch
        self.image_path = image_path

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        self.width = min(self.width, availWidth)
        return self.width, self.height

    def draw(self) -> None:
        canvas = self.canv

        if self.image_path is not None:
            try:
                canvas.drawImage(
                    str(self.image_path),
                    0,
                    0,
                    width=self.width,
                    height=self.height,
                    preserveAspectRatio=False,
                    mask="auto",
                )
            except Exception:
                canvas.setFillColor(COMIC_RED)
                canvas.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        else:
            canvas.setFillColor(COMIC_RED)
            canvas.rect(0, 0, self.width, self.height, fill=1, stroke=0)

        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(0.8)
        canvas.rect(0, 0, self.width, self.height, fill=0, stroke=1)

        canvas.setStrokeColor(COMIC_RED_DARK)
        canvas.setLineWidth(0.5)
        canvas.line(0, 1.2, self.width, 1.2)

        canvas.setFillColor(self.style.textColor)
        canvas.setFont(self.style.fontName, self.style.fontSize)
        text_y = max(3, (self.height - self.style.fontSize) / 2 + 2)
        canvas.drawString(7, text_y, self.title.upper())

def _section_banner(
    title: str,
    styles: dict[str, ParagraphStyle],
    width: float = 3.20 * inch,
) -> SectionBar:
    return SectionBar(
        title,
        styles["section"],
        width=width,
        image_path=_find_section_bars_asset(),
    )

def _mini_table(
    headers: list[str],
    rows: list[list[str]],
    styles: dict[str, ParagraphStyle],
    col_widths: list[float],
) -> KeepTogether:
    data: list[list[Any]] = [
        [Paragraph(f"<b>{_esc(h)}</b>", styles["label"]) for h in headers]
    ]
    for row in rows:
        data.append([Paragraph(_esc(cell), styles["table_body"]) for cell in row])

    table = Table(data, colWidths=col_widths, hAlign="LEFT", repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER),
                ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.HexColor("#BFC5CC")),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#8F98A1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, TABLE_ALT]),
            ]
        )
    )
    return KeepTogether([table])


def _bullet_block(title: str, items: list[str], styles: dict[str, ParagraphStyle]) -> list[Any]:
    parts: list[Any] = []
    if not items:
        return parts

    parts.append(Paragraph(f"<b>{_esc(title)}</b>", styles["label"]))
    for item in items:
        parts.append(Paragraph(f"• {_esc(item)}", styles["body"]))
    parts.append(Spacer(1, 0.04 * inch))
    return parts


def _skill_rows(character: Any, bucket: str) -> list[list[str]]:
    skills = _as_dict(getattr(character, "skills", {}))
    selected = _string_list(skills.get(bucket, []))
    if not selected:
        return []

    context = _make_skill_context(character, bucket)
    rows: list[list[str]] = []
    for name in selected:
        pct = _calc_skill_pct(name, context)
        rows.append([name, f"{pct}%" if pct is not None else "—"])
    return rows


def _weapon_rows(values: Iterable[Any]) -> list[list[str]]:
    rows: list[list[str]] = []
    for value in values or []:
        details = _resolve_weapon_details(_clean_placeholder(str(value or "").strip()))
        if not details["name"]:
            continue

        rows.append(
            [
                details["name"],
                details["range"] or "—",
                details["damage"] or "—",
            ]
        )
    return rows


def _resolve_weapon_details(name: str) -> dict[str, str]:
    cleaned_name = _clean_placeholder(_text(name, ""))
    if not cleaned_name:
        return {
            "name": "",
            "type": "",
            "damage": "",
            "range": "",
            "notes": "",
        }

    raw = WEAPONS_BY_NAME.get(cleaned_name, {})
    if not isinstance(raw, dict):
        raw = {}

    weapon_type = _first_non_empty(
        raw.get("type"),
        raw.get("weapon_type"),
        raw.get("category"),
        raw.get("class"),
        raw.get("group"),
        raw.get("kind"),
        raw.get("weaponClass"),
    )

    damage = _first_non_empty(
        raw.get("damage"),
        raw.get("dmg"),
        raw.get("md"),
        raw.get("sdc_damage"),
        raw.get("damage_sdc"),
        raw.get("damage_dice"),
        raw.get("primary_damage"),
        raw.get("damageRoll"),
    )

    notes = _first_non_empty(
        raw.get("notes"),
        raw.get("special"),
        raw.get("description"),
        raw.get("details"),
        raw.get("summary"),
        raw.get("display"),
    )

    range_text = _first_non_empty(
        raw.get("range"),
        raw.get("effective_range"),
        raw.get("distance"),
        raw.get("max_range"),
    )

    if not weapon_type:
        weapon_type = _parse_weapon_type_from_notes(notes)

    if not damage:
        damage = _parse_weapon_damage_from_notes(notes)

    if not range_text:
        range_text = _parse_weapon_range_from_notes(notes)

    if not damage:
        dice = _first_non_empty(raw.get("dice"), raw.get("damage_dice_count"))
        sides = _first_non_empty(raw.get("sides"), raw.get("damage_dice_sides"))
        bonus = _first_non_empty(raw.get("bonus"), raw.get("damage_bonus"))
        if dice and sides:
            bonus_text = f"+{bonus}" if bonus and not str(bonus).startswith("-") else str(bonus or "")
            damage = f"{dice}D{sides}{bonus_text}"

    return {
        "name": cleaned_name,
        "type": weapon_type,
        "damage": damage,
        "range": range_text,
        "notes": notes,
    }


def _parse_weapon_type_from_notes(notes: str) -> str:
    text = _text(notes, "")
    if not text:
        return ""

    lowered = text.casefold()

    if "revolver" in lowered or "pistol" in lowered or "handgun" in lowered:
        return "Pistol"
    if "rifle" in lowered:
        return "Rifle"
    if "shotgun" in lowered:
        return "Shotgun"
    if "smg" in lowered or "submachine" in lowered:
        return "SMG"
    if "machine gun" in lowered:
        return "Machine Gun"
    if "bow" in lowered:
        return "Bow"
    if "crossbow" in lowered:
        return "Crossbow"
    if "knife" in lowered:
        return "Knife"
    if "sword" in lowered:
        return "Sword"
    if "axe" in lowered:
        return "Axe"
    if "club" in lowered or "mace" in lowered:
        return "Blunt"
    if "grenade" in lowered:
        return "Grenade"

    return ""


def _parse_weapon_damage_from_notes(notes: str) -> str:
    text = _text(notes, "")
    if not text:
        return ""

    match = re.search(r"damage\s*[:\-]?\s*([0-9]+D[0-9]+(?:[+\-][0-9]+)?)", text, flags=re.IGNORECASE)
    if match:
        return match.group(1).upper()

    match = re.search(r"\b([0-9]+D[0-9]+(?:[+\-][0-9]+)?)\b", text, flags=re.IGNORECASE)
    if match:
        return match.group(1).upper()

    return ""


def _parse_weapon_range_from_notes(notes: str) -> str:
    text = _text(notes, "")
    if not text:
        return ""

    match = re.search(r"([0-9]+(?:\s*[-–]\s*[0-9]+)?\s*(?:ft|feet|yd|yards|m|meters))", text, flags=re.IGNORECASE)
    if match:
        return re.sub(r"\s+", " ", match.group(1)).strip()

    return ""


def _weapon_type(raw: dict[str, Any]) -> str:
    candidates = [
        raw.get("type"),
        raw.get("weapon_type"),
        raw.get("category"),
        raw.get("class"),
        raw.get("group"),
        raw.get("kind"),
        raw.get("weaponClass"),
    ]
    text = _first_non_empty(*candidates)
    if text:
        return text

    for key, value in raw.items():
        k = str(key).casefold()
        if "type" in k or "category" in k or "class" in k:
            cleaned = _text(value, "")
            if cleaned:
                return cleaned
    return ""


def _weapon_damage(raw: dict[str, Any]) -> str:
    candidates = [
        raw.get("damage"),
        raw.get("dmg"),
        raw.get("md"),
        raw.get("sdc_damage"),
        raw.get("damage_sdc"),
        raw.get("damage_dice"),
        raw.get("primary_damage"),
        raw.get("damageRoll"),
    ]
    text = _first_non_empty(*candidates)
    if text:
        return text

    dice = _first_non_empty(raw.get("dice"), raw.get("damage_dice_count"))
    sides = _first_non_empty(raw.get("sides"), raw.get("damage_dice_sides"))
    bonus = _first_non_empty(raw.get("bonus"), raw.get("damage_bonus"))
    if dice and sides:
        bonus_text = f"+{bonus}" if bonus and not str(bonus).startswith("-") else str(bonus or "")
        return f"{dice}D{sides}{bonus_text}"

    for key, value in raw.items():
        k = str(key).casefold()
        if "damage" in k or k == "dmg" or k == "md":
            cleaned = _text(value, "")
            if cleaned:
                return cleaned
    return ""


def _make_skill_context(character: Any, bucket: str) -> SkillContext:
    try:
        rules = load_skill_rules()
    except Exception:
        rules = {"professional": {}, "amateur": {}, "meta": {}, "attribute_bonus_mode": "simple"}

    grouped = rules.get("professional", {}) if bucket == "pro" else rules.get("amateur", {})
    lookup: dict[str, dict[str, Any]] = {}
    if isinstance(grouped, dict):
        for _, skills in grouped.items():
            if not isinstance(skills, list):
                continue
            for entry in skills:
                if isinstance(entry, dict):
                    name = str(entry.get("name", "") or "").strip()
                    if name:
                        lookup[name] = entry

    return SkillContext(
        rules=rules,
        lookup=lookup,
        level=_int_value(getattr(character, "level", 1), 1),
        attributes=_as_dict(getattr(character, "attributes", {})),
    )


def _calc_skill_pct(skill_name: str, context: SkillContext) -> int | None:
    if not skill_name:
        return None

    rule = context.lookup.get(skill_name)
    if not isinstance(rule, dict):
        return None

    base = rule.get("base_pct")
    if isinstance(base, list) and base:
        base_val = _int_value(base[0], 0)
    elif isinstance(base, int):
        base_val = base
    else:
        return None

    default_per_level = _int_value(context.rules.get("meta", {}).get("default_per_level", 5), 5)
    per_level = rule.get("per_level")
    if not isinstance(per_level, int) or per_level <= 0:
        per_level = default_per_level

    attrib_name = str(rule.get("attribute", "") or "").strip()
    attrib_score = _int_value(context.attributes.get(attrib_name, 0), 0)
    mode = str(context.rules.get("attribute_bonus_mode", "simple") or "simple").strip().lower()
    attrib_mod = _simple_attribute_mod(attrib_score) if mode == "simple" and attrib_score > 0 else 0

    return base_val + per_level * max(0, context.level - 1) + attrib_mod


def _entry_name_list(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    for value in values or []:
        if isinstance(value, dict):
            name = str(value.get("name", "") or "").strip()
            cost = value.get("cost", "")
            if name and cost not in ("", None):
                out.append(f"{name} ({cost} Bio-E)")
            elif name:
                out.append(name)
        else:
            text = str(value or "").strip()
            if text:
                out.append(text)
    return out


def _selected_bioe_name_list(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    for value in values or []:
        if isinstance(value, dict):
            name = str(value.get("name", "") or "").strip()
            cost = value.get("cost", "")
            if not name:
                continue
            if name.casefold() == "none":
                continue
            if cost not in ("", None):
                out.append(f"{name} ({cost} Bio-E)")
            else:
                out.append(name)
        else:
            text = str(value or "").strip()
            if not text:
                continue
            if text.casefold() == "none":
                continue
            out.append(text)
    return out


def _string_list(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    for value in values or []:
        text = _clean_placeholder(str(value or "").strip())
        if text:
            out.append(text)
    return out


def _string_list(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    for value in values or []:
        text = _clean_placeholder(str(value or "").strip())
        if text:
            out.append(text)
    return out


def _flatten_vehicle_lines(vehicles: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for key, label in (("landcraft", "Land"), ("watercraft", "Water"), ("aircraft", "Air")):
        raw = vehicles.get(key)
        if not raw:
            continue

        if isinstance(raw, list):
            names = [_clean_placeholder(str(v).strip()) for v in raw]
            names = [name for name in names if name]
        else:
            single = _clean_placeholder(str(raw).strip())
            names = [single] if single else []

        for name in names:
            out.append(f"{label}: {name}")
    return out


def _feature_line(human_features: dict[str, Any], prefix: str) -> str:
    label = _clean_placeholder(_text(human_features.get(f"{prefix}_label", "")))
    cost = _text(human_features.get(f"{prefix}_cost", "")).strip()

    if not label and cost:
        return _format_feature_choice("", cost)
    if label:
        return _format_feature_choice(label, cost)
    return "—"


def _format_feature_choice(label: str, cost: str) -> str:
    clean_label = _strip_bioe_suffix(label)
    clean_cost = _normalize_feature_cost(cost)
    normalized = clean_label.casefold()

    if normalized in {"full", "partial", "none"}:
        if clean_cost:
            return f"{clean_label} ({clean_cost} Bio-E)"
        return clean_label

    if clean_cost and clean_label:
        return f"{clean_label} ({clean_cost} Bio-E)"

    return clean_label or (f"({clean_cost} Bio-E)" if clean_cost else "—")


def _combat_summary(combat: dict[str, Any]) -> str:
    if not combat:
        return ""

    ordered = [
        ("Training", combat.get("training")),
        ("Actions/round", combat.get("actions_per_round")),
        ("Initiative", _signed_text(combat.get("initiative"))),
        ("Strike", _signed_text(combat.get("strike"))),
        ("Parry", _signed_text(combat.get("parry"))),
        ("Dodge", _signed_text(combat.get("dodge"))),
        ("Roll with Impact", _signed_text(combat.get("roll_with_impact"))),
        ("Critical range", combat.get("critical_range")),
    ]

    parts = []
    for label, value in ordered:
        text = _text(value, "")
        if text:
            parts.append(f"{label}: {text}")
    return " • ".join(parts)


def _shield_sdc(character: Any, shield_name: str) -> str:
    direct_candidates = [
        getattr(character, "shield_sdc", ""),
        getattr(character, "shield_SDC", ""),
        getattr(character, "shield_hp", ""),
    ]
    direct = _first_non_empty(*direct_candidates)
    if direct:
        return direct

    raw = SHIELD_BY_NAME.get(shield_name, {}) if shield_name else {}
    if not isinstance(raw, dict):
        raw = {}

    candidates = [
        raw.get("sdc"),
        raw.get("SDC"),
        raw.get("hit_points"),
        raw.get("hp"),
        raw.get("value"),
    ]
    found = _first_non_empty(*candidates)
    if found:
        return found

    for key, value in raw.items():
        k = str(key).casefold()
        if "sdc" in k or "hit" in k:
            cleaned = _text(value, "")
            if cleaned:
                return cleaned
    return ""


def _safe_image(image_path: str, width: float, height: float) -> Image | None:
    if not image_path:
        return None

    path = Path(image_path)
    if not path.exists() or not path.is_file():
        return None

    try:
        img = Image(str(path), width=width, height=height)
        img.hAlign = "LEFT"
        return img
    except Exception:
        return None


def _nested_name(value: Any) -> str:
    if isinstance(value, dict):
        return _text(value.get("name", ""))
    return _text(value, "")


def _currency(value: Any) -> str:
    text = _text(value, "")
    if not text:
        return "—"
    if text.startswith("$"):
        return text
    try:
        return f"${int(float(text)):,}"
    except Exception:
        return text


def _signed_text(value: Any) -> str:
    text = _text(value, "")
    if not text:
        return "—"
    try:
        num = int(float(text))
        return f"+{num}" if num > 0 else str(num)
    except Exception:
        return text


def _simple_attribute_mod(score: int) -> int:
    return max(0, (score - 10) // 2)


def _clean_placeholder(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""

    if text.casefold() in {
        "select gear item",
        "select a weapon",
        "select a vehicle",
        "select shield",
        "select armor",
    }:
        return ""
    return text


def _strip_bioe_suffix(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    return re.sub(r"\s*\(\s*\d+\s*bio-?e\s*\)\s*$", "", text, flags=re.IGNORECASE).strip()


def _normalize_feature_cost(value: Any) -> str:
    text = _text(value, "").strip()
    if not text:
        return ""
    match = re.search(r"-?\d+", text)
    return match.group(0) if match else text


def _first_non_empty(*values: Any) -> str:
    for value in values:
        text = _text(value, "")
        if text:
            return text
    return ""


def _int_value(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}

def _attribute_value(attrs: dict[str, Any], short_key: str, long_key: str) -> Any:
    if long_key in attrs and _text(attrs.get(long_key, "")).strip():
        return attrs.get(long_key, "—")
    return attrs.get(short_key, "—")

def _esc(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")