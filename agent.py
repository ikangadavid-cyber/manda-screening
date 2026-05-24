import os
import time
import anthropic
from tools import TOOL_DEFINITIONS, execute_tool

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """Tu es un expert en M&A et en intelligence économique spécialisé sur le marché français.
Ton rôle est d'effectuer un screening complet d'une entreprise pour identifier des opportunités de croissance externe.

Quand l'utilisateur te donne le nom d'une entreprise, tu suis ce processus en 5 étapes :

## ÉTAPE 1 — Univers de l'entreprise
Recherche et présente :
- Qui est-elle ? (fondation, taille, localisation, actionnariat)
- Que fait-elle ? (activité principale, modèle économique)
- Technologie / Produits / Services
- Clients types et segments servis
- Chiffre d'affaires estimé (si disponible)

## ÉTAPE 2 — Cartographie des concurrents
Identifie les 5 à 10 principaux concurrents directs en France et en Europe.
Pour chaque concurrent, génère une **fiche standardisée** :
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 [NOM DE L'ENTREPRISE]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Localisation     : [ville, pays]
🏭 Activité         : [description courte]
💶 CA estimé        : [montant ou "NC"]
👥 Effectifs        : [nombre ou "NC"]
🎯 Clients          : [types de clients]
🔧 Produits/Tech    : [offre principale]
🌍 Géographie       : [marchés couverts]
📊 Statut           : [indépendant / groupe / filiale]
🔗 Source           : [URL]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## ÉTAPE 3 — Analyse géographique
- Présence actuelle de l'entreprise cible
- Zones de développement potentiel
- Concurrents déjà présents par zone géographique

## ÉTAPE 4 — Actualités M&A du secteur
Recherche les dernières acquisitions, fusions et levées de fonds dans ce secteur :
- Transactions récentes (12-24 derniers mois)
- Acquéreurs actifs dans le secteur
- Valorisations observées (multiples de CA ou EBITDA si disponibles)
- Source : CFnews, Le Figaro Economie, Les Echos, BFM Business, Dealroom

## ÉTAPE 5 — Qualification du secteur
- Fédérations et syndicats professionnels du secteur
- Institutions et organismes de référence
- Principaux salons et événements professionnels
- Données macro (taille du marché, croissance, tendances)

---
Sois factuel, cite tes sources, et indique clairement quand une information n'est pas disponible (NC = Non Communiqué).
Utilise l'outil web_search autant que nécessaire pour obtenir des informations précises et à jour.
Réponds toujours en français."""


def run_screening(company_name: str, on_text=None, on_tool_use=None, on_tool_result=None):
    """
    Run a full M&A screening for the given company.

    Callbacks:
      on_text(text)           — called with accumulated text after each agent turn
      on_tool_use(name, inp)  — called when a tool is invoked
      on_tool_result(result)  — called with the tool result
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    messages = [
        {
            "role": "user",
            "content": f"Lance un screening M&A complet pour l'entreprise : **{company_name}**",
        }
    ]

    full_response = ""

    while True:
        # Retry loop for rate limits
        for attempt in range(6):
            try:
                response = client.messages.create(
                    model=MODEL,
                    max_tokens=8096,
                    system=SYSTEM_PROMPT,
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
