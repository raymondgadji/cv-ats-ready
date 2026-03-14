"""
utils/cv_parser.py
US-05 / US-14 : Extraction du texte du CV uploadé.
Supporte PDF et DOCX. Aucun fichier n'est écrit sur disque.
"""

import io


def extract_text_from_cv(file_bytes: bytes, filename: str) -> str:
    """
    Extrait le texte brut d'un CV en mémoire.
    Supporte : .pdf, .doc, .docx
    US-14 : tout est traité en RAM, rien n'est persisté.
    """
    name = filename.lower()

    if name.endswith(".pdf"):
        return _extract_from_pdf(file_bytes)
    elif name.endswith(".docx"):
        return _extract_from_docx(file_bytes)
    elif name.endswith(".doc"):
        return _extract_from_doc(file_bytes)
    else:
        raise ValueError(f"Format non supporté : {filename}. Utilisez PDF ou Word (.docx).")


def _extract_from_pdf(file_bytes: bytes) -> str:
    """Extrait le texte d'un PDF avec PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts)
    except ImportError:
        # Fallback : pdfminer
        return _extract_pdf_pdfminer(file_bytes)


def _extract_pdf_pdfminer(file_bytes: bytes) -> str:
    """Fallback PDF extraction avec pdfminer.six."""
    from pdfminer.high_level import extract_text_to_fp
    from pdfminer.layout import LAParams
    output = io.StringIO()
    extract_text_to_fp(io.BytesIO(file_bytes), output, laparams=LAParams())
    return output.getvalue()


def _extract_from_docx(file_bytes: bytes) -> str:
    """Extrait le texte d'un .docx avec python-docx."""
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def _extract_from_doc(file_bytes: bytes) -> str:
    """
    Extraction basique .doc (ancien format Word).
    On tente une extraction textuelle directe.
    """
    try:
        # Tentative avec antiword via subprocess (si disponible sur le serveur)
        import subprocess
        result = subprocess.run(
            ["antiword", "-"],
            input=file_bytes,
            capture_output=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.decode("utf-8", errors="ignore")
    except Exception:
        pass

    # Dernier recours : extraction brute des strings lisibles
    text = file_bytes.decode("latin-1", errors="ignore")
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 20 and l.isprintable()]
    return "\n".join(lines[:200])
