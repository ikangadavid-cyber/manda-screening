"""
pdf_generator.py — Professional PDF generator for M&A Screening reports.
Uses reportlab to render markdown content into a polished PDF.
"""

import re
import io
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, mm
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
        Table, TableStyle, KeepTogether
    )
    from reportlab.platypus.flowables import Flowable
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# ── Color palette ─────────────────────────────────────────────────────────────
DARK_BLUE  = colors.HexColor("#1E3A5F")
ACCENT     = colors.HexColor("#2E86AB")
LIGHT_GREY = colors.HexColor("#F5F7FA")
MED_GREY   = colors.HexColor("#8A9BB0")
TEXT_BLACK = colors.HexColor("#1A1A2E")
DIVIDER    = colors.HexColor("#CBD5E1")
WHITE      = colors.white

# ── Emoji substitution map ────────────────────────────────────────────────────
EMOJI_MAP = {
    "🏢": "[E]",
    "📍": "[L]",
    "💶": "[CA]",
    "👥": "[N]",
    "🎯": "[C]",
    "🔧": "[P]",
    "🌍": "[G]",
    "📊": "[S]",
    "🔗": "[URL]",
    "✅": "[OK]",
    "❌": "[X]",
    "⚠️": "[!]",
    "⚠":  "[!]",
    # Common extras
    "📋": "[R]",
    "📰": "[N]",
    "⚔️": "[VS]",
    "⚔":  "[VS]",
    "🔍": "[>]",
    "💡": "[i]",
    "🏭": "[F]",
    "🌐": "[WEB]",
    "📈": "[UP]",
    "📉": "[DN]",
    "💰": "[€]",
    "🤝": "[+]",
    "🏆": "[*]",
    "⭐": "[*]",
    "🔑": "[KEY]",
    "📌": "[PIN]",
    "🗓": "[DATE]",
    "📅": "[DATE]",
    "➡️": "->",
    "➡":  "->",
    "•":  "-",
    "–":  "-",
    "—":  "-",
}


def strip_emojis(text: str) -> str:
    """Replace known emojis with ASCII equivalents, then strip remaining non-latin chars."""
    for emoji, replacement in EMOJI_MAP.items():
        text = text.replace(emoji, replacement)
    # Remove any remaining non-BMP characters (emoji range)
    text = re.sub(r"[\U00010000-\U0010ffff]", "", text)
    # Remove variation selectors and zero-width chars
    text = re.sub(r"[︎️​‌‍⁠]", "", text)
    return text


