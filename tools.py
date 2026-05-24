import os
from tavily import TavilyClient

_client = None

def get_tavily():
    global _client
    if _client is None:
        _client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    return _client


def web_search(query: str, max_results: int = 6) -> str:
    try:
        results = get_tavily().search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
        )
        output = []
        for r in results.get("results", []):
            output.append(f"**{r['title']}**\n{r['url']}\n{r['content']}")
        return "\n\n---\n\n".join(output) if output else "Aucun résultat trouvé."
    except Exception as e:
        return f"Erreur de recherche : {e}"


TOOL_DEFINITIONS = [
    {
        "name": "web_search",
        "description": (
            "Effectue une recherche web sur des sources publiques françaises et internationales. "
            "Utiliser pour trouver des informations sur des entreprises, concurrents, actualités M&A, "
            "fédérations professionnelles, chiffres d'affaires, et données sectorielles. "
            "Privilégier des requêtes précises avec le nom de l'entreprise + le type d'info cherchée."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "La requête de recherche. Être précis : inclure le nom de l'entreprise, le secteur, et le type d'information recherchée.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Nombre de résultats (défaut 6, max 10)",
                    "default": 6,
                },
            },
            "required": ["query"],
        },
    }
]


def execute_tool(name: str, inputs: dict) -> str:
    if name == "web_search":
        return web_search(inputs["query"], inputs.get("max_results", 6))
    return f"Outil inconnu : {name}"
