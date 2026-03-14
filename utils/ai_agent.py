"""
utils/ai_agent.py
US-05 : Agent IA Claude — optimisation CV ATS + lettre de motivation.
Zéro prompt côté utilisateur — toute l'intelligence est ici.
"""

import anthropic


# ─────────────────────────────────────────
# TÂCHE 1 — OPTIMISATION CV ATS
# ─────────────────────────────────────────

SYSTEM_PROMPT_ATS = """Tu es un expert en recrutement et en optimisation de CV pour les systèmes ATS (Applicant Tracking Systems).

TON RÔLE : Réécrire et optimiser le CV fourni pour qu'il soit parfaitement adapté à l'offre d'emploi donnée.

RÈGLES ABSOLUES :
1. NE JAMAIS inventer de compétences, d'expériences ou de diplômes qui n'existent pas dans le CV original.
2. NE JAMAIS mentir. Tu reformules, restructures et mets en valeur — mais uniquement ce qui est vrai.
3. CONSERVER toutes les informations importantes du CV original.
4. ADAPTER le vocabulaire pour matcher les mots-clés de l'offre (sans déformer la réalité).

OPTIMISATIONS ATS À APPLIQUER :
- Ajouter une section "Résumé professionnel" de 3-4 lignes avec les mots-clés de l'offre
- Reformuler les titres de postes pour coller aux termes exacts de l'offre si c'est cohérent
- Créer une section "Compétences techniques" avec les mots-clés de l'offre présents dans le profil
- Utiliser des verbes d'action forts et quantifier les résultats quand possible
- Structure claire : pas de colonnes, pas de tableaux, pas d'images — format texte linéaire
- Utiliser des tirets (-) plutôt que des puces spéciales illisibles par les ATS
- Ordre recommandé : Résumé → Compétences → Expériences → Formation → Langues → Divers

FORMAT DE RÉPONSE :
Retourne UNIQUEMENT le CV réécrit, sans commentaire ni explication. Commence directement par le nom du candidat.
"""

def optimize_cv_ats(cv_text: str, job_offer: str, api_key: str) -> str:
    """
    Appelle Claude pour réécrire le CV de manière ATS-optimisée.
    """
    client = anthropic.Anthropic(api_key=api_key)

    user_message = f"""Voici l'offre d'emploi à laquelle le candidat postule :

═══════════════════════════════════
OFFRE D'EMPLOI
═══════════════════════════════════
{job_offer}

═══════════════════════════════════
CV ORIGINAL DU CANDIDAT
═══════════════════════════════════
{cv_text}

Optimise ce CV pour qu'il soit parfaitement ATS-ready pour cette offre spécifique.
"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        system=SYSTEM_PROMPT_ATS,
        messages=[{"role": "user", "content": user_message}],
    )

    return message.content[0].text


# ─────────────────────────────────────────
# TÂCHE 2 — LETTRE DE MOTIVATION
# ─────────────────────────────────────────

STYLES_CONFIG = {
    "motivé": {
        "desc": "enthousiaste, sincère, dynamique. Le candidat est clairement intéressé et le montre.",
        "ton": "chaleureux et direct",
    },
    "très motivé": {
        "desc": "passionné, très engagé, presque urgent dans son désir d'obtenir ce poste.",
        "ton": "intense et convaincant",
    },
    "expert": {
        "desc": "confiant, factuel, met en avant sa séniorité et ses résultats concrets.",
        "ton": "posé, assertif, orienté résultats",
    },
    "débutant": {
        "desc": "humble, volontaire, met en avant son potentiel et sa capacité d'apprentissage rapide.",
        "ton": "modeste mais déterminé",
    },
    "neutre & professionnel": {
        "desc": "sobre, formel, classique. Laisse les faits parler.",
        "ton": "neutre et professionnel",
    },
    "reconversion": {
        "desc": "met en avant le transfert de compétences, explique le changement de voie de manière positive.",
        "ton": "proactif, tourné vers l'avenir",
    },
}

SYSTEM_PROMPT_LM = """Tu es un expert en rédaction de lettres de motivation percutantes et authentiques.

RÈGLES ABSOLUES :
1. NE JAMAIS inventer d'expériences ou compétences absentes du CV.
2. Toujours rester dans le style demandé — sans exagération ni mensonge.
3. La lettre doit être personnalisée pour l'offre ET pour le profil exact du candidat.
4. Format : paragraphes fluides, pas de listes à puces.
5. Longueur : 3 à 4 paragraphes, environ 250-350 mots.

STRUCTURE :
- §1 : Accroche + poste visé + pourquoi cette entreprise/offre
- §2 : Mise en valeur des compétences clés qui matchent l'offre
- §3 : Valeur ajoutée apportée + exemples concrets tirés du CV
- §4 : Conclusion + disponibilité + formule de politesse

FORMAT DE RÉPONSE :
Retourne UNIQUEMENT la lettre, sans commentaire. Commence par "[Ville], le [date]".
"""

def generate_cover_letter(
    cv_text: str,
    job_offer: str,
    style: str,
    precision: str,
    api_key: str,
) -> str:
    """
    Génère une lettre de motivation personnalisée.
    """
    client = anthropic.Anthropic(api_key=api_key)

    style_lower = style.lower()
    style_info = STYLES_CONFIG.get(style_lower, STYLES_CONFIG["motivé"])

    precision_block = ""
    if precision.strip():
        precision_block = f"""
PRÉCISION DU CANDIDAT (à intégrer si possible) :
{precision}
"""

    user_message = f"""Rédige une lettre de motivation dans le style suivant :

STYLE DEMANDÉ : {style}
Description du style : {style_info['desc']}
Ton à adopter : {style_info['ton']}
{precision_block}
═══════════════════════════════════
OFFRE D'EMPLOI
═══════════════════════════════════
{job_offer}

═══════════════════════════════════
CV DU CANDIDAT
═══════════════════════════════════
{cv_text}
"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        system=SYSTEM_PROMPT_LM,
        messages=[{"role": "user", "content": user_message}],
    )

    return message.content[0].text
