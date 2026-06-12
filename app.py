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
header[data-testid="stHeader"] svg,
header[data-testid="stHeader"] span,
header[data-testid="stHeader"] p,
header[data-testid="stHeader"] button {
    filter: invert(1) !important;
    color: #000000 !important;
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
        "found_executives": [],
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
            # Temps écoulé
            m_el, s_el  = divmod(int(elapsed), 60)
            elapsed_str = f"{m_el}:{s_el:02d}"
            # Temps restant en MM:SS précis
            remaining   = max(0, estimated - elapsed)
            m_re, s_re  = divmod(int(remaining), 60)
            if remaining <= 0:
                rem_str   = "Finalisation..."
                rem_color = "#5BAD8C"
            else:
                rem_str   = f"{m_re}:{s_re:02d}"
                rem_color = "#4A7FA5" if remaining > 60 else "#E67E22"
            pct_bar = min(97, int(elapsed / estimated * 100)) if estimated else 50
            timing_html = f"""
            <div style="background:#EEF2F6; border-radius:8px; padding:12px 18px; margin-bottom:12px; font-size:0.85rem;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="color:#4A5568;">⏱ Temps écoulé</span>
                    <span style="color:#4A5568;">Temps restant</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong style="color:#1A2744; font-size:1.3rem; font-family:monospace; letter-spacing:1px;">{elapsed_str}</strong>
                    <strong style="color:{rem_color}; font-size:1.3rem; font-family:monospace; letter-spacing:1px;">{rem_str}</strong>
                </div>
            </div>
            <div style="background:#DDD5C8; border-radius:4px; height:6px; margin-bottom:18px; overflow:hidden;">
                <div style="background:linear-gradient(90deg,#4A7FA5,#5BAD8C); width:{pct_bar}%; height:100%; border-radius:4px; transition:width 0.5s;"></div>
            </div>"""
        else:
            est_min = max(1, int(estimated / 60))
            m_est, s_est = divmod(estimated, 60)
            timing_html = f"""
            <div style="background:#EEF2F6; border-radius:8px; padding:12px 18px; margin-bottom:12px;
                        display:flex; align-items:center; gap:8px; font-size:0.83rem; color:#4A5568;">
                <span>⏱</span>
                <span>Durée estimée : <strong style="color:#4A7FA5; font-family:monospace;">{est_min}:{s_est:02d}</strong></span>
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
        # Rafraîchit le timer à chaque recherche web (~toutes les 5-10s)
        elapsed = time.time() - start_time
        render_progress(st.session_state.current_step, st.session_state.steps_done, elapsed=elapsed)

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

    def find_executives(competitor: str) -> list:
        """Cherche les dirigeants officiels via Pappers (registre Infogreffe)."""
        from tavily import TavilyClient
        import re as _r
        tc = TavilyClient(api_key=tavily_key)
        executives = []
        seen_names = set()
        try:
            # Recherche sur Pappers — source officielle française
            res = tc.search(
                query=f'"{competitor}" site:pappers.fr',
                max_results=5,
                search_depth="advanced",
            )
            # Titres de direction à détecter dans le contenu Pappers
            titre_patterns = [
                r"(Président[^,\n:]*)[:\s]+([A-ZÀ-Ö][a-zà-ö]+(?:\s[A-ZÀ-Ö][a-zà-ö]+)+)",
                r"(G[ée]rant[^,\n:]*)[:\s]+([A-ZÀ-Ö][a-zà-ö]+(?:\s[A-ZÀ-Ö][a-zà-ö]+)+)",
                r"(Directeur [Gg][ée]n[ée]ral[^,\n:]*)[:\s]+([A-ZÀ-Ö][a-zà-ö]+(?:\s[A-ZÀ-Ö][a-zà-ö]+)+)",
                r"(PDG[^,\n:]*)[:\s]+([A-ZÀ-Ö][a-zà-ö]+(?:\s[A-ZÀ-Ö][a-zà-ö]+)+)",
                r"(Administrateur[^,\n:]*)[:\s]+([A-ZÀ-Ö][a-zà-ö]+(?:\s[A-ZÀ-Ö][a-zà-ö]+)+)",
                # Format inversé : NOM Prénom, titre
                r"([A-ZÀÂÉÈÊËÎÏÔÙÛÜ][A-ZÀÂÉÈÊËÎÏÔÙÛÜ\s\-]+),?\s+(Président|Gérant|Directeur|PDG|Fondateur)",
            ]
            for r in res.get("results", []):
                content = r.get("content", "") + " " + r.get("title", "")
                pappers_url = r.get("url", "")
                for pat in titre_patterns:
                    for m in _r.finditer(pat, content):
                        if len(m.groups()) == 2:
                            titre, nom = m.group(1).strip(), m.group(2).strip()
                        else:
                            continue
                        # Nettoyer le nom
                        nom = nom.strip().strip(",").strip()
                        if nom in seen_names or len(nom) < 4:
                            continue
                        seen_names.add(nom)
                        # Lien LinkedIn de recherche pour ce dirigeant
                        import urllib.parse as _up
                        li_url = f"https://www.linkedin.com/search/results/people/?keywords={_up.quote(nom + ' ' + competitor)}"
                        executives.append({
                            "name": nom,
                            "title": titre.split("(")[0].strip(),
                            "url": li_url,
                            "source": pappers_url,
                        })
        except Exception:
            pass

        # Fallback : si Pappers n'a rien trouvé, recherche directe société
        if not executives:
            try:
                res2 = tc.search(
                    query=f'{competitor} gérant président directeur général représentant légal',
                    max_results=4,
                    search_depth="advanced",
                    include_domains=["pappers.fr", "societe.com", "infogreffe.fr", "verif.com"],
                )
                import urllib.parse as _up2
                for r in res2.get("results", []):
                    content = r.get("content", "")
                    for pat in titre_patterns:
                        for m in _r.finditer(pat, content):
                            if len(m.groups()) == 2:
                                titre, nom = m.group(1).strip(), m.group(2).strip()
                            else:
                                continue
                            nom = nom.strip().strip(",")
                            if nom in seen_names or len(nom) < 4:
                                continue
                            seen_names.add(nom)
                            li_url = f"https://www.linkedin.com/search/results/people/?keywords={_up2.quote(nom + ' ' + competitor)}"
                            executives.append({"name": nom, "title": titre.split("(")[0].strip(), "url": li_url, "source": r.get("url","")})
            except Exception:
                pass

        return executives[:6]

    def _extract_competitor_context(competitor: str, report: str) -> str:
        """Extrait la fiche du concurrent depuis le rapport."""
        # Cherche la section ### ... NOM jusqu'au prochain --- ou ###
        pattern = rf'###[^\n]*{_re.escape(competitor)}[^\n]*\n(.*?)(?=\n---|\n###|\Z)'
        match = _re.search(pattern, report, _re.DOTALL | _re.IGNORECASE)
        if match:
            raw = match.group(1).strip()
            # Garde max 800 caractères pour ne pas surcharger le prompt
            return raw[:800]
        return ""

    def generate_contact_email(competitor: str, main_company: str, comp_context: str = "") -> str:
        client = _anthropic.Anthropic(api_key=anthropic_key)

        context_block = ""
        if comp_context:
            context_block = f"""
Voici ce que tu sais déjà sur {competitor} (extrait du rapport de screening) :
---
{comp_context}
---
Utilise 1 ou 2 éléments concrets et précis de ces infos dans l'email pour montrer que tu connais l'entreprise.
Ne cite pas tout — choisis ce qui est le plus pertinent pour amorcer la conversation (ex : leur activité principale, leur géographie, leur modèle, leur dirigeant si mentionné).
"""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=700,
            messages=[{"role": "user", "content": f"""Tu es un professionnel du M&A qui écrit un vrai email de prise de contact — pas un template corporate.

Email pour approcher {competitor}, dans le cadre d'une analyse du secteur de {main_company}.
{context_block}
Règles absolues :
- Écris comme un humain qui envoie un vrai email, pas comme un outil IA
- Objet : court, direct, donne envie d'ouvrir (pas "Prise de contact" ou "Opportunité de collaboration")
- Commence par "Bonjour [Prénom]," — jamais "Madame, Monsieur"
- 3 courts paragraphes : qui tu es / un détail concret sur leur activité qui justifie le contact / ce que tu proposes (30 min, call ou café)
- Zéro jargon : pas de "synergies", "deal flow", "value creation", "best regards"
- Pas de mise en forme (pas de tirets, pas de gras, pas de liste)
- Se signer "[Prénom Nom] — [Titre], [Fonds]" sur deux lignes
- Entièrement en français
- Maximum 10 lignes de corps

Retourne uniquement l'email, format exact :
Objet : [objet]

[corps]"""}]
        )
        return response.content[0].text

    # Détecter les concurrents dans le rapport
    # Pattern 1 : ### Concurrent N° — NOM  (format standard)
    detected = _re.findall(r'###\s+Concurrent[^—\n]*—\s*\**([^\n*]+)', result)
    # Pattern 2 : ### N° — NOM  (sans le mot "Concurrent")
    detected += _re.findall(r'###\s+\d+[^\S\n]*[—–-][^\S\n]*\**([^\n*]+)', result)
    # Pattern 3 : ### NOM DE L'ENTREPRISE  (heading direct sans numéro)
    all_h3 = _re.findall(r'###\s+([^\n]+)', result)
    fmt1 = set(_re.findall(r'###\s+Concurrent[^—\n]*—\s*\**([^\n*]+)', result))
    fmt2 = set(_re.findall(r'###\s+\d+[^\S\n]*[—–-][^\S\n]*\**([^\n*]+)', result))
    already = fmt1 | fmt2
    skip_kw = {"étape","analyse","cartographie","synthèse","positionnement","concurrent","note","fiche","benchmark","géographique","m&a","secteur"}
    for h in all_h3:
        clean = h.strip().strip("*").strip()
        if clean and not any(k in clean.lower() for k in skip_kw) and clean not in already:
            detected.append(clean)
    # Dédoublonner et nettoyer
    seen, unique = set(), []
    for c in detected:
        c = c.strip().strip("*").strip()
        if c and c not in seen:
            seen.add(c)
            unique.append(c)
    detected = unique

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
                        st.session_state.found_executives = []
                        with st.spinner(f"Rédaction de l'email et recherche des dirigeants..."):
                            ctx = _extract_competitor_context(comp, result)
                            st.session_state.generated_email  = generate_contact_email(comp, company, ctx)
                            st.session_state.found_executives = find_executives(comp)
    else:
        # Fallback : saisie manuelle si aucun concurrent détecté
        manual_comp = st.text_input("Nom du concurrent à contacter :",
                                     placeholder="ex : Entreprise XYZ",
                                     key="manual_email_target")
        if manual_comp and st.button("✉️ Générer l'email", type="primary"):
            st.session_state.email_target    = manual_comp
            st.session_state.generated_email = ""
            st.session_state.found_executives = []
            with st.spinner(f"Rédaction de l'email et recherche des dirigeants..."):
                ctx = _extract_competitor_context(manual_comp, result)
                st.session_state.generated_email  = generate_contact_email(manual_comp, company, ctx)
                st.session_state.found_executives = find_executives(manual_comp)

    # Afficher l'email généré
    if st.session_state.generated_email:
        raw = st.session_state.generated_email.strip()

        # Séparer objet et corps
        lines = raw.split("\n")
        subject_line = ""
        body_lines = []
        in_body = False
        for line in lines:
            if line.lower().startswith("objet"):
                subject_line = line.split(":", 1)[-1].strip()
            elif in_body or (subject_line and line.strip() == "" and not in_body):
                in_body = True
                body_lines.append(line)
            elif subject_line and line.strip():
                in_body = True
                body_lines.append(line)

        body_text = "\n".join(body_lines).strip()

        st.markdown(
            f'<div style="font-size:0.82rem;color:#6B7A8D;margin:18px 0 10px 0;">'
            f'Brouillon pour <strong style="color:#1A2744;">{st.session_state.email_target}</strong>'
            f' — personnalisez les champs entre crochets avant envoi</div>',
            unsafe_allow_html=True,
        )

        # Rendu email
        st.markdown(f"""
<div style="background:#FFFFFF; border:1px solid #D4DCE4; border-radius:12px;
            padding:0; overflow:hidden; box-shadow:0 2px 10px rgba(26,39,68,0.07);">

  <div style="background:#F0F4F8; border-bottom:1px solid #D4DCE4;
              padding:12px 20px; display:flex; align-items:center; gap:10px;">
    <span style="font-size:0.78rem; font-weight:600; color:#64748B; min-width:48px;">Objet</span>
    <span style="font-size:0.92rem; font-weight:600; color:#1A2744;">{subject_line}</span>
  </div>

  <div style="padding:22px 24px; font-size:0.93rem; color:#1A202C;
              line-height:1.85; white-space:pre-wrap; font-family:'Inter', sans-serif;">
{body_text}
  </div>

</div>
""", unsafe_allow_html=True)

        # Zone de copie discrète
        with st.expander("📋 Copier le texte brut"):
            st.text_area("", value=raw, height=220, label_visibility="collapsed", key="email_copy_area")

        # Lien page entreprise LinkedIn
        import urllib.parse as _urlparse
        li_company = f"https://www.linkedin.com/search/results/companies/?keywords={_urlparse.quote(st.session_state.email_target)}"
        li_svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" '
                  'viewBox="0 0 24 24" fill="#0A66C2"><path d="M20.447 20.452h-3.554v-5.569'
                  'c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351'
                  'V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 '
                  '5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 '
                  '2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 '
                  '.774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 '
                  '22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>')
        st.markdown(
            f'<div style="margin-top:10px;">'
            f'<a href="{li_company}" target="_blank" style="display:inline-flex;align-items:center;'
            f'gap:6px;background:#FFFFFF;border:1px solid #C8D4DC;border-radius:8px;'
            f'padding:7px 14px;font-size:0.83rem;font-weight:600;color:#0A66C2;text-decoration:none;">'
            f'{li_svg} Voir la page entreprise</a></div>',
            unsafe_allow_html=True,
        )

        # Cartes dirigeants trouvés
        execs = st.session_state.get("found_executives", [])
        if execs:
            st.markdown(
                '<div style="font-size:0.82rem;font-weight:600;color:#64748B;'
                'text-transform:uppercase;letter-spacing:0.05em;margin:18px 0 10px 0;">'
                'Dirigeants identifiés <span style="font-size:0.72rem;font-weight:400;'
                'color:#94A3B8;text-transform:none;">(source : registre officiel Pappers / Infogreffe)</span></div>',
                unsafe_allow_html=True,
            )
            cols = st.columns(min(len(execs), 3))
            for idx, exec_ in enumerate(execs):
                with cols[idx % 3]:
                    st.markdown(
                        f'<a href="{exec_["url"]}" target="_blank" style="text-decoration:none;">'
                        f'<div style="background:#FFFFFF;border:1px solid #C8D4DC;border-radius:10px;'
                        f'padding:12px 14px;transition:box-shadow 0.2s;">'
                        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
                        f'{li_svg}'
                        f'<span style="font-size:0.88rem;font-weight:700;color:#1A2744;">{exec_["name"]}</span>'
                        f'</div>'
                        f'<div style="font-size:0.78rem;color:#64748B;line-height:1.4;">{exec_["title"] or "Dirigeant"}</div>'
                        f'<div style="font-size:0.75rem;color:#0A66C2;margin-top:6px;font-weight:600;">Voir le profil →</div>'
                        f'</div></a>',
                        unsafe_allow_html=True,
                    )
        elif st.session_state.generated_email:
            st.markdown(
                '<div style="font-size:0.8rem;color:#94A3B8;margin-top:12px;font-style:italic;">'
                'Aucun profil dirigeant trouvé publiquement — utilisez la page entreprise LinkedIn.</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # New analysis button
    if st.button("🔍 Nouvelle analyse", type="primary"):
        for k in ["screen", "company", "deliverable_type", "context", "result_text",
                  "current_step", "steps_done", "email_target", "generated_email", "found_executives"]:
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
