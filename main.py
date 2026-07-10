"""
main.py — Backend FastAPI CV ATS
v1.3.0 — PostgreSQL + CORS sécurisé cv-ats.com
"""

import os
import io
import json
import secrets
import datetime

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

import stripe
import psycopg2
from psycopg2.extras import RealDictCursor

from utils.cv_parser import extract_text_from_cv
from utils.ai_agent import optimize_cv_ats, generate_cover_letter
from utils.exporter import export_to_pdf, export_to_docx

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
stripe.api_key        = os.environ.get("STRIPE_SECRET_KEY", "")
ANTHROPIC_API_KEY     = os.environ.get("ANTHROPIC_API_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_URL          = os.environ.get("FRONTEND_URL", "http://localhost:3000")
ADMIN_SECRET          = os.environ.get("ADMIN_SECRET", "cv-ats-admin-2026")
DATABASE_URL          = os.environ.get("DATABASE_URL", "")

PROMO_CODES = {
    "TEST_CV_ATS_READY": ("free",    0),
    "BETA50":            ("percent", 50),
    "LAUNCH20":          ("percent", 20),
}

VALID_FREE_TOKENS: set[str] = set()

# ─────────────────────────────────────────
# POSTGRESQL
# ─────────────────────────────────────────

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    if not DATABASE_URL:
        print("⚠️  DATABASE_URL manquante — logs PostgreSQL désactivés")
        return
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id    SERIAL PRIMARY KEY,
                ts    TIMESTAMPTZ DEFAULT NOW(),
                event TEXT NOT NULL,
                data  JSONB
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ PostgreSQL — table logs prête")
    except Exception as e:
        print(f"❌ PostgreSQL init error : {e}")


def write_log(event: str, data: dict):
    if not DATABASE_URL:
        return
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO logs (event, data) VALUES (%s, %s)",
            (event, json.dumps(data, ensure_ascii=False))
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️  Log DB error : {e}")


def get_logs_from_db(limit: int = 500) -> list:
    if not DATABASE_URL:
        return []
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "SELECT ts, event, data FROM logs ORDER BY ts DESC LIMIT %s",
            (limit,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [
            {"ts": row["ts"].isoformat() + "Z", "event": row["event"], **row["data"]}
            for row in rows
        ]
    except Exception as e:
        print(f"⚠️  Get logs error : {e}")
        return []


# ─────────────────────────────────────────
# APP
# ─────────────────────────────────────────
app = FastAPI(title="CV ATS API", version="1.3.0")

# ✅ CORS sécurisé — domaines autorisés uniquement
ALLOWED_ORIGINS = [
    "https://cv-ats.com",
    "https://www.cv-ats.com",
    "https://cv-ats-ready.fr",           # ancien domaine — garde pendant transition
    "https://www.cv-ats-ready.fr",
    "https://cv-ats-ready.netlify.app",  # Netlify preview
    "http://localhost:3000",             # dev local
    "http://localhost:5500",             # Live Server VS Code
    "http://127.0.0.1:5500",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────

@app.get("/api/health")
def health():
    db_ok = False
    if DATABASE_URL:
        try:
            conn = get_db()
            conn.close()
            db_ok = True
        except Exception:
            pass
    return {
        "status":  "ok",
        "service": "cv-ats",
        "version": "1.3.0",
        "db":      "postgresql ✅" if db_ok else "postgresql ❌ non connecté",
    }


@app.post("/api/fetch-url")
async def fetch_url(url: str = Form(...)):
    """
    Récupère le texte d'une offre d'emploi depuis une URL.
    Extrait uniquement l'offre principale, ignore les suggestions.
    """
    import httpx
    import re

    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL invalide — elle doit commencer par https://")

    BLOCKED_DOMAINS = [
        "facebook.com", "instagram.com", "tiktok.com", "twitter.com", "x.com",
        "paypal.com", "stripe.com", "amazon.com", "google.com", "youtube.com",
    ]
    if any(d in url for d in BLOCKED_DOMAINS):
        raise HTTPException(status_code=400, detail="URL non supportée.")

    LIST_PATTERNS = [
        r"francetravail\.fr/offres/recherche$",
        r"francetravail\.fr/offres/recherche\?",
        r"indeed\.[a-z]+/jobs[^/]",
        r"linkedin\.com/jobs/search",
        r"hellowork\.com/fr-fr/emploi/?$",
        r"hellowork\.com/fr-fr/emploi\?",
    ]
    for pattern in LIST_PATTERNS:
        if re.search(pattern, url):
            raise HTTPException(
                status_code=400,
                detail="Cette URL pointe vers une liste d'offres. Ouvre une offre spécifique et copie son URL."
            )

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        }
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            resp = await client.get(url, headers=headers)

        if resp.status_code == 403:
            if "linkedin" in url:
                detail = "LinkedIn bloque la récupération automatique. Copiez-collez le texte de l'offre directement depuis la page."
            elif "indeed" in url:
                detail = "Indeed bloque la récupération automatique. Copiez-collez le texte de l'offre directement depuis la page."
            else:
                detail = "Ce site bloque la récupération automatique. Copiez-collez le texte de l'offre directement dans le champ."
            raise HTTPException(status_code=400, detail=detail)

        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Impossible d'accéder à la page (erreur {resp.status_code}). Copiez-collez le texte.")

        html_content = resp.text

        for tag in ['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript', 'iframe', 'svg', 'form']:
            html_content = re.sub(rf'<{tag}[^>]*>.*?</{tag}>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = re.sub(r'&nbsp;',  ' ',  text)
        text = re.sub(r'&amp;',   '&',  text)
        text = re.sub(r'&lt;',    '<',  text)
        text = re.sub(r'&gt;',    '>',  text)
        text = re.sub(r'&quot;',  '"',  text)
        text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
        text = re.sub(r'[ \t]+',  ' ',  text)
        text = re.sub(r'\n{3,}',  '\n\n', text)
        text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
        text = text.strip()

        CUT_MARKERS = [
            "D'autres offres peuvent vous intéresser",
            "Découvrez d'autres services",
            "Afficher plus d'offres",
            "Voir plus de services",
            "Offres partenaires",
            "Besoin d'aide sur la recherche",
            "Similar jobs", "Jobs you might like", "More jobs like this",
            "Recommended jobs", "People also viewed",
            "Vous aimerez aussi", "Offres similaires", "Postes similaires",
        ]
        for marker in CUT_MARKERS:
            if marker in text:
                text = text[:text.index(marker)].strip()
                break

        if len(text) < 100:
            if "adecco" in url:
                msg = "Adecco charge son contenu dynamiquement. Copiez-collez le texte de l'offre, ou utilisez l'URL directe du type : adecco.fr/offre-emploi/titre-du-poste-ville-..."
            elif "linkedin" in url:
                msg = "LinkedIn bloque la récupération automatique. Copiez-collez le texte de l'offre directement depuis la page."
            elif "indeed" in url:
                msg = "Indeed bloque la récupération automatique. Copiez-collez le texte de l'offre directement depuis la page."
            elif "welcometothejungle" in url:
                msg = "Welcome to the Jungle charge son contenu dynamiquement. Copiez-collez le texte de l'offre directement."
            else:
                msg = "Ce site charge son contenu dynamiquement — la récupération automatique ne fonctionne pas. Copiez-collez le texte de l'offre directement dans le champ."
            raise HTTPException(status_code=400, detail=msg)

        text = text[:6000]
        return {"text": text, "url": url, "length": len(text)}

    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Timeout — page trop lente. Copiez-collez le texte directement.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur : {str(e)}. Copiez-collez le texte directement.")


@app.post("/api/create-payment-intent")
async def create_payment_intent(
    request: Request,
    promo_code: str = Form(""),
):
    amount        = 120
    promo_valid   = False
    promo_message = ""
    free          = False
    free_token    = ""
    client_secret = ""
    discount_pct  = 0

    code = promo_code.strip().upper()
    if code and code in PROMO_CODES:
        promo_type, promo_value = PROMO_CODES[code]
        promo_valid = True
        if promo_type == "free":
            free          = True
            free_token    = secrets.token_urlsafe(32)
            VALID_FREE_TOKENS.add(free_token)
            promo_message = f"✅ Code {code} : accès 100% gratuit !"
        elif promo_type == "percent":
            discount_pct  = promo_value
            amount        = int(amount * (1 - discount_pct / 100))
            promo_message = f"✅ Code {code} : -{discount_pct}% appliqué !"
    elif code:
        raise HTTPException(status_code=400, detail=f"Code promo invalide : {code}")

    if not free:
        try:
            intent = stripe.PaymentIntent.create(
                amount   = max(amount, 50),
                currency = "eur",
                metadata = {"promo_code": code, "service": "cv-ats"},
            )
            client_secret = intent.client_secret
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))

    write_log("payment_init", {
        "promo_code":   code or None,
        "free":         free,
        "amount_cents": 0 if free else amount,
        "ip":           request.client.host if request.client else "unknown",
        "origin":       request.headers.get("origin", "unknown"),
    })

    return {
        "client_secret": client_secret,
        "amount":        amount,
        "promo_valid":   promo_valid,
        "promo_message": promo_message,
        "free":          free,
        "free_token":    free_token,
        "discount_pct":  discount_pct,
    }


from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.platypus import Flowable


def hex_to_color(hex_str: str):
    """Convertit un code hex en couleur ReportLab."""
    hex_str = hex_str.strip()
    if not hex_str.startswith("#"):
        hex_str = "#" + hex_str
    try:
        return HexColor(hex_str)
    except Exception:
        return HexColor("#FF6B00")


def _parse_cv_sections(cv_text: str) -> dict:
    """Parse le texte du CV en sections."""
    sections = {"header": [], "experience": [], "formation": [], "competences": [], "autres": []}
    current = "header"
    lines = cv_text.strip().split("\n")
    section_map = {
        "expérience": "experience", "experience": "experience",
        "formation": "formation", "éducation": "formation", "education": "formation",
        "compétences": "competences", "competences": "competences", "skills": "competences",
    }
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        lower = line_clean.lower()
        matched = False
        for key, sec in section_map.items():
            if key in lower and len(line_clean) < 60:
                current = sec
                matched = True
                break
        if not matched:
            sections[current].append(line_clean)
    return sections


def export_to_pdf_template(
    cv_text: str,
    cover_letter: str = "",
    template: str = "moderne",
    color: str = "#FF6B00",
    bg_color: str = "#0C0C18",
) -> bytes:
    """Génère un PDF avec template visuel (moderne ou classique)."""
    buffer = io.BytesIO()
    accent = hex_to_color(color)
    bg = hex_to_color(bg_color)
    sections = _parse_cv_sections(cv_text)
    styles = getSampleStyleSheet()

    if template == "moderne":
        # ── TEMPLATE MODERNE — Sidebar colorée gauche + fond sombre droite
        doc = SimpleDocTemplate(buffer, pagesize=A4,
            rightMargin=1.5*cm, leftMargin=1.5*cm,
            topMargin=1.5*cm, bottomMargin=1.5*cm)

        story = []
        body = ParagraphStyle('body', parent=styles['Normal'], fontSize=9,
            textColor=white, fontName='Helvetica', leading=13, spaceAfter=4)
        title = ParagraphStyle('title', parent=styles['Normal'], fontSize=11,
            textColor=accent, fontName='Helvetica-Bold', leading=14, spaceBefore=8, spaceAfter=4)
        name_style = ParagraphStyle('name', parent=styles['Normal'], fontSize=16,
            textColor=white, fontName='Helvetica-Bold', leading=18)

        # Header
        header_text = "\n".join(sections["header"][:3]) if sections["header"] else "CV Optimisé"
        name_line = sections["header"][0] if sections["header"] else "Candidat"

        header_data = [[
            Paragraph(name_line, name_style),
        ]]
        header_table = Table(header_data, colWidths=[17*cm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), bg),
            ('TOPPADDING', (0,0), (-1,-1), 14),
            ('BOTTOMPADDING', (0,0), (-1,-1), 14),
            ('LEFTPADDING', (0,0), (-1,-1), 16),
            ('ROUNDEDCORNERS', [8,8,0,0]),
        ]))
        story.append(header_table)

        # Body — sidebar gauche (accent) + contenu droite
        def make_section(title_text, lines):
            if not lines:
                return None
            left_content = Paragraph(title_text.upper(), ParagraphStyle('st',
                parent=styles['Normal'], fontSize=8, textColor=white,
                fontName='Helvetica-Bold', leading=10))
            # Limiter le contenu pour éviter les débordements
            right_paras = []
            for l in lines[:30]:  # max 30 lignes par section
                if l.strip():
                    right_paras.append(Paragraph(l[:200], body))  # max 200 chars par ligne
            if not right_paras:
                right_paras = [Paragraph("—", body)]
            # Une ligne par tableau séparé pour éviter les cellules trop grandes
            result = []
            first = True
            for para in right_paras:
                row = [[left_content if first else Paragraph("", ParagraphStyle('empty',
                    parent=styles['Normal'], fontSize=1)), para]]
                t = Table(row, colWidths=[4*cm, 13*cm])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (0,-1), accent),
                    ('BACKGROUND', (1,0), (1,-1), bg),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('TOPPADDING', (0,0), (-1,-1), 4),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('LEFTPADDING', (0,0), (-1,-1), 10),
                ]))
                result.append(t)
                first = False
            return result

        for sec_title, sec_key in [
            ("Expérience", "experience"),
            ("Formation", "formation"),
            ("Compétences", "competences"),
            ("Autres", "autres"),
        ]:
            result = make_section(sec_title, sections[sec_key])
            if result:
                for t in result:
                    story.append(t)

        # Footer
        footer_data = [[Paragraph("CV généré par CV-ATS.COM", ParagraphStyle('ft',
            parent=styles['Normal'], fontSize=7, textColor=HexColor('#888899'),
            fontName='Helvetica', alignment=1))]]
        footer_table = Table(footer_data, colWidths=[17*cm])
        footer_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), bg),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('ROUNDEDCORNERS', [0,0,8,8]),
        ]))
        story.append(footer_table)

        # Lettre de motivation si présente
        if cover_letter.strip():
            story.append(Spacer(1, 16))
            lm_title = Paragraph("LETTRE DE MOTIVATION", ParagraphStyle('lmt',
                parent=styles['Normal'], fontSize=12, textColor=accent,
                fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=8))
            story.append(lm_title)
            for line in cover_letter.split("\n"):
                if line.strip():
                    story.append(Paragraph(line.strip(), ParagraphStyle('lmb',
                        parent=styles['Normal'], fontSize=9, textColor=white,
                        fontName='Helvetica', leading=14, spaceAfter=4,
                        alignment=TA_JUSTIFY)))

        doc.build(story)

    else:
        # ── TEMPLATE CLASSIQUE — Fond blanc, ligne accent, typo sobre
        doc = SimpleDocTemplate(buffer, pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm)

        story = []
        DARK = HexColor('#1a1a1a')
        body_cl = ParagraphStyle('body_cl', parent=styles['Normal'], fontSize=10,
            textColor=DARK, fontName='Helvetica', leading=14, spaceAfter=4,
            alignment=TA_JUSTIFY)
        title_cl = ParagraphStyle('title_cl', parent=styles['Normal'], fontSize=11,
            textColor=accent, fontName='Helvetica-Bold', leading=14,
            spaceBefore=12, spaceAfter=4)
        name_cl = ParagraphStyle('name_cl', parent=styles['Normal'], fontSize=18,
            textColor=DARK, fontName='Helvetica-Bold', leading=20, spaceAfter=2)

        # Nom
        name_line = sections["header"][0] if sections["header"] else "Candidat"
        story.append(Paragraph(name_line, name_cl))

        # Ligne accent
        story.append(HRFlowable(width="100%", thickness=2, color=accent, spaceAfter=6))

        # Infos contact
        for line in sections["header"][1:4]:
            story.append(Paragraph(line, ParagraphStyle('contact',
                parent=styles['Normal'], fontSize=9, textColor=HexColor('#555555'),
                fontName='Helvetica', leading=12)))

        story.append(Spacer(1, 8))

        # Sections
        for sec_title, sec_key in [
            ("Expérience Professionnelle", "experience"),
            ("Formation", "formation"),
            ("Compétences", "competences"),
            ("Autres", "autres"),
        ]:
            if not sections[sec_key]:
                continue
            story.append(Paragraph(sec_title.upper(), title_cl))
            story.append(HRFlowable(width="100%", thickness=1, color=accent, spaceAfter=6))
            for line in sections[sec_key]:
                if line.strip():
                    story.append(Paragraph(line, body_cl))

        # Lettre de motivation
        if cover_letter.strip():
            story.append(Spacer(1, 16))
            story.append(Paragraph("LETTRE DE MOTIVATION", title_cl))
            story.append(HRFlowable(width="100%", thickness=1, color=accent, spaceAfter=6))
            for line in cover_letter.split("\n"):
                if line.strip():
                    story.append(Paragraph(line.strip(), body_cl))

        # Footer
        story.append(Spacer(1, 12))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#cccccc'), spaceAfter=4))
        story.append(Paragraph("CV généré par CV-ATS.COM", ParagraphStyle('ft',
            parent=styles['Normal'], fontSize=7, textColor=HexColor('#aaaaaa'),
            fontName='Helvetica', alignment=1)))

        doc.build(story)

    buffer.seek(0)
    return buffer.read()


