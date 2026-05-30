"""
document_extractor.py
---------------------
Extrait le texte brut depuis des fichiers uploadés via Streamlit.
Formats supportés : PDF, DOCX, XLSX/XLS, TXT, MD, CSV.
"""

import io

MAX_CHARS = 8000


def _truncate(text: str) -> str:
    if len(text) > MAX_CHARS:
        return text[:MAX_CHARS] + f"\n\n[... contenu tronqué à {MAX_CHARS} caractères]"
    return text


def extract_text(uploaded_file) -> str:
    """
    Extrait le texte depuis un objet fichier Streamlit uploadé.
    Retourne une chaîne de caractères (texte brut).
    """
    filename: str = uploaded_file.name.lower()
    raw_bytes: bytes = uploaded_file.read()

    try:
        # ── PDF ───────────────────────────────────────────────────────────
        if filename.endswith(".pdf"):
            import pdfplumber
            text_parts = []
            with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return _truncate("\n\n".join(text_parts))

        # ── Word DOCX ─────────────────────────────────────────────────────
        elif filename.endswith(".docx"):
            from docx import Document
            doc = Document(io.BytesIO(raw_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return _truncate("\n\n".join(paragraphs))

        # ── Excel XLSX / XLS ──────────────────────────────────────────────
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(raw_bytes), read_only=True, data_only=True)
            rows_text = []
            for sheet in wb.worksheets:
                rows_text.append(f"[Feuille : {sheet.title}]")
                for row in sheet.iter_rows(values_only=True):
                    cells = [str(c) if c is not None else "" for c in row]
                    if any(c.strip() for c in cells):
                        rows_text.append("\t".join(cells))
            return _truncate("\n".join(rows_text))

        # ── Texte brut : TXT, MD, CSV ─────────────────────────────────────
        elif filename.endswith((".txt", ".md", ".csv")):
            text = raw_bytes.decode("utf-8", errors="replace")
            return _truncate(text)

        else:
            return f"[Format non supporté : {uploaded_file.name}]"

    except Exception as exc:
        return (
            f"[Impossible de lire le fichier « {uploaded_file.name} » : {exc}]"
        )
