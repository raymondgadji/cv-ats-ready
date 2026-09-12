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
    """Extrait le texte d'un PDF avec PyMuPDF (fitz), en tenant compte des colonnes."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text_parts = []
        for page in doc:
            text_parts.append(_extract_page_text_by_column(page))
        doc.close()
        return "\n".join(text_parts)
    except ImportError:
        # Fallback : pdfminer
        return _extract_pdf_pdfminer(file_bytes)


def _extract_page_text_by_column(page) -> str:
    """
    Reconstruit le texte d'une page colonne par colonne plutôt que par simple
    position verticale brute. Beaucoup de CV ont une mise en page 2 colonnes
    (bandeau latéral "Profil"/compétences + corps principal) ; un ordre de lecture
    purement top-to-bottom mélange les deux colonnes ligne par ligne et jumble le
    texte.

    Travaille au niveau du MOT (get_text("words")) et non du bloc : PyMuPDF peut
    fusionner deux colonnes situées sur la même ligne de base en un seul "bloc"
    (aucune séparation visuelle explicite pour son détecteur de blocs), ce qui
    rendrait un simple regroupement par bloc inefficace sur ce cas précis.
    """
    words = page.get_text("words")  # (x0, y0, x1, y1, word, block_no, line_no, word_no)
    if not words:
        return ""

    page_width = page.rect.width
    # Seuil de séparation de colonne : un mot est "colonne gauche" si son bord
    # gauche est dans le premier tiers de la page (heuristique tolérante aux
    # mises en page 2 colonnes classiques, sans casser les CV mono-colonne).
    threshold = page_width / 3

    left_words  = [w for w in words if w[0] < threshold]
    right_words = [w for w in words if w[0] >= threshold]

    def words_to_lines(col_words: list) -> list:
        """Regroupe les mots d'une colonne en lignes (même bande verticale), triées haut → bas puis gauche → droite."""
        col_words = sorted(col_words, key=lambda w: (round(w[1]), w[0]))
        lines = []
        current_line, current_y = [], None
        for w in col_words:
            y = w[1]
            if current_y is not None and abs(y - current_y) > 4:  # nouvelle ligne
                lines.append(" ".join(w[4] for w in current_line))
                current_line = []
            current_line.append(w)
            current_y = y
        if current_line:
            lines.append(" ".join(w[4] for w in current_line))
        return lines

    return "\n".join(words_to_lines(left_words) + words_to_lines(right_words))


def _extract_pdf_pdfminer(file_bytes: bytes) -> str:
    """Fallback PDF extraction avec pdfminer.six."""
    from pdfminer.high_level import extract_text_to_fp
    from pdfminer.layout import LAParams
    output = io.StringIO()
    extract_text_to_fp(io.BytesIO(file_bytes), output, laparams=LAParams())
    return output.getvalue()


def _extract_from_docx(file_bytes: bytes) -> str:
    """
    Extrait le texte d'un .docx avec python-docx.
    Lit aussi le contenu des tableaux : de nombreux CV construisent leur bloc
    "Profil" (ou toute la mise en page 2 colonnes) avec un tableau Word, que
    `doc.paragraphs` seul ignore silencieusement.
    """
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    parts = [p.text for p in doc.paragraphs if p.text.strip()]

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    if p.text.strip():
                        parts.append(p.text.strip())

    return "\n".join(parts)


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
