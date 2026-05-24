import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)

st.set_page_config(
    page_title="Screening M&A",
    page_icon="🔍",
    layout="wide",
)

# Lit les clés depuis Streamlit Cloud (st.secrets) ou depuis .env en local
def get_key(name):
    try:
        return st.secrets[name]
    except Exception:
        return os.environ.get(name, "")

anthropic_key = get_key("ANTHROPIC_API_KEY")
tavily_key    = get_key("TAVILY_API_KEY")

# ── Interface ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/M%26A_icon.svg/120px-M%26A_icon.svg.png", width=60)
    st.markdown("### Screening M&A")
    st.markdown("Outil d'analyse concurrentielle et de croissance externe sur le marché français.")
    st.markdown("---")
    st.markdown("**Sources utilisées**")
    st.markdown(
        "- Pappers, Societe.com, Infogreffe\n"
        "- CFnews, Les Echos, BFM Business\n"
        "- LinkedIn, Crunchbase, Dealroom\n"
        "- INSEE, data.gouv.fr"
    )

st.title("🔍 Screening M&A")
st.markdown("Entrez le nom d'une entreprise pour obtenir un rapport complet : écosystème, concurrents, actualités M&A et qualification du secteur.")

col1, col2 = st.columns([3, 1])
with col1:
    company = st.text_input(
        "Entreprise",
        placeholder="Ex : Edenred, Vinci, Dalkia...",
        label_visibility="collapsed",
    )
with col2:
    run_button = st.button("Lancer le screening", type="primary", use_container_width=True)

if run_button:
    if not company.strip():
        st.warning("Veuillez entrer le nom d'une entreprise.")
        st.stop()
    if not anthropic_key or not tavily_key:
        st.error("Configuration manquante. Contactez l'administrateur.")
        st.stop()

    os.environ["ANTHROPIC_API_KEY"] = anthropic_key
    os.environ["TAVILY_API_KEY"]    = tavily_key

    from agent import run_screening

    st.markdown("---")
    st.subheader(f"Analyse : {company.strip()}")

    tool_log     = st.expander("🔎 Recherches effectuées en temps réel", expanded=True)
    tool_entries = []
    output_area  = st.empty()
    full_text    = [""]

    def on_text(text):
        full_text[0] = text
        output_area.markdown(text)

    def on_tool_use(name, inputs):
        tool_entries.append(f"🔍 {inputs.get('query', '')}")
        with tool_log:
            for e in tool_entries:
                st.markdown(e)

    def on_tool_result(_): pass

    with st.spinner("Analyse en cours... (2 à 5 minutes)"):
        try:
            run_screening(company.strip(), on_text=on_text, on_tool_use=on_tool_use, on_tool_result=on_tool_result)
            st.success("Analyse terminée.")
            st.download_button(
                label="📥 Télécharger l'analyse",
                data=full_text[0],
                file_name=f"screening_{company.strip().replace(' ', '_').lower()}.txt",
                mime="text/plain",
            )
        except Exception as e:
            st.error(f"Erreur : {e}")
