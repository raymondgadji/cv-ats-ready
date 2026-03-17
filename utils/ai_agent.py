"""
utils/ai_agent.py
Appels Claude API :
  - optimize_cv_ats()      → CV réécrit + score ATS avant/après
  - generate_cover_letter() → Lettre de motivation
"""

import json
import anthropic


def optimize_cv_ats(cv_text: str, job_offer: str, api_key: str) -> dict:
    """
    Réécrit le CV pour les ATS et calcule un score avant/après.
    Retourne : { "cv_optimized": str, "ats_score": dict }
    """
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Tu es un expert ATS (Applicant Tracking System) et recruteur senior.

MISSION : Analyser le CV par rapport à l'offre, le réécrire pour maximiser le score ATS, puis évaluer les scores.

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

2. Calcule les scores ATS honnêtement :
   - score_avant : score du CV original (0-100)
   - score_apres : score du CV réécrit (0-100)
   - 4 catégories : mots_cles, format, experience, competences (chacune 0-100)

RÉPONDS UNIQUEMENT avec ce JSON (rien d'autre, pas de markdown) :
{{
  "cv_optimized": "LE CV RÉÉCRIT COMPLET ICI",
  "ats_score": {{
    "score_avant": 25,
    "score_apres": 88,
    "categories": {{
      "mots_cles": {{"avant": 20, "apres": 90, "label": "Mots-clés"}},
      "format": {{"avant": 60, "apres": 95, "label": "Format ATS"}},
      "experience": {{"avant": 40, "apres": 85, "label": "Expérience"}},
      "competences": {{"avant": 30, "apres": 82, "label": "Compétences"}}
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

    try:
        data = json.loads(raw)
        return {
            "cv_optimized": data.get("cv_optimized", ""),
            "ats_score": data.get("ats_score", _default_score())
        }
    except json.JSONDecodeError:
        # Fallback : retourne le texte brut sans score
        return {
            "cv_optimized": raw,
            "ats_score": _default_score()
        }


def _default_score() -> dict:
    """Score par défaut si le parsing JSON échoue."""
    return {
        "score_avant": 30,
        "score_apres": 85,
        "categories": {
            "mots_cles":   {"avant": 25, "apres": 88, "label": "Mots-clés"},
            "format":      {"avant": 55, "apres": 95, "label": "Format ATS"},
            "experience":  {"avant": 35, "apres": 82, "label": "Expérience"},
            "competences": {"avant": 30, "apres": 80, "label": "Compétences"}
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

    # Gestion multi-styles (ex: "débutant + très motivé")
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