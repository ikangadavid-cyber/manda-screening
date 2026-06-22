"""
Agent pour les missions M&A buy-side et sell-side.
Utilise les prompts confidentiels stockés dans prompts/buy_side/ et prompts/sell_side/.
"""
import os
import re
import time
import anthropic
from tools import TOOL_DEFINITIONS, execute_tool

# Répertoire de base = dossier contenant ce fichier (manda-screening/)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Modules nécessitant une recherche web (Tavily)
WEB_SEARCH_MODULES = {
    "buy_01_carto_verticale",
    "buy_02_carto_horizontale",
    "buy_03_recherche_cibles",
    "buy_04_profil_entreprise",
    "buy_05_qualification_cibles",
}

# Modèle par module : Sonnet pour web-search, Haiku pour les slides (3x plus rapide, 4x moins cher)
MODEL_BY_MODULE = {
    "buy_01_carto_verticale":       "claude-sonnet-4-6",
    "buy_02_carto_horizontale":     "claude-sonnet-4-6",
    "buy_03_recherche_cibles":      "claude-sonnet-4-6",
    "buy_04_profil_entreprise":     "claude-sonnet-4-6",
    "buy_05_qualification_cibles":  "claude-sonnet-4-6",
    "buy_06_slide_bandeau":         "claude-haiku-4-5-20251001",
    "buy_07_slide_vert_pos":        "claude-haiku-4-5-20251001",
    "buy_08_slide_horiz_rationnel": "claude-haiku-4-5-20251001",
    "buy_09_slide_horiz_pos":       "claude-haiku-4-5-20251001",
    "buy_10_slide_vert_rationnel":  "claude-haiku-4-5-20251001",
    "sell_01_rapport_entretien":    "claude-haiku-4-5-20251001",
    "sell_02_plan_im":              "claude-sonnet-4-6",
    "sell_03_redaction_slides":     "claude-sonnet-4-6",
    "sell_04_reformulation":        "claude-haiku-4-5-20251001",
}

# Tokens max par module (slides n'ont pas besoin de 8096)
MAX_TOKENS_BY_MODULE = {
    "buy_06_slide_bandeau":         4096,
    "buy_07_slide_vert_pos":        2048,
    "buy_08_slide_horiz_rationnel": 2048,
    "buy_09_slide_horiz_pos":       2048,
    "buy_10_slide_vert_rationnel":  2048,
    "sell_01_rapport_entretien":    6000,
    "sell_04_reformulation":        4096,
}
DEFAULT_MAX_TOKENS = 8096

PROMPT_FILES = {
    # Buy-side
    "buy_01_carto_verticale":       "prompts/buy_side/01_cartographie_verticale.txt",
    "buy_02_carto_horizontale":     "prompts/buy_side/02_cartographie_horizontale.txt",
    "buy_03_recherche_cibles":      "prompts/buy_side/03_recherche_cibles.txt",
    "buy_04_profil_entreprise":     "prompts/buy_side/04_profil_entreprise.txt",
    "buy_05_qualification_cibles":  "prompts/buy_side/05_qualification_cibles.txt",
    "buy_06_slide_bandeau":         "prompts/buy_side/06_slide_bandeau.txt",
    "buy_07_slide_vert_pos":        "prompts/buy_side/07_slide_vertical_positionnement.txt",
    "buy_08_slide_horiz_rationnel": "prompts/buy_side/08_slide_horizontal_rationnel.txt",
    "buy_09_slide_horiz_pos":       "prompts/buy_side/09_slide_horizontal_positionnement.txt",
    "buy_10_slide_vert_rationnel":  "prompts/buy_side/10_slide_vertical_rationnel.txt",
    # Sell-side
    "sell_01_rapport_entretien":    "prompts/sell_side/01_rapport_entretien.txt",
    "sell_02_plan_im":              "prompts/sell_side/02_plan_im.txt",
    "sell_03_redaction_slides":     "prompts/sell_side/03_redaction_slides.txt",
    "sell_04_reformulation":        "prompts/sell_side/04_reformulation.txt",
}


def _load_prompt(module_key: str, company: str) -> str:
    """
    Charge le prompt depuis :
    1. st.secrets["prompts"][module_key]  → production Streamlit Cloud
    2. Fichier local prompts/…            → usage local / dev
    """
    try:
        import streamlit as _st
        text = _st.secrets["prompts"][module_key]
        return text.replace("{company}", company)
    except Exception:
        pass

    rel = PROMPT_FILES.get(module_key)
    if not rel:
        raise FileNotFoundError(f"Prompt introuvable : {module_key}")
    path = os.path.join(_BASE_DIR, rel)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Prompt '{module_key}' absent.\n"
            f"• En local : vérifier {path}\n"
            f"• En production : ajouter la clé [prompts] dans Streamlit Cloud → Settings → Secrets"
        )
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return text.replace("{company}", company)


def _split_prompt(prompt_text: str) -> tuple[str, str]:
    """Sépare le prompt en (system_instructions, input_section)."""
    splits = [
        r"Partie\s+3\s*[:\-—]*\s*INPUT",
        r"PARTIE\s+3\s*[:\-—]*\s*INPUT",
        r"PARTIE\s+3\s*[:\-—]",
        r"Partie\s+3\s*[:\-—]",
        r"3/\s*INPUT",
        r"\[A compléter\]",
    ]
    for pattern in splits:
        m = re.search(pattern, prompt_text, re.IGNORECASE)
        if m:
            return prompt_text[: m.start()].strip(), prompt_text[m.start():].strip()
    return prompt_text.strip(), ""


def run_ma_module(
    module_key: str,
    company: str,
    input_data: str = "",
    on_text=None,
    on_tool_use=None,
    on_tool_result=None,
):
    """
    Exécute un module M&A.

    Args:
        module_key:   Clé du module (cf. PROMPT_FILES)
        company:      Nom de l'acquéreur ou de la société cédée
        input_data:   Données à passer comme INPUT (résultats étapes précédentes, etc.)
        on_text:      Callback texte accumulé
        on_tool_use:  Callback outil déclenché (name, inputs)
        on_tool_result: Callback résultat outil
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    model      = MODEL_BY_MODULE.get(module_key, "claude-sonnet-4-6")
    max_tokens = MAX_TOKENS_BY_MODULE.get(module_key, DEFAULT_MAX_TOKENS)

    prompt_text = _load_prompt(module_key, company)
    instructions, _ = _split_prompt(prompt_text)

    user_parts = [f"Société / Acquéreur : **{company}**"]
    if input_data and input_data.strip():
        user_parts.append(f"\n\n**INPUT / Données disponibles :**\n{input_data.strip()}")
    user_message = "\n".join(user_parts)

    use_web = module_key in WEB_SEARCH_MODULES
    tools   = TOOL_DEFINITIONS if use_web else []

    messages      = [{"role": "user", "content": user_message}]
    full_response = ""

    while True:
        for attempt in range(6):
            try:
                kwargs = {
                    "model":      model,
                    "max_tokens": max_tokens,
                    "system":     instructions,
                    "messages":   messages,
                }
                if tools:
                    kwargs["tools"] = tools
                response = client.messages.create(**kwargs)
                break
            except anthropic.RateLimitError:
                wait = 30 * (attempt + 1)
                if on_text:
                    on_text(full_response + f"\n\n_Pause {wait}s (rate limit)..._")
                time.sleep(wait)
        else:
            raise RuntimeError("Rate limit persistant après 6 tentatives.")

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
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     result,
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    return full_response
