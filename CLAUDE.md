# CLAUDE.md — cv-ats-ready
> Mémoire projet complète. À coller en début de chaque nouvelle session.

---

## 🎯 Vision produit
**cv-ats-ready** (url cible : cv-ats-ready.fr)
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
| Backend | Python FastAPI — dossier C:\Projects\cv_ats_ready\ |
| IA | Claude API — claude-haiku-4-5-20251001 (rapide) |
| Paiement | Stripe (1€/optimisation) + codes promo |
| Export | PDF (reportlab) + DOCX (python-docx) en RAM |
| Parser CV | pypdf (PDF) + python-docx (DOCX) |

---

## 📁 Structure du projet (sur le PC du Founder)

C:\Projects\cv_ats_ready\
├── cv-ats-ready.html          ← Frontend complet (fichier unique)
├── main.py                    ← Backend FastAPI
├── utils/
│   ├── __init__.py
│   ├── ai_agent.py            ← Appels Claude API
│   ├── cv_parser.py           ← Extraction texte PDF/DOCX (pypdf)
│   └── exporter.py            ← Export PDF/DOCX
├── .env                       ← Clés API (NE PAS commiter)
├── requirements.txt
├── Procfile                   ← À CRÉER pour Railway
├── runtime.txt                ← À CRÉER pour Railway
└── venv/

---

## 🔑 Variables d'environnement (.env)

ANTHROPIC_API_KEY=sk-ant-api03-XXXX
STRIPE_SECRET_KEY=sk_test_51TA7v...
STRIPE_WEBHOOK_SECRET=
FRONTEND_URL=http://127.0.0.1:5500

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
URL : http://127.0.0.1:5500/cv-ats-ready.html
Health check : http://localhost:8000/api/health → {"status":"ok"}

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
Multi-sélection styles lettre ✅ (styles combinés envoyés ex: "débutant + très motivé")
Précision libre lettre ✅
Export PDF ✅
Export DOCX ✅
Export texte brut + copier ✅
Watermark "cv-ats-ready.fr — date" ✅
US-14 zéro donnée stockée RAM only ✅
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
→ appelé : finishProgress(() => showResult())

BUG 2 — PyMuPDF incompatible Windows (CORRIGÉ)
→ Remplacé par pypdf==4.3.1
→ utils/cv_parser.py utilise uniquement "from pypdf import PdfReader"

BUG 3 — proxies error Anthropic (CORRIGÉ)
→ pip install anthropic --upgrade → version 0.84.0

BUG 4 — CORS / Failed to fetch (CORRIGÉ)
→ Utiliser Live Server VS Code pas file://
→ Bloqueur pub bloque r.stripe.com : désactiver sur 127.0.0.1 ou navigation privée

---

## 📋 PROCHAINES TÂCHES (dans l'ordre)

### PRIORITÉ 1 — Score ATS (À IMPLÉMENTER — décision Founder 12/03/2026)

Affichage voulu : Score avant/après + détail 4 catégories
Emplacement : DANS la modal de progression ET dans la section résultat

Plan :
1. Modifier utils/ai_agent.py → nouvelle fonction analyze_ats_score() retourne JSON :
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

2. Modifier main.py → retourner ats_score dans réponse /api/optimize (format texte et dans header pour PDF/DOCX)

3. Modifier cv-ats-ready.html :
   - Modal : après étape 4, afficher jauge animée qui monte jusqu'au score final
   - Section résultat : bloc "Score ATS" avec avant/après + 4 barres de progression par catégorie
   - Style : orange pour avant, vert pour après, animations CSS

### PRIORITÉ 2 — Déploiement Railway + domaine

Founder a : GitHub ✅ | domaine cv-ats-ready.fr : ❌ pas encore acheté

Fichiers à créer avant push :
Procfile    → web: uvicorn main:app --host 0.0.0.0 --port $PORT
runtime.txt → python-3.11
.gitignore  → venv/ __pycache__/ .env *.pyc

Étapes déploiement :
1. git init && git add . && git commit -m "MVP cv-ats-ready"
2. Créer repo PRIVÉ sur github.com (nom: cv-ats-ready)
3. git remote add origin + git push
4. Railway.app → New Project → Deploy from GitHub
5. Variables Railway : ANTHROPIC_API_KEY, STRIPE_SECRET_KEY, FRONTEND_URL=https://cv-ats-ready.fr
6. Netlify → glisser-déposer cv-ats-ready.html
7. Acheter cv-ats-ready.fr sur OVH (~7€/an)
8. Connecter domaine Netlify + mettre à jour API_BASE dans le HTML

### PRIORITÉ 3 — Optimisation vitesse (promesse < 30 sec non tenue)

Modèle DÉJÀ changé dans ai_agent.py : claude-haiku-4-5-20251001
  optimize_cv_ats()      → model="claude-haiku-4-5-20251001", max_tokens=2000
  generate_cover_letter() → model="claude-haiku-4-5-20251001", max_tokens=1000
Temps constaté en test : encore ~60 sec → à investiguer (prompt trop long ?)

### PRIORITÉ 4 — Tests mobile (US-13)
- Tester sur iPhone/Android
- Drag & drop peut ne pas marcher → prévoir bouton "Parcourir" alternatif

---

## 💰 Modèle économique

Prix public : 1€ / optimisation
Frais Stripe : ~0,27€ → net ~0,73€
Coût IA Haiku : ~0,01-0,03€ / optimisation
Marge nette : ~95% sur la partie IA
Crédits Anthropic chargés : 16$ (≈ 500+ optimisations)

---

## 🗺️ Feuille de route Station F

SEMAINE 1-2  → Score ATS + déploiement Railway/Netlify + domaine cv-ats-ready.fr
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
Promesse UI : "Résultat en < 30 sec" (nécessite passage à Haiku — PRIORITÉ 3)
