import os
import time
import anthropic
from tools import TOOL_DEFINITIONS, execute_tool

MODEL = "claude-sonnet-4-6"

# ── System prompts per deliverable type ───────────────────────────────────────

_COMMON_INSTRUCTIONS = """
---
RÈGLES STRICTES DE CONTENU ET DE STYLE :

Contenu :
- Sois factuel et précis. Indique NC (Non Communiqué) quand une information est introuvable — ne laisse jamais une cellule vide.
- Cite tes sources avec les URLs dans les tableaux prévus à cet effet.
- Utilise web_search autant que nécessaire. Ne rédige PAS le rapport avec moins de recherches que demandé.
- Réponds toujours en français.
- N'omets JAMAIS un concurrent ou un acteur identifié lors de tes recherches. L'exhaustivité prime.
- Ne poses JAMAIS de questions à l'utilisateur, ne demandes JAMAIS de précisions. Produis toujours le livrable complet.
- Si les recherches web sont indisponibles ou retournent une erreur : continue quand même et produis le livrable avec NC pour les données introuvables. Ne mentionne pas l'échec des recherches dans le livrable.

Style rédactionnel :
- Commence DIRECTEMENT par le contenu du rapport. N'écris jamais de phrase d'introduction sur tes recherches ("Je vais chercher...", "J'ai maintenant...", "Je rencontre des limitations...").
- Écris comme un consultant senior rédigeant une note professionnelle, pas comme un outil IA générant un template.
- Préfère la phrase structurée à la liste à puces excessive. Les listes sont acceptables pour des énumérations claires, pas pour tout.
- N'ajoute aucune note méthodologique, orthographique ou procédurale dans le rapport final.

Mise en forme :
- Interdit : toute notation entre crochets [E], [CA], [L], [N], [!] ou similaire.
- Interdit : les lignes de séparation ━━━━━━━ ou ========= en dehors des fiches concurrentes.
- Interdit : abuser du **gras** — réserver le gras aux titres de champs dans les tableaux et aux termes vraiment clés.
- Obligatoire : utiliser des tableaux Markdown (| col | col |) pour toutes les données structurées comparatives."""

_STEP1_TEMPLATE = """## ÉTAPE 1 — Univers de l'entreprise
Recherche et présente :
- Qui est-elle ? (fondation, taille, localisation, actionnariat)
- Que fait-elle ? (activité principale, modèle économique)
- Technologie / Produits / Services
- Clients types et segments servis
- Chiffre d'affaires estimé (si disponible)"""

_STEP2_TEMPLATE = """## ÉTAPE 2 — Cartographie des concurrents
Identifie AU MINIMUM 8 concurrents directs (idéalement 10 à 12), incluant PME régionales, spécialistes de niche et acteurs européens présents sur le marché français.

MÉTHODE DE RECHERCHE — dans cet ordre :
1. Recherche "[secteur] concurrent France" et "[activité] entreprise France site:pappers.fr"
2. Recherche "[nom société] concurrent direct alternative"
3. Recherche "benchmark [secteur] acteurs France"
4. Pour chaque concurrent trouvé : 2 recherches ciblées (site officiel + Pappers ou LinkedIn)
5. Si moins de 8 concurrents : chercher "[secteur] acteurs régionaux France" et "[secteur] PME France"

RÈGLE : N'omets JAMAIS un concurrent identifié, même de petite taille. Une fiche avec des NC vaut mieux qu'un acteur manquant.

Pour chaque concurrent, produis une fiche structurée complète :

### Concurrent N° — NOM DE L'ENTREPRISE

**🏢 Identité**
| Champ | Information |
|---|---|
| Localisation | ville, pays |
| Statut | indépendant / filiale / groupe / coté en bourse |
| Dirigeant | Prénom Nom, titre (PDG / DG / Fondateur) ou NC |
| Fondation | année ou NC |
| Effectifs | nombre ou fourchette ou NC |

**💼 Activité & Marché**
| Champ | Information |
|---|---|
| Activité principale | description précise (2-3 lignes) |
| Produits / Tech | offre détaillée — produits, logiciels, services |
| Clients cibles | types de clients, secteurs, taille |
| Géographie | marchés couverts (régions, pays) |
| CA estimé | montant en M€ ou fourchette ou NC |
| Point différenciant | ce qui les distingue clairement de la cible |

**🔗 Liens & Sources**
| Champ | Lien |
|---|---|
| Site web | URL du site officiel ou NC |
| LinkedIn | URL page LinkedIn entreprise ou NC |
| Source | URL article ou page de référence datée |

---"""

_STEP3_TEMPLATE = """## ÉTAPE 3 — Analyse géographique
- Présence actuelle de l'entreprise cible
- Zones de développement potentiel
- Concurrents déjà présents par zone géographique"""