@app.post("/api/optimize")
async def optimize(
    request: Request,
    job_offer:              str        = Form(...),
    cv_file:                UploadFile = File(...),
    payment_intent_id:      str        = Form(""),
    free_token:             str        = Form(""),
    wants_cover_letter:     str        = Form("false"),
    cover_letter_style:     str        = Form("neutre & professionnel"),
    cover_letter_precision: str        = Form(""),
    export_format:          str        = Form("texte"),
    edited_cv:              str        = Form(""),
    edited_lm:              str        = Form(""),
    cv_template:            str        = Form("aucun"),
    cv_template_color:      str        = Form("#FF6B00"),
    cv_template_bg:         str        = Form("#0C0C18"),
):
    paid = False
    if free_token:
        if free_token in VALID_FREE_TOKENS:
            paid = True
            VALID_FREE_TOKENS.discard(free_token)
        else:
            paid = True  # BYPASS BÊTA
    elif payment_intent_id:
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if intent.status == "succeeded":
                paid = True
        except stripe.error.StripeError:
            pass

    if not paid:
        raise HTTPException(status_code=402, detail="Paiement non confirmé.")

    cv_bytes = await cv_file.read()
    try:
        cv_text = extract_text_from_cv(cv_bytes, cv_file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if len(cv_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Le CV semble vide ou illisible.")

    try:
        result       = optimize_cv_ats(cv_text=cv_text, job_offer=job_offer, api_key=ANTHROPIC_API_KEY)
        optimized_cv = result["cv_optimized"]
        ats_score    = result["ats_score"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur IA : {str(e)}")

    cover_letter = ""
    if wants_cover_letter.lower() == "true":
        if edited_lm.strip():
            cover_letter = edited_lm.strip()
        else:
            try:
                cover_letter = generate_cover_letter(
                    cv_text=cv_text, job_offer=job_offer,
                    style=cover_letter_style or "neutre & professionnel",
                    precision=cover_letter_precision, api_key=ANTHROPIC_API_KEY,
                )
            except Exception as e:
                cover_letter = f"[Erreur génération lettre : {str(e)}]"

    final_cv = edited_cv.strip() if edited_cv.strip() else optimized_cv

    write_log("optimize", {
        "format":      export_format,
        "wants_lm":    wants_cover_letter == "true",
        "lm_style":    cover_letter_style if wants_cover_letter == "true" else None,
        "score_avant": ats_score.get("score_avant") if ats_score else None,
        "score_apres": ats_score.get("score_apres") if ats_score else None,
        "cv_edited":   bool(edited_cv.strip()),
        "lm_edited":   bool(edited_lm.strip()),
        "promo":       bool(free_token),
        "paid_stripe": bool(payment_intent_id),
        "ip":          request.client.host if request.client else "unknown",
        "origin":      request.headers.get("origin", "unknown"),
    })

    fmt = export_format.lower().strip()
    tpl = cv_template.lower().strip()

    if fmt == "texte":
        return JSONResponse({"cv_optimized": final_cv, "cover_letter": cover_letter, "ats_score": ats_score})
    elif fmt == "pdf":
        # Générer PDF avec template si demandé
        if tpl in ("moderne", "classique"):
            pdf_bytes = export_to_pdf_template(
                cv_text=final_cv,
                cover_letter=cover_letter,
                template=tpl,
                color=cv_template_color,
                bg_color=cv_template_bg,
            )
        else:
            pdf_bytes = export_to_pdf(final_cv, cover_letter)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="cv-ats.pdf"',
                "X-ATS-Score-Avant":  str(ats_score.get("score_avant", 0)),
                "X-ATS-Score-Apres":  str(ats_score.get("score_apres", 0)),
            }
        )
    elif fmt in ("word", "docx"):
        docx_bytes = export_to_docx(final_cv, cover_letter)
        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": 'attachment; filename="cv-ats.docx"',
                "X-ATS-Score-Avant":  str(ats_score.get("score_avant", 0)),
                "X-ATS-Score-Apres":  str(ats_score.get("score_apres", 0)),
            }
        )
    else:
        raise HTTPException(status_code=400, detail=f"Format non supporté : {fmt}")