def escape_xml(text: str) -> str:
    """Escape characters that break reportlab XML parsing."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def safe_paragraph(text: str, style) -> "Paragraph":
    """Create a Paragraph, falling back to plain text on XML parse error."""
    try:
        return Paragraph(text, style)
    except Exception:
        try:
            return Paragraph(escape_xml(text), style)
        except Exception:
            return Paragraph(re.sub(r"<[^>]+>", "", text), style)


# ── Page number / header+footer canvas ───────────────────────────────────────
class HeaderFooterCanvas(canvas.Canvas):
    def __init__(self, *args, company_name="", report_date="", **kwargs):
        super().__init__(*args, **kwargs)
        self.company_name = company_name
        self.report_date = report_date
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_footer(total_pages)
            super().showPage()
        super().save()

    def _draw_footer(self, total_pages):
        page_num = self._saved_page_states.index(
            {k: v for k, v in self.__dict__.items() if k in self._saved_page_states[0]}
        ) if hasattr(self, "_page") else self._pageNumber

        self.saveState()
        w, h = A4

        # Footer line
        self.setStrokeColor(DIVIDER)
        self.setLineWidth(0.5)
        self.line(2 * cm, 1.5 * cm, w - 2 * cm, 1.5 * cm)

        # Footer text
        self.setFont("Helvetica", 8)
        self.setFillColor(MED_GREY)
        self.drawString(2 * cm, 1.0 * cm, f"Screening M&A — {self.company_name}")
        page_text = f"Page {self._pageNumber} / {total_pages}"
        self.drawRightString(w - 2 * cm, 1.0 * cm, page_text)
        self.drawCentredString(w / 2, 1.0 * cm, self.report_date)
        self.restoreState()


# ── Style factory ─────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()

    styles = {}

    styles["title_main"] = ParagraphStyle(
        "title_main",
        fontName="Helvetica-Bold",
        fontSize=26,
        textColor=WHITE,
        alignment=TA_CENTER,
        spaceAfter=4,
        leading=32,
    )
    styles["title_sub"] = ParagraphStyle(
        "title_sub",
        fontName="Helvetica",
        fontSize=13,
        textColor=colors.HexColor("#BFD7ED"),
        alignment=TA_CENTER,
        spaceAfter=2,
        leading=18,
    )
    styles["h2"] = ParagraphStyle(
        "h2",
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=DARK_BLUE,
        spaceBefore=18,
        spaceAfter=6,
        leading=18,
        borderPad=(0, 0, 4, 0),
    )
    styles["h3"] = ParagraphStyle(
        "h3",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=ACCENT,
        spaceBefore=12,
        spaceAfter=4,
        leading=15,
    )
    styles["body"] = ParagraphStyle(
        "body",
        fontName="Helvetica",
        fontSize=9.5,
        textColor=TEXT_BLACK,
        spaceAfter=4,
        leading=14,
    )
    styles["bullet"] = ParagraphStyle(
        "bullet",
        fontName="Helvetica",
        fontSize=9.5,
        textColor=TEXT_BLACK,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3,
        leading=14,
    )
    styles["code_block"] = ParagraphStyle(
        "code_block",
        fontName="Helvetica",
        fontSize=8.5,
        textColor=TEXT_BLACK,
        backColor=LIGHT_GREY,
        leftIndent=10,
        rightIndent=10,
        spaceBefore=4,
        spaceAfter=4,
        leading=13,
        borderWidth=1,
        borderColor=DIVIDER,
        borderPad=6,
    )
    styles["table_header"] = ParagraphStyle(
        "table_header",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=WHITE,
        alignment=TA_CENTER,
        leading=12,
    )
    styles["table_cell"] = ParagraphStyle(
        "table_cell",
        fontName="Helvetica",
        fontSize=8.5,
        textColor=TEXT_BLACK,
        alignment=TA_LEFT,
        leading=12,
    )

    return styles


# ── Cover page ────────────────────────────────────────────────────────────────
def build_cover(company_name: str, deliverable_label: str, report_date: str, styles: dict):
    elements = []
    w, _ = A4

    # Blue header block via a table
    header_data = [[
        safe_paragraph("SCREENING M&amp;A", styles["title_main"]),
    ]]
    header_table = Table(header_data, colWidths=[w - 4 * cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 28),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [DARK_BLUE]),
        ("ROUNDEDCORNERS", [6]),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.6 * cm))

    # Company name block
    company_data = [[
        safe_paragraph(escape_xml(company_name), ParagraphStyle(
            "cname",
            fontName="Helvetica-Bold",
            fontSize=20,
            textColor=DARK_BLUE,
            alignment=TA_CENTER,
            leading=26,
        ))
    ]]
    company_table = Table(company_data, colWidths=[w - 4 * cm])
    company_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LINEBELOW", (0, 0), (-1, -1), 2, ACCENT),
        ("ROUNDEDCORNERS", [4]),
    ]))
    elements.append(company_table)
    elements.append(Spacer(1, 0.4 * cm))

    # Meta info
    meta_data = [[
        safe_paragraph(f"<b>Type de rapport :</b> {escape_xml(deliverable_label)}", styles["body"]),
        safe_paragraph(f"<b>Date :</b> {report_date}", styles["body"]),
    ]]
    meta_table = Table(meta_data, colWidths=[(w - 4 * cm) / 2, (w - 4 * cm) / 2])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=DIVIDER, spaceAfter=8))

    return elements


# ── Markdown table parser ─────────────────────────────────────────────────────
def is_markdown_table_block(lines: list) -> bool:
    """Return True if lines form a markdown table."""
    if len(lines) < 2:
        return False
    has_pipe = all("|" in l for l in lines)
    has_sep = any(re.match(r"^\s*\|?[\s\-:]+\|", l) for l in lines)
    return has_pipe and has_sep


def parse_markdown_table(lines: list, styles: dict) -> Table:
    """Convert markdown table lines into a reportlab Table."""
    rows = []
    header_row = None
    for i, line in enumerate(lines):
        # Skip separator lines (---|---)
        if re.match(r"^\s*\|?[\s\-:]+\|[\s\-:|]*$", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if i == 0:
            header_row = cells
            rows.append([safe_paragraph(f"<b>{escape_xml(c)}</b>", styles["table_header"]) for c in cells])
        else:
            rows.append([safe_paragraph(escape_xml(c), styles["table_cell"]) for c in cells])

    if not rows:
        return None

    col_count = max(len(r) for r in rows)
    # Normalize column count
    for row in rows:
        while len(row) < col_count:
            row.append(safe_paragraph("", styles["table_cell"]))

    w, _ = A4
    available = w - 4 * cm
    col_width = available / col_count

    t = Table(rows, colWidths=[col_width] * col_count, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
        ("BACKGROUND", (0, 1), (-1, -1), WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ("GRID", (0, 0), (-1, -1), 0.5, DIVIDER),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


# ── Main markdown parser ──────────────────────────────────────────────────────
def parse_markdown(text: str, styles: dict) -> list:
    """Convert markdown string to list of reportlab flowables."""
    elements = []
    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # ── Markdown table block detection ───────────────────────────────
        if "|" in line:
            # Collect table block
            table_lines = []
            j = i
            while j < len(lines) and "|" in lines[j]:
                table_lines.append(lines[j])
                j += 1
            if is_markdown_table_block(table_lines):
                t = parse_markdown_table(table_lines, styles)
                if t:
                    elements.append(Spacer(1, 4))
                    elements.append(t)
                    elements.append(Spacer(1, 6))
                i = j
                continue

        # ── Code / fiche blocks (━━━ lines or ``` blocks) ───────────────
        if line.strip().startswith("```") or re.match(r"^[━=]{5,}", line.strip()):
            # Collect until closing ``` or next ━ section
            block_lines = []
            if line.strip().startswith("```"):
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    block_lines.append(strip_emojis(lines[i]))
                    i += 1
            else:
                # It's a ━━━ line — treat single line as divider
                elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=4, spaceBefore=8))
                i += 1
                continue

            if block_lines:
                block_text = "<br/>".join(escape_xml(l) for l in block_lines)
                elements.append(safe_paragraph(block_text, styles["code_block"]))
                elements.append(Spacer(1, 4))
            i += 1
            continue

        # ── Horizontal rule ───────────────────────────────────────────────
        if re.match(r"^\s*[-*_]{3,}\s*$", line):
            elements.append(Spacer(1, 4))
            elements.append(HRFlowable(width="100%", thickness=1, color=DIVIDER, spaceAfter=6))
            i += 1
            continue

        # ── H2 heading ── ## ... ─────────────────────────────────────────
        m = re.match(r"^##\s+(.+)$", line)
        if m:
            heading_text = strip_emojis(m.group(1))
            # Accent bar
            elements.append(Spacer(1, 6))
            bar_data = [[safe_paragraph(escape_xml(heading_text), styles["h2"])]]
            bar_table = Table(bar_data, colWidths=[A4[0] - 4 * cm])
            bar_table.setStyle(TableStyle([
                ("LINEBEFOREBEFORE", (0, 0), (0, 0), 4, ACCENT),
                ("LINEBEFORE", (0, 0), (0, 0), 4, ACCENT),
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ]))
            elements.append(bar_table)
            elements.append(Spacer(1, 4))
            i += 1
            continue

        # ── H3 heading ── ### ... ────────────────────────────────────────
        m = re.match(r"^###\s+(.+)$", line)
        if m:
            heading_text = strip_emojis(m.group(1))
            elements.append(safe_paragraph(escape_xml(heading_text), styles["h3"]))
            i += 1
            continue

        # ── H1 heading ── # ... ──────────────────────────────────────────
        m = re.match(r"^#\s+(.+)$", line)
        if m:
            heading_text = strip_emojis(m.group(1))
            elements.append(safe_paragraph(f"<b>{escape_xml(heading_text)}</b>", styles["h2"]))
            i += 1
            continue

        # ── Bullet point ─────────────────────────────────────────────────
        m = re.match(r"^\s*[-*+]\s+(.+)$", line)
        if m:
            bullet_text = strip_emojis(m.group(1))
            bullet_text = apply_inline_markup(bullet_text)
            elements.append(safe_paragraph(f"• {bullet_text}", styles["bullet"]))
            i += 1
            continue

        # ── Numbered list ────────────────────────────────────────────────
        m = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if m:
            item_text = strip_emojis(m.group(1))
            item_text = apply_inline_markup(item_text)
            num = re.match(r"^\s*(\d+)", line).group(1)
            elements.append(safe_paragraph(f"{num}. {item_text}", styles["bullet"]))
            i += 1
            continue

        # ── Empty line ───────────────────────────────────────────────────
        if line.strip() == "":
            elements.append(Spacer(1, 5))
            i += 1
            continue

        # ── Normal paragraph ─────────────────────────────────────────────
        para_text = strip_emojis(line)
        para_text = apply_inline_markup(para_text)
        elements.append(safe_paragraph(para_text, styles["body"]))
        i += 1

    return elements


def apply_inline_markup(text: str) -> str:
    """Convert markdown inline markup to reportlab XML tags."""
    text = escape_xml(text)
    # Bold: **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)
    # Italic: *text* or _text_
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", r"<i>\1</i>", text)
    # Inline code: `text`
    text = re.sub(r"`(.+?)`", r"<font name='Helvetica'>\1</font>", text)
    # Links: [text](url) → text (url)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1 (\2)", text)
    return text


# ── Public API ────────────────────────────────────────────────────────────────
DELIVERABLE_LABELS = {
    "complet":    "Rapport Complet",
    "fiche":      "Fiche Entreprise",
    "benchmark":  "Benchmark Concurrents",
    "manda":      "Note M&A & Secteur",
    "geo":        "Analyse Géographique",
}


def generate_pdf(markdown_text: str, company_name: str, deliverable_type: str = "complet") -> bytes:
    """
    Generate a PDF from a markdown string.

    Args:
        markdown_text:    Full report as markdown.
        company_name:     Company name for header/footer.
        deliverable_type: One of complet/fiche/benchmark/manda/geo.

    Returns:
        PDF as bytes.
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab is not installed. Run: pip install reportlab")

    report_date = datetime.now().strftime("%d/%m/%Y")
    deliverable_label = DELIVERABLE_LABELS.get(deliverable_type, deliverable_type)

    buffer = io.BytesIO()

    # Custom canvas class with company name and date bound
    class BoundCanvas(HeaderFooterCanvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, company_name=company_name, report_date=report_date, **kwargs)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
        title=f"Screening M&A — {company_name}",
        author="Screening M&A Tool",
        subject=deliverable_label,
    )

    styles = make_styles()
    story = []

    # Cover / header section
    story.extend(build_cover(company_name, deliverable_label, report_date, styles))

    # Body content
    try:
        content_elements = parse_markdown(markdown_text, styles)
        story.extend(content_elements)
    except Exception:
        # Fallback: plain text rendering
        plain = strip_emojis(markdown_text)
        for para in plain.split("\n\n"):
            if para.strip():
                story.append(safe_paragraph(escape_xml(para.strip()), styles["body"]))
                story.append(Spacer(1, 6))

    try:
        doc.build(story, canvasmaker=BoundCanvas)
    except Exception:
        # Last-resort fallback: build with plain text only
        buffer = io.BytesIO()
        doc2 = SimpleDocTemplate(buffer, pagesize=A4)
        plain_story = []
        for chunk in markdown_text.split("\n\n"):
            chunk = strip_emojis(chunk.strip())
            if chunk:
                try:
                    plain_story.append(Paragraph(escape_xml(chunk), styles["body"]))
                except Exception:
                    pass
                plain_story.append(Spacer(1, 6))
        doc2.build(plain_story)

    buffer.seek(0)
    return buffer.read()
