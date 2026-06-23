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

/* ── Email type segmented control ── */
.etype-btn-selected > div > button {
    background: #1A2744 !important;
    border-color: #1A2744 !important;
    color: #F5F0E8 !important;
}
.etype-btn-idle > div > button {
    background: #FDFAF5 !important;
    border: 1.5px solid #C8D4DC !important;
    color: #4A5568 !important;
}
.etype-btn-idle > div > button:hover {
    border-color: #4A7FA5 !important;
    color: #1A2744 !important;
}
</style>
<script>
(function() {
  function disableAutocorrect() {
    document.querySelectorAll('input[type="text"], textarea').forEach(function(el) {
      el.setAttribute('autocorrect', 'off');
      el.setAttribute('autocomplete', 'off');
      el.setAttribute('autocapitalize', 'off');
      el.setAttribute('spellcheck', 'false');
    });
  }
  disableAutocorrect();
  new MutationObserver(disableAutocorrect).observe(document.body, { childList: true, subtree: true });
})();
</script>
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

# ── Mission M&A — définitions ─────────────────────────────────────────────────

BUY_SIDE_STEPS = [
    {
        "key":         "buy_01_carto_verticale",
        "num":         "1a",
        "title":       "Chaîne de valeur",
        "desc":        "Cartographie verticale — acteurs amont / aval et position de l'acquéreur",
        "web_search":  True,
        "needs_input": False,
        "input_label": None,
        "input_hint":  None,
    },
    {
        "key":         "buy_02_carto_horizontale",
        "num":         "1b",
        "title":       "Segments concurrentiels",
        "desc":        "Cartographie horizontale — 2 à 5 segments de marché et rivalité",
        "web_search":  True,
        "needs_input": False,
        "input_label": None,
        "input_hint":  None,
    },
    {
        "key":         "buy_03_recherche_cibles",
        "num":         "2",
        "title":       "Long-list de cibles",
        "desc":        "30 cibles d'acquisition potentielles avec fit stratégique et sources",
        "web_search":  True,
        "needs_input": True,
        "input_label": "Contexte de l'acquéreur",
        "input_hint":  (
            "Secteur d'activité, CA approximatif, fourchette de taille cible, zone géographique, stratégie.\n"
            "Ex : intégrateur industriel électricité / automatisme, CA ~15M€, cibles France 3-15M€."
        ),
    },
    {
        "key":         "buy_04_profil_entreprise",
        "num":         "3",
        "title":       "Fiches cibles",
        "desc":        "Analyse approfondie de chaque société sélectionnée (offre, clients, finances, actionnariat)",
        "web_search":  True,
        "needs_input": True,
        "input_label": "Sociétés à analyser",
        "input_hint":  (
            "Noms des sociétés à profiler (une par ligne). "
            "Ou collez directement les résultats de l'étape Long-list."
        ),
    },
    {
        "key":         "buy_05_qualification_cibles",
        "num":         "4",
        "title":       "Sélection & verdict M&A",
        "desc":        "Classement Liste 1 / 2 / 3 avec rationnel d'acquisition pour chaque cible",
        "web_search":  True,
        "needs_input": True,
        "input_label": "Fiches cibles + contexte acquéreur",
        "input_hint":  (
            "Collez les fiches de l'étape précédente et, si nécessaire, "
            "ajoutez une description de l'acquéreur en tête."
        ),
    },
    {
        "key":         "buy_06_slide_bandeau",
        "num":         "5a",
        "title":       "Slide — Fiche cible",
        "desc":        "Contenu PPT prêt à intégrer — format bandeau (1 ligne / cible)",
        "web_search":  False,
        "needs_input": True,
        "input_label": "Cibles retenues (max 3)",
        "input_hint":  "Collez les fiches des cibles sélectionnées (liste 1 uniquement).",
    },
    {
        "key":         "buy_07_slide_vert_pos",
        "num":         "5b",
        "title":       "Slide — Positionnement vertical",
        "desc":        "Tableau PPT : catégories de la chaîne de valeur + note de positionnement acquéreur (0-3)",
        "web_search":  False,
        "needs_input": True,
        "input_label": "Résultats étape 1a",
        "input_hint":  "Collez le tableau de cartographie verticale (étape 1a).",
    },
    {
        "key":         "buy_08_slide_horiz_rationnel",
        "num":         "5c",
        "title":       "Slide — Rationnel M&A horizontal",
        "desc":        "Tableau PPT : segments concurrentiels + rationnel de rachat + note d'appétit M&A (0-3)",
        "web_search":  False,
        "needs_input": True,
        "input_label": "Résultats étape 1b",
        "input_hint":  "Collez le tableau de cartographie horizontale (étape 1b).",
    },
    {
        "key":         "buy_09_slide_horiz_pos",
        "num":         "5d",
        "title":       "Slide — Positionnement horizontal",
        "desc":        "Tableau PPT : segments concurrentiels + note de présence de l'acquéreur (0-3)",
        "web_search":  False,
        "needs_input": True,
        "input_label": "Résultats étape 1b",
        "input_hint":  "Collez le tableau de cartographie horizontale (étape 1b).",
    },
    {
        "key":         "buy_10_slide_vert_rationnel",
        "num":         "5e",
        "title":       "Slide — Rationnel M&A vertical",
        "desc":        "Tableau PPT : catégories de la chaîne de valeur + rationnel de rachat + note d'appétit (0-3)",
        "web_search":  False,
        "needs_input": True,
        "input_label": "Résultats étape 1a",
        "input_hint":  "Collez le tableau de cartographie verticale (étape 1a).",
    },
]

