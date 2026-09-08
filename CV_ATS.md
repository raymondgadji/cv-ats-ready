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
- MX → IONOS Mail (mx00/mx01.ionos.fr)

**Email pro :** `contact@cv-ats.com` — redirection IONOS (gratuite, pas de boîte mail) → `gadjiraymond7@gmail.com`, créée et testée le 08/09/2026 (aucune adresse n'existait avant, un email envoyé dessus avait rebondi "address not found").

---

## 🔍 SEO Google — statut (08/09/2026)

**Diagnostic initial** : `site:cv-ats.com` ne renvoyait aucun résultat. Cause trouvée : `robots.txt` et `sitemap.xml` étaient tous les deux en 404 (jamais créés), et **le domaine n'avait jamais été ajouté à Google Search Console**.

**Corrigé le 08/09/2026** :
- `robots.txt` + `sitemap.xml` créés, déployés (Netlify), vérifiés en ligne (200 OK).
- Propriété `https://cv-ats.com/` ajoutée et **vérifiée** dans Google Search Console (méthode : enregistrement DNS TXT sur IONOS, propagation quasi instantanée).
- Sitemap soumis avec succès (1 page découverte).
- **Découverte importante** : un ancien sitemap `sitemap_index.xml` (soumis le 24/03/2025, probablement une ancienne version WordPress avant la migration vers le site actuel) traînait avec 0 pages découvertes depuis plus d'un an — signe que le site n'a jamais eu de config SEO fonctionnelle depuis sa refonte.
- **Découverte critique (via l'outil "Inspection d'URL")** : Google avait en réalité **déjà crawlé** cv-ats.com (dernier crawl le 28/08/2026, découvert via des liens entrants depuis koush.app et cv-ats-ready.fr) mais avait choisi de **NE PAS l'indexer** — statut "Crawled - currently not indexed". Ce n'est donc pas (uniquement) un problème de découverte technique, mais un signal de qualité/pertinence perçue par Google — typique d'un site à page unique, sans contenu substantiel ni autorité de domaine (backlinks).
- Réindexation demandée manuellement via l'outil d'inspection d'URL.

**Why:** Corriger le technique (robots.txt, sitemap, GSC) était nécessaire mais pas suffisant — Google a montré qu'il visite déjà le site sans l'indexer, ce qui pointe vers un besoin de contenu réel, pas juste de plomberie SEO.
**How to apply:** Prochaine étape recommandée : construire 2-3 pages de contenu réellement utile et sourcé (ex: "comment fonctionne un ATS", "comment optimiser son CV pour passer les filtres ATS") plutôt que de compter sur la seule page produit pour se faire indexer — même logique que le contenu Koush ("carte Afrique") qui a été cité spontanément par les IA grâce à sa valeur informative, pas à des astuces techniques comme llms.txt (voir mémoire `geo_strategy_insights`).

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
│   ├── ai_agent.py          ← v1.1 — scores ATS dynamiques + minimum 80%
│   ├── autopilot.py         ← Job matching France Travail + Adzuna
│   ├── cv_parser.py
│   └── exporter.py
├── img/                     ← Logos partenaires (base64 dans html)
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
Ne pas connecter GitHub à Netlify — le repo contient requirements.txt et Procfile qui font planter le build.
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
4. Copie robots.txt et sitemap.xml (ajoutés le 08/09/2026 — sans eux, Google n'indexe pas le site, voir points d'attention)
5. Copie les DOSSIERS guide-ats-cv/ et optimiser-cv-ats/ (ajoutés le 08/09/2026, pages SEO — garder la structure de sous-dossiers, pas juste les fichiers index.html à la racine)
6. app.netlify.com → ton site → Deploys → glisse le dossier deploy/ (avec ses sous-dossiers)
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
| Pay as you go | ~~3,99€~~ **1€ HT** (1,20€ TTC) | Prix lancement — 500 premiers users | ✅ Live et actif (08/09/2026) — clé publique Stripe frontend corrigée (était encore en mode test) |
| Illimité | 9,99€ TTC/mois | CV illimités — rentabilisé dès la 3ème opti | ✅ Abonnement Stripe Checkout complet et actif (08/09/2026) — `price_1UDOZXQNdcgobNCllFjGcjpr` |
| Autopilot | 19,99€ TTC/mois | CV illimités + offres matchées + 1 clic | ✅ Abonnement Stripe Checkout complet et actif (08/09/2026) — `price_1UDRE1QNdcgobNClq4zkgRtU`, plus "bientôt disponible" |

---

## 🎟️ Codes promo

```
TEST_CV_ATS_READY → 100% gratuit (réservé aux vrais beta-testeurs externes)
QA_INTERNAL       → 100% gratuit (réservé aux tests internes Raymond + Claude — voir /api/admin/logs *_hors_qa)
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
| cv-ats.com domaine principal | ✅ | Sprint juin |
| CORS sécurisé cv-ats.com | ✅ | Sprint juin |
| main.py v1.3.0 | ✅ | Sprint juin |
| Pricing lancement ~~3,99€~~ → 1€ + badge urgence 500 places | ✅ | Sprint juin |
| Hero réordonné — slogan / pitch / badge / app | ✅ | Sprint juin |
| SEO complet — canonical, og, twitter card, robots, favicon | ✅ | Sprint juin |
| GEO Schema.org — WebApplication + FAQPage JSON-LD | ✅ | Sprint juin |
| og-image.png 1200x630 — preview LinkedIn/WhatsApp | ✅ | Sprint juin |
| Perplexity indexe déjà cv-ats.com | ✅ | Sprint juin |
| Section Social Proof — Station F + Fighters + partenaires | ✅ | Sprint juin |
| Logos base64 — France Travail, Adzuna, Claude, Stripe | ✅ | Sprint juin |
| Pricing — "Rentabilisé dès la 3ème optimisation" | ✅ | Sprint juin |
| FAQ — "Que signifie ATS en français ?" | ✅ | Sprint juin |
| Explainer card — traduction ATS en français | ✅ | Sprint juin |
| Business Plan PDF — 10 sections | ✅ | Sprint juin |
| **Fix scores ATS dynamiques** — supprime valeurs hardcodées | ✅ | Sprint juin |
| **Score ATS après optimisation minimum 80%** | ✅ | Sprint juin |
| **Pitch CCI PDF 5 pages** — 3 pitchs oraux + support visuel | ✅ | Sprint juin |
| **Dossier Round 2 Station F** — Pitch Deck + Preuve produit + Preuve marché + Annexe | ✅ | Sprint juillet |
| **GEO ChatGPT fix** — 3 blocs JSON-LD séparés + SoftwareApplication + knowsAbout + section statique | ✅ | Sprint juillet |
| **Sprint Templates CV** — Q3 "Veux-tu un CV mis en page ?" + 2 color pickers live + preview en direct | ✅ | Sprint juillet |

---

## 🌍 PIPELINE COMMERCIAL AFRIQUE

### Contacts actifs

| Contact | Société | Statut | Action |
|---------|---------|--------|--------|
| **Mahdia FOUSSENI** | ODAH (odah.pro) — réseau pro Afrique | ✅ Call fait — proposition API/widget en cours | Préparer pilot 30 jours |
| **Sébastien N'Goran KOUASSI** | EmploiRapide.Net + FAVITECH | ⏳ Pas de réponse | Relancer message court |
| **Yannick Gnaman** | Agence Emploi Jeune CIV | ✅ Email de présentation envoyé le 08/09/2026 à info@emploijeunes.ci (traction 100+ opti, score 86,6%, Station F top 10%, + offre API Site72) | Attendre sa mise en relation avec la Direction de l'Information et de la Communication |

### Notes call ODAH (Mahdia) — ✅ Call réalisé

**Contexte ODAH :**
- 300+ utilisateurs sur odah.pro
- Les utilisateurs s'inscrivent, uploadent leur CV, postulent aux offres
- Fonctionnement similaire à Indeed — profil + CV + candidature
- Problème constaté : CVs très mal conçus, étudiants utilisent le même CV pour toutes les offres

**Ce qu'elle veut intégrer dans ODAH :**
- Optimiser/réadapter le CV à chaque offre d'emploi spécifique
- **Garder la mise en forme initiale du CV uploadé** ← feedback fort
- Ou proposer un beau template avec options de personnalisation (couleur, police)
- Le dev est basé en Côte d'Ivoire — il faudra une doc API claire

**⚠️ Feedback produit majeur (confirmé par Station F aussi) :**
Plusieurs personnes indépendantes demandent de **conserver la mise en forme du CV original**.
C'est un vrai signal produit — à prioriser dans le backlog.

**Décision partenariat :**
- ❌ Pas de troc services (CV ATS vs marketing digital) — rester pro
- ✅ Intégration technique uniquement : API ou widget
- ✅ Pilot gratuit 30 jours à proposer
- ✅ Doc API à préparer pour le dev ivoirien

**Prochaine étape :** Préparer une proposition technique + pilot pour Mahdia

### Message de relance (pour Sébastien et Yannick)
> Bonjour Mr. [Nom], je me permets de revenir vers vous concernant mon message du [date].
> Avez-vous eu l'occasion de tester CV ATS avec le code TEST_CV_ATS_READY ?
> Je serais ravi d'échanger 15 minutes à votre convenance.
> Cordialement, Raymond Gadji — cv-ats.com

---

## ⏳ Backlog — prochaines sessions

### 🔴 Priorité haute
- [x] **Candidature STIC 2026 soumise** ✅ — juin 2026
- [x] **Sprint Templates CV frontend** ✅ — Q3/Q4 réorganisés, 3 templates, 2 color pickers live, preview en direct
- [x] **Sprint Templates CV backend** ✅ — templates Moderne + Classique avec ReportLab, 2 color pickers, max 2 pages
- [ ] **Fix templates** — tester rendu final PDF Moderne + Classique sur vrai CV utilisateur
- [ ] **Doc API** — documenter l'API CV ATS pour intégration externe (dev ivoirien ODAH)
- [ ] **Pilot ODAH** — préparer proposition technique + 30 jours gratuits pour Mahdia
- [x] **Rendez-vous CCI** ✅ — 3 entretiens avec Philip Dietrich (CCI75) — 16/06, 22/06, 02/07/2026
- [x] **Dossier Round 2 Station F soumis** ✅ — juillet 2026
- [x] **Réponse Round 2** ✅ — non retenu (22/07/2026), top 10% du batch, Landing Zone proposée en échange (249€ HT/poste/mois)
- [x] **Candidature Landing Zone soumise** ✅ — 12/08/2026 (formulaire Fillout)
- [ ] **Négocier la date d'arrivée réelle** sur la Landing Zone (1er octobre ou 1er novembre 2026) — le formulaire n'offrait qu'une seule date (11/09/2026), à corriger par email avec Station F
- [x] **Débloquer le déploiement Railway** ✅ — résolu le 08/09/2026 (Dockerfile + fix $PORT + suppression Custom Start Command fantôme).
- [x] **Code d'abonnement Stripe** ✅ — construit, déployé et vérifié le 08/09/2026 : table `subscribers` (Postgres), `/api/create-checkout-session`, `/api/checkout-success`, webhook `customer.subscription.updated/deleted`, gating dans `/api/optimize` et `/api/autopilot` via `access_token`. Frontend déployé sur Netlify et vérifié en ligne (clé Stripe live + boutons d'abonnement fonctionnels, redirection Stripe Checkout confirmée par Raymond et Claude).
- [ ] **Test optionnel** : abonnement réel de bout en bout avec paiement complet (Illimité et Autopilot) — pas bloquant, à faire quand Raymond le souhaite.
- [ ] **Portail client Stripe** (gestion/résiliation self-service) — pas encore activé pour les abonnements CV ATS (existe déjà pour Site72, à activer séparément si souhaité).
- [ ] **Améliorer Autopilot** — France Travail retourne parfois 204

### 🟡 Priorité moyenne
- [ ] Feedbacks users sur section Social Proof — agrandir logos si nécessaire
- [ ] Redirection cv-ats-ready.fr → cv-ats.com (fichier `_redirects` Netlify)
- [x] Configurer Stripe webhook secret en prod ✅
- [x] Soumettre sitemap sur Google Search Console ✅ — fait le 08/09/2026, voir section SEO ci-dessous
- [ ] Retester GEO dans 1 semaine — Perplexity doit citer le prix 1€
- [ ] **Construire du contenu SEO/GEO ciblé** (2-3 pages utiles et sourcées, ex: "comment optimiser son CV pour un ATS") — Google a crawlé cv-ats.com mais a choisi de ne PAS l'indexer (voir section SEO), signe qu'il faut du contenu substantiel, pas juste du technique.

### 🟢 Idées futures
- [ ] **MCP Server CV ATS** — exposer l'API aux agents IA (inspiré post Sokhna Seck / Convoy AI — étapes 02 et 03 "Agent Ready")
- [ ] **Scoring fit candidat/offre dans Autopilot** — noter chaque offre matchée avec un score de compatibilité (ex: 87% de fit) basé sur le CV optimisé vs l'offre. Tendance qui va devenir la norme dans 6 mois (cf. CVLab Jobs / Zineddine Gomri sur LinkedIn). Être en avance.
- [ ] Fusion avec Link2Job
- [ ] Mode freemium — 1 optimisation gratuite/mois
- [ ] Alertes offres personnalisées (Autopilot avancé)
- [ ] Témoignages vrais utilisateurs

---

## ⚠️ Points d'attention

- **BYPASS BÊTA** dans `/api/optimize` et `/api/autopilot` — les free_tokens non reconnus sont acceptés. À remplacer par Redis avant lancement public payant.
- **✅ Stripe live débloqué et actif (08/09/2026)** : `STRIPE_SECRET_KEY` = clé live du compte site72.fr, déployée avec succès et vérifiée (PaymentIntent créé avec `livemode: true` sur le bon compte). Cause racine des échecs de build : Railway/Railpack auto-générait une liste de paquets apt cassée (nom de paquet obsolète), + un "Custom Start Command" hérité de l'ancien Procfile écrasait silencieusement le CMD du nouveau Dockerfile sans passer par un shell (`$PORT` jamais substitué → 502). Fixé avec un `Dockerfile` dédié (`python:3.11-slim-bookworm`, bons noms de paquets, `CMD ["sh","-c","uvicorn ... --port $PORT"]`) + suppression du Custom Start Command dans Settings Railway.
- **Stripe webhook secret** → à configurer en prod (mode live)
- **Prévisions financières corrigées** (validées CCI) : 2026 ~500€ · 2027 ~36 000€ · 2028 ~77 000€
- **Abonnements Stripe** → société existe désormais (micro-entreprise Raymond, voir RAYMOND_GADJI.md) ; blocage résolu, reste à construire le code d'abonnement (Checkout/webhook) pour Illimité/Autopilot
- **GitHub** → NE JAMAIS pusher `.env` — toujours `git status` avant commit
- **Netlify** → NE PAS connecter GitHub — drag & drop manuel uniquement
- **Clés API** → régénérées suite incident GitGuardian juin 2026 ✅
- **Clé privée SSL** → incident juin 2026 — `_.cv-ats-ready.fr_private_key.key` exposée sur GitHub depuis mars 2026. Signalé par Robin (security researcher bénévole). Actions : `git rm --cached`, `*.key` ajouté au `.gitignore`, certificat SSL réémis sur Ionos. ✅ Résolu le 17 juin 2026.

---

## 📊 Analytics

- **Umami** : cloud.umami.is — Website ID : `1475d8a0-94a1-420c-ad21-4f3b5698430b`
- **Dashboard logs** : `https://web-production-ec873.up.railway.app/api/admin/logs?secret=cv-ats-admin-2026`
- ✅ Données persistantes depuis PostgreSQL Railway
- Stats juin 2026 : 24 optimisations · score moyen 86.1% · 10 lettres générées

---

## 🏆 Concours & Distinctions

### STIC 2026 — Sahal Tech Innovation Challenge ✅ SOUMIS
- Candidature soumise — juin 2026
- Domaine : FinTech & Automatisation
- Dossier PDF : STIC2026_CVATS_Candidature.pdf
- Formulaire : https://docs.google.com/forms/d/e/1FAIpQLSda3SfDegE2CxhcTPVFmsLXZTPT2AtBVvx62znYsNNCUs4xPg/viewform

---

## 📄 Documents produits

- `STIC2026_CVATS_Candidature.pdf` — dossier concours STIC
- `CVATS_BusinessPlan_2026.pdf` — business plan complet 10 sections
- `CVATS_Pitch_CCI_2026.pdf` — pitch CCI 5 pages : 3 formats oraux (15s, 1min, 1min30) + problème/solution + modèle éco + profil
- `CVATS_PitchDeck_Round2_StationF.pdf` — Pitch Deck Round 2 (14 pages)
- `CVATS_ProofExecution_Product.pdf` — Preuve d'exécution produit (3 pages) — liens cliquables ✅
  - 🎬 Loom : https://www.loom.com/share/d6607305f0bf4bd3926d3e3cbcc17a7f
  - 🎬 YouTube : https://youtu.be/YxzzGaG3hP4
- `CVATS_MarketExecution_Proof.pdf` — Preuve d'exécution marché (3 pages)
- `CVATS_Annexe_Screenshots.pdf` — Annexe screenshots + Thomas Hacala + AirBnB (6 pages)
- `RAYMOND_GADJI.md` — contexte fondateur
- `KOUSH_APP.md` — projet GEO Monitor Africa

---

## 🏆 DOSSIER STATION F — ROUND 2

### Réponses formulaire de soumission

**Have you pivoted since Round 1?**
No — itération produit basée sur les feedbacks, pas un pivot. Même problème, même cible, même business model.

**What changes have been made to the founding team?**
No changes have been made to the founding team. Raymond Gadji (Founder & CEO), Mamadou Fedior (Co-Founder) and Saïdi Ahamada (Co-Founder) have been part of the team since Round 1 and remain fully committed to the project.

**What are the most important achievements you've accomplished since your initial Round 1 application?**

Since our Round 1 application, we have accomplished the following key milestones:

Product & Technical:
- Launched CV-ATS.COM in full production — a complete AI agent, not a prototype
- Built and shipped 6 major features based on real user feedback: Autopilot job matching (France Travail + Adzuna APIs), automatic URL fetch, dynamic ATS scoring, 6-style cover letter generator, PDF/Word/Text export, and real-time PostgreSQL analytics
- Rebranded from cv-ats-ready to cv-ats.com following user feedback

Traction:
- 33 real CV optimizations completed — average ATS score improvement from 42% to 86%
- 20 payment intents initiated — strong purchase signal ahead of Stripe activation
- Cited spontaneously by Grok (xAI / Elon Musk) with 39 sources and Perplexity with 10 sources — zero paid advertising

Market Validation:
- 3 official advisory sessions with Philip Dietrich (CCI75 — CCI Paris Île-de-France) — market validation, pitch analysis, business plan review — all signed via DocuSign
- Nearly 20 users provided oral feedback that directly shaped product features — inspired by the Y Combinator / Airbnb methodology of listening to users first
- Thomas Hacala (Station F alumni, founder of Ralator.io) introduced us to GEO — we implemented Schema.org JSON-LD and are now indexed by major AI engines

Recognition:
- Lauréat — Challenge Open Data data.gouv.fr 2026 (creator of the IRD — Indice de Représentativité Démocratique)

**Version courte (400 caractères max — pour le formulaire) :**
CV-ATS.COM launched in production: 33 real optimizations, ATS score +44pts average (42%→86%), 20 payment intents. 6 features shipped from user feedback (Autopilot, URL fetch, dynamic scoring). Cited by Grok (39 sources) + Perplexity (10 sources). 3 official CCI Paris advisory sessions (DocuSign). Rebranded to cv-ats.com.

**Which problem is your startup solving? (version courte 400 chars) :**
95% of companies use ATS software to filter CVs automatically — 75% of candidates are rejected before any human reads them. No affordable, French-language solution exists. CV-ATS.COM rewrites your CV for ATS in 30 seconds for 1€ HT. 33 real optimizations, average score +44pts (42%→86%).

**Which problem is your startup solving? (version longue — référence) :**
Every year, millions of French-speaking job seekers send dozens of applications that never reach a human recruiter. The reason is not a lack of qualifications — it is a software filter called an ATS (Applicant Tracking System), used by 95% of large companies, multinationals, and international organizations to automatically screen CVs before any human reads them. 75% of applications are eliminated at this stage.

The problem is structural and invisible. A candidate can be perfectly qualified for a role, yet their CV gets rejected automatically because it does not contain the exact keywords the ATS is scanning for, or because the formatting confuses the parsing algorithm. They never know why they were rejected. They apply again, with the same CV, and face the same invisible wall.

Existing solutions — Jobscan, Resume Worded — address this problem but only for English-speaking markets. They cost between $30 and $100 per month, require a credit card, and are entirely in English. The French-speaking market — 3.7 million active job seekers in France alone, plus Belgium, Switzerland, Luxembourg, and Quebec — has no accessible, affordable, native-language solution.

Beyond the language barrier, there is a social and economic dimension. Young graduates from working-class backgrounds, career changers, and candidates from African francophone countries applying to multinationals are disproportionately affected. They are the least likely to know about ATS optimization, and the least able to pay $50/month for a tool to fix it.

CV-ATS.COM addresses this problem directly. For 1€ HT — the price of a coffee — any candidate can paste a job offer, upload their CV, and receive in 30 seconds a fully rewritten, ATS-optimized CV with a before/after score across 4 categories, a personalized cover letter in 6 styles, and automatic job matching via the official France Travail and Adzuna APIs.

The product is already in production. 33 real optimizations have been completed, with an average ATS score improvement from 42% to 86% — a gain of 44 points. Real candidates, real CVs, real job offers. The problem is real, the solution works, and the market is waiting.

**Background des co-fondateurs :**

Raymond Gadji — Founder & CEO
Data Analyst & Developer / Self-employed / 2024–present / Lauréat Challenge Open Data data.gouv.fr 2026, creator of IRD (Indice de Représentativité Démocratique), cited by Banque des Territoires. Bootcamp Data Analyst Simplon Paris. Formation Développeur EmLyon La Toile. Certified Hugging Face. Built CV-ATS.COM from zero to production in 3 weeks.

Mamadou Fedior — Co-Founder
Business Development / CV-ATS.COM / 2026–present / EmLyon La Toile graduate. Leads commercial development and B2B partnerships. Core team member since Round 1. Contact: macfedior@hotmail.fr

Saïdi Ahamada — Co-Founder
Product Strategy / CV-ATS.COM / 2026–present / EmLyon La Toile graduate. Leads product strategy and francophone market expansion. Core team member since Round 1. Contact: saidi.ahamada@outlook.com

**One-liner (30 words max) :**
AI agent that rewrites your CV to pass ATS filters in 30 seconds. Includes ATS score, cover letter, and automatic job matching via France Travail.

**Which problem is your startup solving? (400 chars) :**
95% of companies use ATS software to filter CVs — 75% of candidates are rejected before any human reads them. No affordable French-language solution exists. CV-ATS.COM rewrites your CV to pass ATS filters in 30 seconds, generates a cover letter, and matches job offers automatically. 33 optimizations, score +44pts (42%→86%). Cited by Grok and Perplexity.

**Target market (200 chars) :**
French-speaking job seekers in France & Europe. TAM: €22M/year (3.7M candidates × 3,99€). SAM: €2.2M (digital users). SOM: €36K in 2027 (200 subscribers × 9,99€ × 12 months).

**ICP :**
25–35, active on LinkedIn, sending 10+ apps/week with no reply. Knows ATS exist but can't beat them. Wants their CV optimized instantly — no effort, no course, just results in 30 seconds.

**Competitive advantage :**
Unlike ChatGPT (requires effort) or expensive HR tools (€50–200/month), CV-ATS.COM is fully automated, no subscription, €1 per use. Drop your CV and job offer — AI handles everything in 30 seconds. Only French-language ATS tool with official France Travail API integration and cited by Grok + Perplexity.

**What are people currently using instead? :**
ChatGPT (free but requires effort & prompting), Rezi/Jobscan (€20–30/month, English-only), CV coaches (€100–300/session), or nothing at all. Most candidates send unoptimized CVs without knowing ATS exist.

**Cap table :**
Raymond Gadji 100% — Mamadou Fedior and Saïdi Ahamada are active contributors. No formal equity split yet — société not yet created. Open to dilution for the right accelerator or angel investor.

**Total raised to date :** 0

**Fundraising — montant :** 25 000€

**Fundraising — objectifs (200 chars) :**
Company creation: €3.5K. Infrastructure: €3K. Marketing & acquisition: €13K. Founder runway 6 months: €5.5K. Goal: 500 paying users before seed round.

**Startup program :** Yes — Station F Fighters Program — May 2026 (Round 1 completed, applying for Round 2)

**Seats on campus :** 2 — Raymond Gadji (Founder & CEO) + Mamadou Fedior (Co-Founder)

**Anything else :**
cv-ats.com is live, functional, and built entirely by one person in under 3 months. I'm not here to pitch a dream — I'm here to scale a working product. Station F would give me the structure and community to do it faster.

### PDFs soumis
- `CVATS_PitchDeck_Round2_StationF.pdf`
- `CVATS_ProofExecution_Product.pdf` — Loom : https://www.loom.com/share/d6607305f0bf4bd3926d3e3cbcc17a7f · YouTube : https://youtu.be/YxzzGaG3hP4
- `CVATS_MarketExecution_Proof.pdf`
- `CVATS_Annexe_Screenshots.pdf`

---

CV ATS et Link2Job sont deux projets du même founder (Raymond Gadji).
Fusion prévue à terme — cv-ats.com intégré dans link2job.fr.
Pour l'instant les deux tournent indépendamment.
Voir **CLAUDE_LINK_TO_JOB.md** pour le projet Link2Job.
