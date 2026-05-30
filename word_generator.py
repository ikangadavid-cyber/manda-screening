"""
Converts the Markdown report from the M&A agent into a .docx file
using python-docx (already in requirements.txt).
"""
import re
from io import BytesIO

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

DELIVERABLE_LABELS = {
    "complet":   "Rapport Complet",
    "fiche":     "Fiche Entreprise",
    "benchmark": "Benchmark Concurrents",
    "manda":     "Note M&A & Secteur",
    "geo":       "Analyse Géographique",
}


# ── Inline markdown parser ────────────────────────────────────────────────────

def _parse_inline(paragraph, text: str):
    """Split text on **bold**, *italic*, `code` and add styled runs."""
    pattern = r'(\*\*[^*\n]+?\*\*|\*[^*\n]+?\*|`[^`\n]+?`)'
    parts = re.split(pattern, text)
    for part in parts:
        if not part:
            continue
        if part.startswith('**') and part.endswith('**') and len(part) > 4:
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith('*') and part.endswith('*') and len(part) > 2:
            run = paragraph.add_run(part[1:-1])
            run.italic = True
        elif part.startswith('`') and part.endswith('`') and len(part) > 2:
            run = paragraph.add_run(part[1:-1])
            run.font.name = 'Courier New'
            run.font.size = Pt(9)
        else:
            paragraph.add_run(part)


def _add_border(paragraph, color='C8D4DC'):
    """Add a bottom border to a paragraph (used for horizontal rules)."""
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), color)
    pBdr.append(bottom)
    pPr.append(pBdr)


def _shade_paragraph(paragraph, fill='E8EDF2'):
    """Apply a light background fill to a paragraph."""
    pPr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill)
    pPr.append(shd)


# ── Main generator ────────────────────────────────────────────────────────────

def generate_word(markdown_text: str, company_name: str, deliverable_type: str) -> bytes:
    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin    = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin   = Cm(3.0)
        section.right_margin  = Cm(3.0)

    # ── Cover page ────────────────────────────────────────────────────────────
    label = DELIVERABLE_LABELS.get(deliverable_type, "Rapport M&A")

    cover_title = doc.add_heading('', level=0)
    cover_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = cover_title.add_run("Screening M&A")
    run.font.color.rgb = RGBColor(0x1A, 0x27, 0x44)
    run.font.size = Pt(28)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub.add_run(f"{company_name}  ·  {label}")
    sub_run.font.size = Pt(13)
    sub_run.font.color.rgb = RGBColor(0x4A, 0x7F, 0xA5)
    sub_run.bold = True

    doc.add_paragraph()  # spacer

    # ── Parse markdown body ───────────────────────────────────────────────────
    lines = markdown_text.split('\n')
    in_code_block = False
    code_lines: list = []

    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw  # keep original for code blocks

        # ── Code fence ──
        if raw.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_lines = []
            else:
                in_code_block = False
                if code_lines:
                    p = doc.add_paragraph('\n'.join(code_lines))
                    p.style = 'No Spacing'
                    for r in p.runs:
                        r.font.name = 'Courier New'
                        r.font.size = Pt(8.5)
                        r.font.color.rgb = RGBColor(0x1A, 0x27, 0x44)
                    _shade_paragraph(p)
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # ── Headings ──
        if raw.startswith('# '):
            p = doc.add_heading(raw[2:].strip(), level=1)
            for r in p.runs:
                r.font.color.rgb = RGBColor(0x1A, 0x27, 0x44)

        elif raw.startswith('## '):
            p = doc.add_heading(raw[3:].strip(), level=2)
            for r in p.runs:
                r.font.color.rgb = RGBColor(0x1A, 0x27, 0x44)

        elif raw.startswith('### '):
            p = doc.add_heading(raw[4:].strip(), level=3)
            for r in p.runs:
                r.font.color.rgb = RGBColor(0x2D, 0x5A, 0x7A)

        # ── Horizontal rule ──
        elif raw.strip() in ('---', '***', '___') or raw.strip().startswith('━━━'):
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(4)
            _add_border(p)

        # ── Blockquote ──
        elif raw.startswith('> '):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.35)
            _parse_inline(p, raw[2:])
            for r in p.runs:
                r.font.color.rgb = RGBColor(0x3A, 0x50, 0x68)
                r.italic = True

        # ── Unordered list ──
        elif re.match(r'^[-*•] ', raw):
            p = doc.add_paragraph(style='List Bullet')
            _parse_inline(p, re.sub(r'^[-*•] ', '', raw))

        # ── Ordered list ──
        elif re.match(r'^\d+\. ', raw):
            p = doc.add_paragraph(style='List Number')
            _parse_inline(p, re.sub(r'^\d+\. ', '', raw))

        # ── Empty line → small spacer ──
        elif raw.strip() == '':
            doc.add_paragraph().paragraph_format.space_after = Pt(2)

        # ── Normal paragraph ──
        else:
            p = doc.add_paragraph()
            _parse_inline(p, raw)

        i += 1

    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()
