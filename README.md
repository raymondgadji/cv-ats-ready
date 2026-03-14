# cv-ats-ready — Backend

## Setup en 5 minutes

```bash
# 1. Clone & entre dans le dossier
cd cv-ats-ready-backend

# 2. Crée un environnement virtuel
python -m venv venv
source venv/bin/activate   # Mac/Linux
# ou : venv\Scripts\activate  (Windows)

# 3. Installe les dépendances
pip install -r requirements.txt

# 4. Configure les variables d'environnement
cp .env.example .env
# → Ouvre .env et remplis STRIPE_SECRET_KEY et ANTHROPIC_API_KEY

# 5. Lance le serveur
uvicorn main:app --reload --port 8000
```

L'API tourne sur : http://localhost:8000
Doc interactive : http://localhost:8000/docs

## Endpoints principaux

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/api/create-payment-intent` | Crée un PaymentIntent Stripe (US-03) |
| POST | `/api/optimize` | Optimise CV + génère lettre + exporte (US-05, US-10) |
| POST | `/api/webhook/stripe` | Webhook Stripe (confirmation paiement) |
| GET  | `/api/health` | Health check |

## Codes promo configurés

| Code | Réduction | Usage |
|------|-----------|-------|
| `TEST_CV_ATS_READY` | 100% gratuit | Phase de test / bêta |
| `BETA50` | 50% | Offre early adopters |
| `LAUNCH20` | 20% | Lancement public |

Pour modifier les codes → `main.py`, dict `PROMO_CODES`.

## US-14 — Sécurité des données

- Aucun CV n'est écrit sur disque
- Tout le traitement est en RAM (bytes en mémoire)
- Aucune donnée personnelle n'est stockée en base
- Les PaymentIntent Stripe ne contiennent aucune donnée du CV
