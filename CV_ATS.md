# CV_ATS.md
> Mémoire projet complète. À coller en début de chaque nouvelle session avec RAYMOND_GADJI.md
> Anciennement : cv-ats-ready

---

## 🎯 Vision produit

**CV ATS** (rebrand Mai 2026 — Station F Fighters)
Agent IA qui optimise automatiquement les CV pour les ATS (Applicant Tracking Systems).
**Tagline** : "Ton CV optimisé pour les recruteurs"
**Slogan / Hook** : "À chaque candidature son CV"
**Rôles** : Founder (Raymond Gadji) + CTO (Claude)

---

## 🌐 Domaines

| Domaine | Statut | Rôle |
|---------|--------|------|
| cv-ats.com | ✅ Actif — domaine principal | Ionos DNS → Netlify |
| www.cv-ats.com | ✅ Actif | Redirige → cv-ats.com |
| cv-ats-ready.fr | ✅ Actif — alias | Redirige → cv-ats.com |
| cv-ats-ready.netlify.app | ✅ Sous-domaine Netlify | Preview / backup |

**DNS Ionos configuré :**
- Enregistrement A : `@` → `75.2.60.5`
- CNAME : `www` → `cv-ats-ready.netlify.app`

---

## 🏗️ Stack technique

| Couche | Techno |
|--------|--------|
| Frontend | HTML/CSS/JS — fichier unique `cv-ats.html` (= `index.html` sur Netlify) |
| Backend | Python FastAPI v1.3.0 |
| IA | Claude Haiku — claude-haiku-4-5-20251001 |
| Base de données | PostgreSQL Railway (logs persistants) |
| Paiement | Stripe — 1€ HT pay-as-you-go + abonnements à brancher |
| Export | PDF (reportlab) + DOCX (python-docx) en RAM |
| Parser CV | pypdf + pdfminer.six + python-docx |
| Job Matching | France Travail API + Adzuna API |
| Analytics | Umami Cloud (RGPD) |
| HTTP client | httpx (fetch URL offres emploi) |

---

## 📁 Structure du projet

```
C:\Projects\cv_ats_ready\
├── cv-ats.html              ← FICHIER PRINCIPAL (déployé comme index.html sur Netlify)
├── og-image.png             ← Image OG 1200x630 pour partage LinkedIn/WhatsApp
├── og-image.svg             ← Source SVG de l'image OG
├── netlify.toml             ← Config Netlify site statique
├── main.py                  ← v1.3.0
├── utils/
│   ├── __init__.py
│   ├── ai_agent.py
│   ├── autopilot.py         ← Job matching France Travail + Adzuna
│   ├── cv_parser.py
│   └── exporter.py
├── .env                     ← NE JAMAIS PUSHER SUR GITHUB ⚠️
├── .gitignore               ← .env inclus ✅
├── requirements.txt         ← Pour Railway uniquement
└── Procfile                 ← Pour Railway uniquement
```

---

## 🌐 Infrastructure production

| Composant | Service | URL |
|-----------|---------|-----|
| Frontend | Netlify (drag & drop manuel) | https://cv-ats.com |
| Backend | Railway EU West | https://web-production-ec873.up.railway.app |
| Analytics admin | Railway endpoint | https://web-production-ec873.up.railway.app/api/admin/logs?secret=cv-ats-admin-2026 |
| API Health | Railway | https://web-production-ec873.up.railway.app/api/health |
| API Docs | Railway Swagger | https://web-production-ec873.up.railway.app/docs |

**⚠️ Déploiement Netlify — DRAG & DROP uniquement**
Ne pas connecter GitHub à Netlify — le repo contient requirements.txt et Procfile qui font planter le build Netlify.
Procédure : créer un dossier `deploy/` avec `index.html` + `og-image.png` → glisser sur Netlify.

---

## 🚀 Lancer en local

```bash
cd C:\Projects\cv_ats_ready
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```
Frontend : Live Server → `http://127.0.0.1:5500`

---

## 📋 Déploiement Netlify (drag & drop)

```
1. Crée un dossier deploy/ sur le bureau
2. Copie cv-ats.html → renomme en index.html
3. Copie og-image.png
4. app.netlify.com → ton site → Deploys → glisse le dossier deploy/
```

---

## 🔑 Variables d'environnement Railway

```
ANTHROPIC_API_KEY
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
FRONTEND_URL=https://cv-ats.com
ADMIN_SECRET=cv-ats-admin-2026
DATABASE_URL=${{Postgres.DATABASE_URL}}
FRANCE_TRAVAIL_CLIENT_ID
FRANCE_TRAVAIL_CLIENT_SECRET
ADZUNA_APP_ID
ADZUNA_APP_KEY
```

---

## 🎨 Charte graphique

```
Primaire : #FF6B00 | Primaire foncé : #D95A00
Fond sombre : #0C0C18 | Fond clair : #FAFAF8
Succès : #22C55E
Typo titres : Syne 800 | Typo corps : DM Sans
```

---

## 💰 Tarification

| Plan | Prix | Détail | Statut |
|------|------|--------|--------|
| Pay as you go | ~~3,99€~~ **1€ HT** (1,20€ TTC) | Prix lancement — 500 premiers users | ✅ Opérationnel |
| Illimité | 9,99€ TTC/mois | CV illimités | ⏳ Stripe à brancher |
| Autopilot | 19,99€ TTC/mois | CV illimités + offres matchées + 1 clic | ⏳ Stripe à brancher |

