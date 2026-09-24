"""
Agent pour les missions M&A sell-side — Modules acquéreurs.
"""
import os
import re
import time
import anthropic
from tools import TOOL_DEFINITIONS, execute_tool
from agent import _COMMON_INSTRUCTIONS

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WEB_SEARCH_MODULES = {
    "sell_2_recherche_acquereurs",
    "sell_3_profil_acquereur",
}

MODEL_BY_MODULE = {
    "sell_1a_cartographie_verticale":   "claude-sonnet-4-6",
    "sell_1b_cartographie_horizontale": "claude-sonnet-4-6",
    "sell_2_recherche_acquereurs":      "claude-sonnet-4-6",
    "sell_3_profil_acquereur":          "claude-sonnet-4-6",
    "sell_4_qualification_acquereurs":  "claude-sonnet-4-6",
}

MAX_TOKENS_BY_MODULE = {
    "sell_2_recherche_acquereurs":     16000,
    "sell_3_profil_acquereur":         16000,
    "sell_4_qualification_acquereurs": 16000,
}
DEFAULT_MAX_TOKENS = 8096

PROMPT_FILES = {
    "sell_1a_cartographie_verticale":   "prompts/sell_side/1a_acquereurs.txt",
    "sell_1b_cartographie_horizontale": "prompts/sell_side/1b_acquereurs.txt",
    "sell_2_recherche_acquereurs":      "prompts/sell_side/2_acquereurs.txt",
    "sell_3_profil_acquereur":          "prompts/sell_side/3_acquereurs.txt",
    "sell_4_qualification_acquereurs":  "prompts/sell_side/4_acquereurs.txt",
}

MODULE_LABELS = {
    "sell_1a_cartographie_verticale":   "Cartographie verticale",
    "sell_1b_cartographie_horizontale": "Cartographie horizontale",
    "sell_2_recherche_acquereurs":      "Recherche d'acquéreurs",
    "sell_3_profil_acquereur":          "Profil des acquéreurs",
    "sell_4_qualification_acquereurs":  "Qualification des acquéreurs",
}

MODULE_ESTIMATED_SECONDS = {
    "sell_1a_cartographie_verticale":   120,
    "sell_1b_cartographie_horizontale": 120,
    "sell_2_recherche_acquereurs":      300,
    "sell_3_profil_acquereur":          360,
    "sell_4_qualification_acquereurs":  240,
}


def _load_prompt(module_key: str, variables: dict) -> str:
    try:
        import streamlit as _st
        text = _st.secrets["prompts"][module_key]
    except Exception:
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

    company = variables.get("company", "")
    replacements = {
        "[SOCIÉTÉ CONCERNÉE]":                    company,
        "[CA SOCIÉTÉ CONCERNÉE]":                  variables.get("ca", "ND"),
        "[EBITDA SOCIÉTÉ CONCERNÉE]":              "ND",
        "[PAYS DU SIÈGE]":                         variables.get("pays", "ND"),
        "[ZONES GÉOGRAPHIQUES DES ACQUÉREURS]":    variables.get("zones", "France et Europe"),
        "[CATÉGORIES DU MAPPING RETENUES]":        variables.get("categories", "ND"),
        "[NOMBRE D'ACQUÉREURS ATTENDUS]":           str(variables.get("nb_acquereurs", 50)),
        "[ACTIONNARIAT]":                          variables.get("actionnariat", "ND"),
        "[TYPOLOGIE RECHERCHÉE]":                  variables.get("typologie", "industriels et financiers"),
        "[SOCIÉTÉS EXCLUES PAR LE CÉDANT]":        variables.get("exclusions", "Aucune"),
        "[ACTIVITÉ CŒUR]":                         variables.get("activite", company),
        "[SOURCES SECTORIELLES DU MANDAT]":        variables.get("sources_sectorielles", "ND"),
    }
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, str(value))
    return text


def _split_prompt(prompt_text: str) -> tuple[str, str]:
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


def run_sell_side_module(
    module_key: str,
    variables: dict,
    input_data: str = "",
    on_text=None,
    on_tool_use=None,
    on_tool_result=None,
):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    model      = MODEL_BY_MODULE.get(module_key, "claude-sonnet-4-6")
    max_tokens = MAX_TOKENS_BY_MODULE.get(module_key, DEFAULT_MAX_TOKENS)

    prompt_text   = _load_prompt(module_key, variables)
    instructions, _ = _split_prompt(prompt_text)
    instructions  += _COMMON_INSTRUCTIONS

    company = variables.get("company", "")
    user_parts = [f"Société : **{company}**"]
    if variables.get("activite"):
        user_parts.append(f"Activité cœur : {variables['activite']}")
    if variables.get("ca"):
        user_parts.append(f"CA : {variables['ca']}")
    if variables.get("actionnariat"):
        user_parts.append(f"Actionnariat : {variables['actionnariat']}")
    if variables.get("pays"):
        user_parts.append(f"Pays du siège : {variables['pays']}")
    if variables.get("zones"):
        user_parts.append(f"Zones acquéreurs : {variables['zones']}")
    user_parts.append(f"Nombre d'acquéreurs attendus : {variables.get('nb_acquereurs', 50)}")
    if variables.get("typologie"):
        user_parts.append(f"Typologie : {variables['typologie']}")
    if variables.get("exclusions"):
        user_parts.append(f"Exclusions : {variables['exclusions']}")
    if variables.get("categories"):
        user_parts.append(f"Catégories du mapping retenues : {variables['categories']}")
    if input_data and input_data.strip():
        user_parts.append(f"\n\n**Données et contexte :**\n{input_data.strip()}")
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
