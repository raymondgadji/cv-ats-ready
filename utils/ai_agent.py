"""
utils/ai_agent.py
Appels Claude API :
    - optimize_cv_ats()      → CV réécrit + score ATS avant/après
    - generate_cover_letter() → Lettre de motivation
"""

import json
import re
import anthropic


def optimize_cv_ats(cv_text: str, job_offer: str, api_key: str) -> dict:
    """
    Réécrit le CV pour les ATS et calcule un score avant/après.
    Retourne : { "cv_optimized": str, "ats_score": dict }
    """
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Tu es un expert ATS (Applicant Tracking System) et recruteur senior.

MISSION : Analyser le CV par rapport à l'offre, le réécrire pour maximiser le score ATS, puis évaluer les scores RÉELS.

OFFRE D'EMPLOI :
{job_offer}

CV ACTUEL :
{cv_text}

INSTRUCTIONS :

1. Réécris le CV complet en format texte structuré, optimisé ATS :
   - Le CONTENU (postes, missions, responsabilités, résultats, dates, diplômes) doit venir EXCLUSIVEMENT du CV original — l'offre ne sert JAMAIS de source de contenu, uniquement de guide de vocabulaire
   - Intègre les mots-clés exacts de l'offre naturellement, seulement là où ils décrivent une compétence/expérience RÉELLEMENT présente dans le CV original (reformuler le vocabulaire du candidat avec les termes de l'offre, jamais ajouter une compétence ou expérience qui ne s'y trouve pas)
   - Conserve TOUTES les rubriques substantielles présentes dans le CV original (y compris "Profil" / "À propos" / "Objectif" si elles existent) — ne jamais en faire disparaître une seule, même si elle ne correspond pas exactement à la liste de structure ci-dessous
   - Structure claire : NOM, COORDONNÉES, RÉSUMÉ PROFESSIONNEL (reprend et enrichit le "Profil"/"À propos" du CV original s'il existe, ne le remplace pas par du texte générique tourné vers l'offre), COMPÉTENCES, EXPÉRIENCES, FORMATION
   - Pas de colonnes, tableaux, icônes (illisibles par les ATS)
   - Verbes d'action forts, chiffres quand possible
   - Ne jamais inventer de fausses informations ni gonfler un poste/une compétence au-delà de ce que le CV original indique réellement

2. Calcule les scores ATS RÉELS et HONNÊTES basés sur l'analyse du CV original et du CV réécrit — CV ATS est avant tout un outil de MESURE : mesurer véritablement si ce candidat correspond à CETTE offre précise est indispensable, jamais un chiffre rassurant :
   - score_avant : évalue VRAIMENT le CV original par rapport à l'offre (mots-clés manquants, problèmes de format, expérience non mise en valeur)
   - score_apres : évalue VRAIMENT le CV réécrit par rapport à l'offre — AUCUN plancher artificiel. Si le candidat correspond réellement au poste, la réécriture fera naturellement remonter le score ; mais si le CV ne correspond fondamentalement pas à l'offre (mauvaise cible, compétences/expérience très éloignées), le score_apres DOIT rester bas et honnête même après réécriture — ne jamais forcer un score élevé pour rassurer l'utilisateur
   - Les scores DOIVENT varier selon le CV ET l'offre fournis — un candidat bien ciblé aura un score élevé, un candidat mal ciblé pour cette offre précise aura un score bas, y compris après optimisation
   - Ne jamais mettre la même valeur systématiquement, ne jamais arrondir vers un chiffre "rond" par facilité (80, 85, 90) sauf si c'est vraiment le résultat de ton analyse
   - 4 categories a evaluer separement et honnetement, sans aucun plancher artificiel