SELL_SIDE_STEPS = [
    {
        "key":         "sell_01_rapport_entretien",
        "num":         "1",
        "title":       "Rapport d'entretien",
        "desc":        "Retranscription structurée de l'entretien dirigeant en rapport thématique factuel",
        "web_search":  False,
        "needs_input": True,
        "input_label": "Transcription de l'entretien",
        "input_hint":  "Collez ici la transcription complète de l'entretien (verbatim ou reformulé).",
    },
    {
        "key":         "sell_02_plan_im",
        "num":         "2",
        "title":       "Plan de l'IM",
        "desc":        "Architecture détaillée de l'Information Memorandum — ~50 slides en 6 sections",
        "web_search":  False,
        "needs_input": True,
        "input_label": "Contexte de la société",
        "input_hint":  (
            "Activité, positionnement, KPIs clés, actionnariat, contexte de la cession.\n"
            "Ajoutez le rapport d'entretien (étape 1) si disponible."
        ),
    },
    {
        "key":         "sell_03_redaction_slides",
        "num":         "3",
        "title":       "Rédaction des slides",
        "desc":        "Contenu rédactionnel complet de chaque slide — standalone, orienté investisseur",
        "web_search":  False,
        "needs_input": True,
        "input_label": "Plan IM + slides à rédiger + données source",
        "input_hint":  (
            "Précisez les numéros et titres des slides à produire. "
            "Collez le plan IM (étape 2) et toutes les données disponibles."
        ),
    },
    {
        "key":         "sell_04_reformulation",
        "num":         "4",
        "title":       "Reformulation & sourcing",
        "desc":        "Amélioration et sourcing du contenu d'une slide existante — original / reformulé / justification",
        "web_search":  False,
        "needs_input": True,
        "input_label": "Slide à reformuler",
        "input_hint":  "Collez le contenu brut de la slide (texte, bullet points ou markdown).",
    },
]

