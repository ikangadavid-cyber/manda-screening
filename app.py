import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)

st.set_page_config(
    page_title="Screening M&A",
    page_icon="🔍",
    layout="wide",
)

# ── API key helpers ────────────────────────────────────────────────────────────
def get_key(name):
    """Read API keys from Streamlit Cloud (st.secrets) or local .env file."""
    try:
        return st.secrets[name]
    except Exception:
        return os.environ.get(name, "")

anthropic_key = get_key("ANTHROPIC_API_KEY")
tavily_key    = get_key("TAVILY_API_KEY")

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #1E3A5F;
    color: white;
}
section[data-testid="stSidebar"] * {
    color: white !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.2) !important;
}
section[data-testid="stSidebar"] .sidebar-logo {
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    padding: 8px 0 4px 0;
}
section[data-testid="stSidebar"] .sidebar-sources {
    font-size: 0.82rem;
    line-height: 1.8;
    opacity: 0.85;
}

/* ── Main area ── */
.main .block-container {
    max-width: 900px;
    padding-top: 2rem;
    margin: 0 auto;
}

/* ── Main title ── */
.main-title {
    font-size: 2.4rem;
    font-weight: 800;
    color: #1E3A5F;
    letter-spacing: -1px;
    margin-bottom: 0.2rem;
}
.main-subtitle {
    font-size: 1.0rem;
    color: #64748b;
    margin-bottom: 1.8rem;
}

/* ── Deliverable cards ── */
.card-btn {
    background: white;
    border: 2px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px 18px;
    cursor: pointer;
    transition: all 0.15s ease;
    width: 100%;
    text-align: left;
    margin-bottom: 0;
}
.card-btn:hover {
    border-color: #2E86AB;
    box-shadow: 0 4px 12px rgba(46,134,171,0.15);
    transform: translateY(-1px);
}
.card-icon {
    font-size: 1.5rem;
    display: block;
    margin-bottom: 6px;
}
.card-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #1E3A5F;
    display: block;
    margin-bottom: 3px;
}
.card-desc {
    font-size: 0.78rem;
    color: #64748b;
    line-height: 1.4;
}

