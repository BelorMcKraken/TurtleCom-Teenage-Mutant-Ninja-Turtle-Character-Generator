from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.config import project_root


COMIC_RED = colors.HexColor("#9B111E")
COMIC_RED_DARK = colors.HexColor("#5E0A12")
STEEL = colors.HexColor("#2D3E5E")
PAPER = colors.HexColor("#F7F7F4")
SOFT_GREY = colors.HexColor("#E2E2E2")
MID_GREY = colors.HexColor("#C8C8C8")


@dataclass(frozen=True)
class ExportFonts:
    regular: str = "Helvetica"
    bold: str = "Helvetica-Bold"
    italic: str = "Helvetica-Oblique"
    bold_italic: str = "Helvetica-BoldOblique"


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _esc(value: Any) -> str:
    return (
        _text(value, "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _money(value: Any) -> str:
    try:
        return f"${int(value or 0):,}"
    except Exception:
        return "$0"


def _yes_no(value: Any) -> str:
    return "Yes" if bool(value) else "No"


def _clean_support_devices(items: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = _text(item.get("name", "")).strip()
        if not name:
            continue
        out.append(
            {
                "name": name,
                "portable": bool(item.get("portable", False)),
            }
        )
    return out


def _vehicle_type_display(vehicle_type: str) -> str:
    mapping = {
        "truck_van": "Truck or Van",
        "compact_sports_car": "Compact or Sports Car",
        "mid_size_larger_car": "Mid-Size or Larger Car",
        "motorcycle": "Motorcycle",
        "aircraft": "Aircraft",
        "watercraft": "Watercraft",
        "other_vehicle": "Other Vehicle",
    }
    key = _text(vehicle_type).strip()
    return mapping.get(key, key.replace("_", " ").title() if key else "—")


def _find_background_asset() -> Path | None:
    candidates = [
        project_root() / "assets" / "stippled_turtle_shell.png",
        project_root() / "assets" / "images" / "stippled_turtle_shell.png",
        project_root() / "assets" / "stippled_turtle_shell.jpg",
        project_root() / "assets" / "images" / "stippled_turtle_shell.jpg",
        project_root() / "assets" / "shell_background.png",
        project_root() / "assets" / "images" / "shell_background.png",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _find_section_bars_asset() -> Path | None:
    candidates = [
        project_root() / "assets" / "turtlecom_bars.png",
        project_root() / "assets" / "images" / "turtlecom_bars.jpg",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _find_footer_logo() -> Path | None:
    candidates = [
        project_root() / "assets" / "images" / "TurtleCom Logo.png",
        project_root() / "assets" / "TurtleCom Logo.png",
        project_root() / "TurtleCom Logo.png",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _safe_image(image_path: str, max_width: float = 3.1 * inch, max_height: float = 2.6 * inch):
    image_path = _text(image_path).strip()
    if not image_path:
        return None
    path = Path(image_path)
    if not path.exists() or not path.is_file():
        return None

    img = Image(str(path))
    img._restrictSize(max_width, max_height)
    return img


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


def _build_styles(fonts: ExportFonts) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()

    styles: dict[str, ParagraphStyle] = {
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontName=fonts.bold,
            fontSize=20,
            leading=23,
            alignment=TA_CENTER,
            textColor=COMIC_RED,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["BodyText"],
            fontName=fonts.bold,
            fontSize=13,
            leading=16,
            alignment=TA_CENTER,
            textColor=colors.black,
            spaceAfter=4,
        ),
        "meta": ParagraphStyle(
            "meta",
            parent=base["BodyText"],
            fontName=fonts.regular,
            fontSize=11,
            leading=13,
            alignment=TA_CENTER,
            textColor=colors.black,
        ),
        "section": ParagraphStyle(
            "section",
            parent=base["Heading2"],
            fontName=fonts.bold,
            fontSize=13,
            leading=14,
            textColor=colors.white,
            alignment=TA_LEFT,
        ),
        "label": ParagraphStyle(
            "label",
            parent=base["BodyText"],
            fontName=fonts.bold,
            fontSize=10,
            leading=12,
            textColor=colors.black,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName=fonts.regular,
            fontSize=10,
            leading=13,
            textColor=colors.black,
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["BodyText"],
            fontName=fonts.regular,
            fontSize=9,
            leading=11,
            textColor=STEEL,
        ),
    }
    return styles


def _section_banner(title: str, styles: dict[str, ParagraphStyle], width: float = 7.20 * inch) -> SectionBar:
    return SectionBar(
        title,
        styles["section"],
        width=width,
        image_path=_find_section_bars_asset(),
    )


def _build_doc(out_path: Path, fonts: ExportFonts) -> BaseDocTemplate:
    page_width, page_height = LETTER

    margin = 0.50 * inch
    top = 0.58 * inch

    footer_strip_y = 0.12 * inch
    footer_strip_h = 0.62 * inch
    footer_safe_top = footer_strip_y + footer_strip_h + 0.05 * inch
    bottom = footer_safe_top + 0.06 * inch

    frame = Frame(
        margin,
        bottom,
        page_width - (margin * 2),
        page_height - top - bottom,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="main",
    )

    doc = BaseDocTemplate(
        str(out_path),
        pagesize=LETTER,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=top,
        bottomMargin=bottom,
        title="TurtleCom Time Machine Export",
        author="TurtleCom",
    )

    doc.addPageTemplates(
        [
            PageTemplate(
                id="TAExport",
                frames=[frame],
                onPage=_make_page_decor(fonts),
            )
        ]
    )
    return doc


def _make_page_decor(fonts: ExportFonts):
    logo_path = _find_footer_logo()
    bg_path = _find_background_asset()

    def _draw(canvas, doc) -> None:
        w, h = LETTER

        footer_strip_y = 0.12 * inch
        footer_strip_h = 0.62 * inch
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
        body_top = h - 0.58 * inch
        body_y = doc.bottomMargin
        body_h = body_top - body_y

        canvas.setFillColorRGB(1, 1, 1)
        canvas.rect(content_x, body_y, content_w, body_h, fill=1, stroke=0)

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

        footer_y = footer_strip_y + 0.19 * inch
        logo_x = doc.leftMargin
        logo_w = 0.80 * inch
        logo_h = 0.80 * inch
        logo_y = footer_strip_y + 0.02 * inch

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

        footer_message = (
            "This character sheet was created using the TurtleCom "
            "Teenage Mutant Ninja Turtle & Other Strangeness Character Generator."
        )

        canvas.setFillColor(STEEL)
        canvas.setFont(fonts.regular, 10)

        text_left = logo_x + logo_w + 0.10 * inch
        page_label_x = w - doc.rightMargin
        max_text_width = page_label_x - text_left - 0.90 * inch

        words = footer_message.split()
        lines: list[str] = []
        current = ""

        for word in words:
            trial = f"{current} {word}".strip()
            if canvas.stringWidth(trial, fonts.regular, 10) <= max_text_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        footer_text = canvas.beginText()
        footer_text.setTextOrigin(text_left, footer_y)
        footer_text.setFont(fonts.regular, 10)
        footer_text.setFillColor(STEEL)
        footer_text.setLeading(11)

        for line in lines[:2]:
            footer_text.textLine(line)

        canvas.drawText(footer_text)

        canvas.setFont(fonts.bold, 11)
        canvas.drawRightString(page_label_x, footer_y, f"Page {canvas.getPageNumber()}")

        canvas.restoreState()

    return _draw


def _make_kv_table(rows: list[tuple[str, str]], styles: dict[str, ParagraphStyle], width: float) -> Table:
    data: list[list[Any]] = []
    for label, value in rows:
        data.append(
            [
                Paragraph(f"<b>{_esc(label)}:</b>", styles["label"]),
                Paragraph(_esc(value or "—"), styles["body"]),
            ]
        )

    table = Table(data, colWidths=[1.55 * inch, width - 1.55 * inch], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _make_support_table(items: list[dict[str, Any]], styles: dict[str, ParagraphStyle]) -> Table:
    if not items:
        rows = [[Paragraph("No support devices selected.", styles["body"])]]
        table = Table(rows, colWidths=[3.35 * inch], hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.5, MID_GREY),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return table

    rows: list[list[Any]] = [
        [
            Paragraph("<b>Support Device</b>", styles["label"]),
            Paragraph("<b>Portable</b>", styles["label"]),
        ]
    ]
    for item in items:
        rows.append(
            [
                Paragraph(_esc(_text(item.get("name", ""))), styles["body"]),
                Paragraph(_esc(_yes_no(item.get("portable", False))), styles["body"]),
            ]
        )

    table = Table(rows, colWidths=[2.45 * inch, 0.90 * inch], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), SOFT_GREY),
                ("GRID", (0, 0), (-1, -1), 0.5, MID_GREY),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


def _make_cost_table(ta_data: dict[str, Any], styles: dict[str, ParagraphStyle]) -> Table:
    rows: list[list[Any]] = [
        [Paragraph("<b>Base Cost</b>", styles["label"]), Paragraph(_money(ta_data.get("base_cost", 0)), styles["body"])],
        [Paragraph("<b>Installation Cost</b>", styles["label"]), Paragraph(_money(ta_data.get("install_cost", 0)), styles["body"])],
        [Paragraph("<b>Support Device Cost</b>", styles["label"]), Paragraph(_money(ta_data.get("support_cost", 0)), styles["body"])],
        [Paragraph("<b>Total Cost</b>", styles["label"]), Paragraph(f"<b>{_money(ta_data.get('total_cost', 0))}</b>", styles["body"])],
    ]
    table = Table(rows, colWidths=[1.95 * inch, 1.15 * inch], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 2), PAPER),
                ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#E7D9B8")),
                ("GRID", (0, 0), (-1, -1), 0.5, MID_GREY),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


def _device_details_html(ta_data: dict[str, Any]) -> str:
    record = _safe_dict(ta_data.get("device_record", {}))
    lines: list[str] = []

    if record:
        if record.get("recharge_time"):
            lines.append(f"<b>Recharge:</b> {_esc(record.get('recharge_time'))}")
        if record.get("weight_lbs") not in (None, ""):
            lines.append(f"<b>Weight:</b> {_esc(record.get('weight_lbs'))} lbs")
        if record.get("max_area_of_effect"):
            lines.append(f"<b>Area of Effect:</b> {_esc(record.get('max_area_of_effect'))}")
        if record.get("bonus_text"):
            lines.append(f"<b>Bonus:</b> {_esc(record.get('bonus_text'))}")
        if record.get("malfunction_text"):
            lines.append(f"<b>Malfunction:</b> {_esc(record.get('malfunction_text'))}")
        if record.get("details"):
            lines.append(f"<b>Details:</b> {_esc(record.get('details'))}")

    if not lines:
        lines.append("No device detail text was saved for this entry.")

    return "<br/>".join(lines)


def _section_block(title: str, content: Any, styles: dict[str, ParagraphStyle]) -> list[Any]:
    return [
        _section_banner(title, styles),
        Spacer(1, 0.05 * inch),
        content,
        Spacer(1, 0.12 * inch),
    ]


def _build_story(character: Any, styles: dict[str, ParagraphStyle]) -> list[Any]:
    ta_data = _safe_dict(getattr(character, "ta_time_devices", {}) or {})
    support_devices = _clean_support_devices(_safe_list(ta_data.get("selected_support_devices", [])))

    device_name = _text(ta_data.get("device_name", "")).strip() or "Unnamed TA Device"
    device_category = _text(ta_data.get("device_category", "")).strip()
    mount_type = _text(ta_data.get("mount_type", "")).strip()
    vehicle_type = _text(ta_data.get("vehicle_type", "")).strip()
    notes = _text(ta_data.get("notes", "")).strip()
    image_path = _text(ta_data.get("image_path", "")).strip()

    story: list[Any] = []

    story.append(Paragraph("Time Machines & Dimension Devices (TA)", styles["title"]))
    story.append(Paragraph(_esc(device_name), styles["subtitle"]))
    story.append(
        Paragraph(
            _esc(
                " • ".join(
                    part
                    for part in [
                        device_category.replace("_", " ").title() if device_category else "",
                        mount_type.replace("_", " ").title() if mount_type else "",
                        _vehicle_type_display(vehicle_type) if vehicle_type else "",
                    ]
                    if part
                )
            ),
            styles["meta"],
        )
    )
    story.append(Spacer(1, 0.12 * inch))

    left_rows = [
        ("Device Category", device_category.replace("_", " ").title() if device_category else "—"),
        ("Mount Type", mount_type.replace("_", " ").title() if mount_type else "—"),
        ("Vehicle Type", _vehicle_type_display(vehicle_type) if vehicle_type else "—"),
        ("Character", _text(getattr(character, "name", "")).strip() or "—"),
    ]
    left_table = _make_kv_table(left_rows, styles, width=3.35 * inch)

    img = _safe_image(image_path)
    if img is None:
        image_table = Table(
            [[Paragraph("No time machine image loaded.", styles["body"])]],
            colWidths=[3.35 * inch],
            rowHeights=[2.35 * inch],
            hAlign="RIGHT",
        )
        image_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.6, MID_GREY),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ]
            )
        )
    else:
        image_table = Table([[img]], colWidths=[3.35 * inch], hAlign="RIGHT")
        image_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.6, MID_GREY),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

    top_table = Table([[left_table, image_table]], colWidths=[3.45 * inch, 3.45 * inch], hAlign="LEFT")
    top_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(top_table)
    story.append(Spacer(1, 0.16 * inch))

    details_table = Table(
        [[Paragraph(_device_details_html(ta_data), styles["body"])]],
        colWidths=[7.0 * inch],
        hAlign="LEFT",
    )
    details_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, MID_GREY),
                ("BACKGROUND", (0, 0), (-1, -1), PAPER),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.extend(_section_block("Device Details", details_table, styles))

    lower_table = Table(
        [[_make_support_table(support_devices, styles), _make_cost_table(ta_data, styles)]],
        colWidths=[3.55 * inch, 3.25 * inch],
        hAlign="LEFT",
    )
    lower_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.extend(_section_block("Support Devices and Cost Summary", lower_table, styles))

    notes_table = Table(
        [[Paragraph(_esc(notes or "No builder notes.").replace("\n", "<br/>"), styles["body"])]],
        colWidths=[7.0 * inch],
        hAlign="LEFT",
    )
    notes_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, MID_GREY),
                ("BACKGROUND", (0, 0), (-1, -1), PAPER),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.extend(_section_block("Builder Notes", notes_table, styles))

    return story


def export_ta_time_machine_pdf(character: Any, out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fonts = ExportFonts()
    styles = _build_styles(fonts)
    doc = _build_doc(out_path, fonts)
    story = _build_story(character, styles)
    doc.build(story)
    return out_path