_STEP4_TEMPLATE = """## ÉTAPE 4 — Actualités M&A du secteur
Recherche les dernières acquisitions, fusions et levées de fonds dans ce secteur :
- Transactions récentes (12-24 derniers mois)
- Acquéreurs actifs dans le secteur
- Valorisations observées (multiples de CA ou EBITDA si disponibles)
- Source : CFnews, Le Figaro Economie, Les Echos, BFM Business, Dealroom"""

_STEP5_TEMPLATE = """## ÉTAPE 5 — Qualification du secteur
- Fédérations et syndicats professionnels du secteur
- Institutions et organismes de référence
- Principaux salons et événements professionnels
- Données macro (taille du marché, croissance, tendances)"""

SYSTEM_PROMPTS = {
    "complet": (
        "Tu es un expert en M&A et en intelligence économique spécialisé sur le marché français.\n"
        "Ton rôle est d'effectuer un screening complet d'une entreprise pour identifier des opportunités de croissance externe.\n\n"
        "Quand l'utilisateur te donne le nom d'une entreprise, tu suis ce processus en 5 étapes "
        "(effectue 15 à 25 recherches web au total) :\n\n"
        + _STEP1_TEMPLATE + "\n\n"
        + _STEP2_TEMPLATE + "\n\n"
        + _STEP3_TEMPLATE + "\n\n"
        + _STEP4_TEMPLATE + "\n\n"
        + _STEP5_TEMPLATE
        + _COMMON_INSTRUCTIONS
    ),
    "fiche": (
        "Tu es un expert en intelligence économique spécialisé sur le marché français.\n"
        "Ton rôle est de produire une fiche entreprise détaillée et structurée.\n\n"
        "Effectue uniquement l'ÉTAPE 1 ci-dessous (5 à 8 recherches web maximum) :\n\n"
        + _STEP1_TEMPLATE + "\n\n"
        "En plus de l'ÉTAPE 1, enrichis la fiche avec :\n"
        "- Actionnariat et structure capitalistique\n"
        "- Dirigeants clés et équipe de direction\n"
        "- Historique et dates clés\n"
        "- Présence en ligne et réseaux sociaux\n"
        "- Certifications, labels, distinctions\n"
        "- Tout élément permettant de qualifier l'entreprise pour une opération M&A\n"
        + _COMMON_INSTRUCTIONS
    ),
    "benchmark": (
        "Tu es un expert en M&A et en intelligence économique spécialisé sur le marché français.\n"
        "Ton rôle est de produire un benchmark concurrentiel exhaustif avec des fiches détaillées et standardisées.\n\n"
        "Effectue les ÉTAPES 1 et 2 (20 à 30 recherches web au total — sois thorough) et structure le rapport dans CET ORDRE EXACT :\n\n"
        + _STEP1_TEMPLATE + "\n\n"
        "---\n\n"
        "## Synthèse comparative et positionnement stratégique\n\n"
        "Rédige cette synthèse AVANT les fiches concurrentes, sur la base de tes recherches sur le secteur.\n\n"
        "### 📍 Positionnement marché\n"
        "Tableau comparatif : entreprise cible vs principaux concurrents sur les axes clés (taille, géographie, modèle, cible clients).\n\n"
        "### 💪 Forces relatives\n"
        "3 à 5 avantages concurrentiels distinctifs de l'entreprise cible par rapport au marché — une ligne par force, concrète et factuelle.\n\n"
        "### ⚠️ Faiblesses relatives\n"
        "3 à 5 points de faiblesse ou retards par rapport aux concurrents — une ligne par point, sans généralité.\n\n"
        "### 🎯 Opportunités de rapprochement\n"
        "Identifie 2 à 3 cibles de rapprochement pertinentes parmi les concurrents analysés, avec justification courte pour chacune.\n\n"
        "### 📊 Tableau de synthèse\n"
        "Tableau récapitulatif comparant l'ensemble des acteurs sur : CA estimé, effectifs, géographie, statut (indépendant/groupe), point fort clé.\n\n"
        "---\n\n"
        + _STEP2_TEMPLATE + "\n\n"
        + _COMMON_INSTRUCTIONS
    ),
    "manda": (
        "Tu es un expert en M&A spécialisé sur le marché français et européen.\n"
        "Ton rôle est de produire une note M&A et de qualification sectorielle.\n\n"
        "Effectue les ÉTAPES 4 et 5 (8 à 12 recherches web au total) :\n\n"
        + _STEP4_TEMPLATE + "\n\n"
        + _STEP5_TEMPLATE + "\n\n"
        "Accent particulier sur :\n"
        "- Les acquéreurs stratégiques et financiers (fonds PE, industriels) actifs dans ce secteur\n"
        "- Les multiples de valorisation observés dans des transactions comparables\n"
        "- Les fédérations et syndicats professionnels (contacts, événements)\n"
        "- Les salons et conférences clés du secteur (dates, lieux)\n"
        + _COMMON_INSTRUCTIONS
    ),
    "geo": (
        "Tu es un expert en M&A et en développement international spécialisé sur le marché français.\n"
        "Ton rôle est de produire une analyse géographique pour identifier des opportunités de croissance externe.\n\n"
        "Effectue les ÉTAPES 1 et 3 (8 à 12 recherches web au total) :\n\n"
        + _STEP1_TEMPLATE + "\n\n"
        + _STEP3_TEMPLATE + "\n\n"
        "Enrichis l'analyse géographique avec :\n"
        "- Cartographie des acteurs locaux dans chaque zone cible\n"
        "- Barrières à l'entrée et réglementations locales\n"
        "- Entreprises cibles potentielles pour une acquisition dans chaque zone\n"
        "- Tendances de consolidation géographique dans le secteur\n"
        + _COMMON_INSTRUCTIONS
    ),
}