/* ── Progress / waiting screen ── */
.progress-container {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 24px 28px;
    margin: 16px 0;
}
.progress-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1E3A5F;
    margin-bottom: 16px;
}
.step-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 0;
    font-size: 0.9rem;
    color: #334155;
}
.step-row.done   { color: #16a34a; }
.step-row.active { color: #2E86AB; font-weight: 600; }
.step-row.pending{ color: #94a3b8; }
.step-icon { font-size: 1.1rem; min-width: 22px; }
.searching-label {
    font-size: 0.82rem;
    color: #94a3b8;
    margin-top: 14px;
    font-style: italic;
}

/* ── Result area ── */
.result-header {
    font-size: 1.0rem;
    font-weight: 700;
    color: #1E3A5F;
    margin-bottom: 12px;
}

/* ── Company badge ── */
.company-badge {
    display: inline-block;
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    color: #1E40AF;
    font-weight: 700;
    font-size: 1.1rem;
    padding: 6px 16px;
    border-radius: 8px;
    margin-bottom: 20px;
}

/* ── Streamlit button overrides ── */
div[data-testid="stButton"] > button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.15s ease;
}

/* ── Download buttons ── */
div[data-testid="stDownloadButton"] > button {
    border-radius: 8px;
    font-size: 0.88rem;
}

/* ── Expander ── */
details {
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    margin-bottom: 16px !important;
}

/* ── Spinner text ── */
div[data-testid="stSpinner"] > div {
    font-size: 0.9rem;
    color: #64748b;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #F1F5F9; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── Deliverable type definitions ──────────────────────────────────────────────
DELIVERABLES = [
    {
        "key":   "complet",
        "icon":  "📋",
        "title": "Rapport Complet",
        "desc":  "Analyse en 5 étapes : univers, concurrents, géographie, M&A, secteur",
        "steps": [
            "Analyse de l'entreprise",
            "Cartographie des concurrents",
            "Analyse géographique",
            "Actualités M&A",
            "Qualification du secteur",
        ],
    },
    {
        "key":   "fiche",
        "icon":  "🏢",
        "title": "Fiche Entreprise",
        "desc":  "Identité, activité, CA, effectifs, clients, actionnariat",
        "steps": ["Analyse de l'entreprise"],
    },
    {
        "key":   "benchmark",
        "icon":  "⚔️",
        "title": "Benchmark Concurrents",
        "desc":  "Cartographie des acteurs avec fiches standardisées",
        "steps": ["Analyse de l'entreprise", "Cartographie des concurrents"],
    },
    {
        "key":   "manda",
        "icon":  "📰",
        "title": "Note M&A & Secteur",
        "desc":  "Transactions récentes, valorisations, fédérations, salons",
        "steps": ["Actualités M&A", "Qualification du secteur"],
    },
    {
        "key":   "geo",
        "icon":  "🌍",
        "title": "Analyse Géographique",
        "desc":  "Opportunités d'expansion internationale et acteurs locaux",
        "steps": ["Analyse de l'entreprise", "Analyse géographique"],
    },
]

DELIVERABLE_BY_KEY = {d["key"]: d for d in DELIVERABLES}

# ── Session state initialization ──────────────────────────────────────────────
def init_state():
    defaults = {
        "screen":          1,
        "company":         "",
        "deliverable_type": "complet",
        "context":         "",
        "result_text":     "",
        "current_step":    "",
        "steps_done":      [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo">🔍 M&A Screening</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Sources utilisées**")
    st.markdown(
        '<div class="sidebar-sources">'
        "• Pappers, Societe.com, Infogreffe<br>"
        "• CFnews, Les Echos, BFM Business<br>"
        "• LinkedIn, Crunchbase, Dealroom<br>"
        "• INSEE, data.gouv.fr<br>"
        "• Kompass, Corporama"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    if st.session_state.screen != 1:
        if st.button("← Nouvelle analyse", use_container_width=True):
            for k in ["screen", "company", "deliverable_type", "context", "result_text", "current_step", "steps_done"]:
                if k == "screen":
                    st.session_state[k] = 1
                elif k in ["steps_done"]:
                    st.session_state[k] = []
                else:
                    st.session_state[k] = ""
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 1 — INPUT
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.screen == 1:

    st.markdown('<div class="main-title">Screening M&A</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="main-subtitle">Analysez une entreprise en profondeur grâce à l\'intelligence artificielle et aux données publiques.</div>',
        unsafe_allow_html=True,
    )

    # Company name input
    company_input = st.text_input(
        "Entreprise",
        placeholder="Nom de l'entreprise...",
        label_visibility="collapsed",
        key="company_input_field",
    )

    st.markdown("#### Choisissez le type d'analyse")

    # 2x2 + 1 grid for deliverable cards
    col_a, col_b = st.columns(2)
    col_c, col_d = st.columns(2)
    col_e, _, _ = st.columns(3)

    card_cols = [col_a, col_b, col_c, col_d, col_e]

    for idx, deliv in enumerate(DELIVERABLES):
        with card_cols[idx]:
            label = f"{deliv['icon']} {deliv['title']}\n\n_{deliv['desc']}_"
            if st.button(label, key=f"card_{deliv['key']}", use_container_width=True):
                if not company_input.strip():
                    st.warning("Veuillez entrer le nom d'une entreprise.")
                elif not anthropic_key or not tavily_key:
                    st.error("Configuration manquante : clés API introuvables. Contactez l'administrateur.")
                else:
                    st.session_state.company          = company_input.strip()
                    st.session_state.deliverable_type = deliv["key"]
                    st.session_state.screen           = 2
                    st.session_state.steps_done       = []
                    st.session_state.current_step     = ""
                    st.session_state.result_text      = ""
                    st.rerun()

    # Optional context expander
    with st.expander("💡 Informations déjà connues (optionnel)"):
        context_input = st.text_area(
            "Ce que vous savez déjà sur cette entreprise",
            placeholder=(
                "Exemples : secteur d'activité, chiffre d'affaires approximatif, "
                "principaux clients, zone géographique, contexte de l'opération..."
            ),
            height=120,
            key="context_input_field",
        )
        st.session_state.context = context_input


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 2 — WAITING / RUNNING
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.screen == 2:

    company       = st.session_state.company
    deliv_key     = st.session_state.deliverable_type
    deliv_info    = DELIVERABLE_BY_KEY.get(deliv_key, DELIVERABLES[0])
    context       = st.session_state.context
    all_steps     = deliv_info["steps"]

    st.markdown(
        f'<div class="company-badge">{company}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"**{deliv_info['icon']} {deliv_info['title']}** — Analyse en cours...")

    # Progress display placeholder
    progress_placeholder = st.empty()

    def render_progress(current_step: str, steps_done: list):
        html_rows = ""
        for step in all_steps:
            if step in steps_done:
                css   = "done"
                icon  = "✅"
            elif step == current_step:
                css   = "active"
                icon  = "⏳"
            else:
                css   = "pending"
                icon  = "⬜"
            html_rows += (
                f'<div class="step-row {css}">'
                f'<span class="step-icon">{icon}</span>'
                f'<span>{step}</span>'
                f"</div>"
            )
        progress_placeholder.markdown(
            f"""
            <div class="progress-container">
                <div class="progress-title">Progression de l'analyse</div>
                {html_rows}
                <div class="searching-label">L'agent effectue des recherches web...</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_progress("", [])

    # ── Run the agent ──────────────────────────────────────────────────────
    os.environ["ANTHROPIC_API_KEY"] = anthropic_key
    os.environ["TAVILY_API_KEY"]    = tavily_key

    from agent import run_screening

    full_text = [""]

    def on_text(text):
        full_text[0] = text

    def on_tool_use(name, inputs):
        pass  # Intentionally silent — no raw queries shown

    def on_tool_result(_):
        pass

    def on_step(step_name: str):
        # Mark previous current step as done
        if (
            st.session_state.current_step
            and st.session_state.current_step not in st.session_state.steps_done
        ):
            st.session_state.steps_done = st.session_state.steps_done + [st.session_state.current_step]
        st.session_state.current_step = step_name
        render_progress(step_name, st.session_state.steps_done)

    try:
        result = run_screening(
            company_name=company,
            deliverable_type=deliv_key,
            context=context,
            on_text=on_text,
            on_tool_use=on_tool_use,
            on_tool_result=on_tool_result,
            on_step=on_step,
        )
        # Mark last step as done
        final_steps_done = list(st.session_state.steps_done)
        if st.session_state.current_step and st.session_state.current_step not in final_steps_done:
            final_steps_done.append(st.session_state.current_step)

        st.session_state.result_text = result
        st.session_state.steps_done  = final_steps_done
        st.session_state.screen      = 3
        st.rerun()
    except Exception as e:
        st.error(f"Erreur lors de l'analyse : {e}")
        if st.button("← Retour"):
            st.session_state.screen = 1
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 3 — RESULTS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.screen == 3:

    company    = st.session_state.company
    deliv_key  = st.session_state.deliverable_type
    deliv_info = DELIVERABLE_BY_KEY.get(deliv_key, DELIVERABLES[0])
    result     = st.session_state.result_text

    # Header
    st.markdown(
        f'<div class="company-badge">{company}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"**{deliv_info['icon']} {deliv_info['title']}** — Analyse terminée")
    st.markdown("---")

    # Download buttons
    col_dl1, col_dl2, col_dl3 = st.columns([2, 2, 4])

    with col_dl1:
        st.download_button(
            label="📄 Télécharger en TXT",
            data=result,
            file_name=f"screening_{company.replace(' ', '_').lower()}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with col_dl2:
        try:
            from pdf_generator import generate_pdf
            pdf_bytes = generate_pdf(result, company, deliv_key)
            st.download_button(
                label="📕 Télécharger en PDF",
                data=pdf_bytes,
                file_name=f"screening_{company.replace(' ', '_').lower()}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except ImportError:
            st.info("PDF indisponible (reportlab non installé).")
        except Exception as ex:
            st.warning(f"PDF temporairement indisponible : {ex}")

    st.markdown("---")

    # Full report
    st.markdown('<div class="result-header">Rapport d\'analyse</div>', unsafe_allow_html=True)
    st.markdown(result, unsafe_allow_html=False)

    st.markdown("---")

    # New analysis button
    if st.button("🔍 Nouvelle analyse", type="primary"):
        for k in ["screen", "company", "deliverable_type", "context", "result_text", "current_step", "steps_done"]:
            if k == "screen":
                st.session_state[k] = 1
            elif k == "steps_done":
                st.session_state[k] = []
            else:
                st.session_state[k] = ""
        st.rerun()
