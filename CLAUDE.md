# CLAUDE.md — cv-ats-ready
> Mémoire projet complète. À coller en début de chaque nouvelle session.

---

## 🎯 Vision produit
**cv-ats-ready** (url : https://cv-ats-ready.fr)
Agent IA qui optimise automatiquement les CV pour les ATS (Applicant Tracking Systems).
**Tagline** : "Tu viens, tu déposes, on s'occupe du reste."
**Rôles** : Founder (utilisateur) + CTO (Claude)

---

## 👤 Profil Founder
- Passionné IA, data science, data analyse, entrepreneuriat
- Bootcamp data analyse complété, certification Hugging Face (smol agents)
- Connaissances : HTML, CSS, JS (intermédiaire), Python (débutant)
- Projets existants : Trajets Verts Paris · IA Éléphants de Côte d'Ivoire
- Objectif moyen terme : incubation Station F / French Tech

---

## 🏗️ Stack technique (validée et fonctionnelle)

| Couche | Techno |
|--------|--------|
| Frontend | HTML/CSS/JS — fichier unique cv-ats-ready.html |
| Hébergement frontend | Netlify (drag & drop manuel) |
| Backend | Python FastAPI |
| Hébergement backend | Railway |
| IA | Claude API — claude-haiku-4-5-20251001 |
| Paiement | Stripe (1€/optimisation) + codes promo |
| Export | PDF (reportlab) + DOCX (python-docx) en RAM |
| Parser CV | pypdf (PDF) + python-docx (DOCX) |
| Domaine | cv-ats-ready.fr (IONOS) |

---

## 📁 Structure du projet

### Sur le PC du Founder
C:\Projects\cv_ats_ready\
├── cv-ats-ready.html          ← Frontend complet (fichier unique)
├── main.py                    ← Backend FastAPI
├── utils/
│   ├── __init__.py
│   ├── ai_agent.py            ← Appels Claude API
│   ├── cv_parser.py           ← Extraction texte PDF/DOCX (pypdf)
│   └── exporter.py            ← Export PDF/DOCX
├── .env                       ← Clés API (jamais committé)
├── .gitignore                 ← venv/ __pycache__/ .env *.pyc
├── requirements.txt
├── Procfile                   ← web: uvicorn main:app --host 0.0.0.0 --port $PORT
└── runtime.txt                ← python-3.11

### Sur GitHub (repo privé)
https://github.com/raymondgadji/cv-ats-ready

---

## 🌍 URLs de production

| Service | URL |
|---------|-----|
| Site public | https://cv-ats-ready.fr |
| Frontend Netlify | https://ubiquitous-conkies-4ac49f.netlify.app |
| Backend Railway | https://web-production-ec873.up.railway.app |
| Health check | https://web-production-ec873.up.railway.app/api/health |

---

## 🔑 Variables d'environnement

### .env local
ANTHROPIC_API_KEY=sk-ant-api03-XXXX
STRIPE_SECRET_KEY=sk_test_51TA7v...
STRIPE_WEBHOOK_SECRET=
FRONTEND_URL=http://127.0.0.1:5500

### Railway (production)
ANTHROPIC_API_KEY=sk-ant-api03-XXXX
STRIPE_SECRET_KEY=sk_test_51TA7v...
STRIPE_WEBHOOK_SECRET=
FRONTEND_URL=https://cv-ats-ready.fr

---

## 🎨 Charte graphique

Primaire : #FF6B00 (orange vif)
Primaire foncé : #D95A00
Fond sombre : #0C0C18 / #1A1A2E
Fond clair : #FAFAF8
Succès : #22C55E
Typo titres : Syne 800
Typo corps : DM Sans

---

## 🚀 Lancer le projet en local

cd C:\Projects\cv_ats_ready
venv\Scripts\activate
uvicorn main:app --reload --port 8000

Frontend : ouvrir cv-ats-ready.html avec Live Server VS Code
URL locale : http://127.0.0.1:5500/cv-ats-ready.html
Health check local : http://localhost:8000/api/health

⚠️ Pour tester en local, mettre dans cv-ats-ready.html :
const API_BASE = 'http://localhost:8000';
Pour la prod, remettre :
const API_BASE = 'https://web-production-ec873.up.railway.app';

---

## 🚀 Déployer une mise à jour

1. Modifier les fichiers en local
2. git add . && git commit -m "description" && git push
   → Railway redéploie automatiquement le backend
3. Pour le frontend : reglisser cv-ats-ready.html sur Netlify (Deploy manually)

---

## ✅ Statut MVP — CE QUI FONCTIONNE (testé le 12/03/2026)

Upload CV PDF/DOCX drag & drop ✅
Saisie offre d'emploi ✅
Code promo TEST_CV_ATS_READY (-100%) ✅
Paiement Stripe 1€ ✅
Modal de progression animée 4 étapes ✅
CV réécrit ATS par Claude ✅
Affichage CV optimisé ✅
Lettre de motivation 6 styles ✅
Multi-sélection styles lettre ✅
Précision libre lettre ✅
Export PDF ✅
Export DOCX ✅
Export texte brut + copier ✅
Watermark "cv-ats-ready.fr — date" ✅
US-14 zéro donnée stockée RAM only ✅
Déploiement Railway + Netlify ✅
Domaine cv-ats-ready.fr ✅
Responsive mobile ⏳ À tester

---

## 🎟️ Codes promo (dans main.py, dict PROMO_CODES)

TEST_CV_ATS_READY → 100% gratuit (bêta test)
BETA50 → 50% réduction
LAUNCH20 → 20% réduction

---

## 🔌 Endpoints backend

GET  /api/health
POST /api/create-payment-intent  → PaymentIntent Stripe + codes promo
POST /api/optimize               → CV optimisé + lettre + export
POST /api/webhook/stripe         → Webhook (prod uniquement)

---

## ⚠️ Bugs connus et correctifs appliqués

BUG 1 — onDone is not a function (CORRIGÉ dans cv-ats-ready.html ~ligne 1580)
→ startProgressAnimation() retourne maintenant function(callback)

BUG 2 — PyMuPDF incompatible Windows (CORRIGÉ)
→ Remplacé par pypdf==4.3.1

BUG 3 — proxies error Anthropic (CORRIGÉ)
→ pip install anthropic --upgrade → version 0.84.0

BUG 4 — CORS / Failed to fetch (CORRIGÉ)
→ Utiliser Live Server VS Code pas file://
→ En prod : FRONTEND_URL=https://cv-ats-ready.fr dans Railway

BUG 5 — Netlify deploy via GitHub échoue (CORRIGÉ)
→ Toujours utiliser "Deploy manually" sur Netlify (glisser-déposer le HTML)

---

## 📋 PROCHAINES TÂCHES (dans l'ordre)

### PRIORITÉ 1 — Score ATS (À IMPLÉMENTER)

Affichage voulu : Score avant/après + détail 4 catégories
Emplacement : DANS la modal de progression ET dans la section résultat

Plan :
1. Modifier utils/ai_agent.py → optimize_cv_ats() retourne aussi ats_score JSON :
{
  "score_avant": 23,
  "score_apres": 91,
  "categories": {
    "mots_cles": {"score": 85, "label": "Mots-clés"},
    "format": {"score": 95, "label": "Format ATS"},
    "experience": {"score": 90, "label": "Expérience"},
    "competences": {"score": 88, "label": "Compétences"}
  }
}

2. Modifier main.py → retourner ats_score dans réponse /api/optimize

3. Modifier cv-ats-ready.html :
   - Modal : après étape 4, afficher jauge animée qui monte jusqu'au score
   - Section résultat : bloc "Score ATS" avant/après + 4 barres par catégorie
   - Style : orange pour avant, vert pour après, animations CSS

### PRIORITÉ 2 — Optimisation vitesse (promesse < 30 sec non tenue)

Modèle actuel : claude-haiku-4-5-20251001, max_tokens=2000
Temps constaté : encore ~60 sec → investiguer (prompt trop long ?)
Piste : réduire le prompt système dans ai_agent.py

### PRIORITÉ 3 — Tests mobile (US-13)
- Tester sur iPhone/Android
- Drag & drop peut ne pas marcher → prévoir bouton "Parcourir" alternatif

### PRIORITÉ 4 — Webhook Stripe production
- Stripe → Développeurs → Webhooks → Ajouter endpoint
- URL : https://web-production-ec873.up.railway.app/api/webhook/stripe
- Événement : payment_intent.succeeded
- Copier le webhook secret → Railway STRIPE_WEBHOOK_SECRET

---

## 💰 Modèle économique

Prix public : 1€ / optimisation
Frais Stripe : ~0,27€ → net ~0,73€
Coût IA Haiku : ~0,01-0,03€ / optimisation
Marge nette : ~95% sur la partie IA
Crédits Anthropic chargés : 16$ (≈ 500+ optimisations)

---

## 🗺️ Feuille de route Station F

SEMAINE 1-2  → ✅ MVP live sur cv-ats-ready.fr
SEMAINE 2-3  → Score ATS + optimisation vitesse
SEMAINE 3    → Bêta fermée (10-20 testeurs, code TEST_CV_ATS_READY)
SEMAINE 4    → Bêta ouverte (code BETA50 -50%)
SEMAINE 5    → Lancement public 1€
MOIS 3-4     → Dossier Station F : Kbis SASU + revenus + métriques + témoignages

---

## 🏢 Décisions juridiques

Structure recommandée : SASU (capital 2000€ min pour crédibilité Station F)
Plateforme : Qonto (création SASU + compte pro tout-en-un)
Budget création : ~316€ (frais légaux 246,86€ + Qonto 69€ HT) + capital
Statut actuel : Pas encore créée — à faire avant bêta ouverte

---

## 📝 Wording validé

Footer tagline : "Fait avec ❤️ pour les demandeurs d'emploi"
Copyright : © 2026 cv-ats-ready.fr
Promesse UI : "Résultat en < 30 sec" (à tenir — PRIORITÉ 2)