@app.post("/api/autopilot")
async def autopilot(
    request:           Request,
    cv_optimized:      str = Form(...),
    job_offer:         str = Form(...),
    payment_intent_id: str = Form(""),
    free_token:        str = Form(""),
    nb_offres:         int = Form(40),
):
    paid = False
    if free_token:
        if free_token in VALID_FREE_TOKENS:
            paid = True
            VALID_FREE_TOKENS.discard(free_token)
        else:
            paid = True  # BYPASS BÊTA
    elif payment_intent_id:
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if intent.status == "succeeded":
                paid = True
        except stripe.error.StripeError:
            pass

    if not paid:
        raise HTTPException(status_code=402, detail="Plan Autopilot requis. Abonnez-vous pour 19,99€/mois.")

    if len(cv_optimized.strip()) < 50:
        raise HTTPException(status_code=400, detail="CV optimisé invalide.")

    try:
        from utils.autopilot import find_matching_jobs
        results = find_matching_jobs(
            cv_optimized=cv_optimized,
            job_offer=job_offer,
            nb_total=min(nb_offres, 60),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Autopilot : {str(e)}")

    write_log("autopilot", {
        "total_offres":   results["total"],
        "france_travail": results["france_travail"],
        "adzuna":         results["adzuna"],
        "poste_detecte":  results["keywords"]["poste"],
        "localisation":   results["keywords"]["localisation"],
        "ip":             request.client.host if request.client else "unknown",
        "origin":         request.headers.get("origin", "unknown"),
    })

    return JSONResponse(results)


@app.get("/api/admin/logs")
async def get_logs(secret: str = ""):
    if secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Accès refusé")

    logs = get_logs_from_db(limit=500)

    total_opts   = sum(1 for l in logs if l["event"] == "optimize")
    total_pays   = sum(1 for l in logs if l["event"] == "payment_init")
    formats      = {}
    lm_count     = 0
    edited_count = 0
    scores_apres = []

    for l in logs:
        if l["event"] == "optimize":
            fmt = l.get("format", "?")
            formats[fmt] = formats.get(fmt, 0) + 1
            if l.get("wants_lm"):    lm_count += 1
            if l.get("cv_edited"):   edited_count += 1
            if l.get("score_apres"): scores_apres.append(l["score_apres"])

    avg_score = round(sum(scores_apres) / len(scores_apres), 1) if scores_apres else 0

    return JSONResponse({
        "resume": {
            "total_optimisations":   total_opts,
            "total_paiements_init":  total_pays,
            "lettres_generees":      lm_count,
            "cv_edites_par_user":    edited_count,
            "score_ats_moyen_apres": avg_score,
            "formats":               formats,
            "source":                "postgresql ✅ persistant",
        },
        "derniers_logs": logs[:50],
    })


@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request):
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not STRIPE_WEBHOOK_SECRET:
        return JSONResponse({"status": "webhook secret not configured"})

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event["type"] == "payment_intent.succeeded":
        pi = event["data"]["object"]
        write_log("payment_succeeded", {
            "payment_intent_id": pi["id"],
            "amount_cents":      pi["amount"],
            "promo_code":        pi.get("metadata", {}).get("promo_code"),
        })

    return JSONResponse({"status": "ok"})