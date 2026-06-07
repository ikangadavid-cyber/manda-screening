import os
import time
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
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
    color: #1A202C;
}

/* ── Texte du rapport (markdown Streamlit) ── */
.stMarkdown p, .stMarkdown li, .stMarkdown td, .stMarkdown th {
    color: #1A202C !important;
    font-size: 0.95rem;
    line-height: 1.75;
}
.stMarkdown h1 { color: #1A2744 !important; font-size: 1.5rem !important; font-weight: 800 !important; border-bottom: 2px solid #4A7FA5; padding-bottom: 6px; margin-top: 24px !important; }
.stMarkdown h2 { color: #1A2744 !important; font-size: 1.2rem !important; font-weight: 700 !important; margin-top: 20px !important; }
.stMarkdown h3 { color: #2D5A7A !important; font-size: 1.05rem !important; font-weight: 600 !important; }
.stMarkdown strong { color: #1A2744 !important; font-weight: 700 !important; }
.stMarkdown em { color: #3A5068 !important; }
.stMarkdown code { background: #E8EDF2 !important; color: #1A2744 !important; border-radius: 4px; padding: 1px 5px; }
.stMarkdown blockquote { border-left: 3px solid #4A7FA5 !important; padding-left: 12px; color: #3A5068 !important; }
.stMarkdown hr { border-color: #C8D4DC !important; margin: 16px 0 !important; }

/* ── Tableaux ── */
.stMarkdown table { width: 100%; border-collapse: collapse; margin: 12px 0; }
.stMarkdown th { background: #1A2744 !important; color: #F0F4F8 !important; font-weight: 600; padding: 10px 14px; text-align: left; }
.stMarkdown td { color: #1A202C !important; padding: 8px 14px; border-bottom: 1px solid #D4DCE4; }
.stMarkdown tr:nth-child(even) td { background: #EEF2F6 !important; }
.stMarkdown tr:hover td { background: #E4ECF4 !important; }

/* ── Zone résultats ── */
.result-box {
    background: #FFFFFF;
    border: 1px solid #C8D4DC;
    border-radius: 14px;
    padding: 28px 32px;
    margin-top: 16px;
    box-shadow: 0 2px 12px rgba(26,39,68,0.07);
}

/* ── Animations ── */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0);    }
}
@keyframes pulse {
    0%   { opacity: 1;   transform: scale(1);    }
    50%  { opacity: 0.3; transform: scale(1.4);  }
    100% { opacity: 1;   transform: scale(1);    }
}
@keyframes progressSlide {
    from { width: 0%; }
    to   { width: 100%; }
}

/* ── Fond général : crème chaude ── */
[data-testid="stAppViewContainer"] {
    background: #F5F0E8;
}
.main .block-container {
    max-width: 920px;
    padding-top: 2rem;
    margin: 0 auto;
    animation: fadeIn 0.4s ease both;
    background: transparent;
}

/* ── Sidebar : bleu nuit avec texte clair ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1A2744 0%, #243352 100%);
    border-right: none;
    box-shadow: 4px 0 20px rgba(0,0,0,0.15);
}
section[data-testid="stSidebar"] * {
    color: #C8D6E8 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(200,214,232,0.2) !important;
}
section[data-testid="stSidebar"] .sidebar-logo {
    font-size: 1.5rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    padding: 8px 0 4px 0;
    color: #FFFFFF !important;
}
section[data-testid="stSidebar"] .sidebar-accent {
    color: #7EB8D4 !important;
}
section[data-testid="stSidebar"] .sidebar-sources {
    font-size: 0.83rem;
    line-height: 1.9;
    color: #8FA8C4 !important;
}
section[data-testid="stSidebar"] button {
    background: rgba(255,255,255,0.1) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    color: #C8D6E8 !important;
}
section[data-testid="stSidebar"] button:hover {
    background: rgba(255,255,255,0.18) !important;
}

/* ── Titre principal ── */
.main-title {
    font-size: 2.4rem;
    font-weight: 800;
    color: #1A2744;
    letter-spacing: -1px;
    margin-bottom: 0.2rem;
}
.main-title span { color: #4A7FA5; }
.main-subtitle {
    font-size: 1.0rem;
    color: #6B7A8D;
    margin-bottom: 2rem;
    line-height: 1.6;
}

/* ── Cartes livrables ── */
.card-btn {
    background: #FDFAF5;
    border: 1.5px solid #DDD5C8;
    border-radius: 14px;
    padding: 18px 20px;
    cursor: pointer;
    transition: all 0.22s ease;
    width: 100%;
    text-align: left;
}
.card-btn:hover {
    border-color: #4A7FA5;
    border-left: 4px solid #4A7FA5;
    box-shadow: 0 8px 24px rgba(74,127,165,0.18);
    transform: translateY(-3px);
    background: #EEF4F8;
}
.card-btn.selected {
    background: #E8F1F8;
    border: 1.5px solid #4A7FA5;
    border-left: 4px solid #4A7FA5;
}
.card-icon  { font-size: 1.6rem; display: block; margin-bottom: 8px; }
.card-title { font-size: 0.96rem; font-weight: 700; color: #1A2744; display: block; margin-bottom: 4px; }
.card-desc  { font-size: 0.79rem; color: #6B7A8D; line-height: 1.5; }

/* ── Écran d'attente ── */
.progress-topbar      { height: 4px; background: #DDD5C8; border-radius: 2px; margin-bottom: 20px; overflow: hidden; }
.progress-topbar-fill { height: 100%; background: linear-gradient(90deg, #4A7FA5, #5BAD8C); border-radius: 2px; animation: progressSlide 40s linear forwards; }

.progress-container {
    background: #FDFAF5;
    border: 1px solid #DDD5C8;
    border-radius: 14px;
    padding: 26px 30px;
    margin: 16px 0;
    box-shadow: 0 4px 16px rgba(26,39,68,0.07);
}
.progress-header    { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.progress-title     { font-size: 1.05rem; font-weight: 700; color: #1A2744; }
.progress-company   { font-size: 0.88rem; color: #6B7A8D; }
.progress-deliverable {
    display: inline-block;
    background: #E8F1F8;
    border: 1px solid #B8D0E4;
    color: #2D5A7A;
    font-weight: 600;
    font-size: 0.82rem;
    padding: 3px 10px;
    border-radius: 20px;
    margin-top: 2px;
}

.step-row           { display: flex; align-items: center; gap: 10px; padding: 8px 0; font-size: 0.91rem; color: #4A5568; border-bottom: 1px solid #EDE8DF; transition: all 0.25s ease; }
.step-row:last-of-type { border-bottom: none; }
.step-row.done      { color: #2E7D55; }
.step-row.active    { color: #4A7FA5; font-weight: 600; }
.step-row.pending   { color: #A0ADB8; }
.step-icon          { font-size: 1.1rem; min-width: 24px; }

.pulse-dot {
    display: inline-block; width: 8px; height: 8px;
    background: #4A7FA5; border-radius: 50%;
    margin-left: 6px; animation: pulse 1.4s ease-in-out infinite; vertical-align: middle;
}
.searching-label { font-size: 0.82rem; color: #A0ADB8; margin-top: 16px; font-style: italic; display: flex; align-items: center; gap: 6px; }

/* ── Résultat ── */
.result-header { font-size: 1.05rem; font-weight: 700; color: #1A2744; margin-bottom: 14px; }
.company-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #E8F1F8; border: 1px solid #B8D0E4;
    color: #2D5A7A; font-weight: 700; font-size: 1.05rem;
    padding: 6px 16px; border-radius: 8px; margin-bottom: 10px;
}

/* ── Boutons Streamlit ── */
div[data-testid="stButton"] > button {
    border-radius: 10px; font-weight: 600; font-size: 0.9rem;
    transition: all 0.2s ease; letter-spacing: 0.01em;
    background: #FDFAF5; border: 1.5px solid #DDD5C8; color: #1A2744;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: #1A2744; border: none; color: #F5F0E8;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    background: #243352;
    box-shadow: 0 4px 16px rgba(26,39,68,0.3);
    transform: translateY(-1px);
}
div[data-testid="stDownloadButton"] > button {
    border-radius: 10px; font-size: 0.88rem; font-weight: 600; transition: all 0.2s ease;
}

/* ── Expander ── */
details {
    border: 1px solid #DDD5C8 !important; border-radius: 12px !important;
    margin-bottom: 16px !important; background: #FDFAF5 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}
details summary { font-weight: 600 !important; color: #1A2744 !important; padding: 2px 0 !important; }

/* ── Inputs ── */
div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
    background: #FDFAF5 !important;
    border: 1.5px solid #DDD5C8 !important;
    border-radius: 10px !important;
    color: #2D3748 !important;
}
div[data-testid="stTextInput"] input:focus, div[data-testid="stTextArea"] textarea:focus {
    border-color: #4A7FA5 !important;
    box-shadow: 0 0 0 3px rgba(74,127,165,0.15) !important;
}

/* ── File uploader ── */
div[data-testid="stFileUploader"] {
    background: #FDFAF5 !important;
    border: 1.5px dashed #B8C4CC !important;
    border-radius: 12px !important;
}

/* ── Tabs ── */
div[data-testid="stTabs"] button {
    color: #6B7A8D !important;
    font-weight: 500 !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #1A2744 !important;
    font-weight: 700 !important;
    border-bottom: 2px solid #4A7FA5 !important;
}

/* ── File badge ── */
.file-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #EAF5EE; border: 1px solid #A8D5B8;
    color: #2E6B45; font-size: 0.8rem;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
    margin: 4px 4px 4px 0;
}
.file-badge-name {
    max-width: 160px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* ── Section label ── */
.section-label {
    font-size: 0.82rem;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
}

/* ── Spinner ── */
div[data-testid="stSpinner"] > div {
    font-size: 0.9rem;
    color: #64748B;
}

/* ── Barre Streamlit : fond crème, icônes grises ── */
header[data-testid="stHeader"] {
    background: #F5F0E8 !important;
    box-shadow: none !important;
    border-bottom: none !important;
}
header[data-testid="stHeader"] svg {
    filter: invert(0.6) !important;
}
footer { visibility: hidden !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #F1F5F9; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

/* ── Tabs ── */
button[data-baseweb="tab"] {
    font-size: 0.88rem !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Deliverable type definitions ──────────────────────────────────────────────
DELIVERABLES = [
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

# Estimated duration in seconds per deliverable type (used for progress timer)
ESTIMATED_SECONDS = {
    "fiche":     90,    # ~1.5 min
    "benchmark": 210,   # ~3.5 min
    "manda":     180,   # ~3 min
    "geo":       180,   # ~3 min
}

# ── Session state initialization ──────────────────────────────────────────────
def init_state():
    defaults = {
        "screen":           1,
        "company":          "",
        "deliverable_type": "fiche",
        "context":          "",
        "result_text":      "",
        "current_step":     "",
        "steps_done":       [],
        "email_target":     "",
        "generated_email":  "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div class="sidebar-logo">🔍 M&A <span class="sidebar-accent">Screening</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown('<div class="section-label">Sources utilisées</div>', unsafe_allow_html=True)
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
                elif k == "steps_done":
                    st.session_state[k] = []
                else:
                    st.session_state[k] = ""
            st.rerun()

    st.markdown("---")
    st.markdown('<div class="section-label">Inviter un consultant</div>', unsafe_allow_html=True)
    invite_email = st.text_input(
        "Email du consultant",
        placeholder="prenom.nom@cabinet.fr",
        label_visibility="collapsed",
        key="invite_email_field",
    )
    if invite_email and "@" in invite_email:
        subject = "Accès à l'outil M&A Screening IA"
        body = (
            f"Bonjour,\n\n"
            f"Je t'invite à utiliser M&A Screening IA, un outil d'intelligence économique "
            f"qui permet d'analyser une entreprise en profondeur en quelques minutes "
            f"(cartographie concurrentielle, actualités M&A, qualification sectorielle).\n\n"
            f"Accède à l'outil ici : https://screening-ma.streamlit.app\n\n"
            f"Bonne analyse,"
        )
        import urllib.parse
        mailto = f"mailto:{invite_email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
        st.markdown(
            f'<a href="{mailto}" target="_blank" style="'
            'display:block; text-align:center; background:rgba(255,255,255,0.12); '
            'border:1px solid rgba(255,255,255,0.25); border-radius:8px; '
            'color:#C8D6E8 !important; font-size:0.85rem; font-weight:600; '
            'padding:8px 0; margin-top:6px; text-decoration:none; cursor:pointer;">'
            '📨 Envoyer l\'invitation</a>',
            unsafe_allow_html=True,
        )
    elif invite_email:
        st.markdown(
            '<div style="color:#E88; font-size:0.78rem; margin-top:4px;">Email invalide</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(
        '<div class="section-label">À propos</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sidebar-sources">'
        "<strong style='color:#C8D6E8;'>M&A Screening IA</strong><br>"
        "Outil d'intelligence économique alimenté par l'IA pour les professionnels du M&A.<br><br>"
        "Analyse d'entreprises, cartographie concurrentielle, actualités sectorielle et prise de contact — en quelques minutes.<br><br>"
        "✉️ <a href='mailto:contact@screening-ma.fr' style='color:#7EB8D4;'>contact@screening-ma.fr</a>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sidebar-sources" style="margin-top:10px;color:#5A7A94;font-size:0.75rem;">'
        "v1.0 · 2026 · Tous droits réservés"
        "</div>",
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 1 — INPUT
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.screen == 1:

    st.markdown(
        '<div class="main-title">Screening <span>M&A</span></div>',
        unsafe_allow_html=True,
    )
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

    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1A2744 0%, #2D4A7A 100%);
        border-radius: 14px;
        padding: 14px 22px;
        margin: 18px 0 14px 0;
        display: flex;
        align-items: center;
        gap: 12px;
    ">
        <span style="font-size:1.3rem;">📊</span>
        <div>
            <div style="color:#FFFFFF; font-size:1.05rem; font-weight:700; letter-spacing:-0.3px;">
                Choisissez le type d'analyse
            </div>
            <div style="color:#8FA8C8; font-size:0.82rem; margin-top:2px;">
                Cliquez sur un livrable pour lancer l'analyse
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Couleurs d'accent par livrable
    CARD_COLORS = {
        "complet":   ("#4A7FA5", "#E8F1F8"),
        "fiche":     ("#7A5FA5", "#F0EBF8"),
        "benchmark": ("#A5614A", "#F8EEE8"),
        "manda":     ("#2E7D55", "#E8F5EE"),
        "geo":       ("#A5944A", "#F8F3E8"),
    }

    # 2x2 + 1 grid for deliverable cards
    col_a, col_b = st.columns(2)
    col_c, col_d = st.columns(2)
    col_e, _, _ = st.columns(3)

    card_cols = [col_a, col_b, col_c, col_d, col_e]

    # Zone d'erreur visible AU-DESSUS des cartes
    error_zone = st.empty()

    clicked_key = None
    for idx, deliv in enumerate(DELIVERABLES):
        accent, bg = CARD_COLORS[deliv["key"]]
        with card_cols[idx]:
            st.markdown(f"""
            <div style="
                background:{bg};
                border:2px solid {accent}40;
                border-left:4px solid {accent};
                border-radius:12px;
                padding:16px 18px;
                margin-bottom:8px;
            ">
                <span style="font-size:1.5rem;">{deliv['icon']}</span>
                <div style="font-weight:700;color:#1A2744;font-size:0.95rem;margin:6px 0 3px 0;">{deliv['title']}</div>
                <div style="font-size:0.78rem;color:#5A6A7A;line-height:1.4;">{deliv['desc']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Sélectionner", key=f"card_{deliv['key']}", use_container_width=True):
                clicked_key = deliv["key"]

    # Validation centralisée — messages visibles
    if clicked_key:
        if not company_input.strip():
            error_zone.warning("⚠️ Veuillez entrer le nom d'une entreprise avant de choisir un type d'analyse.")
        elif not anthropic_key or not tavily_key:
            error_zone.error("🔑 Clés API manquantes. Contactez l'administrateur.")
        else:
            st.session_state.company          = company_input.strip()
            st.session_state.deliverable_type = clicked_key
            st.session_state.screen           = 2
            st.session_state.steps_done       = []
            st.session_state.current_step     = ""
            st.session_state.result_text      = ""
            st.rerun()

    # Context section — tabs for manual input and document import
    with st.expander("💡 Informations déjà connues (optionnel)"):
        tab_manual, tab_docs = st.tabs(["✏️ Saisie libre", "📎 Importer des documents"])

        with tab_manual:
            manual_context = st.text_area(
                "Ce que vous savez déjà sur cette entreprise",
                placeholder=(
                    "Exemples : secteur d'activité, chiffre d'affaires approximatif, "
                    "principaux clients, zone géographique, contexte de l'opération..."
                ),
                height=130,
                key="context_input_field",
            )

        with tab_docs:
            st.markdown(
                '<div class="section-label">Glissez jusqu\'à 5 fichiers (PDF, Word, Excel, TXT, CSV, MD)</div>',
                unsafe_allow_html=True,
            )
            uploaded_files = st.file_uploader(
                "Importer des documents",
                type=["pdf", "docx", "xlsx", "xls", "txt", "md", "csv"],
                accept_multiple_files=True,
                label_visibility="collapsed",
                key="doc_uploader",
            )

            doc_texts = []
            if uploaded_files:
                from document_extractor import extract_text
                shown = uploaded_files[:5]
                for uf in shown:
                    extracted = extract_text(uf)
                    char_count = len(extracted)
                    doc_texts.append(
                        f"\n\n--- Document : {uf.name} ---\n\n{extracted}"
                    )
                    st.markdown(
                        f'<div class="file-badge">'
                        f'📄 <span class="file-badge-name">{uf.name}</span>'
                        f' &nbsp;·&nbsp; {char_count:,} car.'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                if len(uploaded_files) > 5:
                    st.caption("Seuls les 5 premiers fichiers sont pris en compte.")

        # Combine manual text + document texts into session context
        combined_context = manual_context
        if doc_texts:
            combined_context = combined_context + "".join(doc_texts)
        st.session_state.context = combined_context


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 2 — WAITING / RUNNING
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.screen == 2:

    company    = st.session_state.company
    deliv_key  = st.session_state.deliverable_type
    deliv_info = DELIVERABLE_BY_KEY.get(deliv_key, DELIVERABLES[0])
    context    = st.session_state.context
    all_steps  = deliv_info["steps"]

    # Animated progress bar at top
    st.markdown(
        '<div class="progress-topbar"><div class="progress-topbar-fill"></div></div>',
        unsafe_allow_html=True,
    )

    # Header with company + deliverable type
    st.markdown(
        f'<div class="company-badge">🏢 {company}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<span class="progress-deliverable">{deliv_info["icon"]} {deliv_info["title"]}</span>',
        unsafe_allow_html=True,
    )

    # Progress display placeholder
    progress_placeholder = st.empty()

    estimated = ESTIMATED_SECONDS.get(deliv_key, 180)

    def render_progress(current_step: str, steps_done: list, elapsed: float = 0):
        total  = len(all_steps)
        done_n = len(steps_done)

        # ── Timing display ──
        if elapsed > 0:
            m, s        = divmod(int(elapsed), 60)
            elapsed_str = f"{m}:{s:02d}"
            remaining   = max(0, estimated - elapsed)
            if remaining > 90:
                rem_str = f"~{int(remaining // 60) + 1} min"
            elif remaining > 0:
                rem_str = "moins d'1 min"
            else:
                rem_str = "bientôt..."
            pct_bar = min(97, int(elapsed / estimated * 100)) if estimated else 50
            timing_html = f"""
            <div style="background:#EEF2F6; border-radius:8px; padding:10px 16px; margin-bottom:12px;
                        display:flex; justify-content:space-between; align-items:center; font-size:0.83rem;">
                <span style="color:#4A5568;">⏱ Écoulé : <strong style="color:#1A2744;">{elapsed_str}</strong></span>
                <span style="color:#4A5568;">Temps restant : <strong style="color:#4A7FA5;">{rem_str}</strong></span>
            </div>
            <div style="background:#DDD5C8; border-radius:4px; height:5px; margin-bottom:18px; overflow:hidden;">
                <div style="background:linear-gradient(90deg,#4A7FA5,#5BAD8C); width:{pct_bar}%; height:100%; border-radius:4px;"></div>
            </div>"""
        else:
            est_min = max(1, int(estimated / 60))
            timing_html = f"""
            <div style="background:#EEF2F6; border-radius:8px; padding:10px 16px; margin-bottom:12px;
                        display:flex; align-items:center; gap:8px; font-size:0.83rem; color:#4A5568;">
                <span>⏱</span>
                <span>Durée estimée : <strong style="color:#4A7FA5;">~{est_min} minutes</strong></span>
            </div>"""

        # ── Step rows ──
        html_rows = ""
        for step in all_steps:
            if step in steps_done:
                css   = "done"
                icon  = "✅"
                pulse = ""
            elif step == current_step:
                css   = "active"
                icon  = "⏳"
                pulse = '<span class="pulse-dot"></span>'
            else:
                css   = "pending"
                icon  = "⬜"
                pulse = ""
            html_rows += (
                f'<div class="step-row {css}">'
                f'<span class="step-icon">{icon}</span>'
                f'<span>{step}{pulse}</span>'
                f"</div>"
            )

        progress_placeholder.markdown(
            f"""
            <div class="progress-container">
                <div class="progress-header">
                    <div>
                        <div class="progress-title">Progression de l'analyse</div>
                        <div class="progress-company">{company} &nbsp;·&nbsp; {done_n}/{total} étapes</div>
                    </div>
                </div>
                {timing_html}
                {html_rows}
                <div class="searching-label">
                    <span class="pulse-dot"></span>
                    L'agent effectue des recherches web en temps réel...
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_progress("", [], elapsed=0)

    # Vérification des clés avant de lancer
    if not anthropic_key or not tavily_key:
        st.error("🔑 Clés API manquantes — impossible de lancer l'analyse. Contactez l'administrateur.")
        if st.button("← Retour"):
            st.session_state.screen = 1
            st.rerun()
        st.stop()

    # ── Run the agent ──────────────────────────────────────────────────────
    os.environ["ANTHROPIC_API_KEY"] = anthropic_key
    os.environ["TAVILY_API_KEY"]    = tavily_key

    from agent import run_screening

    full_text  = [""]
    start_time = time.time()

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
        elapsed = time.time() - start_time
        render_progress(step_name, st.session_state.steps_done, elapsed=elapsed)

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
        f'<div class="company-badge">🏢 {company}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"**{deliv_info['icon']} {deliv_info['title']}** — Analyse terminée ✅")
    st.markdown("---")

    # Download buttons
    col_dl1, col_dl2, col_dl3 = st.columns([2, 2, 4])

    with col_dl1:
        try:
            from word_generator import generate_word
            docx_bytes = generate_word(result, company, deliv_key)
            st.download_button(
                label="📝 Télécharger en Word",
                data=docx_bytes,
                file_name=f"screening_{company.replace(' ', '_').lower()}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        except Exception as ex:
            st.warning(f"Word indisponible : {ex}")

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

    # Full report in white box
    st.markdown('<div class="result-header">Rapport d\'analyse</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(result)

    st.markdown("---")

    # ── Email de prise de contact ──────────────────────────────────────────
    import re as _re
    import anthropic as _anthropic

    def generate_contact_email(competitor: str, main_company: str) -> str:
        client = _anthropic.Anthropic(api_key=anthropic_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=700,
            messages=[{"role": "user", "content": f"""Tu es un associé senior d'un fonds d'investissement M&A français.

Rédige un email de première prise de contact pour approcher {competitor}.
Contexte : ton fonds étudie le secteur de {main_company} et souhaite rencontrer les acteurs clés du marché.

Contraintes strictes :
- Objet : percutant, 1 ligne
- Corps : 8 à 12 lignes maximum
- Ton : professionnel, chaleureux, direct — pas de jargon financier agressif
- Se présenter comme "[Prénom Nom], Associé chez [Nom du Fonds]"
- Montrer une connaissance du secteur sans être générique
- Demander un échange informel de 20-30 minutes (call ou café à Paris)
- Formule de politesse élégante en fin de mail
- Entièrement en français
- Ne pas inventer de chiffres ou faits précis sur l'entreprise

Format de sortie — uniquement l'email, rien d'autre :
Objet : [objet]

[Corps de l'email]"""}]
        )
        return response.content[0].text

    # Détecter les concurrents dans le rapport
    detected = _re.findall(r'###\s+Concurrent[^—\n]*—\s*\**([^\n*]+)', result)
    detected = [c.strip() for c in detected if c.strip()]

    st.markdown("""
    <div style="background:linear-gradient(135deg,#1A2744 0%,#2D4A7A 100%);
                border-radius:14px; padding:20px 24px; margin-bottom:20px;">
        <div style="color:#FFFFFF; font-size:1.05rem; font-weight:700; margin-bottom:4px;">
            📧 Préparer une prise de contact
        </div>
        <div style="color:#8FA8C8; font-size:0.83rem;">
            Cliquez sur un concurrent pour générer instantanément un email professionnel de premier contact.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if detected:
        cols_per_row = 3
        rows = [detected[i:i+cols_per_row] for i in range(0, len(detected), cols_per_row)]
        for row in rows:
            cols = st.columns(len(row))
            for col, comp in zip(cols, row):
                with col:
                    if st.button(f"✉️ {comp}", key=f"email_btn_{comp}", use_container_width=True):
                        st.session_state.email_target    = comp
                        st.session_state.generated_email = ""
                        with st.spinner(f"Rédaction de l'email pour {comp}..."):
                            st.session_state.generated_email = generate_contact_email(comp, company)
    else:
        # Fallback : saisie manuelle si aucun concurrent détecté
        manual_comp = st.text_input("Nom du concurrent à contacter :",
                                     placeholder="ex : Entreprise XYZ",
                                     key="manual_email_target")
        if manual_comp and st.button("✉️ Générer l'email", type="primary"):
            st.session_state.email_target    = manual_comp
            st.session_state.generated_email = ""
            with st.spinner(f"Rédaction de l'email pour {manual_comp}..."):
                st.session_state.generated_email = generate_contact_email(manual_comp, company)

    # Afficher l'email généré
    if st.session_state.generated_email:
        st.markdown(
            f'<div style="font-size:0.85rem;color:#6B7A8D;margin:16px 0 6px 0;">'
            f'Email généré pour <strong style="color:#1A2744;">{st.session_state.email_target}</strong>'
            f' — copiez et personnalisez avant envoi :</div>',
            unsafe_allow_html=True,
        )
        st.code(st.session_state.generated_email, language=None)

    st.markdown("---")

    # New analysis button
    if st.button("🔍 Nouvelle analyse", type="primary"):
        for k in ["screen", "company", "deliverable_type", "context", "result_text",
                  "current_step", "steps_done", "email_target", "generated_email"]:
            if k == "screen":
                st.session_state[k] = 1
            elif k == "steps_done":
                st.session_state[k] = []
            else:
                st.session_state[k] = ""
        st.rerun()

    # Disclaimer légal
    st.markdown(
        """
        <div style="
            margin-top: 32px;
            padding: 14px 18px;
            background: #F0EDE8;
            border-left: 3px solid #C8B89A;
            border-radius: 6px;
            font-size: 0.76rem;
            color: #7A6E62;
            line-height: 1.6;
        ">
        <strong style="color:#5A5048;">⚠️ Avertissement</strong> — Les informations présentées dans ce rapport sont
        issues de sources publiques disponibles sur Internet à la date de l'analyse. Elles sont fournies
        à titre indicatif et ne constituent en aucun cas un conseil en investissement, une recommandation
        financière ou une due diligence. Les données (chiffre d'affaires, effectifs, valorisations) sont
        des estimations et doivent être vérifiées auprès des sources primaires avant toute prise de décision.
        </div>
        """,
        unsafe_allow_html=True,
    )
