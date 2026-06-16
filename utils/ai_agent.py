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
   - Intègre les mots-clés exacts de l'offre naturellement
   - Structure claire : NOM, COORDONNÉES, RÉSUMÉ PROFESSIONNEL, COMPÉTENCES, EXPÉRIENCES, FORMATION
   - Pas de colonnes, tableaux, icônes (illisibles par les ATS)
   - Verbes d'action forts, chiffres quand possible
   - Ne jamais inventer de fausses informations

2. Calcule les scores ATS RÉELS et HONNÊTES basés sur l'analyse du CV original et du CV réécrit :
   - score_avant : évalue VRAIMENT le CV original (compte les mots-clés manquants, problèmes de format, expérience non mise en valeur)
   - score_apres : évalue VRAIMENT le CV réécrit après optimisation
   - Les scores DOIVENT varier selon le CV fourni — un bon CV aura un score_avant plus élevé, un mauvais CV aura un score_avant plus bas
   - Ne jamais mettre la même valeur systématiquement
   - 4 catégories à évaluer séparément et honnêtement

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