# ── Step detection map ────────────────────────────────────────────────────────
STEP_TRIGGERS = {
    "ÉTAPE 1": "Analyse de l'entreprise",
    "ETAPE 1": "Analyse de l'entreprise",
    "ÉTAPE 2": "Cartographie des concurrents",
    "ETAPE 2": "Cartographie des concurrents",
    "ÉTAPE 3": "Analyse géographique",
    "ETAPE 3": "Analyse géographique",
    "ÉTAPE 4": "Actualités M&A",
    "ETAPE 4": "Actualités M&A",
    "ÉTAPE 5": "Qualification du secteur",
    "ETAPE 5": "Qualification du secteur",
}


def _detect_steps(text: str, already_emitted: set, on_step):
    """Scan text for step markers and emit callbacks for new ones."""
    if on_step is None:
        return
    for marker, step_name in STEP_TRIGGERS.items():
        if marker in text and step_name not in already_emitted:
            already_emitted.add(step_name)
            on_step(step_name)


def run_screening(
    company_name: str,
    deliverable_type: str = "complet",
    context: str = "",
    on_text=None,
    on_tool_use=None,
    on_tool_result=None,
    on_step=None,
):
    """
    Run an M&A screening for the given company.

    Args:
        company_name:     Name of the company to screen.
        deliverable_type: One of: "complet", "fiche", "benchmark", "manda", "geo".
        context:          Optional string of info the consultant already knows.
        on_text(text):    Called with accumulated text after each agent turn.
        on_tool_use(name, inp): Called when a tool is invoked.
        on_tool_result(result): Called with the tool result.
        on_step(step_name):     Called when a new major step begins.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    system_prompt = SYSTEM_PROMPTS.get(deliverable_type, SYSTEM_PROMPTS["complet"])

    # Build user message
    user_message = ""
    if context and context.strip():
        user_message = (
            "Voici les informations que le consultant connaît déjà sur cette entreprise "
            "— utilise-les directement sans les rechercher à nouveau :\n"
            f"{context.strip()}\n\n"
        )

    # Deliverable-specific prompt
    deliverable_verbs = {
        "complet":   "Lance un screening M&A complet pour l'entreprise",
        "fiche":     "Produis une fiche entreprise détaillée pour",
        "benchmark": "Réalise un benchmark concurrentiel complet pour",
        "manda":     "Produis une note M&A et qualification sectorielle pour",
        "geo":       "Réalise une analyse géographique et de développement pour",
    }
    verb = deliverable_verbs.get(deliverable_type, "Lance un screening M&A complet pour l'entreprise")
    user_message += f"{verb} : **{company_name}**"

    messages = [{"role": "user", "content": user_message}]

    full_response = ""
    emitted_steps: set = set()

    while True:
        # Retry loop for rate limits
        for attempt in range(6):
            try:
                response = client.messages.create(
                    model=MODEL,
                    max_tokens=8096,
                    system=system_prompt,
                    tools=TOOL_DEFINITIONS,
                    messages=messages,
                )
                break
            except anthropic.RateLimitError:
                wait = 30 * (attempt + 1)
                if on_text:
                    on_text(full_response + f"\n\n_Pause {wait}s (rate limit)..._")
                time.sleep(wait)
        else:
            raise RuntimeError("Rate limit persistant après 6 tentatives.")

        # Extract text from this turn
        for block in response.content:
            if block.type == "text":
                full_response += block.text
                if on_text:
                    on_text(full_response)
                # Detect step transitions
                _detect_steps(full_response, emitted_steps, on_step)

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    if on_tool_use:
                        on_tool_use(block.name, block.input)
                    result = execute_tool(block.name, block.input)
                    if on_tool_result:
                        on_tool_result(result)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "user", "content": tool_results})
        else:
            break

    return full_response
