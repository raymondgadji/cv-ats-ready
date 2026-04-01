"""
main.py — Backend FastAPI cv-ats-ready
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
ADMIN_SECRET               = os.environ.get("ADMIN_SECRET", "cv-ats-admin-2026")

# Codes promo → (type, valeur)
PROMO_CODES = {
    "TEST_CV_ATS_READY": ("free",    0),
    "BETA50":            ("percent", 50),
    "LAUNCH20":          ("percent", 20),
}

# Tokens gratuits valides (en mémoire, reset au redémarrage)
VALID_FREE_TOKENS: set[str] = set()

# ─────────────────────────────────────────
# LOGS ANALYTICS (en mémoire + fichier)
# ─────────────────────────────────────────
LOGS: list[dict] = []
LOGS_FILE = "/tmp/cv-ats-ready-logs.json"

def write_log(event: str, data: dict):
    """Écrit un log en mémoire et dans /tmp."""
    entry = {
        "ts":    datetime.datetime.utcnow().isoformat() + "Z",
        "event": event,
        **data
    }
    LOGS.append(entry)
    # Garde les 500 derniers en mémoire
    if len(LOGS) > 500:
        LOGS.pop(0)
    # Persiste dans /tmp (Railway resets entre déploiements, mais utile pour debug)
    try:
        existing = []
        if os.path.exists(LOGS_FILE):
            with open(LOGS_FILE, "r") as f:
                existing = json.load(f)
        existing.append(entry)
        existing = existing[-500:]  # Garde 500 max
        with open(LOGS_FILE, "w") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ─────────────────────────────────────────
# APP
# ─────────────────────────────────────────
app = FastAPI(title="cv-ats-ready API", version="1.1.0")

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
    return {"status": "ok", "service": "cv-ats-ready", "version": "1.1.0"}


@app.post("/api/create-payment-intent")
async def create_payment_intent(
    request: Request,
    promo_code: str = Form(""),
):
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
                amount   = max(amount, 50),
                currency = "eur",
                metadata = {"promo_code": code, "service": "cv-ats-ready"},
            )
            client_secret = intent.client_secret
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # ── Log
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
    edited_cv:              str        = Form(""),   # ← CV édité par l'utilisateur
    edited_lm:              str        = Form(""),   # ← Lettre éditée par l'utilisateur
):
    """
    Endpoint principal :
    1. Vérifie le paiement
    2. Extrait le texte du CV
    3. Optimise le CV (+ calcule score ATS)
    4. Génère la lettre si demandée
    5. Exporte selon le format choisi (en utilisant le contenu édité si fourni)
    """

    # ── 1. Vérification paiement ──────────────────────────
    paid = False

    if free_token:
        if free_token in VALID_FREE_TOKENS:
            paid = True
            VALID_FREE_TOKENS.discard(free_token)
        else:
            # ⚠️ BYPASS BÊTA : token accepté même si Railway a redémarré
            # À remplacer par Redis avant le lancement public payant
            paid = True

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
        # Si l'utilisateur a déjà une lettre éditée, on la réutilise
        if edited_lm.strip():
            cover_letter = edited_lm.strip()
        else:
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

    # ── Si l'utilisateur a édité le CV, on utilise sa version ──
    final_cv = edited_cv.strip() if edited_cv.strip() else optimized_cv

    # ── Log optimisation ──
    write_log("optimize", {
        "format":           export_format,
        "wants_lm":         wants_cover_letter == "true",
        "lm_style":         cover_letter_style if wants_cover_letter == "true" else None,
        "score_avant":      ats_score.get("score_avant") if ats_score else None,
        "score_apres":      ats_score.get("score_apres") if ats_score else None,
        "cv_edited":        bool(edited_cv.strip()),
        "lm_edited":        bool(edited_lm.strip()),
        "promo":            bool(free_token),
        "paid_stripe":      bool(payment_intent_id),
        "ip":               request.client.host if request.client else "unknown",
        "origin":           request.headers.get("origin", "unknown"),
    })

    # ── 5. Export ────────────────────────────────────────
    fmt = export_format.lower().strip()

    if fmt == "texte":
        return JSONResponse({
            "cv_optimized": final_cv,
            "cover_letter": cover_letter,
            "ats_score":    ats_score,
        })

    elif fmt == "pdf":
        pdf_bytes = export_to_pdf(final_cv, cover_letter)
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
        docx_bytes = export_to_docx(final_cv, cover_letter)
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


# ─────────────────────────────────────────
# ENDPOINT ANALYTICS (protégé par secret)
# ─────────────────────────────────────────

@app.get("/api/admin/logs")
async def get_logs(secret: str = ""):
    """
    Dashboard analytics basique.
    Accès : /api/admin/logs?secret=TON_ADMIN_SECRET
    """
    if secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Accès refusé")

    # Calcul des métriques
    total_opts  = sum(1 for l in LOGS if l["event"] == "optimize")
    total_pays  = sum(1 for l in LOGS if l["event"] == "payment_init")
    formats     = {}
    lm_count    = 0
    edited_count= 0
    scores_apres= []

    for l in LOGS:
        if l["event"] == "optimize":
            fmt = l.get("format", "?")
            formats[fmt] = formats.get(fmt, 0) + 1
            if l.get("wants_lm"): lm_count += 1
            if l.get("cv_edited"): edited_count += 1
            if l.get("score_apres"): scores_apres.append(l["score_apres"])

    avg_score = round(sum(scores_apres) / len(scores_apres), 1) if scores_apres else 0

    return JSONResponse({
        "resume": {
            "total_optimisations":     total_opts,
            "total_paiements_init":    total_pays,
            "lettres_generees":        lm_count,
            "cv_edites_par_user":      edited_count,
            "score_ats_moyen_apres":   avg_score,
            "formats": formats,
        },
        "derniers_logs": LOGS[-50:][::-1],  # 50 derniers, plus récent en premier
    })


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
        write_log("payment_succeeded", {
            "payment_intent_id": pi["id"],
            "amount_cents":      pi["amount"],
            "promo_code":        pi.get("metadata", {}).get("promo_code"),
        })

    return JSONResponse({"status": "ok"})