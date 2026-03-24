"""
main.py — Backend FastAPI cv-ats-ready
"""

import os
import io
import uuid
import secrets

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

import stripe
import anthropic

from utils.cv_parser import extract_text_from_cv
from utils.ai_agent import optimize_cv_ats, generate_cover_letter
from utils.exporter import export_to_pdf, export_to_docx

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
stripe.api_key             = os.environ.get("STRIPE_SECRET_KEY", "sk_test_REMPLACE_PAR_TA_CLE")
ANTHROPIC_API_KEY          = os.environ.get("ANTHROPIC_API_KEY", "")
STRIPE_WEBHOOK_SECRET      = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_URL               = os.environ.get("FRONTEND_URL", "http://localhost:3000")

# Codes promo → (type, valeur)
PROMO_CODES = {
    "TEST_CV_ATS_READY": ("free",    0),
    "BETA50":            ("percent", 50),
    "LAUNCH20":          ("percent", 20),
}

# Tokens gratuits valides (en mémoire, reset au redémarrage)
VALID_FREE_TOKENS: set[str] = set()

# ─────────────────────────────────────────
# APP
# ─────────────────────────────────────────
app = FastAPI(title="cv-ats-ready API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "cv-ats-ready", "version": "1.0.0"}


@app.post("/api/create-payment-intent")
async def create_payment_intent(promo_code: str = Form("")):
    """Crée un PaymentIntent Stripe ou génère un token gratuit si code promo 100%."""
    amount = 120  # 1,20 € TTC en centimes
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
            free       = True
            free_token = secrets.token_urlsafe(32)
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
                amount   = max(amount, 50),  # Stripe minimum 0,50 €
                currency = "eur",
                metadata = {"promo_code": code, "service": "cv-ats-ready"},
            )
            client_secret = intent.client_secret
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return {
        "client_secret": client_secret,
        "amount":        amount,
        "promo_valid":   promo_valid,
        "promo_message": promo_message,
        "free":          free,
        "free_token":    free_token,
        "discount_pct":  discount_pct,
    }


@app.post("/api/optimize")
async def optimize(
    job_offer:              str        = Form(...),
    cv_file:                UploadFile = File(...),
    payment_intent_id:      str        = Form(""),
    free_token:             str        = Form(""),
    wants_cover_letter:     str        = Form("false"),
    cover_letter_style:     str        = Form("neutre & professionnel"),
    cover_letter_precision: str        = Form(""),
    export_format:          str        = Form("texte"),
):
    """
    Endpoint principal :
    1. Vérifie le paiement
    2. Extrait le texte du CV
    3. Optimise le CV (+ calcule score ATS)
    4. Génère la lettre si demandée
    5. Exporte selon le format choisi
    """

    # ── 1. Vérification paiement ──────────────────────────
    paid = False

    if free_token and free_token in VALID_FREE_TOKENS:
        paid = True
        VALID_FREE_TOKENS.discard(free_token)   # token à usage unique

    elif payment_intent_id:
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if intent.status == "succeeded":
                paid = True
        except stripe.error.StripeError:
            pass

    if not paid:
        raise HTTPException(status_code=402, detail="Paiement non confirmé. Veuillez réessayer.")

    # ── 2. Extraction texte CV ───────────────────────────
    cv_bytes = await cv_file.read()
    try:
        cv_text = extract_text_from_cv(cv_bytes, cv_file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if len(cv_text.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Le CV semble vide ou illisible. Essaie en format PDF texte (pas scanné)."
        )

    # ── 3. Optimisation CV + score ATS ──────────────────
    try:
        result = optimize_cv_ats(
            cv_text   = cv_text,
            job_offer = job_offer,
            api_key   = ANTHROPIC_API_KEY,
        )
        optimized_cv = result["cv_optimized"]
        ats_score    = result["ats_score"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur IA lors de l'optimisation : {str(e)}")

    # ── 4. Lettre de motivation (optionnelle) ────────────
    cover_letter = ""
    if wants_cover_letter.lower() == "true":
        try:
            cover_letter = generate_cover_letter(
                cv_text   = cv_text,
                job_offer = job_offer,
                style     = cover_letter_style or "neutre & professionnel",
                precision = cover_letter_precision,
                api_key   = ANTHROPIC_API_KEY,
            )
        except Exception as e:
            cover_letter = f"[Erreur génération lettre : {str(e)}]"

    # ── 5. Export ────────────────────────────────────────
    fmt = export_format.lower().strip()

    if fmt == "texte":
        return JSONResponse({
            "cv_optimized": optimized_cv,
            "cover_letter": cover_letter,
            "ats_score":    ats_score,
        })

    elif fmt == "pdf":
        pdf_bytes = export_to_pdf(optimized_cv, cover_letter)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="cv-ats-ready.pdf"',
                "X-ATS-Score-Avant":  str(ats_score.get("score_avant", 0)),
                "X-ATS-Score-Apres":  str(ats_score.get("score_apres", 0)),
            }
        )

    elif fmt in ("word", "docx"):
        docx_bytes = export_to_docx(optimized_cv, cover_letter)
        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": 'attachment; filename="cv-ats-ready.docx"',
                "X-ATS-Score-Avant":  str(ats_score.get("score_avant", 0)),
                "X-ATS-Score-Apres":  str(ats_score.get("score_apres", 0)),
            }
        )

    else:
        raise HTTPException(status_code=400, detail=f"Format non supporté : {fmt}")


@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request):
    """Webhook Stripe — confirmation paiement côté serveur."""
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
        print(f"✅ Paiement confirmé : {pi['id']} — {pi['amount']} centimes")

    return JSONResponse({"status": "ok"})