---

## 🎟️ Codes promo

```
TEST_CV_ATS_READY → 100% gratuit
BETA50            → -50%
LAUNCH20          → -20%
```

---

## 🔌 Endpoints API

```
GET  /api/health
GET  /api/admin/logs?secret=cv-ats-admin-2026
POST /api/fetch-url              ← Récupère texte d'une offre depuis URL
POST /api/create-payment-intent
POST /api/optimize               ← CV + lettre de motivation
POST /api/autopilot              ← Job matching France Travail + Adzuna
POST /api/webhook/stripe
```

---

## ✅ Features livrées

| Feature | Statut | Sprint |
|---------|--------|--------|
| Upload CV PDF/DOCX drag & drop | ✅ | MVP |
| Codes promo | ✅ | MVP |
| Paiement Stripe 1€ | ✅ | MVP |
| CV réécrit ATS par Claude Haiku | ✅ | MVP |
| Score ATS avant/après + 4 catégories | ✅ | MVP |
| CV éditable avant téléchargement | ✅ | MVP |
| Lettre de motivation 6 styles | ✅ | MVP |
| Export PDF / DOCX / Texte | ✅ | MVP |
| Analytics Umami | ✅ | MVP |
| Rebrand → CV ATS | ✅ | Station F |
| Section pricing 3 plans | ✅ | Station F |
| Responsive mobile 768px + 480px | ✅ | Station F |
| PostgreSQL Railway — logs persistants | ✅ | Sprint juin |
| Feature Autopilot — job matching | ✅ | Sprint juin |
| France Travail API + Adzuna API | ✅ | Sprint juin |
| Flow Oui/Non Autopilot après téléchargement | ✅ | Sprint juin |
| 3 offres max plan normal + upsell 19,99€ | ✅ | Sprint juin |
| Fetch URL offre emploi automatique | ✅ | Sprint juin |
| Message erreur statique fetch-url | ✅ | Sprint juin |
| cv-ats.com domaine principal | ✅ | Sprint juin |
| CORS sécurisé cv-ats.com | ✅ | Sprint juin |
| main.py v1.3.0 | ✅ | Sprint juin |
| Pricing lancement ~~3,99€~~ → 1€ + badge urgence 500 places | ✅ | Sprint juin |
| Hero réordonné — slogan / pitch / badge / app | ✅ | Sprint juin |
| **SEO complet** — canonical, og, twitter card, robots, favicon | ✅ | Sprint juin |
| **GEO Schema.org** — WebApplication + FAQPage JSON-LD | ✅ | Sprint juin |
| **og-image.png** 1200x630 — preview LinkedIn/WhatsApp | ✅ | Sprint juin |
| **Perplexity indexe déjà cv-ats.com** | ✅ | Sprint juin |

---

## ⏳ Backlog — prochaines sessions

### 🔴 Priorité haute
- [x] **Candidature STIC 2026 soumise** ✅ — juin 2026
- [ ] **Abonnements Stripe** 9,99€ + 19,99€ récurrents (attente création société + passeport)
- [ ] **Améliorer Autopilot** — France Travail retourne parfois 204

### 🟡 Priorité moyenne
- [ ] Redirection cv-ats-ready.fr → cv-ats.com (fichier `_redirects` Netlify)
- [ ] Configurer Stripe webhook secret en prod
- [ ] Soumettre sitemap sur Google Search Console
- [ ] Retester GEO dans 1 semaine — Perplexity doit citer le prix 1€

### 🟢 Idées futures
- [ ] Fusion avec Link2Job
- [ ] Mode freemium — 1 optimisation gratuite/mois
- [ ] Alertes offres personnalisées (Autopilot avancé)
- [ ] Témoignages vrais utilisateurs

---

## ⚠️ Points d'attention

- **BYPASS BÊTA** dans `/api/optimize` et `/api/autopilot` — les free_tokens non reconnus sont acceptés. À remplacer par Redis avant lancement public payant.
- **Stripe webhook secret** → à configurer en prod
- **Abonnements Stripe** → en attente création société
- **GitHub** → NE JAMAIS pusher `.env` — toujours vérifier avec `git status` avant commit
- **Netlify** → NE PAS connecter GitHub — faire drag & drop manuel uniquement

---

## 📊 Analytics

- **Umami** : cloud.umami.is — Website ID : `1475d8a0-94a1-420c-ad21-4f3b5698430b`
- **Dashboard logs** : `https://web-production-ec873.up.railway.app/api/admin/logs?secret=cv-ats-admin-2026`
- ✅ Données persistantes depuis PostgreSQL Railway

---

## 🏆 Concours & Distinctions

### STIC 2026 — Sahal Tech Innovation Challenge
- Deadline : 20 juin 2026
- Domaine : FinTech & Automatisation
- Dossier PDF prêt : STIC2026_CVATS_Candidature.pdf
- Formulaire : https://docs.google.com/forms/d/e/1FAIpQLSda3SfDegE2CxhcTPVFmsLXZTPT2AtBVvx62znYsNNCUs4xPg/viewform

---

## 🔗 Lien avec Link2Job

CV ATS et Link2Job sont deux projets du même founder (Raymond Gadji).
Fusion prévue à terme — cv-ats.com intégré dans link2job.fr.
Pour l'instant les deux tournent indépendamment.
Voir **CLAUDE_LINK_TO_JOB.md** pour le projet Link2Job.