BUY_SIDE_STEPS_BY_KEY  = {s["key"]: s for s in BUY_SIDE_STEPS}
SELL_SIDE_STEPS_BY_KEY = {s["key"]: s for s in SELL_SIDE_STEPS}

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
        "email_type":       "rachat",
        # Mission M&A
        "ma_universe":      "",   # "buy" or "sell"
        "ma_step_key":      "",   # current module key
        "ma_company":       "",
        "ma_sector":        "",   # secteur d'activité — contexte clé pour les recherches
        "ma_step_result":   {},   # dict: step_key -> result text
        "ma_running":       False,
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
            for k in ["screen", "company", "deliverable_type", "context", "result_text",
                      "current_step", "steps_done", "ma_universe", "ma_company",
                      "ma_step_key", "ma_running"]:
                if k == "screen":
                    st.session_state[k] = 1
                elif k in ("steps_done",):
                    st.session_state[k] = []
                elif k == "ma_step_result":
                    st.session_state[k] = {}
                else:
                    st.session_state[k] = ""
            st.session_state.ma_step_result = {}
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

    tab_standard, tab_mission = st.tabs(["🔍 Analyses rapides", "💼 Mission M&A"])

    # ── TAB 2 : Mission M&A ────────────────────────────────────────────────
    with tab_mission:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#1A2744 0%,#243352 100%);
                    border-radius:14px; padding:20px 24px; margin-bottom:20px;">
            <div style="color:#FFFFFF; font-size:1.1rem; font-weight:700; margin-bottom:6px;">
                Missions M&A professionnelles
            </div>
            <div style="color:#8FA8C8; font-size:0.85rem; line-height:1.6;">
                Flux guidé étape par étape. Chaque résultat alimente l'étape suivante.
                Choisissez votre type de mission ci-dessous.
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_buy, col_sell = st.columns(2)
        with col_buy:
            st.markdown("""
            <div style="background:#E8F5EE; border:2px solid #2E7D5540;
                        border-left:4px solid #2E7D55; border-radius:12px; padding:18px 20px;">
                <div style="font-size:1.5rem;">📈</div>
                <div style="font-weight:700; color:#1A2744; font-size:0.97rem; margin:8px 0 4px 0;">
                    Buy-side — Acquisition
                </div>
                <div style="font-size:0.79rem; color:#5A6A7A; line-height:1.5;">
                    Cartographie du marché, recherche et qualification de cibles, préparation des slides PPT.
                </div>
                <div style="font-size:0.76rem; color:#2E7D55; font-weight:600; margin-top:10px;">
                    9 modules · Recherche web incluse
                </div>
            </div>
            """, unsafe_allow_html=True)
            buy_company = st.text_input(
                "Nom de l'acquéreur",
                placeholder="Ex : Milliris, Acuitis...",
                key="buy_company_input",
            )
            if st.button("📈 Lancer la mission Buy-side", key="start_buy", use_container_width=True, type="primary"):
                if not buy_company.strip():
                    st.warning("⚠️ Entrez le nom de l'acquéreur.")
                elif not anthropic_key or not tavily_key:
                    st.error("🔑 Clés API manquantes.")
                else:
                    st.session_state.ma_universe    = "buy"
                    st.session_state.ma_company     = buy_company.strip()
                    st.session_state.ma_sector      = ""
                    st.session_state.ma_step_key    = BUY_SIDE_STEPS[0]["key"]
                    st.session_state.ma_step_result = {}
                    st.session_state.screen         = 4
                    st.rerun()

        with col_sell:
            st.markdown("""
            <div style="background:#F0EBF8; border:2px solid #7A5FA540;
                        border-left:4px solid #7A5FA5; border-radius:12px; padding:18px 20px;">
                <div style="font-size:1.5rem;">📋</div>
                <div style="font-weight:700; color:#1A2744; font-size:0.97rem; margin:8px 0 4px 0;">
                    Sell-side — Cession / IM
                </div>
                <div style="font-size:0.79rem; color:#5A6A7A; line-height:1.5;">
                    Rapport d'entretien, plan de l'Information Memorandum, rédaction et reformulation des slides.
                </div>
                <div style="font-size:0.76rem; color:#7A5FA5; font-weight:600; margin-top:10px;">
                    4 modules · Sans recherche web
                </div>
            </div>
            """, unsafe_allow_html=True)
            sell_company = st.text_input(
                "Nom de la société cédée",
                placeholder="Ex : Koki Software...",
                key="sell_company_input",
            )
            if st.button("📋 Lancer la mission Sell-side", key="start_sell", use_container_width=True, type="primary"):
                if not sell_company.strip():
                    st.warning("⚠️ Entrez le nom de la société.")
                elif not anthropic_key:
                    st.error("🔑 Clé API Anthropic manquante.")
                else:
                    st.session_state.ma_universe    = "sell"
                    st.session_state.ma_company     = sell_company.strip()
                    st.session_state.ma_sector      = ""
                    st.session_state.ma_step_key    = SELL_SIDE_STEPS[0]["key"]
                    st.session_state.ma_step_result = {}
                    st.session_state.screen         = 4
                    st.rerun()

    # ── TAB 1 : Analyses rapides ───────────────────────────────────────────
    with tab_standard:
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
        """Cherche les dirigeants via plusieurs sources puis extrait les noms avec Claude."""
        from tavily import TavilyClient
        import anthropic as _ant
        import json as _json
        import urllib.parse as _up

        tc = TavilyClient(api_key=tavily_key)
        all_content = []

        queries = [
            f'"{competitor}" gérant président directeur général site:pappers.fr',
            f'"{competitor}" dirigeants fondateur PDG CEO direction site:societe.com OR site:verif.com',
            f'"{competitor}" équipe direction dirigeants LinkedIn',
        ]
        for q in queries:
            try:
                res = tc.search(query=q, max_results=4, search_depth="advanced")
                for r in res.get("results", []):
                    snippet = f"[{r.get('url','')}]\n{r.get('title','')}\n{r.get('content','')}"
                    all_content.append(snippet)
            except Exception:
                pass

        if not all_content:
            return []

        # Claude extrait les dirigeants intelligemment depuis les sources brutes
        combined = "\n\n---\n\n".join(all_content[:8])[:4000]
        client = _ant.Anthropic(api_key=anthropic_key)
        try:
            resp = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=400,
                messages=[{"role": "user", "content":
                    f"""Extrais les noms et titres des dirigeants actuels de "{competitor}" depuis ces résultats.

{combined}

Règles :
- Uniquement des personnes en poste actuellement (pas d'anciens dirigeants)
- Titres acceptés : PDG, DG, Président, Directeur, Fondateur, Gérant, CEO, CFO, COO, VP, Associé, Partner
- Maximum 5 personnes
- Si vraiment aucun dirigeant identifiable, retourne []

Retourne UNIQUEMENT ce JSON (rien d'autre) :
[{{"name": "Prénom Nom", "title": "Titre"}}]"""}]
            )
            text = resp.content[0].text.strip()
            match = _re.search(r'\[.*?\]', text, _re.DOTALL)
            if match:
                raw = _json.loads(match.group())
                executives = []
                for e in raw:
                    n, t = e.get("name","").strip(), e.get("title","").strip()
                    if n and t and len(n) > 3:
                        executives.append({"name": n, "title": t})
                # Cherche l'URL directe du profil LinkedIn pour chaque dirigeant
                comp_lower = competitor.lower()
                for ex in executives[:5]:
                    profile_url = None
                    try:
                        li_res = tc.search(
                            query=f'"{ex["name"]}" "{competitor}" site:linkedin.com/in',
                            max_results=5,
                            search_depth="basic",
                        )
                        for r in li_res.get("results", []):
                            u = r.get("url", "")
                            if "linkedin.com/in/" not in u:
                                continue
                            # Vérifie que le snippet mentionne bien l'entreprise
                            snippet = (r.get("content", "") + r.get("title", "")).lower()
                            if comp_lower in snippet or ex["name"].split()[0].lower() in snippet:
                                profile_url = u.split("?")[0].rstrip("/")
                                break
                    except Exception:
                        pass
                    # Fallback : recherche LinkedIn avec nom + société (résultats filtrés)
                    if not profile_url:
                        kw = _up.quote(f"{ex['name']} {competitor}")
                        profile_url = f"https://www.linkedin.com/search/results/people/?keywords={kw}"
                    ex["url"] = profile_url
                return executives[:5]
        except Exception:
            pass
        return []

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

    EMAIL_TYPE_LABELS = {
        "rachat":   "Investisseur — Rachat",
        "levee":    "M&A — Levée de fonds",
        "buildup":  "Investisseur — Build-up",
    }

    EMAIL_TYPE_PROMPTS = {
        "rachat": """Tu es un investisseur ou un fonds qui envisage d'acquérir {competitor}.
Tu as fait tes recherches sur leur secteur et leur activité de façon indépendante — ne mentionne aucune autre société ni aucune source dans le message.
{context_block}
Rédige un message LinkedIn de premier contact, discret et professionnel.

CONTRAINTES ABSOLUES :
- Ne mentionne jamais le nom d'une autre entreprise, ni pourquoi tu les as repérés
- Objet (max 200 caractères) : sobre, sans les mots "rachat" ou "acquisition"
- Corps du message : 900 caractères MAXIMUM (LinkedIn InMail) — sois très concis
- Commence par "Bonjour [Prénom]," — laisse "[Prénom]" entre crochets, n'invente jamais un prénom
- Ligne 1 : qui tu es en une phrase (fonds/investisseur, secteur d'activité)
- Ligne 2 : 1 observation concrète sur {competitor} qui montre que tu les connais — sans citer de source
- Ligne 3 : proposer un échange de 20 min, confidentiel, sans engagement
- Ton : direct, humain, jamais corporatif — aucun jargon (pas de "synergies", "due diligence", "deal flow")
- Pas de mise en forme : pas de tirets, pas de gras, pas de listes
- Signature : "[Prénom Nom] — [Titre], [Fonds]"
- Entièrement en français""",

        "levee": """Tu es un conseiller M&A accompagnant des dirigeants dans des opérations de financement et de croissance.
Tu as identifié {competitor} comme une société à fort potentiel — de façon indépendante, sans mentionner aucune autre société ni source dans le message.
{context_block}
Rédige un message LinkedIn de premier contact, orienté opportunité de croissance.

CONTRAINTES ABSOLUES :
- Ne mentionne jamais le nom d'une autre entreprise, ni la démarche qui t'a conduit à les contacter
- Objet (max 200 caractères) : axé croissance, sans les mots "levée de fonds" ou "financement"
- Corps du message : 900 caractères MAXIMUM (LinkedIn InMail) — sois très concis
- Commence par "Bonjour [Prénom]," — laisse "[Prénom]" entre crochets, n'invente jamais un prénom
- Ligne 1 : qui tu es en une phrase (conseil M&A, réseau de fonds, secteur)
- Ligne 2 : 1 observation sur leur marché ou leur activité qui justifie l'intérêt — sans citer de source
- Ligne 3 : proposer un échange de 20 min pour voir si tu peux les aider à accélérer
- Ton : conseiller, pas vendeur — facilitateur qui apporte de la valeur
- Aucun anglicisme excessif, aucun jargon corporate
- Pas de mise en forme : pas de tirets, pas de gras, pas de listes
- Signature : "[Prénom Nom] — [Titre], [Cabinet]"
- Entièrement en français""",

        "buildup": """Tu es un investisseur actionnaire d'une société active dans le même secteur que {competitor}, avec une stratégie de consolidation — tu cherches des acteurs complémentaires pour construire un leader de marché.
Tu as identifié {competitor} de façon indépendante — ne mentionne aucune autre société ni aucune source dans le message.
{context_block}
Rédige un message LinkedIn de premier contact, entre pairs du même secteur.

CONTRAINTES ABSOLUES :
- Ne mentionne jamais le nom d'une autre société, ni la démarche qui t'a mené à les contacter
- Objet (max 200 caractères) : axé vision commune du marché, sans les mots "build-up", "rachat" ou "acquisition"
- Corps du message : 900 caractères MAXIMUM (LinkedIn InMail) — sois très concis
- Commence par "Bonjour [Prénom]," — laisse "[Prénom]" entre crochets, n'invente jamais un prénom
- Ligne 1 : qui tu es, ta société et son positionnement dans ce secteur (une phrase)
- Ligne 2 : 1 point de complémentarité ou de vision partagée avec {competitor} — sans citer de source
- Ligne 3 : proposer un échange informel de 20 min pour partager les perspectives du marché
- Ton : entrepreneur à entrepreneur, long terme, pas financier
- Zéro jargon : pas de "build-up", "synergies", "closing", "multiple", "plateforme"
- Pas de mise en forme : pas de tirets, pas de gras, pas de listes
- Signature : "[Prénom Nom] — [Titre], [Société]"
- Entièrement en français""",
    }

    def generate_contact_email(competitor: str, main_company: str, comp_context: str = "", email_type: str = "rachat") -> str:
        client = _anthropic.Anthropic(api_key=anthropic_key)

        context_block = ""
        if comp_context:
            context_block = (
                f"\nVoici ce que tu sais sur {competitor} (utilise 1 ou 2 éléments concrets) :\n"
                f"---\n{comp_context}\n---\n"
            )

        prompt_template = EMAIL_TYPE_PROMPTS.get(email_type, EMAIL_TYPE_PROMPTS["rachat"])
        prompt = prompt_template.format(
            competitor=competitor,
            main_company=main_company,
            context_block=context_block,
        )

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=700,
            messages=[{"role": "user", "content":
                f"{prompt}\n\nRetourne uniquement l'email, format exact :\nObjet : [objet]\n\n[corps]"}]
        )
        return response.content[0].text

    import urllib.parse as _urlparse

    li_svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" '
              'viewBox="0 0 24 24" fill="#0A66C2"><path d="M20.447 20.452h-3.554v-5.569'
              'c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351'
              'V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 '
              '5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 '
              '2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 '
              '.774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 '
              '22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>')

    # ══════════════════════════════════════════════════════════════════════
    # BENCHMARK : email de prise de contact par concurrent
    # ══════════════════════════════════════════════════════════════════════
    if deliv_key == "benchmark":

        # Détection stricte des concurrents (patterns benchmark uniquement)
        detected = _re.findall(r'###\s+Concurrent[^—\n]*—\s*\**([^\n*]+)', result)
        detected += _re.findall(r'###\s+\d+[^\S\n]*[—–-][^\S\n]*\**([^\n*]+)', result)
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
                Préparer une prise de contact
            </div>
            <div style="color:#8FA8C8; font-size:0.83rem;">
                Choisissez le type d'approche, puis cliquez sur un concurrent pour générer le message LinkedIn.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Sélecteur type d'email
        _etype_current = st.session_state.get("email_type", "rachat")
        _etype_options = [
            ("rachat",  "Investisseur — Rachat"),
            ("levee",   "M&A — Levée de fonds"),
            ("buildup", "Investisseur — Build-up"),
        ]
        _etype_cols = st.columns(3)
        for _ec, (_ek, _el) in zip(_etype_cols, _etype_options):
            _css_class = "etype-btn-selected" if _etype_current == _ek else "etype-btn-idle"
            _ec.markdown(f'<div class="{_css_class}">', unsafe_allow_html=True)
            with _ec:
                if st.button(_el, key=f"etype_{_ek}", use_container_width=True):
                    st.session_state.email_type = _ek
                    st.rerun()
            _ec.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)

        if detected:
            cols_per_row = 3
            rows = [detected[i:i+cols_per_row] for i in range(0, len(detected), cols_per_row)]
            for row in rows:
                cols = st.columns(len(row))
                for col, comp in zip(cols, row):
                    with col:
                        if st.button(f"✉️ {comp}", key=f"email_btn_{comp}", use_container_width=True):
                            st.session_state.email_target     = comp
                            st.session_state.generated_email  = ""
                            st.session_state.found_executives = []
                            with st.spinner("Rédaction du message et recherche des dirigeants..."):
                                ctx = _extract_competitor_context(comp, result)
                                st.session_state.generated_email  = generate_contact_email(comp, company, ctx, email_type=st.session_state.email_type)
                                st.session_state.found_executives = find_executives(comp)
        else:
            manual_comp = st.text_input("Nom du concurrent à contacter :",
                                         placeholder="ex : Entreprise XYZ",
                                         key="manual_email_target")
            if manual_comp and st.button("✉️ Générer le message", type="primary"):
                st.session_state.email_target     = manual_comp
                st.session_state.generated_email  = ""
                st.session_state.found_executives = []
                with st.spinner("Rédaction du message et recherche des dirigeants..."):
                    ctx = _extract_competitor_context(manual_comp, result)
                    st.session_state.generated_email  = generate_contact_email(manual_comp, company, ctx, email_type=st.session_state.email_type)
                    st.session_state.found_executives = find_executives(manual_comp)

        # Afficher le message généré
        if st.session_state.generated_email:
            raw = st.session_state.generated_email.strip()
            lines = raw.split("\n")
            subject_line, body_lines, in_body = "", [], False
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

            with st.expander("📋 Copier le texte brut"):
                st.text_area("", value=raw, height=220, label_visibility="collapsed", key="email_copy_area")

            li_company = f"https://www.linkedin.com/search/results/companies/?keywords={_urlparse.quote(st.session_state.email_target)}"
            st.markdown(
                f'<div style="margin-top:10px;">'
                f'<a href="{li_company}" target="_blank" style="display:inline-flex;align-items:center;'
                f'gap:6px;background:#FFFFFF;border:1px solid #C8D4DC;border-radius:8px;'
                f'padding:7px 14px;font-size:0.83rem;font-weight:600;color:#0A66C2;text-decoration:none;">'
                f'{li_svg} Voir la page entreprise</a></div>',
                unsafe_allow_html=True,
            )

            execs = st.session_state.get("found_executives", [])
            if execs:
                st.markdown(
                    '<div style="font-size:0.82rem;font-weight:600;color:#64748B;'
                    'text-transform:uppercase;letter-spacing:0.05em;margin:18px 0 10px 0;">'
                    'Dirigeants identifiés'
                    '<span style="font-size:0.72rem;font-weight:400;color:#94A3B8;'
                    'text-transform:none;margin-left:6px;">(Pappers / Infogreffe)</span></div>',
                    unsafe_allow_html=True,
                )
                cols = st.columns(min(len(execs), 3))
                for idx, exec_ in enumerate(execs):
                    with cols[idx % 3]:
                        st.markdown(
                            f'<a href="{exec_["url"]}" target="_blank" style="text-decoration:none;">'
                            f'<div style="background:#FFFFFF;border:1px solid #C8D4DC;border-radius:10px;'
                            f'padding:12px 14px;">'
                            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
                            f'{li_svg}'
                            f'<span style="font-size:0.88rem;font-weight:700;color:#1A2744;">{exec_["name"]}</span>'
                            f'</div>'
                            f'<div style="font-size:0.78rem;color:#64748B;">{exec_["title"] or "Dirigeant"}</div>'
                            f'<div style="font-size:0.75rem;color:#0A66C2;margin-top:6px;font-weight:600;">Voir le profil →</div>'
                            f'</div></a>',
                            unsafe_allow_html=True,
                        )
            else:
                st.markdown(
                    '<div style="font-size:0.8rem;color:#94A3B8;margin-top:12px;font-style:italic;">'
                    'Aucun profil dirigeant trouvé — utilisez la page entreprise LinkedIn.</div>',
                    unsafe_allow_html=True,
                )

    # ══════════════════════════════════════════════════════════════════════
    # AUTRES LIVRABLES : liens LinkedIn pertinents extraits du rapport
    # ══════════════════════════════════════════════════════════════════════
    else:
        import anthropic as _ant
        import json as _json

        def extract_linkedin_entities(report: str, deliv_type: str, main_co: str) -> list:
            """Extrait via Claude Haiku les entités les plus pertinentes du rapport."""
            instructions = {
                "fiche": (
                    "Ce rapport est une fiche entreprise. "
                    "Retourne la société principale et ses filiales ou partenaires clés mentionnés."
                ),
                "manda": (
                    "Ce rapport contient des actualités M&A. "
                    "Extrais les acquéreurs actifs, fonds d'investissement et fédérations professionnelles mentionnés."
                ),
                "geo": (
                    "Ce rapport est une analyse géographique. "
                    "Extrais les entreprises et acteurs locaux les plus importants mentionnés par zone."
                ),
            }
            instruction = instructions.get(deliv_type, "Extrais les principales organisations mentionnées.")
            client = _ant.Anthropic(api_key=anthropic_key)
            try:
                resp = client.messages.create(
                    model="claude-haiku-4-5",
                    max_tokens=350,
                    messages=[{"role": "user", "content":
                        f"""{instruction}

{report[:3500]}

Règles :
- Maximum 6 entités, pertinentes pour une prise de contact professionnelle
- Exclure "{main_co}" lui-même
- Retourne UNIQUEMENT ce JSON :
[{{"name": "Nom exact", "type": "Acquéreur / Fonds / Fédération / Entreprise"}}]"""}]
                )
                text = resp.content[0].text.strip()
                match = _re.search(r'\[.*?\]', text, _re.DOTALL)
                if match:
                    raw = _json.loads(match.group())
                    entities = []
                    for e in raw:
                        n = e.get("name", "").strip()
                        t = e.get("type", "").strip()
                        if n and len(n) > 2:
                            li_url = f"https://www.linkedin.com/search/results/companies/?keywords={_urlparse.quote(n)}"
                            entities.append({"name": n, "type": t, "url": li_url})
                    return entities[:6]
            except Exception:
                pass
            return []

        st.markdown("""
        <div style="background:linear-gradient(135deg,#1A2744 0%,#2D4A7A 100%);
                    border-radius:14px; padding:20px 24px; margin-bottom:20px;">
            <div style="color:#FFFFFF; font-size:1.05rem; font-weight:700; margin-bottom:4px;">
                Liens LinkedIn pertinents
            </div>
            <div style="color:#8FA8C8; font-size:0.83rem;">
                Acteurs clés identifiés dans ce rapport — cliquez pour accéder directement à leur page.
            </div>
        </div>
        """, unsafe_allow_html=True)

        li_key = f"li_entities_{deliv_key}_{company}"
        if li_key not in st.session_state:
            with st.spinner("Identification des contacts LinkedIn pertinents..."):
                st.session_state[li_key] = extract_linkedin_entities(result, deliv_key, company)

        entities = st.session_state.get(li_key, [])
        if entities:
            cols_per_row = 3
            rows = [entities[i:i+cols_per_row] for i in range(0, len(entities), cols_per_row)]
            for row in rows:
                cols = st.columns(len(row))
                for col, ent in zip(cols, row):
                    with col:
                        st.markdown(
                            f'<a href="{ent["url"]}" target="_blank" style="text-decoration:none;">'
                            f'<div style="background:#FFFFFF;border:1px solid #C8D4DC;border-radius:10px;'
                            f'padding:14px 16px;margin-bottom:8px;">'
                            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
                            f'{li_svg}'
                            f'<span style="font-size:0.88rem;font-weight:700;color:#1A2744;">{ent["name"]}</span>'
                            f'</div>'
                            f'<div style="font-size:0.75rem;color:#64748B;">{ent["type"]}</div>'
                            f'<div style="font-size:0.75rem;color:#0A66C2;margin-top:6px;font-weight:600;">Voir sur LinkedIn →</div>'
                            f'</div></a>',
                            unsafe_allow_html=True,
                        )
        else:
            st.markdown(
                '<div style="font-size:0.83rem;color:#94A3B8;font-style:italic;">'
                'Aucune entité identifiée dans ce rapport.</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # New analysis button
    if st.button("🔍 Nouvelle analyse", type="primary"):
        for k in ["screen", "company", "deliverable_type", "context", "result_text",
                  "current_step", "steps_done", "email_target", "generated_email",
                  "found_executives", "email_type"]:
            if k == "screen":
                st.session_state[k] = 1
            elif k in ("steps_done", "found_executives"):
                st.session_state[k] = []
            elif k == "email_type":
                st.session_state[k] = "rachat"
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


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 4 — MISSION M&A (wizard étape par étape)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.screen == 4:
    from ma_agent import run_ma_module
    import re as _re4

    universe   = st.session_state.ma_universe
    ma_company = st.session_state.ma_company
    ma_sector  = st.session_state.get("ma_sector", "")
    step_key   = st.session_state.ma_step_key
    results    = st.session_state.ma_step_result

    steps_list = BUY_SIDE_STEPS if universe == "buy" else SELL_SIDE_STEPS
    steps_by_k = BUY_SIDE_STEPS_BY_KEY if universe == "buy" else SELL_SIDE_STEPS_BY_KEY
    step_keys  = [s["key"] for s in steps_list]
    step_info  = steps_by_k.get(step_key, steps_list[0])
    step_idx   = step_keys.index(step_key) if step_key in step_keys else 0

    uni_color    = "#2E7D55" if universe == "buy" else "#7A5FA5"
    uni_bg       = "#E8F5EE" if universe == "buy" else "#F0EBF8"
    uni_label    = "Buy-side — Acquisition" if universe == "buy" else "Sell-side — Cession / IM"
    uni_icon     = "📈" if universe == "buy" else "📋"
    n_total      = len(steps_list)
    n_done       = sum(1 for k in step_keys if k in results)
    already_done = step_key in results

    # ── Animations CSS ────────────────────────────────────────────────────────
    st.markdown("""
<style>
@keyframes blink  { 0%,100%{opacity:1}  50%{opacity:0}   }
@keyframes popIn  { 0%{transform:scale(.85);opacity:0} 70%{transform:scale(1.04)} 100%{transform:scale(1);opacity:1} }
.ticker-pill  { animation: popIn 0.25s ease both; }
.insight-card { animation: popIn 0.35s ease both; }
.done-banner  { animation: popIn 0.4s ease both;  }
</style>
""", unsafe_allow_html=True)

    # ── Header mission ────────────────────────────────────────────────────────
    hc1, hc2 = st.columns([5, 1])
    with hc1:
        pct = int(n_done / n_total * 100)
        st.markdown(
            f"""<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
  <span style="font-size:1.5rem;">{uni_icon}</span>
  <div>
    <div style="font-size:1.05rem;font-weight:800;color:#1A2744;letter-spacing:-0.3px;">
      Mission {uni_label} &nbsp;·&nbsp; <span style="color:{uni_color};">{ma_company}</span>
    </div>
    <div style="font-size:0.76rem;color:#94A3B8;margin-top:2px;">
      {n_done}/{n_total} étapes complétées{"&nbsp;·&nbsp;✅ Mission terminée !" if n_done == n_total else ""}
    </div>
  </div>
</div>
<div style="background:#E2E8F0;border-radius:99px;height:5px;overflow:hidden;margin-bottom:2px;">
  <div style="background:linear-gradient(90deg,{uni_color},{uni_color}66);width:{pct}%;height:100%;
              border-radius:99px;transition:width .5s ease;"></div>
</div>""",
            unsafe_allow_html=True,
        )
    with hc2:
        if st.button("✕ Quitter", use_container_width=True):
            st.session_state.screen = 1
            st.rerun()

    # ── Pastilles d'étapes (cliquables si faites) ─────────────────────────────
    step_cols = st.columns(n_total)
    for col, s in zip(step_cols, steps_list):
        is_done    = s["key"] in results
        is_current = s["key"] == step_key
        with col:
            if is_done or is_current:
                lbl = ("✅ " if is_done else "▶ ") + s["num"]
                if st.button(lbl, key=f"snav_{s['key']}", use_container_width=True, help=s["title"]):
                    st.session_state.ma_step_key = s["key"]
                    st.rerun()
            else:
                st.markdown(
                    f'<div style="text-align:center;background:#F1F5F9;border:1.5px solid #DDE4EA;'
                    f'border-radius:8px;padding:6px 2px;color:#CBD5E1;font-size:0.78rem;font-weight:700;">'
                    f'{s["num"]}</div>',
                    unsafe_allow_html=True,
                )

    # Barre de progression fine
    st.markdown(
        f'<div style="background:#DDD5C8;border-radius:4px;height:3px;margin:12px 0 20px 0;overflow:hidden;">'
        f'<div style="background:{uni_color};width:{pct}%;height:100%;border-radius:4px;transition:width .4s;"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Carte étape courante ──────────────────────────────────────────────────
    web_badge = (
        '<span style="background:#EAF5EE;border:1px solid #A8D5B8;color:#2E6B45;'
        'font-size:0.72rem;font-weight:700;padding:3px 10px;border-radius:20px;">'
        '🌐 Recherche web · Sonnet</span>'
        if step_info.get("web_search") else
        '<span style="background:#EEF2F6;border:1px solid #CBD5E1;color:#64748B;'
        'font-size:0.72rem;font-weight:700;padding:3px 10px;border-radius:20px;">'
        '⚡ Rapide · Haiku</span>'
    )
    st.markdown(
        f'<div style="background:#FDFAF5;border-left:4px solid {uni_color};border-radius:0 12px 12px 0;'
        f'padding:18px 22px;margin-bottom:18px;box-shadow:0 2px 10px rgba(26,39,68,0.06);">'
        f'<div style="font-size:0.7rem;font-weight:700;color:{uni_color};text-transform:uppercase;'
        f'letter-spacing:0.09em;margin-bottom:5px;">Étape {step_info["num"]} / {n_total}</div>'
        f'<div style="font-size:1.15rem;font-weight:800;color:#1A2744;margin-bottom:4px;">'
        f'{step_info["title"]}</div>'
        f'<div style="font-size:0.84rem;color:#6B7A8D;margin-bottom:10px;">{step_info["desc"]}</div>'
        f'{web_badge}</div>',
        unsafe_allow_html=True,
    )

    # ── ÉTAT A : résultat déjà disponible ────────────────────────────────────
    if already_done:
        res_text = results[step_key]
        n_rows   = len(_re4.findall(r'^\|[^-\|]', res_text, _re4.MULTILINE))
        n_heads  = len(_re4.findall(r'^#{1,3} ', res_text, _re4.MULTILINE))
        n_src    = len(_re4.findall(r'https?://', res_text))
        m1 = f"{n_rows} lignes" if n_rows > 1 else f"{n_heads} sections" if n_heads else f"{len(res_text.split())} mots"
        m2 = f"{n_src} sources" if n_src else "Structuré"

        # Cartes de métriques
        st.markdown(
            f'<div style="display:flex;gap:10px;margin-bottom:18px;">'
            f'<div class="insight-card" style="flex:1;background:#E8F5EE;border:1px solid #A8D5B8;'
            f'border-radius:10px;padding:12px;text-align:center;">'
            f'<div style="font-size:1.25rem;font-weight:800;color:#1B5E3B;">{m1}</div>'
            f'<div style="font-size:0.7rem;color:#2E7D55;font-weight:600;margin-top:2px;">Résultat</div></div>'
            f'<div class="insight-card" style="flex:1;background:#E8F1F8;border:1px solid #B8D0E4;'
            f'border-radius:10px;padding:12px;text-align:center;animation-delay:.07s;">'
            f'<div style="font-size:1.25rem;font-weight:800;color:#2D5A7A;">{m2}</div>'
            f'<div style="font-size:0.7rem;color:#4A7FA5;font-weight:600;margin-top:2px;">Qualité</div></div>'
            f'<div class="insight-card" style="flex:1;background:#F0EBF8;border:1px solid #C4B0D8;'
            f'border-radius:10px;padding:12px;text-align:center;animation-delay:.14s;">'
            f'<div style="font-size:1.25rem;font-weight:800;color:#5A3F8A;">✅ OK</div>'
            f'<div style="font-size:0.7rem;color:#7A5FA5;font-weight:600;margin-top:2px;">Export dispo</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        with st.expander("📄 Voir le résultat complet", expanded=False):
            st.markdown(res_text)
            try:
                from word_generator import generate_word
                fname = f"{ma_company}_{step_info['num']}_{step_info['title'].replace(' ', '_')}.docx"
                st.download_button(
                    "📝 Télécharger en Word",
                    data=generate_word(res_text, ma_company, "fiche"),
                    file_name=fname,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            except Exception:
                pass

        if st.button("🔄 Relancer cette étape", key=f"rerun_{step_key}"):
            new_r = {k: v for k, v in results.items() if k != step_key}
            st.session_state.ma_step_result = new_r
            st.rerun()

        # Navigation
        st.markdown("---")
        nav1, _, nav3 = st.columns([1, 2, 1])
        with nav1:
            if step_idx > 0:
                ps = steps_list[step_idx - 1]
                if st.button(f"← {ps['num']}. {ps['title']}", key=f"prev_{step_key}", use_container_width=True):
                    st.session_state.ma_step_key = ps["key"]
                    st.rerun()
        with nav3:
            if step_idx < n_total - 1:
                ns = steps_list[step_idx + 1]
                if st.button(f"Étape suivante : {ns['title']} →", key=f"next_{step_key}",
                             type="primary", use_container_width=True):
                    nk = f"ma_input_{ns['key']}"
                    if ns.get("needs_input"):
                        st.session_state[nk] = results.get(step_key, "")[:4000]
                    st.session_state.ma_step_key = ns["key"]
                    st.rerun()
            else:
                st.success("🎉 Mission complète — toutes les étapes sont terminées.")

    # ── ÉTAT B : étape à lancer ───────────────────────────────────────────────
    else:
        input_key  = f"ma_input_{step_key}"
        step_input = ""

        if step_info.get("needs_input"):
            if input_key not in st.session_state and step_idx > 0:
                pk = step_keys[step_idx - 1]
                if pk in results:
                    st.session_state[input_key] = results[pk][:4000]

            step_input = st.text_area(
                step_info["input_label"],
                value=st.session_state.get(input_key, ""),
                placeholder=step_info["input_hint"],
                height=190,
                key=f"ta_{step_key}",
            )
            st.session_state[input_key] = step_input

            up_files = st.file_uploader(
                "Joindre un document (optionnel)",
                type=["pdf", "docx", "txt", "md", "xlsx"],
                accept_multiple_files=True,
                key=f"up_{step_key}",
            )
            if up_files:
                from document_extractor import extract_text
                for uf in up_files[:3]:
                    step_input += f"\n\n--- {uf.name} ---\n{extract_text(uf)}"

        run_label = "🔍 Lancer la recherche" if step_info.get("web_search") else "⚡ Lancer l'analyse"
        launch = st.button(run_label, key=f"run_{step_key}", type="primary", use_container_width=True)

        if launch:
            # ── Feedback immédiat dès le clic ────────────────────────────────
            status_ph = st.empty()
            status_ph.markdown(
                f'<div style="background:#1A2744;color:#C8D6E8;border-radius:10px;'
                f'padding:14px 20px;font-size:0.88rem;font-weight:600;margin-bottom:10px;">'
                f'⏳ &nbsp; Étape {step_info["num"]} — {step_info["title"]} en cours...'
                f'<span style="font-size:0.78rem;font-weight:400;opacity:.7;margin-left:8px;">'
                f'({"30–90 sec, recherches web" if step_info.get("web_search") else "10–30 sec"})</span></div>',
                unsafe_allow_html=True,
            )

            os.environ["ANTHROPIC_API_KEY"] = anthropic_key
            os.environ["TAVILY_API_KEY"]    = tavily_key

            output_ph = st.empty()
            queries   = []

            def _on_tool(name, inp):
                q = (inp.get("query", inp.get("q", ""))[:75] if isinstance(inp, dict) else str(inp)[:75])
                if q:
                    queries.append(q)

            def _on_text(text):
                cursor = (f'<span style="display:inline-block;width:2px;height:13px;'
                          f'background:{uni_color};margin-left:2px;vertical-align:middle;'
                          f'animation:blink 1s step-end infinite;"></span>')
                output_ph.markdown(
                    f'<div style="background:#FFFFFF;border:1px solid #DDD5C8;border-radius:10px;'
                    f'padding:20px 24px;max-height:340px;overflow-y:auto;'
                    f'font-size:0.87rem;line-height:1.8;color:#1A202C;">'
                    + text[:5000].replace("\n", "<br>")
                    + cursor + '</div>',
                    unsafe_allow_html=True,
                )

            try:
                with st.spinner(f"Étape {step_info['num']} — {step_info['title']}…"):
                    result = run_ma_module(
                        module_key=step_key,
                        company=ma_company,
                        sector=ma_sector,
                        input_data=step_input,
                        on_text=_on_text,
                        on_tool_use=_on_tool,
                    )

                new_results = dict(results)
                new_results[step_key] = result
                st.session_state.ma_step_result = new_results

                status_ph.empty()
                output_ph.empty()

                # Banner de succès
                n_rows  = len(_re4.findall(r'^\|[^-\|]', result, _re4.MULTILINE))
                n_heads = len(_re4.findall(r'^#{1,3} ', result, _re4.MULTILINE))
                m1 = f"{n_rows} lignes" if n_rows > 1 else f"{n_heads} sections" if n_heads else f"{len(result.split())} mots"
                src_count = f" · {len(queries)} sources" if queries else ""

                st.markdown(
                    f'<div class="done-banner" style="background:linear-gradient(135deg,{uni_color} 0%,{uni_color}99 100%);'
                    f'border-radius:14px;padding:18px 24px;margin:12px 0;color:#FFFFFF;'
                    f'display:flex;align-items:center;gap:16px;">'
                    f'<div style="font-size:2rem;">✅</div>'
                    f'<div><div style="font-weight:800;font-size:1.05rem;">Étape {step_info["num"]} terminée</div>'
                    f'<div style="opacity:.85;font-size:0.82rem;margin-top:2px;">'
                    f'{step_info["title"]} · {m1}{src_count}</div></div></div>',
                    unsafe_allow_html=True,
                )

                with st.expander("📄 Voir le résultat", expanded=True):
                    st.markdown(result)
                    try:
                        from word_generator import generate_word
                        fname = f"{ma_company}_{step_info['num']}_{step_info['title'].replace(' ', '_')}.docx"
                        st.download_button(
                            "📝 Télécharger en Word",
                            data=generate_word(result, ma_company, "fiche"),
                            file_name=fname,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        )
                    except Exception:
                        pass

                if step_idx < n_total - 1:
                    ns = steps_list[step_idx + 1]
                    st.markdown('<div style="margin-top:14px;"></div>', unsafe_allow_html=True)
                    if st.button(
                        f"Passer à l'étape {ns['num']} — {ns['title']} →",
                        key=f"next_after_run_{step_key}",
                        type="primary",
                        use_container_width=True,
                    ):
                        nk = f"ma_input_{ns['key']}"
                        if ns.get("needs_input"):
                            st.session_state[nk] = result[:4000]
                        st.session_state.ma_step_key = ns["key"]
                        st.rerun()
                else:
                    st.balloons()
                    st.success("🎉 Mission complète — toutes les étapes sont terminées !")

            except Exception as e:
                import traceback
                status_ph.empty()
                output_ph.empty()
                st.error(f"❌ Erreur étape {step_info['num']} : {e}")
                with st.expander("🔍 Détail technique", expanded=False):
                    st.code(traceback.format_exc())

        elif step_idx > 0:
            st.markdown("---")
            ps = steps_list[step_idx - 1]
            if st.button(f"← {ps['num']}. {ps['title']}", key=f"prev_{step_key}"):
                st.session_state.ma_step_key = ps["key"]
                st.rerun()
