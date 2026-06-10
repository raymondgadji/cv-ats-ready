"""
utils/autopilot.py — CV ATS v2
Job matching France Travail API + Adzuna
"""

import os
import re
import json
import httpx
from typing import Optional

FRANCE_TRAVAIL_CLIENT_ID     = os.environ.get("FRANCE_TRAVAIL_CLIENT_ID", "")
FRANCE_TRAVAIL_CLIENT_SECRET = os.environ.get("FRANCE_TRAVAIL_CLIENT_SECRET", "")
ADZUNA_APP_ID                = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY               = os.environ.get("ADZUNA_APP_KEY", "")


# ─────────────────────────────────────────
# EXTRACTION MOTS-CLÉS
# ─────────────────────────────────────────

def extract_keywords(cv_text: str, job_offer: str) -> dict:
    """
    Extrait le poste et mots-clés depuis l'offre d'emploi.
    Stratégie : chercher les mots-clés métier les plus fréquents.
    """
    import re
    from collections import Counter

    IGNORE_WORDS = {
        "coordonnées","nom","prénom","adresse","email","téléphone","tel",
        "mobile","linkedin","profil","curriculum","vitae","date","naissance",
        "nationalité","permis","contact","évoluez","vers","métier","bonjour",
        "construisez","carrière","votre","notre","poste","offre","emploi",
        "le","la","les","un","une","des","de","du","et","en","à","au","aux",
        "pour","par","sur","avec","dans","qui","que","est","sont","nous",
        "vous","ils","elles","je","tu","il","elle","se","sa","son","ses",
        "cette","ce","cet","ces","mais","aussi","très","plus","tout","tous",
        "bien","faire","nous","votre","entre","ainsi","dont","lors","après",
        "avant","sans","sous","lors","même","comme","plus","dans","être",
        "avoir","nous","vous","leur","leurs","cette","afin","type","cadre",
        "sein","nous","vous","toute","toutes","tous","chaque","autre","autres",
    }

    # ── Mots-clés métier : les plus fréquents dans l'offre, longueur > 4
    words = re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', job_offer.lower())
    filtered = [w for w in words if w not in IGNORE_WORDS]
    freq = Counter(filtered)
    # Top 3 mots les plus fréquents = le cœur du métier
    top = [w for w, _ in freq.most_common(10) if len(w) >= 5][:3]
    keywords = " ".join(top)

    # ── Poste : top 2 mots-clés suffisent pour une bonne query
    poste = " ".join(top[:2]) if top else keywords[:40]

    # ── Localisation dans l'offre et le CV
    localisation = ""
    VILLES = [
        "paris","lyon","marseille","toulouse","bordeaux","nantes","lille",
        "strasbourg","montpellier","nice","rennes","grenoble","dijon","angers",
    ]
    combined = (cv_text + " " + job_offer).lower()
    for ville in VILLES:
        if re.search(r'\b' + ville + r'\b', combined):
            localisation = ville.capitalize()
            break

    print(f"🎯 Keywords extraits — poste: '{poste}' | keywords: '{keywords}' | loc: '{localisation}'")

    return {
        "poste":        poste,
        "keywords":     keywords,
        "localisation": localisation,
    }


# ─────────────────────────────────────────
# FRANCE TRAVAIL API — token OAuth2
# ─────────────────────────────────────────