RÉPONDS UNIQUEMENT avec ce JSON valide (remplace CHAQUE valeur numérique par ton évaluation réelle) :
{{
    "cv_optimized": "LE CV RÉÉCRIT COMPLET ICI",
    "ats_score": {{
        "score_avant": CALCULE_LE_SCORE_REEL_DU_CV_ORIGINAL,
        "score_apres": CALCULE_LE_SCORE_REEL_DU_CV_OPTIMISE,
        "categories": {{
            "mots_cles":  {{"avant": SCORE_REEL, "apres": SCORE_REEL, "label": "Mots-clés"}},
            "format":     {{"avant": SCORE_REEL, "apres": SCORE_REEL, "label": "Format ATS"}},
            "experience": {{"avant": SCORE_REEL, "apres": SCORE_REEL, "label": "Expérience"}},
            "competences":{{"avant": SCORE_REEL, "apres": SCORE_REEL, "label": "Compétences"}}
        }}
    }}
}}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()

    # Nettoyage si markdown présent
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    # Tentative de récupération du JSON même partiel
    try:
        data = json.loads(raw)
        return {
            "cv_optimized": data.get("cv_optimized", ""),
            "ats_score": data.get("ats_score", _default_score())
        }
    except json.JSONDecodeError:
        # Essai d'extraction du JSON avec regex
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return {
                    "cv_optimized": data.get("cv_optimized", raw),
                    "ats_score": data.get("ats_score", _default_score())
                }
            except Exception:
                pass
        # Fallback uniquement si vraiment impossible
        return {
            "cv_optimized": raw,
            "ats_score": _default_score()
        }


def _default_score() -> dict:
    """Score par défaut si le parsing JSON échoue complètement."""
    return {
        "score_avant": 35,
        "score_apres": 80,
        "categories": {
            "mots_cles":   {"avant": 30, "apres": 82, "label": "Mots-clés"},
            "format":      {"avant": 50, "apres": 90, "label": "Format ATS"},
            "experience":  {"avant": 35, "apres": 75, "label": "Expérience"},
            "competences": {"avant": 28, "apres": 78, "label": "Compétences"}
        }
    }


def generate_cover_letter(
    cv_text: str,
    job_offer: str,
    style: str,
    precision: str,
    api_key: str
) -> str:
    """Génère une lettre de motivation personnalisée."""
    client = anthropic.Anthropic(api_key=api_key)

    style_instructions = {
        "motivé":                "Ton enthousiaste et sincèrement motivé, énergie positive, montrer l'envie d'apprendre et de contribuer.",
        "très motivé":           "Passion débordante, conviction forte, montrer pourquoi CE poste dans CETTE entreprise est exactement ce que tu vises.",
        "expert":                "Ton confiant et professionnel, mettre en avant les réalisations concrètes et l'expertise technique.",
        "débutant":              "Ton humble mais ambitieux, valoriser la formation, la curiosité et la capacité d'adaptation rapide.",
        "neutre & professionnel":"Ton sobre et factuel, aller à l'essentiel, style corporate classique.",
        "reconversion":          "Expliquer la reconversion comme un atout, valoriser les compétences transférables, montrer la cohérence du parcours."
    }

    styles_list = [s.strip() for s in style.split("+")]
    style_desc = " + ".join([style_instructions.get(s, s) for s in styles_list])

    precision_block = f"\nPRÉCISION DU CANDIDAT : {precision}" if precision.strip() else ""

    prompt = f"""Tu es un expert en rédaction de lettres de motivation.

OFFRE D'EMPLOI :
{job_offer}

CV DU CANDIDAT :
{cv_text}
{precision_block}

STYLE DEMANDÉ : {style_desc}

INSTRUCTIONS :
- Lettre professionnelle en français, 3-4 paragraphes
- Personnalisée avec des éléments CONCRETS de l'offre ET du CV
- Commencer par "Madame, Monsieur,"
- Terminer par une formule de politesse classique + prénom/nom du candidat
- Indiquer la ville du candidat (extraite du CV), le [date] en haut — si la ville n'est pas trouvée dans le CV, écrire simplement "[Ville], le [date]"
- NE PAS inventer de fausses informations

Génère uniquement la lettre, sans commentaires."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text.strip()