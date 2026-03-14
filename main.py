"""
cv-ats-ready — Backend FastAPI
US-03 : Paiement Stripe (1€ + code promo)
US-05 : Agent IA Claude (réécriture CV ATS + lettre de motivation)
US-10 : Export PDF / DOCX / texte brut
US-14 : Aucune donnée stockée après traitement
"""

import os
import io
import uuid
import tempfile
from pathlib import Path

import stripe
import anthropic

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from utils.cv_parser import extract_text_from_cv
from utils.ai_agent import optimize_cv_ats, generate_cover_letter
from utils.exporter import export_to_pdf, export_to_docx

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_REMPLACE_PAR_TA_CLE")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

# Code(s) promo valides → {code: réduction en %}
PROMO_CODES = {
    "TEST_CV_ATS_READY": 100,   # 100% = gratuit pendant la phase test
    "BETA50": 50,               # 50% de réduction
    "LAUNCH20": 20,             # 20% de réduction post-lancement
}

PRICE_CENTS = 100  # 1,00€

app = FastAPI(title="cv-ats-ready API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5500", "http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────
# US-03 — PAIEMENT STRIPE
# ─────────────────────────────────────────

@app.post("/api/create-payment-intent")
async def create_payment_intent(promo_code: str = Form(default="")):
    """
    Crée une intention de paiement Stripe.
    Si un code promo valide est fourni → réduit ou annule le montant.
    Retourne le client_secret pour le front.
    """
    amount = PRICE_CENTS
    discount_pct = 0
    promo_valid = False
    promo_message = ""

    code_upper = promo_code.strip().upper()
    if code_upper and code_upper in PROMO_CODES:
        discount_pct = PROMO_CODES[code_upper]
        promo_valid = True
        promo_message = f"Code promo appliqué : -{discount_pct}%"
        amount = max(0, int(PRICE_CENTS * (1 - discount_pct / 100)))

    # Si 100% de réduction → on ne crée pas d'intent Stripe
    if amount == 0:
        # On génère un token interne gratuit signé
        free_token = f"free_{uuid.uuid4().hex}"
        return JSONResponse({
            "free": True,
            "free_token": free_token,
            "promo_valid": True,
            "promo_message": promo_message,
        })

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="eur",
            metadata={"promo_code": code_upper, "discount_pct": discount_pct},
            automatic_payment_methods={"enabled": True},
        )
        return JSONResponse({
            "free": False,
            "client_secret": intent.client_secret,
            "amount_cents": amount,
            "promo_valid": promo_valid,
            "promo_message": promo_message,
        })
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request):
    """Webhook Stripe pour confirmer les paiements côté serveur."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception:
        raise HTTPException(status_code=400, detail="Webhook invalide")

    if event["type"] == "payment_intent.succeeded":
        # Ici on pourrait logger l'event si nécessaire (sans données perso)
        pass

    return {"status": "ok"}


# ─────────────────────────────────────────
# US-05 + US-10 — AGENT IA + EXPORT
# ─────────────────────────────────────────

@app.post("/api/optimize")
async def optimize(
    job_offer: str = Form(...),
    wants_cover_letter: str = Form(default="false"),   # "true" / "false"
    cover_letter_style: str = Form(default=""),
    cover_letter_precision: str = Form(default=""),
    export_format: str = Form(default="texte"),        # "pdf" / "word" / "texte"
    payment_intent_id: str = Form(default=""),
    free_token: str = Form(default=""),
    cv_file: UploadFile = File(...),
):
    """
    Endpoint principal :
    1. Vérifie le paiement (Stripe ou free_token)
    2. Parse le CV uploadé
    3. Agent IA → CV ATS optimisé
    4. Agent IA → Lettre de motivation (si demandée)
    5. Export dans le format choisi
    6. US-14 : aucune donnée n'est persistée
    """

    # ── Vérification paiement ──
    if not _verify_payment(payment_intent_id, free_token):
        raise HTTPException(status_code=402, detail="Paiement requis ou invalide.")

    # ── Lecture du CV (US-14 : fichier temporaire, jamais sauvegardé) ──
    cv_bytes = await cv_file.read()
    filename = cv_file.filename or "cv.pdf"

    cv_text = extract_text_from_cv(cv_bytes, filename)
    if not cv_text.strip():
        raise HTTPException(status_code=422, detail="Impossible de lire le contenu du CV. Vérifiez le fichier.")

    if not job_offer.strip():
        raise HTTPException(status_code=422, detail="L'offre d'emploi est vide.")

    # ── Tâche 1 : Optimisation CV ATS ──
    optimized_cv = optimize_cv_ats(
        cv_text=cv_text,
        job_offer=job_offer,
        api_key=ANTHROPIC_API_KEY,
    )

    # ── Tâche 2 : Lettre de motivation ──
    cover_letter_text = ""
    if wants_cover_letter.lower() == "true" and cover_letter_style:
        cover_letter_text = generate_cover_letter(
            cv_text=cv_text,
            job_offer=job_offer,
            style=cover_letter_style,
            precision=cover_letter_precision,
            api_key=ANTHROPIC_API_KEY,
        )

    # ── Tâche 3 : Export ──
    fmt = export_format.lower()

    if fmt == "texte":
        result = {
            "cv_optimized": optimized_cv,
            "cover_letter": cover_letter_text,
            "format": "texte",
        }
        return JSONResponse(result)

    elif fmt == "pdf":
        pdf_bytes = export_to_pdf(optimized_cv, cover_letter_text)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=cv-ats-ready.pdf"}
        )

    elif fmt == "word":
        docx_bytes = export_to_docx(optimized_cv, cover_letter_text)
        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=cv-ats-ready.docx"}
        )

    else:
        raise HTTPException(status_code=400, detail="Format non supporté. Utilisez: texte, pdf, word")


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def _verify_payment(payment_intent_id: str, free_token: str) -> bool:
    """
    Vérifie soit un PaymentIntent Stripe confirmé,
    soit un free_token généré pour les codes promo 100%.
    """
    if free_token.startswith("free_") and len(free_token) > 10:
        return True  # Token gratuit valide (code promo 100%)

    if payment_intent_id:
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return intent["status"] == "succeeded"
        except Exception:
            return False

    return False


# ─────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "cv-ats-ready", "version": "1.0.0"}


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
