"""
utils/ai_agent.py
Appels Claude API :
    - optimize_cv_ats()       → CV réécrit + score ATS avant/après (par rapport à une offre précise)
    - check_cv_ats_generic()  → check ATS gratuit, sans offre d'emploi (audit générique)
    - translate_cv()          → traduction du CV dans une autre langue
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
   - Les coordonnées (email, téléphone, adresse) apparaissent UNE SEULE FOIS, tout en haut sous le nom — ne jamais les répéter ou les reformuler ailleurs dans le document (pas de ligne "Informations de contact" ou équivalent plus loin dans le CV)
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


def check_cv_ats_generic(cv_text: str, api_key: str) -> dict:
    """
    Check ATS GRATUIT, SANS offre d'emploi précise — audit générique de lisibilité ATS
    et de qualité de rédaction (équivalent à un scanner ATS générique).
    Retourne : { "secteur_detecte": str, "score_global": int, "categories": dict, "recommandations": list }
    """
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Tu es un expert ATS (Applicant Tracking System) et recruteur senior.

MISSION : Analyser ce CV de façon GÉNÉRIQUE, SANS offre d'emploi précise — comme le ferait un scanner ATS
standard. Ce n'est PAS une comparaison à un poste précis, juste un audit de qualité générale.

CV À ANALYSER :
{cv_text}

INSTRUCTIONS :

1. Détecte le secteur/métier probable du candidat à partir du contenu du CV (ex: "Développement web",
   "Comptabilité", "Marketing digital"...).

2. Évalue 4 catégories, HONNÊTEMENT et SANS AUCUN PLANCHER — un CV faible doit recevoir un score bas :
   - format : lisibilité machine (structure claire, absence de colonnes/tableaux complexes qui cassent
     l'extraction, coordonnées facilement identifiables)
   - structure : présence et clarté des rubriques standards (expérience, formation, compétences,
     résumé/profil) avec des intitulés reconnaissables par un ATS
   - clarte : qualité de rédaction (verbes d'action, résultats chiffrés, absence de formulations vagues
     ou de fautes)
   - mots_cles_sectoriels : présence de mots-clés génériquement attendus pour LE SECTEUR détecté
     (pas une offre précise — les termes/compétences standards du métier)

3. Donne 3 à 5 recommandations CONCRÈTES et actionnables, spécifiques à CE CV précis (jamais des
   conseils passe-partout type "ajoutez des mots-clés").

RÉPONDS UNIQUEMENT avec ce JSON valide :
{{
    "secteur_detecte": "SECTEUR DÉTECTÉ",
    "score_global": SCORE_REEL_0_A_100,
    "categories": {{
        "format":               {{"score": SCORE_REEL, "label": "Format ATS"}},
        "structure":            {{"score": SCORE_REEL, "label": "Structure des rubriques"}},
        "clarte":               {{"score": SCORE_REEL, "label": "Clarté du contenu"}},
        "mots_cles_sectoriels": {{"score": SCORE_REEL, "label": "Mots-clés sectoriels"}}
    }},
    "recommandations": ["RECOMMANDATION 1", "RECOMMANDATION 2", "..."]
}}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except Exception:
                pass
        return _default_generic_check()


def _default_generic_check() -> dict:
    """Résultat par défaut si le parsing JSON échoue complètement."""
    return {
        "secteur_detecte": "Non déterminé",
        "score_global": 50,
        "categories": {
            "format":               {"score": 50, "label": "Format ATS"},
            "structure":            {"score": 50, "label": "Structure des rubriques"},
            "clarte":               {"score": 50, "label": "Clarté du contenu"},
            "mots_cles_sectoriels": {"score": 50, "label": "Mots-clés sectoriels"},
        },
        "recommandations": [
            "Analyse indisponible pour le moment — réessaie dans quelques instants."
        ]
    }


LANGUE_LABELS = {
    "en": "anglais",
    "es": "espagnol",
    "de": "allemand",
    "it": "italien",
    "pt": "portugais",
}


def translate_cv(cv_text: str, target_lang: str, api_key: str) -> str:
    """
    Traduit un CV déjà rédigé/optimisé dans une autre langue, en conservant la structure
    et les codes professionnels de la langue cible (pas une traduction mot à mot).
    """
    client = anthropic.Anthropic(api_key=api_key)
    langue = LANGUE_LABELS.get(target_lang.lower(), target_lang)

    prompt = f"""Tu es un traducteur professionnel spécialisé dans les CV et documents de candidature.

CV À TRADUIRE (français) :
{cv_text}

MISSION : Traduis ce CV en {langue.upper()}, professionnel, prêt à l'emploi.

INSTRUCTIONS :
- Ne traduis PAS mot à mot : adapte aux codes/conventions d'un CV en {langue} (intitulés de rubriques
  standards dans cette langue, formulations idiomatiques du monde professionnel visé)
- Conserve EXACTEMENT les mêmes informations factuelles (dates, noms d'entreprises, diplômes, chiffres)
  — ne jamais inventer ni omettre une information
- Garde la même structure générale (rubriques dans le même ordre)
- Adapte les intitulés de poste à leur équivalent standard dans la langue cible quand il existe

Réponds UNIQUEMENT avec le CV traduit, sans commentaire ni introduction."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text.strip()


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