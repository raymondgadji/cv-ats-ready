"""
utils/autopilot.py — CV ATS
Scrape des offres d'emploi depuis France Travail API + Adzuna
en fonction des mots-clés extraits du CV optimisé.
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
# EXTRACTION MOTS-CLÉS depuis le CV optimisé
# ─────────────────────────────────────────

def extract_keywords(cv_text: str, job_offer: str) -> dict:
    """
    Extrait le poste visé et les mots-clés principaux
    depuis le CV optimisé et l'offre d'origine.
    Retourne : { "poste": str, "keywords": str, "localisation": str }
    """
    # Cherche un titre de poste dans les premières lignes du CV
    lines = [l.strip() for l in cv_text.split("\n") if l.strip()]
    poste = lines[1] if len(lines) > 1 else lines[0] if lines else ""

    # Nettoie le poste (enlève les caractères parasites)
    poste = re.sub(r"[|•·–—]", "", poste).strip()
    if len(poste) > 60:
        poste = poste[:60]

    # Cherche la localisation (Paris, Lyon, etc.)
    localisation = ""
    loc_patterns = [
        r"\b(Paris|Lyon|Marseille|Toulouse|Bordeaux|Nantes|Lille|Strasbourg|"
        r"Montpellier|Nice|Rennes|Grenoble|Dijon|Angers|remote|télétravail)\b"
    ]
    for pattern in loc_patterns:
        match = re.search(pattern, cv_text + " " + job_offer, re.IGNORECASE)
        if match:
            localisation = match.group(1)
            break

    # Mots-clés depuis l'offre d'emploi (premiers mots significatifs)
    stopwords = {"le","la","les","un","une","des","de","du","et","en","à","au","pour",
                 "par","sur","avec","dans","qui","que","est","sont","nous","vous","ils"}
    words = re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', job_offer.lower())
    keywords = " ".join([w for w in words if w not in stopwords][:8])

    return {
        "poste":        poste or keywords[:40],
        "keywords":     keywords,
        "localisation": localisation,
    }


# ─────────────────────────────────────────
# FRANCE TRAVAIL API
# ─────────────────────────────────────────

def _get_france_travail_token() -> Optional[str]:
    """Obtient un token OAuth2 France Travail."""
    if not FRANCE_TRAVAIL_CLIENT_ID or not FRANCE_TRAVAIL_CLIENT_SECRET:
        return None
    try:
        resp = httpx.post(
            "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
            "?realm=%2Fpartenaire",
            data={
                "grant_type":    "client_credentials",
                "client_id":     FRANCE_TRAVAIL_CLIENT_ID,
                "client_secret": FRANCE_TRAVAIL_CLIENT_SECRET,
                "scope":         "api_offresdemploiv2 o2dsoffre",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
    except Exception as e:
        print(f"⚠️  France Travail token error : {e}")
    return None


def fetch_france_travail(keywords: dict, nb: int = 25) -> list:
    """Récupère des offres depuis France Travail API."""
    token = _get_france_travail_token()
    if not token:
        print("⚠️  France Travail : pas de token")
        return []

    try:
        params = {
            "motsCles":   keywords["poste"] or keywords["keywords"],
            "range":      f"0-{nb - 1}",
            "sort":       "1",  # tri par pertinence
        }
        if keywords["localisation"]:
            params["commune"] = keywords["localisation"]

        resp = httpx.get(
            "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept":        "application/json",
            },
            params=params,
            timeout=15,
        )

        if resp.status_code != 200:
            print(f"⚠️  France Travail API {resp.status_code} : {resp.text[:200]}")
            return []

        offres = resp.json().get("resultats", [])
        results = []
        for o in offres:
            results.append({
                "source":      "France Travail",
                "titre":       o.get("intitule", ""),
                "entreprise":  o.get("entreprise", {}).get("nom", "Non précisé"),
                "localisation":o.get("lieuTravail", {}).get("libelle", ""),
                "contrat":     o.get("typeContratLibelle", ""),
                "url":         o.get("origineOffre", {}).get("urlOrigine", "")
                               or f"https://candidat.francetravail.fr/offres/recherche/detail/{o.get('id','')}",
                "date":        o.get("dateCreation", "")[:10] if o.get("dateCreation") else "",
                "description": o.get("description", "")[:300] + "..." if o.get("description") else "",
                "salaire":     o.get("salaire", {}).get("libelle", ""),
            })
        return results

    except Exception as e:
        print(f"⚠️  France Travail fetch error : {e}")
        return []


# ─────────────────────────────────────────
# ADZUNA API
# ─────────────────────────────────────────

def fetch_adzuna(keywords: dict, nb: int = 25) -> list:
    """Récupère des offres depuis Adzuna API."""
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        print("⚠️  Adzuna : clés manquantes")
        return []

    try:
        query = keywords["poste"] or keywords["keywords"]
        params = {
            "app_id":        ADZUNA_APP_ID,
            "app_key":       ADZUNA_APP_KEY,
            "results_per_page": nb,
            "what":          query,
            "content-type":  "application/json",
            "sort_by":       "relevance",
        }
        if keywords["localisation"]:
            params["where"] = keywords["localisation"]

        resp = httpx.get(
            "https://api.adzuna.com/v1/api/jobs/fr/search/1",
            params=params,
            timeout=15,
        )

        if resp.status_code != 200:
            print(f"⚠️  Adzuna API {resp.status_code} : {resp.text[:200]}")
            return []

        offres = resp.json().get("results", [])
        results = []
        for o in offres:
            results.append({
                "source":      "Adzuna",
                "titre":       o.get("title", ""),
                "entreprise":  o.get("company", {}).get("display_name", "Non précisé"),
                "localisation":o.get("location", {}).get("display_name", ""),
                "contrat":     o.get("contract_type", "") or o.get("contract_time", ""),
                "url":         o.get("redirect_url", ""),
                "date":        o.get("created", "")[:10] if o.get("created") else "",
                "description": o.get("description", "")[:300] + "..." if o.get("description") else "",
                "salaire":     f"{o['salary_min']:.0f}€ - {o['salary_max']:.0f}€/an"
                               if o.get("salary_min") and o.get("salary_max") else "",
            })
        return results

    except Exception as e:
        print(f"⚠️  Adzuna fetch error : {e}")
        return []


# ─────────────────────────────────────────
# FONCTION PRINCIPALE
# ─────────────────────────────────────────

def find_matching_jobs(cv_optimized: str, job_offer: str, nb_total: int = 40) -> dict:
    """
    Fonction principale appelée depuis main.py.
    Retourne les offres matchées depuis France Travail + Adzuna.
    """
    keywords = extract_keywords(cv_optimized, job_offer)
    nb_each  = nb_total // 2  # moitié depuis chaque source

    ft_jobs  = fetch_france_travail(keywords, nb=nb_each)
    az_jobs  = fetch_adzuna(keywords,         nb=nb_each)

    # Mélange les deux sources en alternant
    all_jobs = []
    for i in range(max(len(ft_jobs), len(az_jobs))):
        if i < len(ft_jobs): all_jobs.append(ft_jobs[i])
        if i < len(az_jobs): all_jobs.append(az_jobs[i])

    return {
        "keywords":          keywords,
        "total":             len(all_jobs),
        "france_travail":    len(ft_jobs),
        "adzuna":            len(az_jobs),
        "offres":            all_jobs,
    }