def _get_france_travail_token() -> Optional[str]:
    if not FRANCE_TRAVAIL_CLIENT_ID or not FRANCE_TRAVAIL_CLIENT_SECRET:
        print(f"⚠️  France Travail : CLIENT_ID={bool(FRANCE_TRAVAIL_CLIENT_ID)} SECRET={bool(FRANCE_TRAVAIL_CLIENT_SECRET)}")
        return None
    try:
        # ✅ URL correcte 2026
        resp = httpx.post(
            "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire",
            data={
                "grant_type":    "client_credentials",
                "client_id":     FRANCE_TRAVAIL_CLIENT_ID,
                "client_secret": FRANCE_TRAVAIL_CLIENT_SECRET,
                "scope":         "api_offresdemploiv2 o2dsoffre",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        print(f"🔑 France Travail token status : {resp.status_code}")
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            print(f"✅ France Travail token OK : {token[:20]}...")
            return token
        else:
            print(f"❌ France Travail token error : {resp.text[:300]}")
    except Exception as e:
        print(f"❌ France Travail token exception : {e}")
    return None


def fetch_france_travail(keywords: dict, nb: int = 25) -> list:
    token = _get_france_travail_token()
    if not token:
        return []
    try:
        # Mots-clés courts — top 2 mots max pour France Travail
        mots = (keywords["poste"] or keywords["keywords"]).split()[:2]
        query_ft = " ".join(mots)

        params = {
            "motsCles": query_ft,
            "range":    f"0-{nb - 1}",
            "sort":     "1",
        }
        # ✅ Pas de filtre géographique — trop restrictif, laisse chercher France entière

        resp = httpx.get(
            "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept":        "application/json",
            },
            params=params,
            timeout=15,
        )
        print(f"🔍 France Travail search status : {resp.status_code}")
        # ✅ 200 = OK, 206 = Partial Content (résultats trouvés, pagination possible)
        if resp.status_code == 204:
            print(f"⚠️  France Travail : aucun résultat (204)")
            return []
        if resp.status_code not in (200, 206):
            print(f"❌ France Travail search error : {resp.text[:300]}")
            return []

        offres = resp.json().get("resultats", [])
        print(f"✅ France Travail : {len(offres)} offres trouvées")
        results = []
        for o in offres:
            results.append({
                "source":       "France Travail",
                "titre":        o.get("intitule", ""),
                "entreprise":   o.get("entreprise", {}).get("nom", "Non précisé"),
                "localisation": o.get("lieuTravail", {}).get("libelle", ""),
                "contrat":      o.get("typeContratLibelle", ""),
                "url":          o.get("origineOffre", {}).get("urlOrigine", "")
                                or f"https://candidat.francetravail.fr/offres/recherche/detail/{o.get('id','')}",
                "date":         o.get("dateCreation", "")[:10] if o.get("dateCreation") else "",
                "description":  (o.get("description", "")[:300] + "...") if o.get("description") else "",
                "salaire":      o.get("salaire", {}).get("libelle", ""),
            })
        return results
    except Exception as e:
        print(f"❌ France Travail fetch exception : {e}")
        return []


# ─────────────────────────────────────────
# ADZUNA API
# ─────────────────────────────────────────

def fetch_adzuna(keywords: dict, nb: int = 25) -> list:
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        print(f"⚠️  Adzuna : APP_ID={bool(ADZUNA_APP_ID)} APP_KEY={bool(ADZUNA_APP_KEY)}")
        return []
    try:
        # Query courte pour Adzuna — max 3 mots clés
        mots = (keywords["poste"] or keywords["keywords"]).split()[:3]
        query = " ".join(mots)
        params = {
            "app_id":           ADZUNA_APP_ID,
            "app_key":          ADZUNA_APP_KEY,
            "results_per_page": nb,
            "what":             query,
            "sort_by":          "relevance",
        }
        if keywords["localisation"]:
            params["where"] = keywords["localisation"]

        resp = httpx.get(
            "https://api.adzuna.com/v1/api/jobs/fr/search/1",
            params=params,
            timeout=15,
        )
        print(f"🔍 Adzuna search status : {resp.status_code}")
        if resp.status_code != 200:
            print(f"❌ Adzuna error : {resp.text[:300]}")
            return []

        offres = resp.json().get("results", [])
        print(f"✅ Adzuna : {len(offres)} offres trouvées")
        results = []
        for o in offres:
            results.append({
                "source":       "Adzuna",
                "titre":        o.get("title", ""),
                "entreprise":   o.get("company", {}).get("display_name", "Non précisé"),
                "localisation": o.get("location", {}).get("display_name", ""),
                "contrat":      o.get("contract_type", "") or o.get("contract_time", ""),
                "url":          o.get("redirect_url", ""),
                "date":         o.get("created", "")[:10] if o.get("created") else "",
                "description":  (o.get("description", "")[:300] + "...") if o.get("description") else "",
                "salaire":      f"{o['salary_min']:.0f}€ - {o['salary_max']:.0f}€/an"
                                if o.get("salary_min") and o.get("salary_max") else "",
            })
        return results
    except Exception as e:
        print(f"❌ Adzuna fetch exception : {e}")
        return []


# ─────────────────────────────────────────
# FONCTION PRINCIPALE
# ─────────────────────────────────────────

def find_matching_jobs(cv_optimized: str, job_offer: str, nb_total: int = 40) -> dict:
    keywords = extract_keywords(cv_optimized, job_offer)
    print(f"🎯 Autopilot keywords : {keywords}")
    nb_each  = nb_total // 2

    ft_jobs = fetch_france_travail(keywords, nb=nb_each)
    az_jobs = fetch_adzuna(keywords,         nb=nb_each)

    all_jobs = []
    for i in range(max(len(ft_jobs), len(az_jobs))):
        if i < len(ft_jobs): all_jobs.append(ft_jobs[i])
        if i < len(az_jobs): all_jobs.append(az_jobs[i])

    return {
        "keywords":       keywords,
        "total":          len(all_jobs),
        "france_travail": len(ft_jobs),
        "adzuna":         len(az_jobs),
        "offres":         all_jobs,
    }