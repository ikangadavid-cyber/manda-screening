"""
Agent pour les missions M&A sell-side.
Utilise les prompts stockés dans prompts/sell_side/ (ou Streamlit secrets).
"""
import os
import re
import time
import anthropic
from tools import TOOL_DEFINITIONS, execute_tool
from agent import _COMMON_INSTRUCTIONS

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WEB_SEARCH_MODULES = {
    "sell_03_redaction_slides",
    "sell_04_reformulation",
}

MODEL_BY_MODULE = {
    "sell_01_rapport_entretien": "claude-sonnet-4-6",
    "sell_02_plan_im":           "claude-sonnet-4-6",
    "sell_03_redaction_slides":  "claude-sonnet-4-6",
    "sell_04_reformulation":     "claude-sonnet-4-6",
}

MAX_TOKENS_BY_MODULE = {
    "sell_02_plan_im": 16000,
}
DEFAULT_MAX_TOKENS = 8096

PROMPT_FILES = {
    "sell_01_rapport_entretien": "prompts/sell_side/01_rapport_entretien.txt",
    "sell_02_plan_im":           "prompts/sell_side/02_plan_im.txt",
    "sell_03_redaction_slides":  "prompts/sell_side/03_redaction_slides.txt",
    "sell_04_reformulation":     "prompts/sell_side/04_reformulation.txt",
}

MODULE_LABELS = {
    "sell_01_rapport_entretien": "Rapport d'entretien",
    "sell_02_plan_im":           "Plan de l'Information Memorandum",
    "sell_03_redaction_slides":  "Rédaction des slides",
    "sell_04_reformulation":     "Reformulation",
}

MODULE_ESTIMATED_SECONDS = {
    "sell_01_rapport_entretien": 90,
    "sell_02_plan_im":           240,
    "sell_03_redaction_slides":  180,
    "sell_04_reformulation":     120,
}


def _load_prompt(module_key: str, company: str, subsidiary: str = "") -> str:
    try:
        import streamlit as _st
        text = _st.secrets["prompts"][module_key]
        text = text.replace("{company}", company)
        if subsidiary:
            text = text.replace("{company_subsidiary}", subsidiary)
        return text
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
    text = text.replace("{company}", company)
    if subsidiary:
        text = text.replace("{company_subsidiary}", subsidiary)
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
    company: str,
    subsidiary: str = "",
    input_data: str = "",
    on_text=None,
    on_tool_use=None,
    on_tool_result=None,
):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    model      = MODEL_BY_MODULE.get(module_key, "claude-sonnet-4-6")
    max_tokens = MAX_TOKENS_BY_MODULE.get(module_key, DEFAULT_MAX_TOKENS)

    prompt_text   = _load_prompt(module_key, company, subsidiary)
    instructions, _ = _split_prompt(prompt_text)
    instructions  += _COMMON_INSTRUCTIONS

    user_parts = [f"Société : **{company}**"]
    if subsidiary:
        user_parts.append(f"Filiale / entité secondaire : **{subsidiary}**")
    if input_data and input_data.strip():
        user_parts.append(f"\n\n**Documents / Données disponibles :**\n{input_data.strip()}")
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
