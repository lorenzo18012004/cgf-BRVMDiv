"""
# faire un truc multi factorielle pour ajuster les poids quand ya les dividendes par exmeple etc 
# si un titre monte trop dans l'indice faut etre capable de s'adapter.
# 
# 
# CGF ETF Dividende BRVM Dashboard — ETF Dividende BRVM
"""
import json, os, re, sys, subprocess, base64, requests
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="CGF ETF Dividende BRVM Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inter:wght@300;400;500;600&display=swap');
*, *::before, *::after { box-sizing: border-box; }

:root {
    /* ── Palette Private Banking ── */
    --c-bg:       #f7f5f0;          /* parchemin chaud */
    --c-white:    #ffffff;
    --c-navy:     #0c1a2e;          /* marine profond */
    --c-navy2:    #14263d;
    --c-gold:     #b8973f;          /* or mat */
    --c-gold-lt:  #d4b96a;          /* or clair */
    --c-gold-bg:  rgba(184,151,63,0.08);
    --c-text:     #0c1a2e;
    --c-text2:    #3d4f63;
    --c-muted:    #7d8fa3;
    --c-border:   #e0dbd2;          /* bord chaud */
    --c-border2:  #ccc5b9;
    --c-pos:      #2d7a4f;          /* vert discret */
    --c-neg:      #c0392b;          /* rouge discret */
    --shadow-xs:  0 1px 3px rgba(12,26,46,0.06);
    --shadow-sm:  0 2px 8px rgba(12,26,46,0.08), 0 1px 3px rgba(12,26,46,0.05);
    --shadow-md:  0 8px 32px rgba(12,26,46,0.10), 0 2px 8px rgba(12,26,46,0.06);
    --shadow-gold: 0 4px 20px rgba(184,151,63,0.18);
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', -apple-system, system-ui, sans-serif !important;
    background: var(--c-bg) !important;
    color: var(--c-text) !important;
}
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
header[data-testid="stHeader"] { display: none !important; height: 0 !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
#MainMenu, footer { visibility: hidden !important; }

.block-container {
    padding: 0 3rem 4rem 3rem !important;
    max-width: 100% !important;
}

/* ══ Navbar — marine profond, sobriété Maison de Gestion ══════════════ */
.cgf-navbar {
    background: var(--c-navy);
    padding: 0 3rem;
    height: 60px;
    display: flex;
    align-items: center;
    gap: 24px;
    margin: 0 -3rem 2.5rem -3rem;
    border-bottom: 1px solid rgba(184,151,63,0.25);
}
.cgf-logo {
    font-family: 'Inter', sans-serif;
    font-size: 0.62rem; font-weight: 700;
    color: var(--c-gold-lt);
    text-transform: uppercase; letter-spacing: 0.22em;
    border: 1px solid rgba(184,151,63,0.45);
    padding: 5px 13px; border-radius: 3px;
    flex-shrink: 0;
}
.cgf-nav-dot { display: none; }
.cgf-nav-brand {
    font-size: 0.76rem; font-weight: 400; color: rgba(255,255,255,0.5);
    letter-spacing: 0.04em; flex-shrink: 0;
}
.cgf-nav-sep { color: rgba(255,255,255,0.15); padding: 0 6px; font-size: 0.8rem; }
.cgf-nav-page { font-size: 0.76rem; font-weight: 400; color: rgba(255,255,255,0.38); }
.cgf-nav-page-active {
    font-size: 0.76rem; font-weight: 500;
    color: var(--c-gold-lt);
    letter-spacing: 0.02em;
}
.cgf-nav-spacer { flex: 1; }
.cgf-nav-badge {
    font-size: 0.58rem; font-weight: 500; color: var(--c-gold);
    text-transform: uppercase; letter-spacing: 0.1em;
    border: 1px solid rgba(184,151,63,0.3);
    padding: 3px 10px; border-radius: 2px;
}

/* ══ Landing ══════════════════════════════════════════════════════════ */
.landing-outer {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; min-height: 76vh; gap: 8px; text-align: center;
}
.landing-brand {
    font-family: 'Inter', sans-serif;
    font-size: 0.58rem; font-weight: 600; color: var(--c-gold);
    text-transform: uppercase; letter-spacing: 0.28em; margin: 0;
}
.landing-title {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 4rem; font-weight: 500; font-style: italic;
    color: var(--c-navy); letter-spacing: -0.01em;
    margin: 10px 0 6px 0; line-height: 1.1;
}
.landing-sub {
    font-size: 0.8rem; font-weight: 400; color: var(--c-muted);
    letter-spacing: 0.06em; text-transform: uppercase;
    margin: 0 0 52px 0; max-width: 380px;
}
.landing-cards { display: flex; gap: 20px; flex-wrap: wrap; justify-content: center; }
.lcard {
    display: flex; flex-direction: column; gap: 14px;
    width: 268px; padding: 32px 28px 26px 28px;
    border: 1px solid var(--c-border);
    text-decoration: none !important; color: inherit;
    background: var(--c-white);
    box-shadow: var(--shadow-sm);
    text-align: left;
    transition: border-color 0.25s, box-shadow 0.25s, transform 0.2s;
    position: relative; overflow: hidden;
    border-radius: 2px;
}
.lcard::after {
    content: ''; position: absolute;
    bottom: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--c-gold) 0%, var(--c-gold-lt) 100%);
    transform: scaleX(0); transform-origin: left;
    transition: transform 0.3s ease;
}
.lcard:hover {
    border-color: var(--c-border2);
    box-shadow: var(--shadow-gold);
    transform: translateY(-5px);
    text-decoration: none !important;
}
.lcard:hover::after { transform: scaleX(1); }
.lcard-tag {
    font-size: 0.54rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.18em; color: var(--c-gold);
    display: inline-block; width: fit-content;
}
.lcard-tag-bt { color: var(--c-muted); }
.lcard-tag-lv { color: var(--c-gold); }
.lcard-name {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 1.8rem; font-weight: 500; font-style: italic;
    color: var(--c-navy); letter-spacing: 0;
}
.lcard-desc { font-size: 0.73rem; color: var(--c-text2); line-height: 1.7; flex: 1; }
.lcard-arrow { font-size: 0.9rem; color: var(--c-border2); transition: color 0.2s, transform 0.2s; display: inline-block; }
.lcard:hover .lcard-arrow { color: var(--c-gold); transform: translateX(6px); }

/* ══ Section headers ══════════════════════════════════════════════════ */
.cgf-section {
    font-family: 'Inter', sans-serif;
    font-size: 0.57rem; font-weight: 600; color: var(--c-muted);
    text-transform: uppercase; letter-spacing: 0.18em;
    margin: 36px 0 18px 0; padding-bottom: 10px;
    border-bottom: 1px solid var(--c-border);
    position: relative;
}
.cgf-section::after {
    content: ''; position: absolute;
    bottom: -1px; left: 0;
    width: 32px; height: 1px;
    background: var(--c-gold);
}
.cgf-pos { color: var(--c-pos) !important; font-weight: 600; }
.cgf-neg { color: var(--c-neg) !important; font-weight: 600; }

/* ══ Metric cards ═════════════════════════════════════════════════════ */
[data-testid="stMetric"],
[data-testid="metric-container"] {
    background: var(--c-white) !important;
    border: 1px solid var(--c-border) !important;
    border-radius: 2px !important;
    padding: 22px 22px 18px 22px !important;
    box-shadow: var(--shadow-xs) !important;
    transition: box-shadow 0.2s, border-color 0.2s !important;
    position: relative !important; overflow: hidden !important;
}
[data-testid="stMetric"]::before,
[data-testid="metric-container"]::before {
    content: ''; position: absolute;
    left: 0; top: 0; bottom: 0; width: 2px;
    background: var(--c-gold); opacity: 0;
    transition: opacity 0.2s;
}
[data-testid="stMetric"]:hover::before,
[data-testid="metric-container"]:hover::before { opacity: 1 !important; }
[data-testid="stMetric"]:hover,
[data-testid="metric-container"]:hover {
    border-color: var(--c-border2) !important;
    box-shadow: var(--shadow-sm) !important;
}
[data-testid="stMetricValue"],
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-family: 'Cormorant Garamond', Georgia, serif !important;
    font-size: 2rem !important; font-weight: 500 !important;
    color: var(--c-navy) !important;
    letter-spacing: -0.01em !important; line-height: 1.1 !important;
}
[data-testid="stMetricLabel"],
[data-testid="stMetric"] [data-testid="stMetricLabel"] {
    font-size: 0.56rem !important; font-weight: 600 !important; color: var(--c-muted) !important;
    text-transform: uppercase !important; letter-spacing: 0.16em !important;
}
[data-testid="stMetricDelta"],
[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-size: 0.76rem !important; font-weight: 400 !important;
}

/* ══ Boutons ══════════════════════════════════════════════════════════ */
.stButton > button {
    font-family: 'Inter', system-ui, sans-serif !important;
    font-weight: 500 !important; font-size: 0.76rem !important;
    letter-spacing: 0.06em !important; text-transform: uppercase !important;
    border-radius: 2px !important; padding: 9px 22px !important;
    background: var(--c-navy) !important; color: var(--c-gold-lt) !important;
    border: 1px solid rgba(184,151,63,0.3) !important;
    box-shadow: var(--shadow-xs) !important;
    transition: background 0.2s, border-color 0.2s, box-shadow 0.2s !important;
}
.stButton > button:hover {
    background: var(--c-navy2) !important;
    border-color: var(--c-gold) !important;
    box-shadow: var(--shadow-gold) !important;
}

/* ══ Chart containers ═════════════════════════════════════════════════ */
[data-testid="stPlotlyChart"] {
    background: var(--c-white) !important;
    border: 1px solid var(--c-border) !important;
    border-radius: 2px !important;
    overflow: hidden !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ══ DataFrames ═══════════════════════════════════════════════════════ */
[data-testid="stDataFrame"] {
    border: 1px solid var(--c-border) !important;
    border-radius: 2px !important;
    overflow: hidden !important;
    box-shadow: var(--shadow-xs) !important;
    background: var(--c-white) !important;
}

/* ══ Expanders ════════════════════════════════════════════════════════ */
[data-testid="stExpander"] {
    border: 1px solid var(--c-border) !important;
    border-radius: 2px !important;
    background: var(--c-white) !important;
    box-shadow: var(--shadow-xs) !important;
}
[data-testid="stExpander"] summary {
    font-size: 0.78rem !important; font-weight: 500 !important;
    color: var(--c-text2) !important; padding: 13px 18px !important;
    letter-spacing: 0.02em !important;
}

/* ══ Onglets ══════════════════════════════════════════════════════════ */
[data-testid="stTabs"] > div:first-child { border-bottom: 1px solid var(--c-border) !important; gap: 0 !important; }
[data-testid="stTabs"] button {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.72rem !important; font-weight: 500 !important;
    text-transform: uppercase !important; letter-spacing: 0.1em !important;
    color: var(--c-muted) !important;
    padding: 11px 22px !important; border-radius: 0 !important; background: transparent !important;
    border: none !important; border-bottom: 1px solid transparent !important; margin-bottom: -1px !important;
    transition: color 0.15s !important;
}
[data-testid="stTabs"] button:hover { color: var(--c-text2) !important; }
[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--c-navy) !important;
    border-bottom: 1px solid var(--c-gold) !important;
    font-weight: 600 !important;
}
[data-testid="stTabs"] button p {
    font-size: 0.72rem !important; text-transform: uppercase !important; letter-spacing: 0.1em !important;
}

/* ══ Alerts ═══════════════════════════════════════════════════════════ */
[data-testid="stAlertContainer"] { border-radius: 2px !important; font-size: 0.8rem !important; }

/* ══ Inputs ═══════════════════════════════════════════════════════════ */
[data-testid="stSelectbox"] label, [data-testid="stMultiSelect"] label, [data-testid="stDateInput"] label {
    font-size: 0.56rem !important; font-weight: 600 !important; color: var(--c-muted) !important;
    text-transform: uppercase !important; letter-spacing: 0.16em !important;
}
[data-testid="stSelectbox"] > div > div,
[data-testid="stTextInput"] > div > div > input {
    border-radius: 2px !important;
    border-color: var(--c-border) !important;
    font-size: 0.82rem !important;
    background: var(--c-white) !important;
}

/* ══ Progress bar ═════════════════════════════════════════════════════ */
[data-testid="stProgressBar"] > div {
    background: var(--c-border) !important;
    border-radius: 1px !important;
}
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, var(--c-gold) 0%, var(--c-gold-lt) 100%) !important;
    border-radius: 1px !important;
}

/* ══ Misc ═════════════════════════════════════════════════════════════ */
hr { border: none !important; border-top: 1px solid var(--c-border) !important; margin: 28px 0 !important; }
.stCaption, [data-testid="stCaptionContainer"] p {
    font-size: 0.68rem !important; color: var(--c-muted) !important; letter-spacing: 0.02em !important;
}
code, pre { font-size: 0.74rem !important; background: var(--c-white) !important; border-radius: 2px !important;
    border: 1px solid var(--c-border) !important; }
[data-testid="stMarkdown"] p { font-size: 0.84rem !important; line-height: 1.75 !important; color: var(--c-text2) !important; }

/* ══ Scrollbar ════════════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--c-border2); border-radius: 0; }
::-webkit-scrollbar-thumb:hover { background: var(--c-muted); }

/* ══ Bande statut bas de page ════════════════════════════════════ */
.status-bar {
    position: fixed; bottom: 0; left: 0; right: 0; z-index: 9999;
    background: #fffbe6; border-top: 1px solid #e6d87a;
    padding: 4px 16px; display: flex; align-items: center; gap: 8px;
    font-size: 0.62rem; color: #7a6a00; font-weight: 500;
}
.status-bar-dot { width: 6px; height: 6px; border-radius: 50%; background: #c9861a; flex-shrink: 0; }
/* Composant iframe JS SPA (se cache lui-même via JS) */
div[data-testid="stCustomComponentV1"] { margin: 0 !important; padding: 0 !important; }
/* Boutons split view */
.split-controls { margin-left:auto; display:flex; align-items:center; gap:3px; padding-bottom:5px; }
.split-btn { cursor:pointer; padding:5px 10px; border-radius:4px; font-size:1rem; color:#c8d8e8; transition:all 0.15s; user-select:none; line-height:1; text-decoration:none !important; }
.split-btn:hover { background:rgba(255,255,255,0.14); color:#ffffff; }
.split-btn-on { background:rgba(184,151,63,0.25); color:#d4b96a; }



/* ══ Onglets ouverts (style navigateur) ══════════════════════════ */
.otab-bar {
    display: flex; align-items: flex-end; gap: 2px;
    background: #e8e4de; padding: 6px 20px 0;
    border-bottom: 1px solid var(--c-border);
    overflow-x: auto; scrollbar-width: none;
}
.otab-bar::-webkit-scrollbar { display: none; }
.otab-item {
    display: inline-flex; align-items: stretch;
    background: #d8d2c8; border: 1px solid #ccc5b9;
    border-bottom: none; border-radius: 5px 5px 0 0;
    overflow: hidden; position: relative; top: 1px;
    transition: background 0.12s;
    max-width: 200px;
}
.otab-item:hover { background: #ede9e2; }
.otab-item.ot-active {
    background: var(--c-bg); border-color: var(--c-border);
    border-top: 2px solid var(--c-gold);
    box-shadow: 0 -1px 0 var(--c-bg);
}
.otab-link {
    padding: 6px 10px 6px 13px; font-size: 0.67rem; font-weight: 500;
    color: #5a6a7a; text-decoration: none !important;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    max-width: 160px;
}
.otab-item.ot-active .otab-link { color: var(--c-navy); font-weight: 650; }
.otab-close {
    padding: 6px 9px 6px 3px; font-size: 0.8rem; line-height: 1;
    color: #8a9db5; text-decoration: none !important;
    display: flex; align-items: center;
    border-radius: 0 3px 0 0;
}
.otab-close:hover { color: var(--c-neg); background: rgba(192,57,43,0.08); }

/* ══ Barre d'onglets ══════════════════════════════════════════════ */
.tab-bar {
    display: flex; align-items: center; gap: 0;
    background: #ffffff !important;
    padding: 0 24px; overflow-x: auto; scrollbar-width: none;
    border-bottom: 2px solid #b8973f;
    margin: 0 -3rem 2rem -3rem;
}
.tab-bar::-webkit-scrollbar { display: none; }
.tab {
    display: inline-block;
    padding: 12px 20px;
    color: var(--c-muted);
    font-size: 0.66rem; font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase;
    text-decoration: none !important;
    border-bottom: 2px solid transparent;
    white-space: nowrap;
    transition: color 0.15s, border-color 0.15s;
}
.tab:hover { color: var(--c-navy); border-bottom-color: var(--c-gold-lt); }
.tab.tab-active {
    color: var(--c-navy); border-bottom-color: var(--c-gold); font-weight: 700;
}
.tab-dot {
    width: 5px; height: 5px; border-radius: 50%;
    display: inline-block; flex-shrink: 0;
}

.sub-tab-bar {
    display: flex; gap: 0; align-items: stretch;
    background: var(--c-white);
    border-bottom: 1px solid var(--c-border);
    padding: 0 24px; overflow-x: auto; scrollbar-width: none;
    margin-bottom: 24px;
}
.sub-tab-bar::-webkit-scrollbar { display: none; }
.sub-tab {
    display: inline-block;
    padding: 12px 18px;
    color: var(--c-text2);
    font-size: 0.68rem; font-weight: 600;
    letter-spacing: 0.10em; text-transform: uppercase;
    text-decoration: none !important;
    border-bottom: 2px solid transparent;
    white-space: nowrap;
    transition: color 0.15s, border-color 0.15s;
}
.sub-tab:hover { color: var(--c-navy); border-bottom-color: var(--c-gold-lt); }
.sub-tab.sub-active { color: var(--c-navy); border-bottom-color: var(--c-gold); font-weight: 700; }

/* ══ KPI Cards (grille dashboard live) ═══════════════════════════ */
.kpi-card {
    background: #fff;
    border: 1px solid var(--c-border);
    border-top: 2px solid var(--c-gold);
    margin-bottom: 0;
    height: 100%;
}
.kpi-card-hd {
    font-size: 0.52rem; font-weight: 600; color: var(--c-muted);
    text-transform: uppercase; letter-spacing: 0.18em;
    padding: 13px 22px 10px 22px;
    border-bottom: 1px solid #f5f2ed;
}
.kc-row { display: flex; align-items: stretch; }
.kc {
    display: flex; flex-direction: column;
    padding: 14px 18px; flex: 1;
    border-right: 1px solid #f5f2ed;
    min-width: 0;
}
.kc:last-child { border-right: none; }
.kc-l {
    font-size: 0.5rem; font-weight: 600; color: var(--c-muted);
    text-transform: uppercase; letter-spacing: 0.14em; margin-bottom: 5px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.kc-v {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 1.3rem; font-weight: 500; font-style: italic;
    color: var(--c-navy); line-height: 1.1;
}
.kpi-rebal-bar {
    height: 3px; background: var(--c-border);
    border-radius: 1px; overflow: hidden; margin: 0 22px 4px 22px;
}
.kpi-rebal-fill {
    height: 100%;
    background: linear-gradient(90deg, #b8973f, #d4b96a);
    border-radius: 1px;
}
</style>
""", unsafe_allow_html=True)

# ── Constantes ────────────────────────────────────────────────────────────────
BASE       = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE, "data")
HALAL_DIR  = DATA_DIR   # alias conservé pour compatibilité
DIV_DIR    = DATA_DIR
sys.path.insert(0, os.path.join(BASE, "scripts"))

# Sur Streamlit Cloud, les fichiers live sont lus depuis GitHub (toujours frais)
_GITHUB_RAW_DEFAULT = "https://raw.githubusercontent.com/lorenzo18012004/cgf-BRVMDiv/main"
_GITHUB_RAW   = _GITHUB_RAW_DEFAULT   # fallback public repo — pas besoin de secret
_GITHUB_TOKEN = None
_GITHUB_REPO  = None
try:
    _GITHUB_RAW   = st.secrets.get("github_raw",   _GITHUB_RAW_DEFAULT)
    _GITHUB_TOKEN = st.secrets.get("github_token", None)
    _GITHUB_REPO  = st.secrets.get("github_repo",  None)
except Exception:
    pass

_VERIFIED_GH_PATH = "test_ETFDividende/verified_rebals.json"

def _gh_get_verified():
    """Lit verified_rebals.json depuis l'API GitHub. Retourne (dict, sha)."""
    if not _GITHUB_TOKEN or not _GITHUB_REPO:
        return None, None
    try:
        import requests as _r
        h = {"Authorization": f"token {_GITHUB_TOKEN}", "User-Agent": "cgf-dashboard"}
        resp = _r.get(f"https://api.github.com/repos/{_GITHUB_REPO}/contents/{_VERIFIED_GH_PATH}", headers=h, timeout=10)
        if resp.status_code == 404:
            return {}, None
        resp.raise_for_status()
        d = resp.json()
        return json.loads(base64.b64decode(d["content"]).decode("utf-8")), d["sha"]
    except Exception:
        return None, None

def _gh_save_verified(data, sha=None):
    """Écrit verified_rebals.json sur GitHub via l'API."""
    if not _GITHUB_TOKEN or not _GITHUB_REPO:
        return False
    try:
        import requests as _r
        h = {"Authorization": f"token {_GITHUB_TOKEN}", "User-Agent": "cgf-dashboard", "Content-Type": "application/json"}
        content_b64 = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")).decode("ascii")
        body = {"message": "chore: vérifications rebalancements", "content": content_b64}
        if sha:
            body["sha"] = sha
        resp = _r.put(f"https://api.github.com/repos/{_GITHUB_REPO}/contents/{_VERIFIED_GH_PATH}", headers=h, json=body, timeout=15)
        resp.raise_for_status()
        return True
    except Exception:
        return False
_LIVE_FILES = {
    "nav_latest.json", "intraday_nav.json", "dashboard_data.json",
    "rebal_detail.json", "backtest_metrics.json", "launch_state.json",
    "brvm_composition_history.json", "brvm_composition_latest.json",
    "nav_intraday_history.json", "verified_rebals.json",
}

COLOR       = "#b8973f"   # or mat — ligne ETF
COLOR2      = "#4a7fa5"   # bleu acier — ligne secondaire
BENCH_COLOR = "#8a9db5"   # ardoise — ligne benchmark
ACCENT      = "rgba(184,151,63,0.10)"
POS_COLOR   = "#2d7a4f"
NEG_COLOR   = "#c0392b"

PLOTLY_LAYOUT = dict(
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    font=dict(family="Inter, -apple-system, system-ui, sans-serif", color="#3d4f63", size=12),
    xaxis=dict(
        showgrid=True, gridcolor="#f0ede8", gridwidth=1,
        linecolor="#e0dbd2", linewidth=1,
        tickfont=dict(size=11, color="#7d8fa3"),
        tickcolor="#e0dbd2",
    ),
    yaxis=dict(
        showgrid=True, gridcolor="#f0ede8", gridwidth=1,
        linecolor="#e0dbd2", linewidth=1,
        tickfont=dict(size=11, color="#7d8fa3"),
        tickcolor="#e0dbd2",
        zeroline=False,
    ),
    margin=dict(l=52, r=20, t=44, b=40),
    hoverlabel=dict(
        bgcolor="#0c1a2e", font_color="#f5f0e8",
        font_size=12, font_family="Inter, system-ui, sans-serif",
        bordercolor="#b8973f",
    ),
)

# ── Helpers ───────────────────────────────────────────────────────────────────
def _section(title):
    st.markdown(f'<p class="cgf-section">{title}</p>', unsafe_allow_html=True)

def _kpi_html(*items):
    """Affiche une rangée de cartes KPI compactes.
    items: tuples (label, value) ou (label, value, color_hex)
    """
    cards = ""
    for item in items:
        lbl, val = item[0], item[1]
        col = item[2] if len(item) > 2 else None
        v_style = f' style="color:{col}"' if col else ""
        cards += f'<div class="kc"><div class="kc-l">{lbl}</div><div class="kc-v"{v_style}>{val}</div></div>'
    st.markdown(
        f'<div class="kpi-card" style="margin-bottom:14px"><div class="kc-row">{cards}</div></div>',
        unsafe_allow_html=True
    )

@st.cache_data(ttl=60)
def load_json(path):
    filename = os.path.basename(path)
    if _GITHUB_RAW and filename in _LIVE_FILES:
        try:
            rel = os.path.relpath(path, BASE).replace("\\", "/")
            r = requests.get(f"{_GITHUB_RAW}/{rel}", timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
    if not os.path.exists(path): return None
    with open(path, encoding="utf-8-sig") as f: return json.load(f)

@st.cache_data(ttl=5)
def load_json_fresh(path):
    filename = os.path.basename(path)
    if _GITHUB_RAW and filename in _LIVE_FILES:
        try:
            rel = os.path.relpath(path, BASE).replace("\\", "/")
            r = requests.get(f"{_GITHUB_RAW}/{rel}", timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
    if not os.path.exists(path): return None
    with open(path, encoding="utf-8-sig") as f: return json.load(f)

EXCEL_PATH      = os.path.join(BASE, "BRVM_Consolidated_Kendall_updated.xlsx")
RICHBOURSE_PATH = os.path.join(HALAL_DIR, "richbourse_history.json")

@st.cache_data(ttl=120)
def _github_reachable():
    """Vérifie si le dépôt GitHub de données live est accessible."""
    if not _GITHUB_RAW:
        return True
    try:
        r = requests.get(f"{_GITHUB_RAW}/test_ETFDividende/nav_latest.json", timeout=5)
        return r.status_code == 200
    except Exception:
        return False

@st.cache_data(ttl=1800)
def load_close_history():
    """
    Charge l'historique des cours de clôture.
    Base : Excel (prix split-ajustés, 2008→date derniere mise a jour).
    Complement : Richbourse JSON pour les dates posterieures a l'Excel.
    Exception : SAFC — données Excel corrompues, remplacées par Richbourse.
    Retourne (DataFrame, error_msg|None).
    """
    df_xl = pd.DataFrame()
    last_xl = pd.Timestamp("2000-01-01")
    excel_error = None

    # ── Base : Excel ───────────────────────────────────────────────────────
    if os.path.exists(EXCEL_PATH):
        try:
            xl    = pd.ExcelFile(EXCEL_PATH)
            sheet = next((s for s in xl.sheet_names if "Cours_Close" in s), xl.sheet_names[1])
            df_xl = pd.read_excel(EXCEL_PATH, sheet_name=sheet,
                                  index_col=0, parse_dates=True).sort_index()
            last_xl = df_xl.index.max()
        except Exception as _e:
            excel_error = str(_e)

    # ── Complement + corrections : Richbourse JSON ────────────────────────
    if os.path.exists(RICHBOURSE_PATH):
        try:
            with open(RICHBOURSE_PATH, "r", encoding="utf-8") as f:
                rb = json.load(f)

            # Nouvelles dates (apres derniere date Excel)
            new_records = {}
            safc_records = {}
            for ticker, days in rb.items():
                for date_str, vals in days.items():
                    dt = pd.Timestamp(date_str)
                    if isinstance(vals, dict):
                        # Privilegier close_adj pour continuite avec l'historique Excel ajuste
                        val = vals.get("close_adj") or vals.get("close")
                    else:
                        val = vals
                    if dt > last_xl:
                        if date_str not in new_records:
                            new_records[date_str] = {}
                        new_records[date_str][ticker] = val
                    # SAFC : toujours prendre Richbourse cours normal (Excel corrompu)
                    if ticker == "SAFC":
                        safc_records[dt] = vals.get("close") if isinstance(vals, dict) else vals

            if new_records:
                df_new = pd.DataFrame.from_dict(new_records, orient="index")
                df_new.index = pd.to_datetime(df_new.index)
                df_new = df_new.reindex(columns=df_xl.columns) if not df_xl.empty else df_new
                df_xl  = pd.concat([df_xl, df_new]).sort_index() if not df_xl.empty else df_new

            # Corriger SAFC dans tout le DataFrame
            if safc_records and "SAFC" in df_xl.columns:
                s_safc = pd.Series(safc_records).sort_index()
                df_xl.loc[df_xl.index.isin(s_safc.index), "SAFC"] = s_safc.reindex(
                    df_xl.index[df_xl.index.isin(s_safc.index)]
                ).values

        except Exception:
            pass

    return (df_xl if not df_xl.empty else pd.DataFrame()), excel_error

@st.cache_data(ttl=60)
def richbourse_source_info():
    """Retourne la source active et la dernière date disponible."""
    if os.path.exists(RICHBOURSE_PATH):
        try:
            with open(RICHBOURSE_PATH, "r", encoding="utf-8") as f:
                rb = json.load(f)
            all_dates = [d for days in rb.values() for d in days.keys()]
            if all_dates:
                last = max(all_dates)
                n_t = len(rb)
                return f"Richbourse ({n_t} tickers · dernier: {last})"
        except Exception:
            pass
    if os.path.exists(EXCEL_PATH):
        return "Excel (fallback)"
    return "Aucune source"

@st.cache_data(ttl=300)
def detect_recent_splits(lookback_days = 10):
    """
    Détecte les splits/ajustements récents depuis sika_history.json.
    Méthode : variation > 30% entre deux séances consécutives.
    """
    sika_path = os.path.join(HALAL_DIR, "sika_history.json")
    if not os.path.exists(sika_path):
        return []
    try:
        with open(sika_path, "r", encoding="utf-8") as f:
            sika = json.load(f)
    except Exception:
        return []

    splits = []
    cutoff = (pd.Timestamp.now() - pd.Timedelta(days=lookback_days * 3)).strftime("%Y-%m-%d")

    for ticker, days in sika.items():
        recent = {d: v for d, v in days.items() if d >= cutoff}
        if len(recent) < 2:
            continue
        sorted_dates = sorted(recent.keys())

        prev_close = None
        for date_str in sorted_dates[-lookback_days:]:
            v = recent[date_str]
            c = v.get("close") if isinstance(v, dict) else (float(v) if isinstance(v, (int, float)) else None)
            if c and prev_close and prev_close > 0:
                chg = abs(c / prev_close - 1.0)
                if chg > 0.30:
                    splits.append({"ticker": ticker, "date": date_str, "type": "variation",
                                   "ratio": round(c / prev_close, 4), "close": c, "prev_close": prev_close})
                    break
            prev_close = c

    return splits

@st.cache_data(ttl=60)
def scrape_sika_open():
    """Scrape sikafinance.com pour récupérer le prix d'ouverture du jour."""
    try:
        import requests, warnings
        warnings.filterwarnings("ignore")
        resp = requests.get(
            "https://sikafinance.com/marches/aaz",
            headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "fr-FR"},
            verify=False, timeout=15,
        )
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        results = {}
        for a in soup.find_all("a", href=re.compile(r"/marches/cotation_[A-Z]", re.I)):
            m = re.search(r"cotation_([A-Z0-9]+)", a["href"], re.I)
            if not m:
                continue
            ticker = m.group(1).upper()
            if any(x in ticker for x in ("BRVM", "SIKA", "COMPO")):
                continue
            row = a.find_parent("tr")
            if not row:
                continue
            cells = row.find_all(["td", "th"])
            # Colonnes : Nom | Ouv | +Haut | +Bas | Vol | Vol XOF | Dernier | Variation
            def _p(c):
                return c.get_text(strip=True).replace("\xa0","").replace(" ","").replace(",",".").replace("%","")
            if len(cells) >= 8:
                try:
                    results[ticker] = {
                        "open":      float(_p(cells[1])),
                        "dernier":   float(_p(cells[6])),
                        "variation": float(_p(cells[7])),
                    }
                except (ValueError, IndexError):
                    try:
                        results[ticker] = {"open": float(_p(cells[1])), "dernier": None, "variation": None}
                    except ValueError:
                        pass
            elif len(cells) >= 2:
                try:
                    results[ticker] = {"open": float(_p(cells[1])), "dernier": None, "variation": None}
                except ValueError:
                    pass
        return results
    except Exception:
        return {}


def to_series(lst):
    if not lst: return pd.Series(dtype=float)
    df = pd.DataFrame(lst, columns=["date", "value"])
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")["value"]

def pct(v, sign=True, dec=2):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
    return f"{v*100:+.{dec}f}%" if sign else f"{v*100:.{dec}f}%"

# ── Chargement données ────────────────────────────────────────────────────────
dd_path = os.path.join(HALAL_DIR, "dashboard_data.json")
bm_path = os.path.join(HALAL_DIR, "backtest_metrics.json")
vl_path = os.path.join(HALAL_DIR, "validation_results.json")
sc_path = os.path.join(HALAL_DIR, "scalability_results.json")

dd = load_json(dd_path)
bm = load_json(bm_path) or {}
vl = load_json(vl_path) or {}
sc = load_json(sc_path) or []
_ls_path     = os.path.join(HALAL_DIR, "launch_state.json")
_launch_data = load_json(_ls_path) or {}
_launch_date_label = _launch_data.get("launch_date", "")
if _launch_date_label:
    try:
        _dt = pd.Timestamp(_launch_date_label)
        _launch_date_label = f"{_dt.day:02d}/{_dt.month:02d}/{_dt.year}"
    except Exception:
        pass

if not dd:
    st.error("dashboard_data.json introuvable. Relancer les pipelines.")
    st.stop()

_github_offline = _GITHUB_RAW and not _github_reachable()

# ── Navigation ────────────────────────────────────────────────────────────────
_ALL_SEC_LABELS = {
    "overview": "Vue d'ensemble", "performance": "Performance",
    "te": "Tracking Error", "composition": "Composition ETF",
    "indice": "Composition Indice Dividende", "rebalancements": "Rebalancements",
    "stress": "Stress Tests", "scalabilite": "Scalabilité",
    "walkforward": "Walk-Forward", "methodologie": "Méthodologie",
    "situation": "Situation actuelle",
    "rebalancement_action": "Rebalancer",
    "ap": "AP", "analyse": "Analyse approfondie",
}

_page        = st.query_params.get("page", "live")
_url_section = st.query_params.get("section", None)
_split   = st.query_params.get("split", "1") if _page in ("live", "backtest") else "1"
_nosplit = st.query_params.get("nosplit", "0")
_p = [st.query_params.get(f"p{i}", "") for i in range(1, 5)]

_live_sec_keys = {"situation", "rebalancements", "rebalancement_action", "ap", "analyse"}
_bt_sec_keys   = {"overview", "performance", "te", "composition", "indice",
                  "rebalancements", "stress", "scalabilite", "walkforward", "methodologie"}
_valid_secs    = _live_sec_keys if _page == "live" else _bt_sec_keys

# Nettoyer : section invalide pour cette page
if _url_section and _page in ("live", "backtest") and _url_section not in _valid_secs:
    st.query_params.update({"page": _page})
    st.rerun()

def _sub_url(page, section):
    return f"?page={page}&section={section}"

def _go_back():
    st.query_params.clear()
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# LANDING — helper : export Excel complet
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def _build_excel_complet(_cache_key = ""):
    """Export Excel 100% données LIVE — aucune donnée backtest."""
    import io as _io
    _nl  = load_json(os.path.join(HALAL_DIR, "nav_latest.json")) or {}
    _la  = load_json(os.path.join(HALAL_DIR, "launch_state.json")) or {}
    _ih  = load_json(os.path.join(HALAL_DIR, "nav_intraday_history.json")) or {}
    _ina = load_json(os.path.join(HALAL_DIR, "intraday_nav.json")) or {}
    _launch_date = _la.get("launch_date", "2026-01-01")

    output = _io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        # ── 1. Métriques LIVE uniquement ──────────────────────────────────────
        # Seule perf_since_launch est une vraie métrique live.
        # perf_ytd / 3m / 1y / vol / sharpe / maxDD viennent du backtest → exclus.
        _met = {
            "ETF":                     _nl.get("etf_name", "CGF ETF Dividende BRVM"),
            "Date_calcul":             _nl.get("calc_date"),
            "VL_par_part_FCFA":        _nl.get("vl_par_part_fcfa"),
            "NAV_indice_live":         _nl.get("nav_indice"),
            "AUM_MFCFA":               _nl.get("aum_mfcfa"),
            "Nb_parts":                _nl.get("n_parts"),
            "Perf_depuis_lancement_%": _nl.get("perf_since_launch"),
            "Date_lancement":          _la.get("launch_date"),
            "Prix_emission_FCFA":      _la.get("par_fcfa"),
            "NAV_ancre_lancement":     _la.get("nav_index_at_launch"),
            "Nb_titres_panier":        _nl.get("n_basket"),
        }
        pd.DataFrame([_met]).T.reset_index().rename(
            columns={"index": "Metrique", 0: "Valeur"}
        ).to_excel(writer, sheet_name="Metriques_live", index=False)

        # ── 2. VL journalière LIVE (depuis lancement) ─────────────────────────
        # Source : nav_live_series (VL FCFA officielle fin de journée)
        _ls = _nl.get("nav_live_series", [])
        _vl_rows = []
        # Construire un lookup depuis nav_intraday_history (dernier snap du jour)
        _ih_lookup = {}
        for _d, _pts in _ih.items():
            if _d >= _launch_date and isinstance(_pts, list) and _pts:
                lp = _pts[-1]
                _ih_lookup[_d] = {
                    "NAV_indice":        lp.get("nav_indice"),
                    "dividende_officiel":    lp.get("dividende_index"),
                    "Perf_lancement_%":  lp.get("perf_since_launch"),
                    "Var_1j_%":          lp.get("change_1d_pct"),
                    "AUM_MFCFA":         lp.get("aum_mfcfa"),
                }
        for _row in _ls:
            _d, _vl = _row[0], _row[1]
            _extra = _ih_lookup.get(_d, {})
            _vl_rows.append({"Date": _d, "VL_FCFA": _vl, **_extra})
        if _vl_rows:
            pd.DataFrame(_vl_rows).to_excel(writer, sheet_name="VL_journaliere_live", index=False)

        # ── 3. Panier ETF courant ──────────────────────────────────────────────
        _bsk = _nl.get("basket", [])
        if _bsk:
            pd.DataFrame(_bsk).to_excel(writer, sheet_name="Panier_ETF", index=False)

        # ── 4. iNAV aujourd'hui ────────────────────────────────────────────────
        _snaps = _ina.get("snapshots", [])
        if _snaps:
            _snap_clean = [{k: v for k, v in s.items()
                            if k not in ("prices_by_ticker", "ticker_contributions")}
                           for s in _snaps]
            pd.DataFrame(_snap_clean).to_excel(writer, sheet_name="iNAV_today", index=False)

        # ── 5. iNAV historique LIVE (tous les jours depuis lancement) ─────────
        _inh_rows = []
        for _dt, _pts in sorted(_ih.items()):
            if _dt >= _launch_date:
                for _pt in (_pts if isinstance(_pts, list) else []):
                    _inh_rows.append({"Date": _dt, **_pt})
        if _inh_rows:
            pd.DataFrame(_inh_rows).to_excel(writer, sheet_name="iNAV_historique_live", index=False)

        # ── 6. Cours de clôture LIVE (depuis lancement, tous les tickers) ─────
        if os.path.exists(RICHBOURSE_PATH):
            with open(RICHBOURSE_PATH, "r", encoding="utf-8") as _f:
                _rh = json.load(_f)
            _dates_live = sorted({d for v in _rh.values() for d in v if d >= _launch_date})
            _tickers    = sorted(_rh.keys())
            _rows_cl, _rows_adj, _rows_vol = [], [], []
            for _dt in _dates_live:
                _rc = {"Date": _dt}; _ra = {"Date": _dt}; _rv = {"Date": _dt}
                for _tk in _tickers:
                    _v = _rh[_tk].get(_dt)
                    if _v is None:
                        _rc[_tk] = _ra[_tk] = _rv[_tk] = None
                    elif isinstance(_v, dict):
                        _rc[_tk] = _v.get("close"); _ra[_tk] = _v.get("close_adj"); _rv[_tk] = _v.get("volume")
                    else:
                        _rc[_tk] = _ra[_tk] = float(_v); _rv[_tk] = None
                _rows_cl.append(_rc); _rows_adj.append(_ra); _rows_vol.append(_rv)
            if _rows_cl:
                pd.DataFrame(_rows_cl ).to_excel(writer, sheet_name="Cours_cloture_live",  index=False)
                pd.DataFrame(_rows_adj).to_excel(writer, sheet_name="Cours_ajustes_live",  index=False)
                pd.DataFrame(_rows_vol).to_excel(writer, sheet_name="Volumes_live",        index=False)

        # ── 7. Indice Indice Dividende officiel LIVE (depuis lancement) ─────────────────
        _idx_path = os.path.join(HALAL_DIR, "brvm30_index_history.json")
        if os.path.exists(_idx_path):
            with open(_idx_path, "r", encoding="utf-8") as _f:
                _idx = json.load(_f)
            _idx_rows = [{"Date": d, "Indice Dividende": v} for d, v in sorted(_idx.items()) if d >= _launch_date]
            if _idx_rows:
                pd.DataFrame(_idx_rows).to_excel(writer, sheet_name="Indice_Dividende_live", index=False)

    return output.getvalue()

# ══════════════════════════════════════════════════════════════════════════════
# LANDING
# ══════════════════════════════════════════════════════════════════════════════
def _render_landing():
    st.query_params.update({"page": "live", "section": "situation"})
    st.rerun()

    st.markdown("""
    <div class="landing-outer">
        <p class="landing-brand">CGF Bourse &nbsp;·&nbsp; Afrique de l'Ouest</p>
        <h1 class="landing-title">ETF Dividende BRVM</h1>
        <p class="landing-sub">Suivi en temps réel &nbsp;·&nbsp; Performance &nbsp;·&nbsp; Gestion</p>
        <div class="landing-cards">
            <a href="?page=backtest" class="lcard" target="_self">
                <span class="lcard-tag lcard-tag-bt">Simulation</span>
                <span class="lcard-name">Backtest</span>
                <span class="lcard-desc">Performance historique, Tracking Error, Composition, Stress Tests — données 2023–2026</span>
                <span class="lcard-arrow">→</span>
            </a>
            <a href="?page=live" class="lcard" target="_self">
                <span class="lcard-tag lcard-tag-lv">Réel</span>
                <span class="lcard-name">Live</span>
                <span class="lcard-desc">VL en temps réel, iNAV intraday, gestion opérationnelle — depuis le lancement</span>
                <span class="lcard-arrow">→</span>
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Mode nosplit (panneau split view) : masquer nav, garder le design ─────────
if _nosplit == "1" and _page in ("live", "backtest"):
    st.markdown("""<style>
    .cgf-navbar,.tab-bar,.otab-bar,.sub-tab-bar{display:none!important;}
    div[data-testid="stCustomComponentV1"]{display:none!important;}
    section[data-testid="stMain"]>div{padding-top:0.5rem!important;}
    section[data-testid="stMain"]{padding-left:0.75rem!important;padding-right:0.75rem!important;}
    [data-testid="stAppViewBlockContainer"]{padding-left:0.75rem!important;padding-right:0.75rem!important;}
    </style>""", unsafe_allow_html=True)
    # Pas de selectbox — la section est contrôlée par l'app principale

# ── Navigation sub-sections ──────────────────────────────────────────────────
_lsec = st.query_params.get("section", None) if _page == "live"     else None
_bsec = st.query_params.get("section", None) if _page == "backtest" else None

# Mémoriser la dernière section active par page (uniquement les sections valides)
if _page == "live"     and _lsec and _lsec in _live_sec_keys: st.session_state["_lt_active"] = _lsec
elif _page == "backtest" and _bsec and _bsec in _bt_sec_keys:  st.session_state["_bt_active"] = _bsec

# ── Header commun ────────────────────────────────────────────────────────────
_live_labels = {
    "situation":            "Situation actuelle",
    "rebalancements":       "Rebalancements",
    "rebalancement_action": "Rebalancer",
    "ap":                   "AP",
    "analyse":              "Analyse approfondie",
}
_bt_labels = {
    "overview":       "Vue d'ensemble",
    "performance":    "Performance",
    "te":             "Tracking Error",
    "composition":    "Composition ETF",
    "indice":         "Composition Indice Dividende",
    "rebalancements": "Rebalancements",
    "stress":         "Stress Tests",
    "scalabilite":    "Scalabilité",
    "walkforward":    "Walk-Forward",
}
if _page == "backtest" and _bsec:
    _nav_crumb = f'<span class="cgf-nav-page">Backtest</span><span class="cgf-nav-sep"> / </span><span class="cgf-nav-page-active">{_bt_labels.get(_bsec, _bsec)}</span>'
elif _page == "backtest":
    _nav_crumb = '<span class="cgf-nav-page-active">Backtest — Simulation 2023–2026</span>'
elif _lsec:
    _nav_crumb = f'<span class="cgf-nav-page">Live</span><span class="cgf-nav-sep"> / </span><span class="cgf-nav-page-active">{_live_labels.get(_lsec, _lsec)}</span>'
elif _page == "live":
    _nav_crumb = '<span class="cgf-nav-page-active">Live — ETF Réel</span>'
else:
    _nav_crumb = '<span class="cgf-nav-page-active">Accueil</span>'


# ── Barre d'onglets principaux ────────────────────────────────────────────────
_main_tabs = [
    ("live",     "Live",     "#2d7a4f"),
    ("backtest", "Backtest", "#4a7fa5"),
]
_tab_items = ""
for _tk, _tl, _tc in _main_tabs:
    _cls = "tab tab-active" if _page == _tk else "tab"
    _tu = f"?page={_tk}"
    if _page == _tk:
        _tab_style = "display:inline-flex;align-items:center;gap:7px;padding:9px 24px;background:#f7f5f0;color:#0c1a2e !important;font-size:0.78rem;font-weight:700;letter-spacing:0.06em;text-decoration:none !important;border:1px solid #e0dbd2;border-bottom:none;border-radius:5px 5px 0 0;position:relative;top:2px;white-space:nowrap;"
    else:
        _tab_style = "display:inline-flex;align-items:center;gap:7px;padding:9px 24px;background:#2a4a6e;color:#ffffff !important;font-size:0.78rem;font-weight:600;letter-spacing:0.06em;text-decoration:none !important;border:1px solid #4a7fa5;border-bottom:none;border-radius:5px 5px 0 0;position:relative;top:2px;white-space:nowrap;"
    _dot = f'<span style="width:5px;height:5px;border-radius:50%;background:{_tc};display:inline-block;margin-right:6px;flex-shrink:0;vertical-align:middle"></span>'
    _tab_items += f'<a href="{_tu}" target="_self" class="{_cls}" style="text-decoration:none">{_dot}{_tl}</a>'

if _page in ("live", "backtest") and _nosplit != "1":
    def _spurl(sv):
        _q = [f"page={_page}", f"split={sv}"]
        if _url_section: _q.append(f"section={_url_section}")
        return "?" + "&".join(_q)
    def _sbtn(sv, icon, title):
        _on = _split == sv
        _s = f"padding:4px 8px;border-radius:4px;text-decoration:none;color:{'var(--c-gold)' if _on else 'var(--c-muted)'};font-size:0.9rem;{'border-bottom:2px solid var(--c-gold);' if _on else ''}"
        return f'<a href="{_spurl(sv)}" target="_self" title="{title}" class="split-btn {"split-btn-on" if _on else ""}" style="{_s}">{icon}</a>'
    _sp_html = (
        f'<span style="margin-left:auto;display:flex;align-items:center;gap:3px;padding-bottom:5px">'
        + _sbtn("1","[ ]","Vue unique") + _sbtn("2","[|]","2 panneaux") + _sbtn("4","[+]","4 panneaux")
        + '</span>'
    )
else:
    _sp_html = ""
_tabbar_style = "display:flex;align-items:center;gap:0;background:#ffffff;padding:0;border-bottom:2px solid #b8973f;margin-bottom:1.5rem;overflow-x:auto;"
if _page != "landing":
    st.markdown(f'<div style="{_tabbar_style}">{_tab_items}{_sp_html}</div>', unsafe_allow_html=True)

# ── Mode split ────────────────────────────────────────────────────────────────
if _split != "1" and _nosplit != "1" and _page in ("live", "backtest"):
    import streamlit.components.v1 as _stc_sp
    _n_panels = 4 if _split == "4" else 2
    _all_secs_sp = sorted(_valid_secs, key=lambda k: _ALL_SEC_LABELS.get(k, k))
    _cur_panels: list[str] = []
    for _pi in range(_n_panels):
        _pp = _p[_pi] or (_url_section if _pi == 0 else "")
        if not _pp or _pp not in _all_secs_sp:
            _pp = _all_secs_sp[_pi % len(_all_secs_sp)]
        _cur_panels.append(_pp)
    _pcols = st.columns([3] * _n_panels + [2])
    for _pi in range(_n_panels):
        with _pcols[_pi]:
            _ppsel = st.selectbox(
                "", options=_all_secs_sp,
                format_func=lambda k: _ALL_SEC_LABELS.get(k, k),
                index=_all_secs_sp.index(_cur_panels[_pi]),
                key=f"_ppsel_{_pi}", label_visibility="collapsed",
            )
            if _ppsel != _cur_panels[_pi]:
                st.query_params[f"p{_pi+1}"] = _ppsel
                st.rerun()
    with _pcols[_n_panels]:
        _clu = f"?page={_page}"
        if _cur_panels: _clu += f"&section={_cur_panels[0]}"
        st.markdown(
            f'<a href="{_clu}" target="_self" style="display:inline-block;margin-top:4px;padding:5px 12px;'
            'background:#e2e8f0;border-radius:6px;text-decoration:none;color:#374151;font-size:0.83rem">'
            'Vue simple</a>', unsafe_allow_html=True)
    # Query-strings des panneaux — le chemin absolu vient du JS
    _panel_qs = []
    for _sec in _cur_panels:
        _panel_qs.append(f"?page={_page}&section={_sec}&nosplit=1")
    _pqs_json  = "[" + ",".join(f'"{q}"' for q in _panel_qs) + "]"
    _grid_rows = "1fr" if _split == "2" else "1fr 1fr"
    _h_frame   = 700 if _split == "2" else 450
    # Les iframes sont injectées DIRECTEMENT dans window.parent.document
    # (pas dans le sandbox du composant) → pas de blocage tracking prevention.
    # Le composant lui-même est invisible (height=4).
    _stc_sp.html(f"""<html><body><script>(function(){{
  var pd  = window.parent.document;
  var base= window.parent.location.href.split('?')[0];
  var qs  = {_pqs_json};
  var h   = {_h_frame};
  var rows= '{_grid_rows}';
  // Supprimer grille précédente si rerun
  var old = pd.getElementById('_cgf_split');
  if (old) old.remove();
  // Créer grille CSS dans le DOM de la page principale
  var g = pd.createElement('div');
  g.id  = '_cgf_split';
  g.style.cssText = 'display:grid;grid-template-columns:1fr 1fr;grid-template-rows:'+rows+';gap:2px;margin-top:4px';
  qs.forEach(function(q){{
    var f = pd.createElement('iframe');
    f.src = base + q;
    f.style.cssText = 'border:0;width:100%;height:'+h+'px';
    f.scrolling = 'yes';
    g.appendChild(f);
  }});
  // Insérer après l'élément du composant
  var fe  = window.frameElement;
  var cmp = fe && (fe.closest('[data-testid="stCustomComponentV1"]') || fe.parentElement);
  if (cmp) {{ cmp.insertAdjacentElement('afterend', g); }}
  else {{
    var main = pd.querySelector('section[data-testid="stMain"] > div') || pd.body;
    main.appendChild(g);
  }}
}})();</script></body></html>""", height=4, scrolling=False)
    st.stop()

# ── Sous-onglets ──────────────────────────────────────────────────────────────
if _page == "backtest":
    _bt_secs = [
        ("overview",       "Vue d'ensemble"),
        ("performance",    "Performance"),
        ("te",             "Tracking Error"),
        ("composition",    "Composition ETF"),
        ("indice",         "Composition Indice Dividende"),
        ("rebalancements", "Rebalancements"),
        ("stress",         "Stress Tests"),
        ("scalabilite",    "Scalabilité"),
        ("walkforward",    "Walk-Forward"),
        ("methodologie",   "Méthodologie"),
    ]
    _sub_items = ""
    for _sk, _sl in _bt_secs:
        _scls = "sub-tab sub-active" if _bsec == _sk else "sub-tab"
        _sub_items += f'<a href="{_sub_url("backtest",_sk)}" target="_self" class="{_scls}" style="text-decoration:none;color:inherit">{_sl}</a>'
    st.markdown(f'<div class="sub-tab-bar">{_sub_items}</div>', unsafe_allow_html=True)

elif _page == "live":
    _lv_secs = [
        ("situation",           "Situation actuelle"),
        ("rebalancements",      "Rebalancements"),
        ("rebalancement_action","Rebalancer"),
        ("ap",                  "AP"),
        ("analyse",             "Analyse approfondie"),
    ]
    _sub_items = ""
    for _sk, _sl in _lv_secs:
        _scls = "sub-tab sub-active" if _lsec == _sk else "sub-tab"
        _sub_items += f'<a href="{_sub_url("live",_sk)}" target="_self" class="{_scls}" style="text-decoration:none;color:inherit">{_sl}</a>'
    st.markdown(f'<div class="sub-tab-bar">{_sub_items}</div>', unsafe_allow_html=True)

# ── Barre de téléchargement (haut de page — Live + Backtest) ─────────────────
if _page in ("live", "backtest"):
    import glob as _glob
    _today_pname = f"rapport_journalier_{pd.Timestamp.now(tz='UTC').strftime('%Y-%m-%d')}.pdf"
    _pdf_found   = sorted(_glob.glob(os.path.join(BASE, "data", "pdfs", "journalier", "**", "rapport_journalier_*.pdf"), recursive=True), reverse=True)
    _today_pp    = next((p for p in _pdf_found if _today_pname in p), None)
    _latest_dp   = _today_pp if _today_pp else (_pdf_found[0] if _pdf_found else None)
    _hdr1, _hdr2 = st.columns(2)
    with _hdr1:
        if _latest_dp and os.path.exists(_latest_dp):
            with open(_latest_dp, "rb") as _f:
                st.download_button("Rapport du jour (PDF)", data=_f.read(),
                    file_name=os.path.basename(_latest_dp),
                    mime="application/pdf", use_container_width=True, key="dl_pdf_day")
        else:
            st.caption("Rapport du jour non disponible")
    with _hdr2:
        try:
            _xl_key = dd.get("metrics", {}).get("te", "") or pd.Timestamp.now().strftime("%Y-%m-%d")
            st.download_button("Export Excel complet", data=_build_excel_complet(_xl_key),
                file_name=f"CGF_ETFDividende_ETF_export_{pd.Timestamp.now().strftime('%Y-%m-%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, key="dl_xl_hdr")
        except Exception as _xe:
            st.caption(f"Excel indisponible ({_xe})")

# ══════════════════════════════════════════════════════════════════════════════
# BACKTEST
# ══════════════════════════════════════════════════════════════════════════════
def _render_backtest():
    """Section backtest — simulation 2023–2026, métriques et graphiques."""
    global _bsec

    nav_e_full = to_series(dd.get("nav_etf", {}))
    nav_b_full = to_series(dd.get("nav_bench", {}))
    if nav_e_full.empty:
        st.error("Données NAV ETF indisponibles dans dashboard_data.json. Relancer le pipeline.")
        st.stop()
    d_min = nav_e_full.index.min().date()
    d_max = nav_e_full.index.max().date()

    def _date_filter(key="bt_period"):
        _fc1, _ = st.columns([3, 5])
        with _fc1:
            dr = st.date_input("Période", (d_min, d_max), min_value=d_min, max_value=d_max, key=key)
        s = pd.Timestamp(dr[0]) if len(dr) == 2 else nav_e_full.index.min()
        e = pd.Timestamp(dr[1]) if len(dr) == 2 else nav_e_full.index.max()
        return s, e

    # ── Backtest : par défaut → Vue d'ensemble ────────────────────────────────
    if not _bsec:
        _bsec = "overview"

    # ── Vue d'ensemble ────────────────────────────────────────────────────────
    elif _bsec == "overview":
        start_dt, end_dt = _date_filter()
        st.markdown("---")
        m = dd.get("metrics", {})
        c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)
        c1.metric("TE progressive T+3", pct(bm.get("te_t3", m.get("te")), sign=False), help="TE réaliste : exécution étalée sur l'ADV + décalage règlement T+3 BRVM (ventes J0, achats J+3, cash en transit gagne 0%)")
        c2.metric("TD cumulé",      pct(m.get("td")),                 help="ETF PR nette vs Indice Dividende — période complète")
        c3.metric("TD /an",         pct(m.get("td_ann")),             help="TD net annualisé")
        c4.metric("Rebalancements", str(bm.get("n_rebal", "—")))
        c5.metric("Titres moy.",    str(bm.get("n_titres_avg", "—")))
        c6.metric("Turnover moy.",  pct(bm.get("turnover_avg", 0), sign=False))
        c7.metric("Frais gestion",  pct(abs(m.get("mgmt_fee_cumul", 0)), sign=False))
        c8.metric("Coût tx/an",     pct(bm.get("cost_tx_ann", 0), sign=False))

        # ── Règles de sélection du panier ─────────────────────────────────
        sp = bm.get("selection_params", {})
        if sp:
            _section("Méthodologie complète")
            _top_n      = sp.get("force_top_n", 5)
            _part_rate  = sp.get("participation_rate_pct", 15)
            _thr_pct    = sp.get("large_threshold_pct", 3)
            _n_large    = sp.get("max_exec_large_days", 40)
            _n_small    = sp.get("max_exec_small_days", 20)
            _adv_min    = sp.get("min_adv_mfcfa", 0.5)
            _w_min      = sp.get("min_basket_weight_pct", 0.1)
            _drift_thr  = sp.get("drift_threshold_pct", 1)
            _rf_rate    = sp.get("dividende_placement_taux", 3)
            _mgmt_fee   = sp.get("mgmt_fee_ann_pct", 0.6)
            st.html(f"""
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;margin-top:8px">

  <!-- BLOC 1 : COMPOSITION -->
  <div style="background:#fff;border:1px solid var(--c-border);border-top:3px solid var(--c-gold);padding:24px 22px;border-radius:2px">
    <div style="font-size:0.6rem;letter-spacing:.18em;text-transform:uppercase;color:var(--c-gold);font-weight:700;margin-bottom:14px">01 — Composition du panier</div>

    <div style="margin-bottom:16px">
      <div style="font-size:0.72rem;font-weight:600;color:var(--c-navy);margin-bottom:6px">Top {_top_n} titres — OTC</div>
      <div style="font-size:0.78rem;color:var(--c-text2);line-height:1.6">Tenus à leur <strong>poids exact Dividende</strong> via bloc OTC négocié. Aucune contrainte de liquidité.</div>
    </div>

    <div style="margin-bottom:16px">
      <div style="font-size:0.72rem;font-weight:600;color:var(--c-navy);margin-bottom:6px">25 titres restants — Plafond ADV</div>
      <div style="background:var(--c-gold-bg);border-left:3px solid var(--c-gold);padding:10px 12px;border-radius:1px;font-family:monospace;font-size:0.75rem;color:var(--c-navy);margin-bottom:8px">
        max_w = {_part_rate}% × ADV × N / AUM
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
        <div style="background:#f7f5f0;border:1px solid var(--c-border);padding:8px 10px;border-radius:2px;text-align:center">
          <div style="font-size:0.6rem;color:var(--c-muted);margin-bottom:2px">Grands ≥ {_thr_pct}% Dividende</div>
          <div style="font-size:1.1rem;font-weight:700;color:var(--c-navy)">{_n_large} j</div>
        </div>
        <div style="background:#f7f5f0;border:1px solid var(--c-border);padding:8px 10px;border-radius:2px;text-align:center">
          <div style="font-size:0.6rem;color:var(--c-muted);margin-bottom:2px">Petits &lt; {_thr_pct}% Dividende</div>
          <div style="font-size:1.1rem;font-weight:700;color:var(--c-navy)">{_n_small} j</div>
        </div>
      </div>
      <div style="font-size:0.72rem;color:var(--c-text2);margin-top:10px;line-height:1.5">Si un titre dépasse son plafond, l'excès est <strong>redistribué proportionnellement</strong> aux titres non plafonnés.</div>
    </div>

    <div style="border-top:1px solid var(--c-border);padding-top:12px;display:grid;grid-template-columns:1fr 1fr;gap:8px">
      <div>
        <div style="font-size:0.6rem;color:var(--c-muted);text-transform:uppercase;letter-spacing:.1em">ADV minimum</div>
        <div style="font-size:0.82rem;font-weight:600;color:var(--c-navy)">{_adv_min} M FCFA/j</div>
      </div>
      <div>
        <div style="font-size:0.6rem;color:var(--c-muted);text-transform:uppercase;letter-spacing:.1em">Poids minimum</div>
        <div style="font-size:0.82rem;font-weight:600;color:var(--c-navy)">{_w_min}%</div>
      </div>
    </div>
  </div>

  <!-- BLOC 2 : REBALANCEMENT -->
  <div style="background:#fff;border:1px solid var(--c-border);border-top:3px solid var(--c-gold);padding:24px 22px;border-radius:2px">
    <div style="font-size:0.6rem;letter-spacing:.18em;text-transform:uppercase;color:var(--c-gold);font-weight:700;margin-bottom:14px">02 — Rebalancement</div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px">
      <div style="background:#f7f5f0;border:1px solid var(--c-border);padding:10px;border-radius:2px;text-align:center">
        <div style="font-size:0.6rem;color:var(--c-muted);margin-bottom:2px">Cible mise à jour</div>
        <div style="font-size:0.78rem;font-weight:700;color:var(--c-navy)">Trimestriel</div>
        <div style="font-size:0.65rem;color:var(--c-muted)">jan / avr / jul / oct</div>
      </div>
      <div style="background:#f7f5f0;border:1px solid var(--c-border);padding:10px;border-radius:2px;text-align:center">
        <div style="font-size:0.6rem;color:var(--c-muted);margin-bottom:2px">Seuil de dérive</div>
        <div style="font-size:0.78rem;font-weight:700;color:var(--c-navy)">&gt; {_drift_thr}%</div>
        <div style="font-size:0.65rem;color:var(--c-muted)">vérification mensuelle</div>
      </div>
    </div>

    <div style="margin-bottom:16px">
      <div style="font-size:0.72rem;font-weight:600;color:var(--c-navy);margin-bottom:8px">Règlement T+3 BRVM</div>
      <div style="display:flex;flex-direction:column;gap:4px">
        <div style="display:flex;align-items:center;gap:8px;font-size:0.75rem">
          <span style="background:var(--c-navy);color:#fff;padding:2px 7px;border-radius:10px;font-size:0.65rem;font-weight:600;white-space:nowrap">J0</span>
          <span style="color:var(--c-text2)">Ventes exécutées — cash en transit</span>
        </div>
        <div style="margin-left:18px;color:var(--c-muted);font-size:0.72rem">↓ 0% (non placé)</div>
        <div style="display:flex;align-items:center;gap:8px;font-size:0.75rem">
          <span style="background:var(--c-gold);color:#fff;padding:2px 7px;border-radius:10px;font-size:0.65rem;font-weight:600;white-space:nowrap">J+3</span>
          <span style="color:var(--c-text2)">Cash reçu → <strong>achats démarrent</strong></span>
        </div>
        <div style="margin-left:18px;color:var(--c-muted);font-size:0.72rem">↓ exécution étalée</div>
        <div style="display:flex;align-items:center;gap:8px;font-size:0.75rem">
          <span style="background:var(--c-pos);color:#fff;padding:2px 7px;border-radius:10px;font-size:0.65rem;font-weight:600;white-space:nowrap">J+6</span>
          <span style="color:var(--c-text2)">Titres achetés reçus</span>
        </div>
      </div>
    </div>

    <div>
      <div style="font-size:0.72rem;font-weight:600;color:var(--c-navy);margin-bottom:8px">Spread de transaction (selon ADV)</div>
      <table style="width:100%;border-collapse:collapse;font-size:0.72rem">
        <tr style="background:var(--c-gold-bg)">
          <th style="padding:4px 8px;text-align:left;color:var(--c-navy);font-weight:600;border-bottom:1px solid var(--c-border)">ADV</th>
          <th style="padding:4px 8px;text-align:right;color:var(--c-navy);font-weight:600;border-bottom:1px solid var(--c-border)">Spread</th>
        </tr>
        <tr><td style="padding:4px 8px;color:var(--c-text2);border-bottom:1px solid #f0ece6">≥ 100 M FCFA/j</td><td style="padding:4px 8px;text-align:right;font-weight:600;color:var(--c-pos)">25 bps</td></tr>
        <tr style="background:#fafaf8"><td style="padding:4px 8px;color:var(--c-text2);border-bottom:1px solid #f0ece6">≥ 30</td><td style="padding:4px 8px;text-align:right;font-weight:600;color:var(--c-pos)">40 bps</td></tr>
        <tr><td style="padding:4px 8px;color:var(--c-text2);border-bottom:1px solid #f0ece6">≥ 10</td><td style="padding:4px 8px;text-align:right;font-weight:600;color:#8a6a00">80 bps</td></tr>
        <tr style="background:#fafaf8"><td style="padding:4px 8px;color:var(--c-text2);border-bottom:1px solid #f0ece6">≥ 5</td><td style="padding:4px 8px;text-align:right;font-weight:600;color:#8a6a00">125 bps</td></tr>
        <tr><td style="padding:4px 8px;color:var(--c-text2)">< 5</td><td style="padding:4px 8px;text-align:right;font-weight:600;color:var(--c-neg)">175 bps</td></tr>
      </table>
    </div>
  </div>

  <!-- BLOC 3 : DIVIDENDES & FRAIS -->
  <div style="background:#fff;border:1px solid var(--c-border);border-top:3px solid var(--c-gold);padding:24px 22px;border-radius:2px">
    <div style="font-size:0.6rem;letter-spacing:.18em;text-transform:uppercase;color:var(--c-gold);font-weight:700;margin-bottom:14px">03 — Dividendes &amp; Frais</div>

    <div style="margin-bottom:20px">
      <div style="font-size:0.72rem;font-weight:600;color:var(--c-navy);margin-bottom:10px">Distribution semestrielle</div>
      <div style="display:flex;flex-direction:column;gap:10px">
        <div style="display:flex;gap:12px;align-items:flex-start">
          <div style="width:32px;height:32px;background:var(--c-gold-bg);border:1px solid var(--c-gold);border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:0.65rem;font-weight:700;color:var(--c-gold)">1</div>
          <div>
            <div style="font-size:0.75rem;font-weight:600;color:var(--c-navy)">Réserve de dividendes</div>
            <div style="font-size:0.72rem;color:var(--c-text2);line-height:1.5">Dividendes reçus capitalisés au taux sans risque <strong>{_rf_rate}%/an</strong> jusqu'à distribution.</div>
          </div>
        </div>
        <div style="display:flex;gap:12px;align-items:flex-start">
          <div style="width:32px;height:32px;background:var(--c-gold-bg);border:1px solid var(--c-gold);border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:0.65rem;font-weight:700;color:var(--c-gold)">2</div>
          <div>
            <div style="font-size:0.75rem;font-weight:600;color:var(--c-navy)">Ex-date convention BRVM</div>
            <div style="font-size:0.72rem;color:var(--c-text2);line-height:1.5"><strong>1er juillet</strong> de l'année N+1 pour les dividendes de l'exercice N.</div>
          </div>
        </div>
        <div style="display:flex;gap:12px;align-items:flex-start">
          <div style="width:32px;height:32px;background:var(--c-gold-bg);border:1px solid var(--c-gold);border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:0.65rem;font-weight:700;color:var(--c-gold)">3</div>
          <div>
            <div style="font-size:0.75rem;font-weight:600;color:var(--c-navy)">Dates de distribution</div>
            <div style="font-size:0.72rem;color:var(--c-text2);line-height:1.5">Dernier jour de bourse de <strong>juin</strong> et de <strong>décembre</strong>.</div>
          </div>
        </div>
      </div>
    </div>

    <div style="border-top:1px solid var(--c-border);padding-top:16px">
      <div style="font-size:0.72rem;font-weight:600;color:var(--c-navy);margin-bottom:10px">Frais de gestion</div>
      <div style="display:flex;align-items:center;justify-content:space-between;background:var(--c-gold-bg);border:1px solid rgba(184,151,63,0.25);padding:12px 16px;border-radius:2px">
        <div style="font-size:0.75rem;color:var(--c-text2)">Déduits <strong>quotidiennement</strong> de la VL</div>
        <div style="font-size:1.4rem;font-weight:700;color:var(--c-navy);font-family:'Cormorant Garamond',Georgia,serif">{_mgmt_fee}%<span style="font-size:0.7rem;color:var(--c-muted);font-family:Inter,sans-serif">/an</span></div>
      </div>
      <div style="margin-top:10px;background:#f7f5f0;border:1px solid var(--c-border);padding:10px 12px;border-radius:2px">
        <div style="font-size:0.65rem;color:var(--c-muted);text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px">Poche de liquidité</div>
        <div style="font-size:0.75rem;color:var(--c-text2)"><strong>1% du NAV</strong> en cash permanent, capitalisé au taux sans risque {_rf_rate}%/an.</div>
      </div>
    </div>
  </div>

</div>
""")

        nav_e = nav_e_full.loc[start_dt:end_dt]
        nav_b = nav_b_full.loc[start_dt:end_dt]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=nav_b.index, y=nav_b.values,
            name="Indice Dividende", line=dict(color=BENCH_COLOR, width=1.5, dash="dot")))
        fig.add_trace(go.Scatter(x=nav_e.index, y=nav_e.values,
            name="ETF NAV nette", line=dict(color=COLOR, width=2)))
        fig.update_layout(**PLOTLY_LAYOUT, height=280,
            title="Performance Price Return (base 100)", hovermode="x unified",
            legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(fig, width='stretch')

        _section("Décomposition Tracking Difference")
        td_items = {
            "TD net total":              m.get("td", 0),
            "ETF brut vs Indice Dividende":     m.get("td_gross", 0),
            "dont Frais de gestion":     m.get("td", 0) - m.get("td_gross", 0),
        }
        st.dataframe(pd.DataFrame([{"Composante": k, "Valeur": pct(v)} for k, v in td_items.items()]),
                     width='stretch', hide_index=True)

    # ── Performance ───────────────────────────────────────────────────────────
    elif _bsec == "performance":
        start_dt, end_dt = _date_filter("bt_perf")
        st.markdown("---")
        nav_e = nav_e_full.loc[start_dt:end_dt]
        nav_b = nav_b_full.loc[start_dt:end_dt]
        nav_g = to_series(dd.get("nav_gross", [])).loc[start_dt:end_dt]

        fig_main = go.Figure()
        fig_main.add_trace(go.Scatter(x=nav_b.index, y=nav_b.values,
            name="Indice Dividende", line=dict(color=BENCH_COLOR, width=1.5, dash="dot")))
        fig_main.add_trace(go.Scatter(x=nav_e.index, y=nav_e.values,
            name="NAV nette", line=dict(color=COLOR, width=2.5)))
        if len(nav_g):
            fig_main.add_trace(go.Scatter(x=nav_g.index, y=nav_g.values,
                name="NAV brute", line=dict(color=COLOR, width=1, dash="dash"), visible="legendonly"))
        fig_main.update_layout(**PLOTLY_LAYOUT, height=420,
            title="Performance Price Return (base 100)", hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5))
        st.plotly_chart(fig_main, width='stretch')

        annual = bm.get("annual", [])
        if annual:
            _section("Performances annuelles")
            rows = []
            for a in annual:
                td_net  = a.get("td", 0) or 0
                td_gr   = a.get("td_gross", 0) or 0
                frais   = td_net - td_gr
                rows.append({
                    "Année":             str(a.get("year", "")),
                    "TE":                pct(a.get("te"), sign=False),
                    "TD net":            pct(td_net),
                    "ETF brut vs indice": pct(td_gr),
                    "Frais gestion":     pct(frais),
                })
            st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)

            if len(annual) >= 2:
                years   = [str(a["year"]) for a in annual]
                td_grs  = [(a.get("td_gross", 0) or 0) * 100 for a in annual]
                td_nets = [(a.get("td", 0) or 0) * 100 for a in annual]
                fees    = [((a.get("td", 0) or 0) - (a.get("td_gross", 0) or 0)) * 100 for a in annual]
                fig_ann = go.Figure()
                fig_ann.add_trace(go.Bar(x=years, y=td_grs, name="ETF brut vs indice", marker_color="#d1d5db", opacity=0.9))
                fig_ann.add_trace(go.Bar(x=years, y=fees,   name="Frais gestion",      marker_color="#a78bfa", opacity=0.8))
                fig_ann.add_trace(go.Scatter(x=years, y=td_nets, name="TD net",
                    mode="lines+markers", line=dict(color=COLOR, width=2.5), marker=dict(size=8, color=COLOR)))
                fig_ann.add_hline(y=0, line_color="#e5e7eb", line_width=1)
                fig_ann.update_layout(**PLOTLY_LAYOUT, height=300, barmode="relative",
                    title="Décomposition TD par année", yaxis_title="Impact (%)",
                    legend=dict(orientation="h", y=-0.3), hovermode="x unified")
                st.plotly_chart(fig_ann, width='stretch')

        _section("Écart cumulé ETF NAV nette vs Indice Dividende")
        nav_g2 = to_series(dd.get("nav_etf")).loc[start_dt:end_dt]
        nav_b2 = nav_b_full.loc[start_dt:end_dt]
        common = nav_g2.index.intersection(nav_b2.index)
        ar = (nav_g2.loc[common] / nav_b2.loc[common] - 1) * 100
        fig_ar = go.Figure()
        fig_ar.add_trace(go.Scatter(x=ar.index, y=ar.values,
            name="Écart ETF vs Indice Dividende", line=dict(color=COLOR, width=2),
            fill="tozeroy", fillcolor=ACCENT))
        fig_ar.add_hline(y=0, line_color="#e5e7eb", line_width=1)
        fig_ar.update_layout(**PLOTLY_LAYOUT, height=260, hovermode="x unified", yaxis_title="Écart (%)", showlegend=False)
        st.plotly_chart(fig_ar, width='stretch')

        # ── Impact des dividendes — PR vs TR ─────────────────────────────────
        _section("Impact des dividendes — Price Return vs Total Return")

        _dv_hist  = load_json(os.path.join(HALAL_DIR, "dividend_history.json")) or {}
        _dv_map   = _dv_hist.get("history", {})
        _sh_dv    = load_json(os.path.join(HALAL_DIR, "sika_history.json")) or {}
        _rd_dv    = load_json(os.path.join(HALAL_DIR, "rebal_detail.json")) or {}

        # Tickers différents entre dividend_history et sika_history
        _DV_TK     = {"TOTC": "TTLC", "VIVC": "SHEC", "TOSG": None, "NLCI": None}
        _DV_TK_REV = {v: k for k, v in _DV_TK.items() if v}  # TTLC→TOTC, SHEC→VIVC

        # Poids Indice Dividende par date de rebalancement (basket + excluded)
        _b30_wh = {}
        for _rv in _rd_dv.get("rebalancings", []):
            _dtr = _rv.get("date")
            if not _dtr: continue
            _ww = {}
            for _it in _rv.get("basket", []) + _rv.get("excluded", []):
                _tk, _wb = _it.get("ticker"), _it.get("w_brvm30", 0)
                if _tk and _wb: _ww[_tk] = _wb
            if _ww: _b30_wh[_dtr] = _ww
        _b30_srt = sorted(_b30_wh.keys())
        _wh_srt  = sorted((dd.get("w_history") or {}).keys())

        def _w_at(wh, srt, ds):
            past = [d for d in srt if d <= ds]
            return wh[past[-1]] if past else {}

        def _px_at(tk, ds):
            sh_tk = _sh_dv.get(tk, {})
            cands = [d for d in sh_tk if d <= ds and sh_tk[d].get("close")]
            return sh_tk[max(cands)]["close"] if cands else None

        _DV_YRS  = ["2022", "2023", "2024", "2025"]
        # Ex-date = date réelle du rebal de l'année N+1 (évite le décalage weekend 01-juil)
        _rebal_by_yr = {}
        for _wd in _wh_srt:
            _wy = _wd[:4]
            if _wy not in _rebal_by_yr:
                _rebal_by_yr[_wy] = _wd
        _EX_DTS  = {yr: (_rebal_by_yr.get(str(int(yr)+1)) or f"{int(yr)+1}-07-07")
                    for yr in _DV_YRS}
        _AUM_DV  = 5_000   # M FCFA

        # Calcul rendement dividende par exercice
        _yields_dv   = {}
        _div_rows_dv = []
        for _yr in _DV_YRS:
            _exd = _EX_DTS[_yr]
            if pd.Timestamp(_exd) > nav_e_full.index[-1]:
                break

            _b30_w = _w_at(_b30_wh, _b30_srt, _exd)
            _etf_w = _w_at(dd.get("w_history") or {}, _wh_srt, _exd)
            _tot_b = sum(_b30_w.values()) or 1.0
            _br_y = _et_y = _cash = 0.0

            for _tkb, _wb in _b30_w.items():
                _tks  = _DV_TK.get(_tkb, _tkb)
                if not _tks: continue
                _div  = (_dv_map.get(_tkb) or _dv_map.get(_tks) or {}).get(_yr)
                if not _div: continue
                _px   = _px_at(_tks, _exd)
                if not _px: continue
                _br_y += (_wb / _tot_b) * (_div / _px)

            for _tke, _we in _etf_w.items():
                _tkd  = _DV_TK_REV.get(_tke, _tke)
                _div  = (_dv_map.get(_tke) or _dv_map.get(_tkd) or {}).get(_yr)
                if not _div: continue
                _px   = _px_at(_tke, _exd)
                if not _px: continue
                _dyi  = _div / _px
                _et_y += _we * _dyi
                _cash += _we * _AUM_DV * _dyi

            _yields_dv[_yr] = {"brvm30": _br_y, "etf": _et_y, "cash": _cash}
            _div_rows_dv.append({
                "Exercice":          _yr,
                "Ex-date (conv.)":   _exd,
                "Rend. div. Indice Dividende": f"{_br_y*100:.2f}%",
                "Rend. div. ETF":    f"{_et_y*100:.2f}%",
                "Gap (pp)":          f"{(_et_y - _br_y)*100:+.2f}",
                "Cash ETF (M FCFA)": f"{_cash:.1f}",
            })

        # Séries TR : appliquer un multiplicateur cumulatif à chaque ex-date
        _b30_f = pd.Series(1.0, index=nav_b_full.index, dtype=float)
        _etf_f = pd.Series(1.0, index=nav_e_full.index, dtype=float)
        for _yr, _yd in _yields_dv.items():
            _ex_ts = pd.Timestamp(_EX_DTS[_yr])
            if _ex_ts <= nav_b_full.index[-1]:
                _b30_f.loc[_ex_ts:] *= (1 + _yd["brvm30"])
            if _ex_ts <= nav_e_full.index[-1]:
                _etf_f.loc[_ex_ts:] *= (1 + _yd["etf"])

        _nav_b_tr = (nav_b_full * _b30_f).loc[start_dt:end_dt]
        _nav_e_tr = (nav_e_full * _etf_f).loc[start_dt:end_dt]

        # Graphe 4 courbes
        _fig_tr = go.Figure()
        _fig_tr.add_trace(go.Scatter(x=nav_b.index, y=nav_b.values,
            name="Indice Dividende", line=dict(color=BENCH_COLOR, width=1.5, dash="dot")))
        _fig_tr.add_trace(go.Scatter(x=_nav_b_tr.index, y=_nav_b_tr.values,
            name="Indice Dividende TR", line=dict(color=BENCH_COLOR, width=2.5)))
        _fig_tr.add_trace(go.Scatter(x=nav_e.index, y=nav_e.values,
            name="ETF PR (net frais)", line=dict(color=COLOR, width=1.5, dash="dot")))
        _fig_tr.add_trace(go.Scatter(x=_nav_e_tr.index, y=_nav_e_tr.values,
            name="ETF TR (net frais)", line=dict(color=COLOR, width=2.5)))
        _fig_tr.update_layout(**PLOTLY_LAYOUT, height=420,
            title="Price Return vs Total Return (dividendes réinvestis, base 100)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5))
        st.plotly_chart(_fig_tr, width='stretch')

        # KPIs
        if _yields_dv:
            _tot_br = sum(v["brvm30"] for v in _yields_dv.values())
            _tot_et = sum(v["etf"]    for v in _yields_dv.values())
            _tot_ca = sum(v["cash"]   for v in _yields_dv.values())
            _n_yr_d = len(_yields_dv)
            _gap_pp = (_tot_et - _tot_br) * 100
            _ck1, _ck2, _ck3, _ck4 = st.columns(4)
            _ck1.metric("Rend. div. Indice Dividende (cumulé)", f"{_tot_br*100:.2f}%",
                        help="Somme des rendements dividendes de l'indice sur toute la période")
            _ck2.metric("Rend. div. ETF (cumulé)",    f"{_tot_et*100:.2f}%",
                        delta=f"{_gap_pp:+.2f} pp vs indice",
                        delta_color="normal" if _gap_pp >= 0 else "inverse",
                        help="Dividendes collectés par l'ETF / NAV à chaque ex-date")
            _ck3.metric("Cash collecté ETF (cumulé)", f"{_tot_ca:.0f} M FCFA")
            _ck4.metric("Rend. div. ETF moyen / an",  f"{_tot_et/_n_yr_d*100:.2f}%")

        # Table annuelle
        if _div_rows_dv:
            st.caption("Convention : dividendes de l'exercice N détachés au 1er juillet N+1 (BRVM)")
            st.dataframe(pd.DataFrame(_div_rows_dv), use_container_width=True, hide_index=True)

    # ── Tracking Error ────────────────────────────────────────────────────────
    elif _bsec == "te":
        start_dt, end_dt = _date_filter("bt_te")
        st.markdown("---")
        m = dd.get("metrics", {})
        te_t3 = bm.get("te_t3", bm.get("te_prog", 0))
        st.metric("TE progressive + T+3", pct(te_t3, sign=False),
                  help="TE réaliste : trades étalés sur l'ADV + décalage règlement T+3 BRVM (ventes J0 → cash J+3, achats démarrent J+3). Cash en transit gagne 0%.")

        _section("TE hebdomadaire glissante (52 semaines)")
        nav_g = to_series(dd.get("nav_gross", dd["nav_etf"])).loc[start_dt:end_dt]
        nav_b = nav_b_full.loc[start_dt:end_dt]
        gw  = nav_g.resample("W-FRI").last().dropna()
        bw  = nav_b.resample("W-FRI").last().dropna()
        cw  = gw.index.intersection(bw.index)
        act = (gw.loc[cw].pct_change() - bw.loc[cw].pct_change()).dropna()
        te_roll = act.rolling(52).std() * np.sqrt(52) * 100
        fig_te = go.Figure()
        fig_te.add_trace(go.Scatter(x=te_roll.index, y=te_roll.values,
            name="TE glissante", line=dict(color=COLOR, width=2)))
        fig_te.add_hline(y=2.5, line_dash="dash", line_color="#c0392b", annotation_text="Seuil 2.5%")
        fig_te.update_layout(**PLOTLY_LAYOUT, height=300,
            yaxis_title="TE (%)", hovermode="x unified", showlegend=False)
        st.plotly_chart(fig_te, width='stretch')

        _section("Distribution des écarts hebdomadaires ETF vs Indice Dividende")
        act2 = (gw.loc[cw].pct_change() - bw.loc[cw].pct_change()).dropna() * 100
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(x=act2.values, nbinsx=30, marker_color=COLOR, opacity=0.75))
        fig_hist.update_layout(plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
                               height=260, bargap=0.05, showlegend=False,
                               font=dict(family="Inter, system-ui, sans-serif", color="#4b5563"))
        st.plotly_chart(fig_hist, width='stretch')

        boot = vl.get("bootstrap", {})
        if boot:
            _section("Intervalle de confiance Bootstrap (N = 500 simulations)")
            st.caption(
                "La TE (1,67 %) est calculée sur une période historique précise. "
                "Le bootstrap rééchantillonne 500 fois les écarts journaliers pour estimer "
                "la plage probable de la TE si l'histoire avait été légèrement différente. "
                "Intervalle étroit → TE stable. Intervalle large → TE sensible au régime de marché."
            )
            c1, c2, c3 = st.columns(3)
            c1.metric("TE médiane", pct(boot.get("te_med", 0), False))
            c2.metric("TE P5  (borne basse)", pct(boot.get("te_p5", 0), False))
            c3.metric("TE P95 (borne haute)", pct(boot.get("te_p95", 0), False))
            te_vals = np.linspace(boot.get("te_p5", 0), boot.get("te_p95", 0), 100)
            spread  = (boot.get("te_p95", 0) - boot.get("te_p5", 0)) / 3.29 or 1e-6
            fig_boot = go.Figure()
            fig_boot.add_trace(go.Scatter(
                x=te_vals * 100,
                y=np.exp(-0.5 * ((te_vals - boot.get("te_med", 0)) / spread) ** 2),
                fill="tozeroy", line=dict(color=COLOR), fillcolor=ACCENT,
            ))
            fig_boot.add_vline(x=boot.get("te_med", 0) * 100, line_color=COLOR, annotation_text="Médiane")
            fig_boot.add_vline(x=2.5, line_dash="dash", line_color="#c0392b", annotation_text="Seuil 2.5%")
            fig_boot.update_layout(**PLOTLY_LAYOUT, height=240,
                title=f"Distribution TE bootstrap (N={boot.get('n_sim', 500)} simulations)",
                xaxis_title="TE (%)", yaxis_title="Densité", showlegend=False)
            st.plotly_chart(fig_boot, width='stretch')

    # ── Composition ETF ──────────────────────────────────────────────────────
    elif _bsec == "composition":
        wh = dd.get("w_history", {})
        if not wh:
            st.warning("Pas d'historique de composition.")
        else:
            dates_wh = sorted(wh.keys())
            sel_date = st.selectbox("Date de rebalancement", dates_wh, index=len(dates_wh) - 1)
            w = pd.Series(wh[sel_date]).sort_values(ascending=False)

            # Charger rebal_detail pour cette date (exclusions + cause)
            _rd_comp = load_json(os.path.join(HALAL_DIR, "rebal_detail.json")) or {}
            _rebal_sel = next(
                (r for r in _rd_comp.get("rebalancings", []) if r.get("date") == sel_date),
                None)
            _excluded_sel = _rebal_sel.get("excluded", []) if _rebal_sel else []
            _basket_sel   = _rebal_sel.get("basket",   []) if _rebal_sel else []
            _forced_tks   = {b["ticker"] for b in _basket_sel if b.get("force_otc") or b.get("force")}

            col1, col2 = st.columns([1.2, 1])
            with col1:
                fig_pie = go.Figure(go.Pie(
                    labels=w.index, values=(w.values * 100).round(2), hole=0.38,
                    marker=dict(colors=px.colors.qualitative.Pastel),
                    textposition="inside", textinfo="percent+label",
                ))
                fig_pie.update_layout(
                    plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
                    title=f"Composition — {sel_date}", height=380,
                    legend=dict(orientation="v", x=1.05),
                    margin=dict(l=20, r=120, t=40, b=20),
                    font=dict(family="Inter, system-ui, sans-serif", color="#4b5563"),
                )
                st.plotly_chart(fig_pie, width='stretch')
            with col2:
                _basket_rows = []
                for tk, v in w.items():
                    _bi = next((b for b in _basket_sel if b["ticker"] == tk), {})
                    _tag = " OTC" if tk in _forced_tks else ""
                    _w_etf  = v * 100
                    _w_b30  = _bi.get('w_brvm30', 0) * 100 if _bi else 0.0
                    _capped = _w_b30 > 0 and (_w_etf < _w_b30 - 0.05) and tk not in _forced_tks
                    _basket_rows.append({
                        "Titre":         tk + _tag,
                        "Poids ETF":     f"{_w_etf:.2f}%",
                        "Poids Indice Dividende":  f"{_w_b30:.2f}%" if _bi else "—",
                        "Capé ADV":      "⚠ oui" if _capped else "",
                        "ADV (M FCFA)":  f"{_bi.get('adv_mfcfa', 0):.1f}" if _bi else "—",
                    })
                st.caption("OTC = top 5 titres tenus a leur poids exact via gre-a-gre  ·  ⚠ Capé = poids ETF < poids indice à cause de l'ADV")
                st.dataframe(pd.DataFrame(_basket_rows), width='stretch', hide_index=True, height=360)

            # ── Titres exclus ──────────────────────────────────────────────
            if _excluded_sel:
                _section("Titres exclus de ce rebalancement — cause détaillée")

                def _excl_cause(e):
                    r    = e.get("raison", "")
                    w_b  = e.get("w_brvm30", 0)
                    adv  = e.get("adv_mfcfa", 0)
                    req  = e.get("adv_req",   0)
                    ratio = adv / req if req > 0 else 0
                    exec_d = e.get("exec_days") or (e.get("trade_mfcfa", 0) / adv if adv > 0 else None)
                    stale  = e.get("stale_ratio")
                    # Raisons explicites
                    if "Float" in r:
                        return "Float trop petit (< 7 Md FCFA)"
                    if "Absent" in r:
                        return "Absent de l'Indice Dividende à cette date"
                    if stale is not None and stale >= 0.70:
                        return f"Prix stale : {stale*100:.0f}% de jours sans cotation (3 mois)"
                    if "ADV limité" in r or "ADV insuffisant" in r or "consécutifs" in r:
                        return r
                    # 'OK' = exclusion ADV standard dans l'ancien backtest
                    if adv > 0 and req > 0 and adv < req:
                        days_str = f" — {exec_d:.0f}j d'exécution estimés" if exec_d else ""
                        forced_note = " (aurait du être forcé >= 3%)" if w_b >= 0.03 else ""
                        return f"ADV insuffisant : {adv:.1f} M FCFA (requis {req:.1f} M FCFA, ratio {ratio:.2f}){days_str}{forced_note}"
                    if adv > 0 and req > 0 and adv >= req:
                        return f"ADV OK ({adv:.1f}/{req:.1f}) — exclu pour autre raison"
                    return "ADV insuffisant (détail non disponible)"

                _excl_rows = []
                for e in sorted(_excluded_sel, key=lambda x: x.get("w_brvm30", 0), reverse=True):
                    _excl_rows.append({
                        "Titre":       e.get("ticker", ""),
                        "Poids Indice Dividende": f"{e.get('w_brvm30', 0)*100:.2f}%",
                        "ADV (M FCFA)": f"{e.get('adv_mfcfa', 0):.1f}" if e.get("adv_mfcfa") else "—",
                        "Cause":        _excl_cause(e),
                    })
                st.dataframe(pd.DataFrame(_excl_rows), width='stretch', hide_index=True)

            _section("Évolution des poids par rebalancement")
            all_w = pd.DataFrame({d: pd.Series(wh[d]) for d in dates_wh}).T.fillna(0)
            all_w.index = pd.to_datetime(all_w.index)
            fig_bar = go.Figure()
            colors_pie = px.colors.qualitative.Pastel
            for j, ticker in enumerate(all_w.columns):
                fig_bar.add_trace(go.Bar(x=all_w.index, y=all_w[ticker] * 100,
                    name=ticker, marker_color=colors_pie[j % len(colors_pie)]))
            fig_bar.update_layout(**PLOTLY_LAYOUT, height=300, barmode="stack",
                yaxis_title="Poids (%)", hovermode="x unified",
                legend=dict(orientation="h", y=-0.3))
            st.plotly_chart(fig_bar, width='stretch')

    # ── Composition de l'Indice Dividende ────────────────────────────────────────
    elif _bsec == "indice":
        rd_idx = load_json(os.path.join(HALAL_DIR, "rebal_detail.json"))
        if not rd_idx or not rd_idx.get("rebalancings"):
            st.info("Données rebal_detail.json nécessaires pour cette section.")
        else:
            rebals_idx = rd_idx["rebalancings"]

            # Reconstruit Indice Dividende complet = basket (in ETF) + excluded (in index but liquid-filtered)
            index_hist  = {}
            sector_map  = {}
            for r in rebals_idx:
                date    = r["date_label"]
                weights = {}
                for b in r.get("basket", []):
                    weights[b["ticker"]] = b.get("w_brvm30", 0)
                    sector_map[b["ticker"]] = b.get("secteur", "—")
                for e in r.get("excluded", []):
                    weights[e["ticker"]] = e.get("w_brvm30", 0)
                    sector_map[e["ticker"]] = e.get("secteur", "—")
                total = sum(weights.values())
                if total > 0:
                    weights = {t: v / total for t, v in weights.items()}
                index_hist[date] = weights

            dates_idx   = sorted(index_hist.keys())
            all_tickers_idx = sorted({t for w in index_hist.values() for t in w})

            _section("Résumé")
            avg_n_idx = sum(len(v) for v in index_hist.values()) / len(index_hist)
            avg_cov   = sum(
                sum(b.get("w_brvm30", 0) for b in r.get("basket", []))
                for r in rebals_idx
            ) / len(rebals_idx)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Rebalancements",          len(dates_idx))
            c2.metric("Titres uniques (total)",   len(all_tickers_idx))
            c3.metric("Titres moy. / rebal.",     f"{avg_n_idx:.0f}")
            c4.metric("Couverture ETF moy.",      f"{avg_cov*100:.1f}%")

            st.markdown("---")
            sel_date_idx = st.selectbox("Date de rebalancement", dates_idx,
                                        index=len(dates_idx) - 1, key="idx_date")
            w_sel = pd.Series(index_hist[sel_date_idx]).sort_values(ascending=False)

            rd_rebal_idx = next((r for r in rebals_idx if r["date_label"] == sel_date_idx), None)
            etf_tickers_idx  = {b["ticker"] for b in (rd_rebal_idx.get("basket",   []) if rd_rebal_idx else [])}
            excl_tickers_idx = {e["ticker"] for e in (rd_rebal_idx.get("excluded", []) if rd_rebal_idx else [])}

            col1, col2 = st.columns([1.4, 1])
            with col1:
                bar_colors_idx = [COLOR if t in etf_tickers_idx else "#e8ecf0" for t in w_sel.index]
                fig_bidx = go.Figure(go.Bar(
                    x=w_sel.index, y=(w_sel.values * 100).round(2),
                    marker_color=bar_colors_idx,
                    text=[f"{v*100:.1f}%" for v in w_sel.values], textposition="outside",
                ))
                fig_bidx.update_layout(**PLOTLY_LAYOUT, height=380,
                    title=f"Indice Dividende — {sel_date_idx}",
                    xaxis_tickangle=-45, yaxis_title="Poids (%)", showlegend=False,
                    annotations=[dict(x=0.99, y=0.98, xref="paper", yref="paper",
                        text="Bleu = dans ETF · Gris = exclu liquidité",
                        showarrow=False, font=dict(size=10, color="#7d8fa3"), xanchor="right")])
                st.plotly_chart(fig_bidx, width='stretch')
            with col2:
                _w_etf_idx = {b["ticker"]: b.get("w_etf", 0) * 100
                              for b in (rd_rebal_idx.get("basket", []) if rd_rebal_idx else [])}
                df_w_idx = pd.DataFrame({
                    "Ticker":       w_sel.index,
                    "Poids Indice Dividende": [f"{v*100:.2f}%" for v in w_sel.values],
                    "Cible ETF %":  [f"{_w_etf_idx[t]:.2f}%" if t in _w_etf_idx else "exclu"
                                     for t in w_sel.index],
                    "Secteur":      [sector_map.get(t, "—") for t in w_sel.index],
                    "Statut":       ["ETF" if t in etf_tickers_idx else "Exclu" for t in w_sel.index],
                })
                st.dataframe(df_w_idx, width='stretch', hide_index=True, height=360)

            _section("Evolution des poids Indice Dividende par rebalancement")
            df_idx_full = pd.DataFrame(
                {d: pd.Series(index_hist[d]) for d in dates_idx}
            ).T.fillna(0) * 100
            colors_pal = px.colors.qualitative.Pastel + px.colors.qualitative.Set2
            fig_stk = go.Figure()
            for j, ticker in enumerate(df_idx_full.columns):
                fig_stk.add_trace(go.Bar(
                    x=df_idx_full.index, y=df_idx_full[ticker],
                    name=ticker, marker_color=colors_pal[j % len(colors_pal)],
                ))
            fig_stk.update_layout(**PLOTLY_LAYOUT, height=320, barmode="stack",
                yaxis_title="Poids (%)", hovermode="x unified",
                legend=dict(orientation="h", y=-0.4))
            st.plotly_chart(fig_stk, width='stretch')

            _section("Rotations dans l'Indice Dividende")
            rot_rows = []
            for i in range(1, len(rebals_idx)):
                prev_t_idx = set(index_hist[dates_idx[i-1]].keys())
                curr_t_idx = set(index_hist[dates_idx[i]].keys())
                ent_idx = sorted(curr_t_idx - prev_t_idx)
                exi_idx = sorted(prev_t_idx - curr_t_idx)
                rot_rows.append({
                    "Date":       dates_idx[i],
                    "Entrées":    " · ".join(ent_idx) if ent_idx else "—",
                    "Sorties":    " · ".join(exi_idx) if exi_idx else "—",
                    "Nb entrées": len(ent_idx),
                    "Nb sorties": len(exi_idx),
                    "Nb titres":  len(curr_t_idx),
                })
            if rot_rows:
                st.dataframe(pd.DataFrame(rot_rows), width='stretch', hide_index=True)

    # ── Rebalancements ────────────────────────────────────────────────────────
    elif _bsec == "rebalancements":
        rlog = dd.get("rebal_history", [])
        if not rlog:
            st.caption("Pas d'historique de rebalancements.")
        else:
            df_r   = pd.DataFrame(rlog)
            df_r["date"] = pd.to_datetime(df_r["date"])
            df_eff = df_r[~df_r["skipped"]].copy()

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Rebal. effectifs", len(df_eff))
            c2.metric("Rebal. annulés",   int(df_r["skipped"].sum()))
            c3.metric("Turnover moyen",   pct(df_eff["turnover"].mean() if len(df_eff) else 0, sign=False))
            c4.metric("Coûts totaux",     f"{df_r['cost_bps'].sum():.0f} bps")

            fig_to = make_subplots(specs=[[{"secondary_y": True}]])
            fig_to.add_trace(go.Bar(x=df_eff["date"], y=df_eff["turnover"] * 100,
                name="Turnover (%)", marker_color=COLOR, opacity=0.7), secondary_y=False)
            fig_to.add_trace(go.Scatter(x=df_eff["date"], y=df_eff["cost_bps"],
                name="Coût (bps)", line=dict(color="#f59e0b", width=2),
                mode="lines+markers", marker=dict(size=6)), secondary_y=True)
            fig_to.update_layout(plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
                title="Turnover et coûts par rebalancement", height=300, hovermode="x unified",
                legend=dict(orientation="h", y=-0.25),
                font=dict(family="Inter, system-ui, sans-serif", color="#4b5563"))
            fig_to.update_yaxes(title_text="Turnover (%)", secondary_y=False, showgrid=True, gridcolor="#f3f4f6")
            fig_to.update_yaxes(title_text="Coût (bps)", secondary_y=True)
            st.plotly_chart(fig_to, width='stretch')

            fig_nav = go.Figure(go.Scatter(
                x=df_eff["date"], y=df_eff["nav_after"], mode="lines+markers",
                line=dict(color=COLOR, width=2), marker=dict(size=7, color=COLOR),
            ))
            fig_nav.update_layout(**PLOTLY_LAYOUT, height=240,
                title="NAV après chaque rebalancement", yaxis_title="NAV (base 100)", showlegend=False)
            st.plotly_chart(fig_nav, width='stretch')

            df_display = df_r.copy()
            df_display["turnover"]  = df_display["turnover"].map(lambda v: f"{v * 100:.2f}%")
            df_display["cost_bps"]  = df_display["cost_bps"].map(lambda v: f"{v:.0f}")
            df_display["nav_after"] = df_display["nav_after"].map(lambda v: f"{v:.2f}")
            df_display["skipped"]   = df_display["skipped"].map(lambda v: "Annulé" if v else "Effectué")
            df_display["date"]      = df_display["date"].dt.strftime("%d/%m/%Y")
            st.dataframe(df_display.rename(columns={
                "date": "Date", "turnover": "Turnover", "cost_bps": "Coût (bps)",
                "nav_after": "NAV après", "skipped": "Statut",
            }), width='stretch', hide_index=True)

    # ── Stress Tests ──────────────────────────────────────────────────────────
    elif _bsec == "stress":
        stress = vl.get("stress_tests", [])
        ewma   = vl.get("ewma_sensitivity", [])
        boot   = vl.get("bootstrap", {})

        if stress:
            col1, col2 = st.columns(2)
            with col1:
                ref_te   = next((s["te"] for s in stress if "éf" in s.get("name", "")), stress[0]["te"])
                c_stress = [COLOR if abs(s["te"] - ref_te) < 0.001 else "#d1d5db" for s in stress]
                fig_st   = go.Figure()
                fig_st.add_trace(go.Bar(x=[s["name"] for s in stress],
                    y=[s["te"] * 100 for s in stress], marker_color=c_stress))
                fig_st.add_hline(y=2.5, line_dash="dash", line_color="#c0392b", annotation_text="Seuil 2.5%")
                fig_st.update_layout(**PLOTLY_LAYOUT, height=300,
                    title="TE par scénario", yaxis_title="TE (%)", xaxis_tickangle=-25, showlegend=False)
                st.plotly_chart(fig_st, width='stretch')
            with col2:
                st.dataframe(pd.DataFrame([{"Scénario": s["name"], "TE": pct(s["te"], False),
                    "TD": pct(s["td"]), "Turnover": pct(s["turnover"], False)} for s in stress]),
                    width='stretch', hide_index=True)
        else:
            st.caption("Pas de stress tests.")


        if boot:
            _section("Analyse Bootstrap")
            c1, c2, c3 = st.columns(3)
            c1.metric("TE médiane", pct(boot.get("te_med", 0), False))
            c2.metric("TE P5",      pct(boot.get("te_p5", 0), False))
            c3.metric("TE P95",     pct(boot.get("te_p95", 0), False))
            te_vals = np.linspace(boot.get("te_p5", 0), boot.get("te_p95", 0), 100)
            spread  = (boot.get("te_p95", 0) - boot.get("te_p5", 0)) / 3.29 or 1e-6
            fig_boot = go.Figure()
            fig_boot.add_trace(go.Scatter(
                x=te_vals * 100,
                y=np.exp(-0.5 * ((te_vals - boot.get("te_med", 0)) / spread) ** 2),
                fill="tozeroy", line=dict(color=COLOR), fillcolor=ACCENT,
            ))
            fig_boot.add_vline(x=boot.get("te_med", 0) * 100, line_color=COLOR, annotation_text="Médiane")
            fig_boot.add_vline(x=2.5, line_dash="dash", line_color="#c0392b", annotation_text="Seuil 2.5%")
            fig_boot.update_layout(**PLOTLY_LAYOUT, height=240,
                title=f"Distribution TE bootstrap (N={boot.get('n_sim', 300)} simulations)",
                xaxis_title="TE (%)", yaxis_title="Densité", showlegend=False)
            st.plotly_chart(fig_boot, width='stretch')

    # ── Scalabilité ───────────────────────────────────────────────────────────
    elif _bsec == "scalabilite":
        if not sc:
            st.caption("Pas de données scalabilité. Lancez rebuild_backtest.py.")
        else:
            # Normalisation : nouveau format (liste de dicts avec aum_mfcfa) ou ancien
            _sc_new = [s for s in sc if 'aum_mfcfa' in s]
            _sc_old = [s for s in sc if 'aum_mfcfa' not in s]

            if _sc_new:
                df_s = pd.DataFrame(_sc_new)
                _labels = df_s['label'].tolist()
                _aums   = df_s['aum_mfcfa'].tolist()

                # ── Métriques synthétiques ──────────────────────────────────
                _section("Vue d'ensemble — Impact de l'AUM sur la réplication")

                # Point de rupture : premier AUM où TE > 2%
                _rupture = next((row['label'] for _, row in df_s.iterrows()
                                 if row['te'] * 100 > 2.0), "≥ 50 Md")
                _capped_max = df_s['n_capped_avg'].max()
                _te_min = df_s['te'].min() * 100
                _te_max = df_s['te'].max() * 100
                _mc1, _mc2, _mc3, _mc4 = st.columns(4)
                _mc1.metric("TE à 5 Md",  f"{df_s[df_s['aum_mfcfa']==5000]['te'].iloc[0]*100:.2f}%"
                            if 5000 in _aums else "N/A")
                _mc2.metric("TE à 10 Md", f"{df_s[df_s['aum_mfcfa']==10000]['te'].iloc[0]*100:.2f}%"
                            if 10000 in _aums else "N/A")
                _mc3.metric("Seuil TE > 2%", _rupture)
                _mc4.metric("Plafonnés max (avg)", f"{_capped_max:.1f} titres")

                st.markdown("---")

                # ── Graphiques ──────────────────────────────────────────────
                _gc1, _gc2 = st.columns(2)

                with _gc1:
                    _bar_c = ["#2d7a4f" if v*100 < 1 else "#c9861a" if v*100 < 2 else "#c0392b"
                              for v in df_s["te"]]
                    fig_te = go.Figure()
                    fig_te.add_trace(go.Bar(
                        x=_labels, y=df_s["te"]*100,
                        marker_color=_bar_c,
                        text=[f"{v*100:.2f}%" for v in df_s["te"]],
                        textposition="outside", name="TE"))
                    fig_te.add_trace(go.Scatter(
                        x=_labels, y=df_s["td"]*100,
                        mode="lines+markers",
                        line=dict(color="#b8973f", width=2, dash="dot"),
                        marker=dict(size=7), name="TD",
                        yaxis="y2"))
                    fig_te.add_hline(y=2.0, line_dash="dash", line_color="#c0392b",
                                     annotation_text="Seuil 2%")
                    fig_te.add_hline(y=1.0, line_dash="dot", line_color="#c9861a",
                                     annotation_text="Seuil 1%")
                    fig_te.update_layout(
                        **PLOTLY_LAYOUT, height=380,
                        title="TE & TD selon l'AUM",
                        yaxis_title="TE (%)", showlegend=True,
                        yaxis2=dict(title="TD (%)", overlaying="y", side="right",
                                    showgrid=False),
                        legend=dict(orientation="h", y=-0.25),
                        xaxis_tickangle=-30,
                    )
                    st.plotly_chart(fig_te, width='stretch')

                with _gc2:
                    fig_cap = go.Figure()
                    fig_cap.add_trace(go.Bar(
                        x=_labels, y=df_s["n_capped_avg"],
                        marker_color="#4a7fa5", opacity=0.85,
                        text=[f"{v:.1f}" for v in df_s["n_capped_avg"]],
                        textposition="outside", name="Plafonnés"))
                    fig_cap.add_trace(go.Bar(
                        x=_labels, y=df_s["n_exclu_avg"],
                        marker_color="#c0392b", opacity=0.75,
                        text=[f"{v:.1f}" for v in df_s["n_exclu_avg"]],
                        textposition="outside", name="Exclus"))
                    fig_cap.update_layout(
                        **PLOTLY_LAYOUT, height=380,
                        title="Titres plafonnés & exclus (moy. par trimestre)",
                        barmode="stack", yaxis_title="Nb titres",
                        legend=dict(orientation="h", y=-0.25),
                        xaxis_tickangle=-30,
                    )
                    st.plotly_chart(fig_cap, width='stretch')

                # ── Tableau récapitulatif ───────────────────────────────────
                st.markdown("---")
                _section("Tableau récapitulatif")
                df_tbl = df_s[[
                    'label', 'te', 'td', 'turnover', 'cost_tx_ann',
                    'basket_n_avg', 'n_capped_avg', 'n_exclu_avg', 'coverage_avg'
                ]].copy()
                df_tbl['te']           = df_tbl['te'].map(lambda v: f"{v*100:.2f}%")
                df_tbl['td']           = df_tbl['td'].map(lambda v: f"{v*100:+.2f}%")
                df_tbl['turnover']     = df_tbl['turnover'].map(lambda v: f"{v*100:.1f}%")
                df_tbl['cost_tx_ann']  = df_tbl['cost_tx_ann'].map(lambda v: f"{v*100:.3f}%")
                df_tbl['basket_n_avg'] = df_tbl['basket_n_avg'].map(lambda v: f"{v:.1f}")
                df_tbl['n_capped_avg'] = df_tbl['n_capped_avg'].map(lambda v: f"{v:.1f}")
                df_tbl['n_exclu_avg']  = df_tbl['n_exclu_avg'].map(lambda v: f"{v:.1f}")
                df_tbl['coverage_avg'] = df_tbl['coverage_avg'].map(lambda v: f"{v*100:.1f}%")
                df_tbl.columns = ['AUM', 'TE', 'TD', 'Turnover', 'Coût tx/an',
                                   'Titres moy.', 'Plafonnés moy.', 'Exclus moy.', 'Couverture']
                st.dataframe(df_tbl, width='stretch', hide_index=True)

                # ── Titres goulots d'étranglement ───────────────────────────
                st.markdown("---")
                _section("Titres goulots — lesquels bloquent en premier")

                # Construire matrice ticker × AUM (fréquence de plafonnement)
                _all_tickers_cap = sorted(set(
                    r['ticker'] for s in _sc_new for r in s.get('top_capped', [])
                ))
                if _all_tickers_cap:
                    _heatmap_data = []
                    for s in _sc_new:
                        _freq_map = {r['ticker']: r['freq'] for r in s.get('top_capped', [])}
                        _heatmap_data.append([_freq_map.get(tk, 0) for tk in _all_tickers_cap])

                    fig_heat = go.Figure(go.Heatmap(
                        z=_heatmap_data,
                        x=_all_tickers_cap,
                        y=_labels,
                        colorscale=[[0, '#f7f5f0'], [0.33, '#c9861a'], [1.0, '#c0392b']],
                        zmin=0, zmax=1,
                        text=[[f"{v:.0%}" if v > 0 else "" for v in row] for row in _heatmap_data],
                        texttemplate="%{text}",
                        colorbar=dict(title="Fréq. plaf.", tickformat=".0%"),
                    ))
                    fig_heat.update_layout(
                        **PLOTLY_LAYOUT, height=320,
                        title="Fréquence de plafonnement par titre et par AUM",
                        xaxis_title="Ticker", yaxis_title="AUM",
                    )
                    st.plotly_chart(fig_heat, width='stretch')

                # ── Détail trimestriel pour un AUM choisi ───────────────────
                with st.expander("Détail trimestriel pour un AUM spécifique"):
                    _sel_label = st.selectbox(
                        "Choisir l'AUM", _labels, key="sc_aum_sel",
                        index=min(1, len(_labels)-1)
                    )
                    _sel_sc = next((s for s in _sc_new if s['label'] == _sel_label), None)
                    if _sel_sc and _sel_sc.get('rebal_detail'):
                        _rd_sc = _sel_sc['rebal_detail']
                        _rows_rd = []
                        for r in _rd_sc:
                            _rows_rd.append({
                                'Date': r['date'],
                                'Titres': r['basket_n'],
                                'Plafonnés': r['capped_n'],
                                'Exclus': r['exclu_n'],
                                'Couverture': f"{r['coverage']*100:.1f}%",
                                'Tickers plafonnés': ', '.join(r['capped']) or '—',
                                'Tickers exclus': ', '.join(r['exclu']) or '—',
                            })
                        st.dataframe(pd.DataFrame(_rows_rd), width='stretch', hide_index=True)

            elif _sc_old:
                # Ancien format de compatibilité
                df_s = pd.DataFrame(_sc_old)
                st.dataframe(df_s, width='stretch', hide_index=True)

    # ── Walk-Forward ──────────────────────────────────────────────────────────
    elif _bsec == "walkforward":
        wf = vl.get("walk_forward", [])
        if not wf:
            st.caption("Pas de données walk-forward.")
        else:
            df_wf = pd.DataFrame(wf)
            col1, col2 = st.columns(2)
            with col1:
                fig_wf = go.Figure()
                fig_wf.add_trace(go.Bar(x=df_wf["label"], y=df_wf["te_oos"] * 100,
                    name="TE OOS", marker_color=COLOR, opacity=0.8,
                    text=[f"{v * 100:.2f}%" for v in df_wf["te_oos"]], textposition="outside"))
                fig_wf.add_trace(go.Scatter(x=df_wf["label"], y=df_wf["te_is"] * 100,
                    name="TE In-Sample", line=dict(color="#d1d5db", dash="dot", width=2), mode="lines+markers"))
                fig_wf.add_hline(y=2.5, line_dash="dash", line_color="#c0392b", annotation_text="Seuil 2.5%")
                fig_wf.update_layout(**PLOTLY_LAYOUT, height=340,
                    title="TE In-Sample vs Out-of-Sample", xaxis_tickangle=-25, yaxis_title="TE (%)",
                    legend=dict(orientation="h", y=-0.3))
                st.plotly_chart(fig_wf, width='stretch')
            with col2:
                colors_td = ["#2d7a4f" if v >= 0 else "#c0392b" for v in df_wf["td_oos"]]
                fig_td_wf = go.Figure()
                fig_td_wf.add_trace(go.Bar(x=df_wf["label"], y=df_wf["td_oos"] * 100,
                    marker_color=colors_td,
                    text=[f"{v * 100:+.2f}%" for v in df_wf["td_oos"]], textposition="outside"))
                fig_td_wf.add_hline(y=0, line_color="#e5e7eb", line_width=1)
                fig_td_wf.update_layout(**PLOTLY_LAYOUT, height=340,
                    title="TD Out-of-Sample par période", xaxis_tickangle=-25, yaxis_title="TD (%)", showlegend=False)
                st.plotly_chart(fig_td_wf, width='stretch')

            colors_d = ["#2d7a4f" if v <= 0.005 else "#c9861a" if v <= 0.01 else "#c0392b" for v in df_wf["delta_te"]]
            fig_delta = go.Figure()
            fig_delta.add_trace(go.Bar(x=df_wf["label"], y=df_wf["delta_te"] * 100,
                marker_color=colors_d,
                text=[f"{v * 100:+.2f}%" for v in df_wf["delta_te"]], textposition="outside"))
            fig_delta.add_hline(y=0, line_color="#e5e7eb")
            fig_delta.update_layout(**PLOTLY_LAYOUT, height=260,
                title="Delta TE = OOS − IS (détection d'overfitting)",
                xaxis_tickangle=-25, yaxis_title="Delta TE (%)", showlegend=False,
                annotations=[dict(x=0.5, y=1.05, xref="paper", yref="paper",
                    text="Vert = stable · Orange = attention · Rouge = overfitting",
                    showarrow=False, font=dict(size=11, color="#7d8fa3"))])
            st.plotly_chart(fig_delta, width='stretch')

            df_wf_disp = df_wf.copy()
            for c in ["te_oos", "te_is", "td_oos", "delta_te"]:
                if c in df_wf_disp.columns:
                    df_wf_disp[c] = df_wf_disp[c].map(lambda v: pct(v, "td" in c, 2))
            st.dataframe(df_wf_disp.rename(columns={
                "label": "Période", "te_oos": "TE OOS", "te_is": "TE IS",
                "td_oos": "TD OOS", "delta_te": "Delta TE",
            })[[c for c in ["Période", "TE OOS", "TE IS", "TD OOS", "Delta TE"] if c in df_wf_disp.rename(columns={"label":"Période","te_oos":"TE OOS","te_is":"TE IS","td_oos":"TD OOS","delta_te":"Delta TE"}).columns]],
            width='stretch', hide_index=True)

    elif _bsec == "methodologie":
        _section("Méthodologie — Formules du backtest et du live")
        st.caption("Toutes les formules utilisées dans le backtest et le système live. "
                   "Les indices i désignent les titres du panier, t les jours ouvrés.")

        def _lx(title, formula, legend=None, note=None):
            st.markdown(f"**{title}**")
            st.latex(formula)
            if legend:
                st.caption("Légende — " + "  ·  ".join(legend))
            if note:
                st.caption(note)
            st.markdown("")

        st.markdown("---")
        st.markdown("#### Backtest — Construction de la NAV")

        _lx("Valeur mark-to-market des positions (nombre d'actions fixe entre rebals)",
            r"V_i^t = V_i^{t-1} \times \frac{P_i^t}{P_i^{t-1}} \qquad "
            r"w_i^{t-1} = \frac{V_i^{t-1}}{\displaystyle\sum_j V_j^{t-1}}",
            legend=[
                "V_i^t = valeur de la position sur le titre i au jour t (en fraction de la NAV)",
                "P_i^t = prix de clôture du titre i au jour t (source : Sika Finance, non ajusté dividendes)",
                "w_i^t = poids effectif du titre i au jour t (dérive librement entre deux rebalancements)",
            ],
            note="À chaque rebalancement, V_i est réinitialisé à w_i^cible. "
                 "Entre deux rebals, les poids dérivent avec les prix — ETF physique buy-and-hold.")

        _lx("Rendement journalier effectif (99% panier + 1% poche de liquidité)",
            r"r_t = (1 - c_{\text{cash}}) \cdot \underbrace{\sum_i w_i^{t-1} \cdot \left(\frac{P_i^t}{P_i^{t-1}} - 1\right)}_{r_{\text{panier}}} + c_{\text{cash}} \cdot r_{\text{RF}}",
            legend=[
                "r_t = rendement journalier effectif de l'ETF au jour t",
                "c_cash = poche de liquidité = 1 % du NAV, tenue en cash",
                "r_panier = rendement mark-to-market du panier de titres (99 % de l'AUM)",
                "r_RF = rendement journalier sans risque = (1 + 3%/an)^{1/252} − 1 ≈ 0,0118 %/j",
                "w_i^{t-1} = poids effectif de la veille (après dérive mark-to-market)",
            ],
            note="La poche de 1 % facilite les flux de souscription/rachat et les frais. "
                 "Elle est capitalisée au taux UEMOA (3 %/an). Seuls les titres avec prix valide à J et J-1 contribuent.")

        _lx("Coût de transaction à chaque rebalancement (spread variable par titre)",
            r"\text{cost\_rebal} = \sum_k \left|w_k^{\text{new}} - w_k^{\text{drift}}\right| \times s_k \div 2",
            legend=[
                "s_k = spread one-way du titre k selon son ADV : 25 bps (ADV ≥ 100 MFCFA), 40 bps (≥ 30), 80 bps (≥ 10), 125 bps (≥ 5), 175 bps (< 5 MFCFA)",
                "w_k^new = poids cible du titre k après rebalancement",
                "w_k^drift = poids effectif du titre k juste avant rebalancement (après dérive mark-to-market)",
                "÷ 2 = conversion en turnover one-way (achats = ventes, on compte une seule fois)",
            ],
            note="Le spread variable reflète la liquidité réelle de la BRVM : les gros titres (SNTS, ORAC) "
                 "coûtent 25 bps, les petits titres peu liquides jusqu'à 175 bps. "
                 "Top 5 OTC : le spread s'applique sur les deltas uniquement (pas la position totale).")

        _lx("NAV brute (Price Return, après coûts de transaction)",
            r"\text{NAV\_gross}_t = \text{NAV\_gross}_{t-1} \times (1 + r_t) \times \begin{cases} (1 - \text{cost\_rebal}) & \text{si jour de rebalancement} \\ 1 & \text{sinon} \end{cases}",
            legend=[
                "NAV_gross_t = valeur liquidative brute au jour t (base 100 au 2023-01-02)",
                "r_t = rendement journalier du panier",
                "cost_rebal = coût de transaction du rebalancement (voir formule ci-dessus)",
            ],
            note="La NAV brute inclut les frictions de transaction mais pas les frais de gestion annuels.")

        _lx("NAV nette (après frais de gestion — formule récursive quotidienne)",
            r"\text{NAV\_net}_t = \text{NAV\_net}_{t-1} \times (1 + r_t) \times (1-f)^{\!\frac{1}{252}} "
            r"\times \begin{cases} (1 - \text{cost\_rebal}) & \text{si jour de rebalancement} \\ 1 & \text{sinon} \end{cases}",
            legend=[
                "NAV_net_t = valeur liquidative nette de frais au jour t (base 100 au 2023-01-02)",
                "f = taux de frais de gestion annuel = 0,6 %/an",
                "(1-f)^{1/252} = facteur de frais journalier appliqué chaque jour ouvré (~0,9976 par jour)",
                "r_t = rendement journalier du panier (mark-to-market)",
            ],
            note="Formule récursive : les frais s'accumulent jour après jour sans recalcul depuis J0. "
                 "Conforme à la pratique standard des fonds de gestion.")

        _lx("Dividendes reçus — réserve de distribution semestrielle",
            r"\text{Rés}_{t} = \left(\text{Rés}_{t-1} + \sum_i w_i^t \cdot \frac{d_i}{P_i^{t-1}} \cdot \text{NAV}_t\right) \times (1 + r_{\text{RF}})",
            legend=[
                "Rés_t = réserve de dividendes cumulée (en pts NAV), capitalisée quotidiennement au RF",
                "d_i = dividende brut versé par le titre i (en FCFA/action) — ex-date ≈ 1er juillet de l'année N+1 (convention BRVM : exercice Y payé en Y+1)",
                "P_i^{t-1} = prix de clôture de la veille (base de calcul du rendement dividende)",
                "w_i^t = poids effectif du titre i au jour de l'ex-date",
                "r_RF = (1 + 3%/an)^{1/252} − 1 — taux de placement de la réserve jusqu'à la distribution",
            ],
            note="L'ETF est un fonds à distribution (Price Return) — les dividendes NE sont PAS réinvestis dans la NAV. "
                 "Ils sont mis en réserve et versés aux porteurs le dernier jour ouvré de juin et de décembre. "
                 "La NAV reflète uniquement la performance prix du panier (hors dividendes reçus).")

        _lx("Benchmark Indice Dividende (Price Return)",
            r"\text{Bench}_t = \frac{\text{Dividende\_PR}_t}{\text{Dividende\_PR}_{t_0}} \times 100",
            legend=[
                "IndiceDividende_PR_t = valeur de l'Indice Dividende Price Return au jour t",
                "t_0 = premier jour du backtest (2023-01-02)",
                "Base 100 = valeur 100 au démarrage du backtest",
            ],
            note="Lu depuis l'Excel officiel BRVM (colonne PR). Aucun dividende réintégré — "
                 "cohérent avec l'ETF qui distribue les dividendes plutôt que de les capitaliser.")

        st.markdown("---")
        st.markdown("#### Backtest — Métriques de qualité")

        _lx("Tracking Error (TE) annualisée",
            r"\text{TE} = \sqrt{252} \times \sigma\!\left(r_t^{\text{ETF}} - r_t^{\text{Bench}}\right)",
            legend=[
                "TE = tracking error annualisée (mesure la volatilité de l'écart ETF vs indice)",
                "r_t^ETF = rendement journalier de la NAV nette de l'ETF",
                "r_t^Bench = rendement journalier de l'indice Indice Dividende",
                "σ = écart-type empirique des écarts journaliers (ddof=1)",
                "√252 = facteur d'annualisation (252 jours ouvrés par an)",
            ],
            note="Une TE de 2% signifie que l'ETF peut s'écarter de ±2% de l'indice sur un an.")

        _lx("Tracking Difference (TD) cumulée",
            r"\text{TD} = \frac{\text{NAV\_net}_T}{\text{Bench}_T} - 1",
            legend=[
                "TD = écart de performance cumulé entre l'ETF et son benchmark",
                "NAV_net_T = NAV nette au dernier jour T du backtest",
                "Bench_T = valeur du benchmark au dernier jour T (base 100)",
            ],
            note="Négatif si l'ETF sous-performe l'indice (attendu car frais + coûts de transaction). "
                 "Pour un ETF PR avec 0,6%/an de frais, une TD de -1% à -2%/an est normale.")

        _lx("Tracking Difference annualisée",
            r"\text{TD\_ann} = (1 + \text{TD})^{\,\frac{1}{n}} - 1 "
            r"\qquad n = \frac{T_{\text{last}} - T_{\text{first}}}{365{,}25} \text{ (années calendaires)}",
            legend=[
                "TD_ann = tracking difference ramenée à une année (pour comparer des périodes différentes)",
                "TD = tracking difference cumulée sur toute la période",
                "n = durée en années calendaires (ex. 3 ans et 6 mois → n = 3,5)",
                "T_last - T_first = nombre de jours calendaires entre le début et la fin du backtest",
                "365,25 = durée moyenne d'une année civile (tient compte des années bissextiles)",
            ],
            note="Convention standard des reporting de fonds : on utilise les jours calendaires réels, "
                 "pas 252 jours ouvrés — car les dividendes et frais courent aussi les weekends.")

        _lx("Turnover moyen par rebalancement",
            r"\text{Turnover} = \frac{1}{N-1}\sum_{j=1}^{N-1} \frac{1}{2}\sum_k \left|w_k^{j} - w_k^{j-1}\right|",
            legend=[
                "Turnover = fraction moyenne du panier renouvelée à chaque rebalancement",
                "N = nombre total de rebalancements sur le backtest",
                "w_k^j = poids du titre k dans le panier après le rebalancement j",
                "w_k^{j-1} = poids du titre k après le rebalancement précédent",
            ],
            note="One-way : un turnover de 10% signifie que 10% du panier est vendu (et 10% acheté). "
                 "Coût associé : 10% × spread_moyen (variable selon les titres tradés).")

        st.markdown("---")
        st.markdown("#### Règles de sélection du panier — Stratégie hybride OTC + ADV-cap")

        st.markdown(
            "**Stratégie hybride (depuis 2024) :**\n\n"
            "- **Principaux titres Dividende** (SNTS, ...) : tenus à leur poids Dividende exact "
            "via OTC (gré-à-gré). Aucune contrainte ADV — construction progressive en blocs OTC.\n"
            "- **25 titres restants** : sélection ADV-cap + redistribution classique. "
            "Exclus si ADV < 0,5 MFCFA/j ou poids résiduel < 0,1 %.\n\n"
            "**Rebalancement :** cible mise à jour trimestriellement (jan/avr/jul/oct). "
            "Vérification mensuelle : on ne trade que les titres dont |w_actuel − w_cible| > 1 % "
            "(seuil de dérive), ce qui réduit les frais inutiles.\n\n"
            "**Poche de liquidité :** 1 % du NAV tenu en cash (capitalisé au RF 3 %/an) — "
            "absorbe les flux de souscription/rachat sans toucher au panier."
        )
        st.markdown("")

        _lx("ADV — Average Daily Volume (volume journalier moyen, en M FCFA)",
            r"\text{ADV}_i = \frac{\displaystyle\sum_{j=1}^{N} \text{Vol}_j^i \times P_j^i \times 10^{-6}}{N}"
            r"\qquad N = \text{63 jours ouvrés avant le rebalancement}",
            legend=[
                "ADV_i = volume journalier moyen du titre i sur les 63 derniers jours ouvrés (en M FCFA)",
                "Vol_j^i = nombre de titres i échangés au jour j (source : Sika Finance)",
                "P_j^i = prix de clôture du titre i au jour j (en FCFA)",
                "N = taille de la fenêtre = 63 jours ouvrés (~3 mois), jours sans volume inclus",
            ],
            note="N inclut TOUS les jours de la fenêtre, y compris les jours à volume nul. "
                 "Cela évite de surestimer la liquidité des titres qui ne cotent que sporadiquement.")

        _lx("Stale ratio (taux de jours sans cotation)",
            r"\text{Stale}_i = \frac{\#\{j \in \text{fenêtre 63j} : \text{Vol}_j^i = 0\}}{\text{nb jours dans la fenêtre}}",
            legend=[
                "Stale_i = proportion de jours sans volume pour le titre i sur la fenêtre de 63j",
                "# {...} = nombre de jours vérifiant la condition Vol = 0",
            ],
            note="Titre exclu si Stale ≥ 70 % (moins de 30 % des jours avec une transaction). "
                 "Exception : les principaux titres Dividende (par capitalisation) sont tenus via OTC quoi qu'il arrive — le stale ratio ne s'applique pas à eux.")

        _lx("Plafond ADV — poids maximum exécutable en N jours (titres hors top 5 OTC)",
            r"\text{max\_w}_i = \min\!\left(\frac{20\% \times \text{ADV}_i \times N_i}{\text{AUM}},\ w_{\text{budget}}\right)",
            legend=[
                "max_w_i = poids maximum attribuable au titre i dans le panier ADV-capped",
                "20 % = taux de participation maximum (screen + petits blocs OTC)",
                "ADV_i = volume journalier moyen du titre i sur les 63 derniers jours (en M FCFA)",
                "N_i = 40 jours si w_i^{Dividende} ≥ 3 % (grand titre), sinon 20 jours (petit titre)",
                "AUM = actif sous gestion de référence (M FCFA)",
                "w_budget = 1 − Σ(poids des top 5 OTC) = budget disponible pour les 25 restants",
            ],
            note="Si le poids cible dépasse max_w_i, l'excédent est redistribué aux titres non-plafonnés. "
                 "Itération jusqu'à convergence (max 50 tours). Les top 5 titres ne sont PAS soumis à cette contrainte.")

        _lx("Poids minimum après redistribution (titres hors top 5 OTC)",
            r"w_i^{\text{rest}} = \frac{w_i^{\text{Dividende}}}{\displaystyle\sum_{k \in \text{restants}} w_k^{\text{Dividende}}} \times w_{\text{budget}} \geq 0{,}1\%",
            legend=[
                "w_i^rest = poids du titre i parmi les 25 titres ADV-capped (normalisé au budget restant)",
                "w_i^Dividende = poids brut du titre i dans l'indice Indice Dividende officiel",
                "w_budget = 1 − Σ(poids top 5 OTC) ≈ 40−50 % du panier",
            ],
            note="Si w_rest < 0,1 % → titre exclu et budget redistribué. "
                 "Les top 5 OTC sont toujours à leur poids Dividende exact — jamais exclus.")

        st.markdown("---")
        st.markdown("#### Bootstrap TE (N = 500 simulations)")

        st.markdown(
            "**Pourquoi un intervalle de confiance ?**  \n"
            "La TE instantanée (ex. 1,67 %) est calculée sur un historique précis (2023–2026). "
            "Mais cette valeur dépend de la période choisie : si le marché avait été plus volatile "
            "ou si la composition avait changé différemment, la TE aurait été différente. "
            "Le bootstrap répond à la question : *à quel point peut-on faire confiance à ce chiffre ?*  \n"
            "On tire 500 échantillons aléatoires (avec remise) dans les écarts historiques et on "
            "recalcule la TE à chaque fois. L'intervalle [P5, P95] montre la plage probable de la TE "
            "si l'histoire avait été légèrement différente.  \n"
            "**Interprétation** : intervalle étroit → TE stable, robuste. "
            "Intervalle large → TE sensible au régime de marché, à surveiller."
        )
        st.markdown("")

        _lx("Simulation par rééchantillonnage avec remise",
            r"\text{TE}^{(b)} = \sqrt{252} \times \sigma\!\left(\text{tirage}_{\text{remise}}\!\left\{r_t^{\text{ETF}} - r_t^{\text{Bench}}\right\}\right)",
            legend=[
                "TE^(b) = tracking error calculée sur le b-ième tirage aléatoire (1 tirage = 1 simulation)",
                "tirage_remise{...} = on pioche aléatoirement N écarts journaliers parmi les N historiques, avec remise (un même jour peut être pioché plusieurs fois)",
                "σ = écart-type empirique (ddof=1) du tirage",
                "√252 = annualisation",
            ],
            note="500 simulations, seed = 42 (résultats reproductibles). "
                 "L'intervalle [P5, P95] exclut les 5% de simulations les plus basses et les 5% les plus hautes.")

        st.markdown("---")
        st.markdown("#### Live — Calcul de la VL quotidienne")

        _lx("Rendement journalier live (mark-to-market)",
            r"r_{\text{jour}} = \sum_i \frac{w_i^{t-1}}{100} \times \frac{P_i^t}{P_i^{t-1}} - 1",
            legend=[
                "r_jour = rendement brut du portefeuille au jour t",
                "w_i^{t-1} = poids_pct du titre i stocké dans nav_latest.json (mis à jour chaque soir)",
                "P_i^t = dernier prix de clôture disponible du titre i (source : sika_history.json)",
                "P_i^{t-1} = prix stocké dans le champ dernier_prix du basket (prix du calcul précédent)",
            ],
            note="Les poids dérivent avec les prix entre deux rebalancements (mark-to-market). "
                 "Après chaque calcul, poids_pct et dernier_prix sont mis à jour dans nav_latest.json.")

        _lx("NAV indice live (nette de frais — formule récursive quotidienne)",
            r"\text{NAV\_indice}_t = \text{NAV\_indice}_{t-1} \times (1 + r_{\text{jour}}) \times (1-f)^{\!\frac{1}{252}}",
            legend=[
                "NAV_indice_t = valeur liquidative indice nette de frais au jour t",
                "NAV_indice_{t-1} = NAV du calcul précédent (stockée dans nav_latest.json)",
                "r_jour = rendement brut du portefeuille calculé ci-dessus",
                "f = taux de frais annuel = 0,6 %/an",
                "(1-f)^{1/252} = facteur de frais quotidien (~0,99998 par jour ouvré)",
            ],
            note="Même formule récursive que le backtest — cohérence garantie entre simulation et production.")

        _lx("VL par part",
            r"\text{VL}_t = \text{par} \times \frac{\text{NAV\_indice}_t}{\text{NAV\_indice}_{\text{lancement}}}",
            legend=[
                "VL_t = valeur liquidative par part en FCFA au jour t",
                "par = valeur nominale à l'émission = 100 000 FCFA",
                "NAV_indice_t = NAV indice du jour",
                "NAV_indice_lancement = NAV indice fixée au jour du lancement (19 juin 2026)",
            ],
            note="La VL par part est la valeur à laquelle les investisseurs souscrivent ou rachètent leurs parts.")

        _lx("AUM (Actif sous gestion, en M FCFA)",
            r"\text{AUM}_t = \text{VL}_t \times N_{\text{parts}} \times 10^{-6}",
            legend=[
                "AUM_t = actif sous gestion total au jour t (en millions de FCFA)",
                "VL_t = valeur liquidative par part en FCFA",
                "N_parts = nombre de parts en circulation = 50 000 parts",
                "10^{-6} = conversion FCFA → M FCFA",
            ])

        _lx("Performance depuis le lancement",
            r"\text{Perf}_{\text{lct}} = \frac{\text{NAV\_indice}_t}{\text{NAV\_indice}_{\text{lancement}}} - 1",
            legend=[
                "Perf_lct = performance cumulée nette de frais depuis le lancement",
                "NAV_indice_t = NAV indice du jour",
                "NAV_indice_lancement = NAV indice au jour du lancement (19 juin 2026)",
            ])

        _lx("ADV live (onglet Liquidité)",
            r"\text{ADV}_i^{\text{live}} = \frac{1}{N}\sum_{j \in \text{63j ouvr. avant aujourd'hui}} \text{Vol}_j^i \times P_j^i \times 10^{-6}",
            legend=[
                "ADV_i^live = volume journalier moyen du titre i calculé en temps réel",
                "Vol_j^i = volume échangé du titre i au jour j (nombre de titres)",
                "P_j^i = prix de clôture du titre i au jour j (en FCFA)",
                "N = 63 jours ouvrés avant aujourd'hui (tous les jours inclus, même sans volume)",
            ],
            note="Calculé à chaque chargement du dashboard depuis sika_history.json.")

        _lx("Jours d'exécution live",
            r"\text{exec\_days}_i^{\text{live}} = \frac{\text{pv\_mfcfa}_i}{\text{ADV}_i^{\text{live}}}",
            legend=[
                "exec_days_i^live = nombre de jours estimé pour liquider la position sur le titre i",
                "pv_mfcfa_i = valeur actuelle de la position sur le titre i (en M FCFA)",
                "ADV_i^live = volume journalier moyen du titre i sur les 63 derniers jours (en M FCFA)",
            ],
            note="Indicateur de liquidité opérationnelle : plus ce chiffre est élevé, "
                 "plus le titre est difficile à liquider rapidement sans impact marché.")

# ══════════════════════════════════════════════════════════════════════════════
# LIVE
# ══════════════════════════════════════════════════════════════════════════════
def _render_live():
    """Section live — ETF réel, iNAV, rebalancements, AP, analyse approfondie."""
    global _lsec

    alert_path        = os.path.join(HALAL_DIR, "new_rebal_alert.json")
    rebal_detail_path = os.path.join(HALAL_DIR, "rebal_detail.json")
    nav_latest_path   = os.path.join(HALAL_DIR, "nav_latest.json")
    intraday_path     = os.path.join(HALAL_DIR, "intraday_nav.json")

    # ── Live landing ──────────────────────────────────────────────────────────
    if not _lsec:
        _lsec = "situation"
    if False:

        st.markdown(f"""
        <div class="landing-outer" style="min-height:55vh">
            <p class="landing-brand">CGF BOURSE · Live</p>
            <h1 class="landing-title" style="font-size:1.7rem">ETF Dividende BRVM — Production</h1>
            <p class="landing-sub" style="margin-bottom:32px">Depuis le lancement · {_launch_date_label}</p>
            <div class="landing-cards" style="flex-wrap:wrap; justify-content:center; max-width:560px; gap:14px">
                <a href="?page=live&section=situation" class="lcard" target="_self">
                    <span class="lcard-tag lcard-tag-lv">Temps réel</span>
                    <span class="lcard-name">Situation actuelle</span>
                    <span class="lcard-desc">VL par part, AUM, performance depuis le lancement, iNAV intraday</span>
                    <span class="lcard-arrow">→</span>
                </a>
                <a href="?page=live&section=rebalancements" class="lcard" target="_self">
                    <span class="lcard-tag lcard-tag-lv">Opérations</span>
                    <span class="lcard-name">Rebalancements</span>
                    <span class="lcard-desc">Historique complet — entrées, sorties, trades, temps d'exécution</span>
                    <span class="lcard-arrow">→</span>
                </a>
                <a href="?page=live&section=ap" class="lcard" target="_self">
                    <span class="lcard-tag" style="color:#d1d5db">Inactif</span>
                    <span class="lcard-name">AP</span>
                    <span class="lcard-desc">Apports / rachats — aucune opération enregistrée pour l'instant</span>
                    <span class="lcard-arrow">→</span>
                </a>
                <a href="?page=live&section=analyse" class="lcard" target="_self">
                    <span class="lcard-tag lcard-tag-lv">Analytics</span>
                    <span class="lcard-name">Analyse approfondie</span>
                    <span class="lcard-desc">Graphiques détaillés, pipeline de mise à jour, alertes et logs</span>
                    <span class="lcard-arrow">→</span>
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Situation actuelle ────────────────────────────────────────────────────
    elif _lsec == "situation":
        alert = load_json_fresh(alert_path)
        if alert:
            st.error(f"Nouveau rebalancement détecté — {alert['rebal_date']} | {alert['n_tickers']} tickers | {alert.get('detected_at', '')}")
            with st.expander("Composition officielle OCR", expanded=True):
                col_al, col_ar = st.columns([2, 1])
                with col_al:
                    if alert.get("exits"):
                        st.markdown(f"**Sorties ({len(alert['exits'])}) :** {' · '.join(alert['exits'])}")
                    if alert.get("entries"):
                        st.markdown(f"**Entrées ({len(alert['entries'])}) :** {' · '.join(alert['entries'])}")
                    comp = sorted(alert.get("composition", []))
                    cols_comp = st.columns(5)
                    for i, t in enumerate(comp):
                        marker = "+" if t in alert.get("entries", []) else ("-" if t in alert.get("exits", []) else " ")
                        cols_comp[i % 5].markdown(f"`{marker}` {t}")
                with col_ar:
                    st.markdown("**Actions requises**")
                    st.markdown(str(alert.get("action_required", "")).replace("\n", "  \n"))
                st.markdown("---")
                col_v2, col_v3 = st.columns(2)
                with col_v2:
                    if st.button("Effacer l'alerte", width='stretch'):
                        try:
                            os.remove(alert_path); load_json_fresh.clear()
                            st.success("Alerte effacée."); st.rerun()
                        except Exception as e: st.error(str(e))
                with col_v3:
                    st.info(f"Source : {alert.get('pdf_slug', '—')}")

        splits = detect_recent_splits()
        if splits:
            tickers_str = ", ".join(f"{s['ticker']} (ratio {s['ratio']:.4f} le {s['date']})" for s in splits)
            st.warning(f"Ajustement de cours détecté (split/dividende) sur {len(splits)} titre(s) — {tickers_str}. Vérifier si le panier doit être recalculé.")


        @st.fragment
        def _live_fragment():
            nl       = load_json(nav_latest_path)
            intraday = load_json(intraday_path)
            launch   = load_json(os.path.join(HALAL_DIR, "launch_state.json"))
            _bm_snap = load_json(bm_path) or {}
            today_str      = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d")
            today_intraday = (intraday or {}).get("date") == today_str
            launched       = launch is not None
            launch_date    = launch["launch_date"] if launched else None

            last_snap = None
            if today_intraday and intraday.get("snapshots"):
                last_snap = intraday["snapshots"][-1]

            if last_snap:
                vl_val   = last_snap.get("vl_live_fcfa") or last_snap.get("vl_par_part")
                aum_val  = last_snap.get("aum_mfcfa")
                chg_jour = last_snap.get("change_day_pct") if last_snap.get("change_day_pct") is not None else last_snap.get("change_1d_pct")
                perf_lct = last_snap.get("perf_since_launch")
                ts_label = f"Aujourd'hui {last_snap['time']} UTC"
            elif nl:
                vl_val   = nl.get("vl_par_part_fcfa")
                aum_val  = nl.get("aum_mfcfa")
                chg_jour = None
                perf_lct = nl.get("perf_since_launch")
                ts_label = f"Cloture {nl.get('calc_date', '—')}"
            else:
                vl_val = aum_val = chg_jour = perf_lct = None
                ts_label = "—"

            age = (nl or {}).get("data_age_biz_days", 0)
            if age and age > 0 and not today_intraday:
                st.warning(f"Données vieilles de {age} jour(s). Dernier scraping : {(nl or {}).get('calc_date', '—')}")

            # ── Calcul TE / TD / MDD live (avant bandeau) ────────────────────
            import numpy as _np
            _brvm30_hist_te      = load_json(os.path.join(HALAL_DIR, "brvm30_index_history.json")) or {}
            _dividende_idx_at_launch_te = float(_brvm30_hist_te[launch_date]) if launch_date and launch_date in _brvm30_hist_te else (launch or {}).get("etfdividende_index_at_launch")
            _brvm30_now = None
            if _brvm30_hist_te:
                _te_snaps_early = (intraday or {}).get("snapshots", [])
                if _te_snaps_early:
                    _brvm30_now = _te_snaps_early[-1].get("dividende_index")
                if not _brvm30_now:
                    _brvm30_now = _brvm30_hist_te.get(today_str)
                if not _brvm30_now:
                    _brvm30_now = float(_brvm30_hist_te[max(_brvm30_hist_te.keys())])
            _perf_idx = (float(_brvm30_now) / _dividende_idx_at_launch_te - 1) * 100 if (_brvm30_now and _dividende_idx_at_launch_te) else None

            _launch_ts_te = pd.Timestamp(launch_date) if launch_date else pd.Timestamp("1900-01-01")
            _ih = load_json(os.path.join(HALAL_DIR, "nav_intraday_history.json")) or {}
            _closes_etf = {}
            _closes_idx = {}
            for _d, _pts in _ih.items():
                if _pts and pd.Timestamp(_d) >= _launch_ts_te:
                    _lp = _pts[-1]
                    _vl = _lp.get("vl_fcfa") or _lp.get("vl")
                    _bv = _lp.get("dividende_index")
                    if _vl: _closes_etf[_d] = float(_vl)
                    # Utiliser l'Indice Dividende du même snapshot que le VL (pas le lendemain matin)
                    if _bv:
                        _closes_idx[_d] = float(_bv)
                    elif _d in _brvm30_hist_te:
                        _closes_idx[_d] = float(_brvm30_hist_te[_d])
            _te_snaps = (intraday or {}).get("snapshots", [])
            if _te_snaps:
                _ls = _te_snaps[-1]
                _vl_now = _ls.get("vl_live_fcfa") or _ls.get("vl_par_part", 0)
                _bv_now = _ls.get("dividende_index")
                if _vl_now: _closes_etf[today_str] = float(_vl_now)
                if _bv_now: _closes_idx[today_str] = float(_bv_now)

            _te = _td = _n_seances = None
            _etf_cl = pd.Series(_closes_etf).sort_index()
            _idx_cl = pd.Series(_closes_idx).sort_index()
            _n_seances = len(_etf_cl)
            _MIN_REPR  = 30   # seuil de représentativité statistique
            if len(_etf_cl) >= 2 and len(_idx_cl) >= 2:
                _ret_etf = _etf_cl.pct_change().dropna()
                _ret_idx = _idx_cl.pct_change().dropna()
                _common  = _ret_etf.index.intersection(_ret_idx.index)
                if len(_common) >= 1:
                    _active = _ret_etf.loc[_common] - _ret_idx.loc[_common]
                    _te = float(_active.std(ddof=1) * _np.sqrt(252) * 100) if len(_common) >= 2 else float(abs(_active.iloc[0]) * _np.sqrt(252) * 100)
                if _dividende_idx_at_launch_te and not _etf_cl.empty and not _idx_cl.empty:
                    _par_te  = float((launch or {}).get("par_fcfa", 100000))
                    _etf_cum = _etf_cl.iloc[-1] / _par_te
                    _idx_cum = _idx_cl.iloc[-1] / _dividende_idx_at_launch_te
                    _td = (_etf_cum / _idx_cum - 1) * 100

            _live_cagr = _live_sharpe = _live_maxdd = None
            if len(_etf_cl) >= 2:
                _ret_live  = _etf_cl.pct_change().dropna()
                _total_ret = _etf_cl.iloc[-1] / _etf_cl.iloc[0] - 1
                _n_live    = len(_etf_cl)
                _live_cagr = ((1 + _total_ret) ** (252 / _n_live) - 1) * 100
                if _ret_live.std() > 0:
                    _live_sharpe = float(_ret_live.mean() / _ret_live.std() * (252 ** 0.5))
                _roll_max   = _etf_cl.cummax()
                _live_maxdd = float(((_etf_cl - _roll_max) / _roll_max * 100).min())
            elif len(_etf_cl) == 1:
                _live_maxdd = 0.0

            # * = données < 30 séances : chiffres affichés mais non représentatifs
            _non_repr = _n_seances is not None and _n_seances < _MIN_REPR
            _nr_note  = ' <span style="font-size:0.55rem;color:#c9861a;font-style:normal">*</span>' if _non_repr else ""
            _te_str   = (f"{_te:.2f}%{_nr_note}" if _te is not None else "—")
            _td_str   = (f"{_td:+.3f}% ({_td*100:+.0f} bps){_nr_note}" if _td is not None else "—")

            # ── Bandeau synthétique (vue d'ensemble rapide) ───────────────────
            if nl or (intraday and (intraday or {}).get("snapshots")):
                _snap_s = ((intraday or {}).get("snapshots") or [{}])[-1]
                _vl_s   = _snap_s.get("vl_live_fcfa") or (nl or {}).get("vl_par_part_fcfa")
                _aum_s  = _snap_s.get("aum_mfcfa") or (nl or {}).get("aum_mfcfa")
                _perf_s = _snap_s.get("perf_since_launch") or (nl or {}).get("perf_since_launch")
                _te_s   = _te          # live, pas backtest
                _max_s  = _live_maxdd  # live, pas backtest
                _nb_s   = len((nl or {}).get("basket") or [])
                _te_alert = _te_s is not None and _te_s > 2.5 and not _non_repr
                _bg_te    = "background:#fdf3f2;border-left:2px solid #c0392b" if _te_alert else "background:#f3faf6;border-left:2px solid #2d7a4f"
                st.markdown(f"""
                <div style="display:flex;gap:0;margin-bottom:20px;
                             background:#ffffff;border:1px solid #e0dbd2;flex-wrap:wrap;align-items:stretch;
                             box-shadow:0 2px 8px rgba(12,26,46,0.07);overflow:hidden">
                  <div style="min-width:140px;padding:16px 24px;border-right:1px solid #ede9e2">
                    <div style="font-size:0.54rem;color:#7d8fa3;text-transform:uppercase;letter-spacing:.16em;margin-bottom:6px;font-weight:600">VL / part</div>
                    <div style="font-family:'Cormorant Garamond',Georgia,serif;font-size:1.5rem;font-weight:500;color:#0c1a2e;font-style:italic">{f"{_vl_s:,.0f} FCFA" if _vl_s else "—"}</div>
                  </div>
                  <div style="min-width:140px;padding:16px 24px;border-right:1px solid #ede9e2">
                    <div style="font-size:0.54rem;color:#7d8fa3;text-transform:uppercase;letter-spacing:.16em;margin-bottom:6px;font-weight:600">AUM</div>
                    <div style="font-family:'Cormorant Garamond',Georgia,serif;font-size:1.5rem;font-weight:500;color:#0c1a2e;font-style:italic">{f"{_aum_s:,.1f} M FCFA" if _aum_s else "—"}</div>
                  </div>
                  <div style="min-width:140px;padding:16px 24px;border-right:1px solid #ede9e2">
                    <div style="font-size:0.54rem;color:#7d8fa3;text-transform:uppercase;letter-spacing:.16em;margin-bottom:6px;font-weight:600">Perf. lancement</div>
                    <div style="font-family:'Cormorant Garamond',Georgia,serif;font-size:1.5rem;font-weight:500;font-style:italic;color:{'#2d7a4f' if (_perf_s or 0)>=0 else '#c0392b'}">{f"{_perf_s:+.2f}%" if _perf_s is not None else "—"}</div>
                  </div>
                  <div style="min-width:140px;padding:16px 24px;border-right:1px solid #ede9e2;{_bg_te}">
                    <div style="font-size:0.54rem;color:#7d8fa3;text-transform:uppercase;letter-spacing:.16em;margin-bottom:6px;font-weight:600">TE annualisée</div>
                    <div style="font-family:'Cormorant Garamond',Georgia,serif;font-size:1.5rem;font-weight:500;font-style:italic;color:{'#c0392b' if _te_alert else '#0c1a2e'}">{f"{_te_s:.2f}% {'' if _te_alert else ''}" if _te_s is not None else "—"}</div>
                  </div>
                  <div style="min-width:140px;padding:16px 24px;border-right:1px solid #ede9e2">
                    <div style="font-size:0.54rem;color:#7d8fa3;text-transform:uppercase;letter-spacing:.16em;margin-bottom:6px;font-weight:600">Max Drawdown</div>
                    <div style="font-family:'Cormorant Garamond',Georgia,serif;font-size:1.5rem;font-weight:500;color:#0c1a2e;font-style:italic">{f"{_max_s:.2f}%" if _max_s is not None else "—"}</div>
                  </div>
                  <div style="min-width:100px;padding:16px 24px">
                    <div style="font-size:0.54rem;color:#7d8fa3;text-transform:uppercase;letter-spacing:.16em;margin-bottom:6px;font-weight:600">Titres</div>
                    <div style="font-family:'Cormorant Garamond',Georgia,serif;font-size:1.5rem;font-weight:500;color:#0c1a2e;font-style:italic">{_nb_s or "—"}</div>
                  </div>
                  <div style="margin-left:auto;padding:16px 24px;display:flex;align-items:center">
                    <span style="font-size:0.6rem;color:#7d8fa3;letter-spacing:0.08em;text-transform:uppercase">{today_str} &nbsp;·&nbsp; ↻ 5 min</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

            _n_parts = int((nl or {}).get("n_parts", 0) or (launch or {}).get("n_parts", 0))

            # ── Alerte TE > 2.5% ──────────────────────────────────────────────
            _te_early = _bm_snap.get("tracking_error_pct")
            if _te_early is not None and _te_early > 2.5:
                _alert_cfg_te = load_json(os.path.join(HALAL_DIR, "alert_config.json")) or {}
                if _alert_cfg_te.get("enabled"):
                    try:
                        import subprocess as _sp_te
                        _sp_te.Popen(
                            [sys.executable, os.path.join(HALAL_DIR, "send_alert.py"), "--force"],
                            creationflags=0x08000000 if sys.platform == "win32" else 0,
                        )
                    except Exception:
                        pass
                st.error(f"Tracking Error élevée : {_te_early:.2f}% ({_te_early*100:.0f} bps) — seuil 2.5% dépassé. "
                         f"{'Email d\'alerte envoyé.' if _alert_cfg_te.get('enabled') else 'Activez les alertes email dans la config.'}")

            # (_bm conservé pour l'alerte TE uniquement — pas affiché dans les KPI)
            _bm = _bm_snap

            # ── Rebalancement ──────────────────────────────────────────────────
            _last_rebal_str  = (nl or {}).get("last_rebal_date")
            _progress_pct    = _days_remaining = _next_rebal_str = None
            _last_rebal_dt   = _next_rebal_dt  = None
            if _last_rebal_str:
                from dateutil.relativedelta import relativedelta
                _last_rebal_dt  = pd.Timestamp(_last_rebal_str)
                _next_rebal_dt  = _last_rebal_dt + relativedelta(months=12)
                while _next_rebal_dt.weekday() >= 5:
                    _next_rebal_dt += pd.Timedelta(days=1)
                _today_dt       = pd.Timestamp.now().normalize()
                _days_remaining = (_next_rebal_dt - _today_dt).days
                _cycle_days     = (_next_rebal_dt - _last_rebal_dt).days
                _elapsed_days   = (_today_dt - _last_rebal_dt).days
                _progress_pct   = min(100, max(0, int(_elapsed_days / _cycle_days * 100))) if _cycle_days > 0 else 0
                _next_rebal_str = _next_rebal_dt.strftime("%d/%m/%Y")
                _dr_color       = "#c0392b" if _days_remaining <= 14 else "#c9861a" if _days_remaining <= 30 else "#2d7a4f"

            # ── Panneau KPI grille complète ────────────────────────────────────
            def _kc(lbl, val, color=None, sub=None):
                vs = f"color:{color};" if color else ""
                sh = f'<span style="font-size:0.64rem;color:#7d8fa3;margin-left:6px">{sub}</span>' if sub else ""
                return (f'<div class="kc"><div class="kc-l">{lbl}</div>'
                        f'<div class="kc-v" style="{vs}">{val}{sh}</div></div>')

            _pc = "#2d7a4f" if (perf_lct or 0) >= 0 else "#c0392b"
            _ic = "#2d7a4f" if (_perf_idx or 0) >= 0 else "#c0392b"
            _vc = "#2d7a4f" if (chg_jour or 0) >= 0 else "#c0392b"
            _dc = "#2d7a4f" if (_td or 0) >= 0 else "#c0392b"

            # Ligne 1 : carte unique (infos non dupliquées depuis la barre du haut)
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-card-hd">Portefeuille — {ts_label}
                <span style="font-weight:400;color:#7d8fa3;font-size:0.6rem;margin-left:8px">ETF vs Indice Dividende BRVM</span>
              </div>
              <div style="display:flex;flex-wrap:wrap">
                {_kc("Variation jour", f"{chg_jour:+.3f}%" if chg_jour is not None else "—", color=_vc)}
                {_kc("Parts émises", f"{_n_parts:,}" if _n_parts else "—")}
                {_kc("Indice Dividende (même pér.)", f"{_perf_idx:+.2f}%" if _perf_idx is not None else "—", color=_ic)}
                {_kc("Tracking Diff.", _td_str, color=_dc)}
              </div>
            </div>""", unsafe_allow_html=True)

            # Ligne 2 : Rebalancement (pleine largeur)
            if _progress_pct is not None:
                _dr_txt = f"{_days_remaining}j" if _days_remaining >= 0 else "Dépassé"
                st.markdown(f"""
                <div class="kpi-card">
                  <div class="kpi-card-hd">Rebalancement ETFDividende</div>
                  <div style="display:flex;flex-wrap:wrap">
                    {_kc("Dernier", _last_rebal_dt.strftime("%d/%m/%Y"))}
                    {_kc("Prochain (est.)", _next_rebal_str)}
                    {_kc("Jours restants", _dr_txt, color=_dr_color)}
                    {_kc("Avancement", f"{_progress_pct}%")}
                  </div>
                  <div style="padding:0 22px 14px">
                    <div style="height:3px;background:#e0dbd2;border-radius:1px;overflow:hidden">
                      <div style="height:100%;width:{_progress_pct}%;background:linear-gradient(90deg,#b8973f,#d4b96a);border-radius:1px"></div>
                    </div>
                    <div style="display:flex;justify-content:space-between;margin-top:5px">
                      <span style="font-size:0.58rem;color:#7d8fa3">{_last_rebal_dt.strftime("%d/%m/%Y")}</span>
                      <span style="font-size:0.58rem;color:#b8973f;font-weight:600">{_progress_pct}%</span>
                      <span style="font-size:0.58rem;color:#7d8fa3">{_next_rebal_str}</span>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="kpi-card">
                  <div class="kpi-card-hd">Rebalancement ETFDividende</div>
                  <div style="padding:20px 22px;color:#7d8fa3;font-size:0.75rem">Données indisponibles</div>
                </div>""", unsafe_allow_html=True)

            # ── Dividendes (Ligne 3) ───────────────────────────────────────────
            _dlog_s   = load_json(os.path.join(HALAL_DIR, "dividend_log.json")) or {}
            _sika_s   = load_json(os.path.join(HALAL_DIR, "sika_dividendes.json")) or {}
            _basket_s = {b["ticker"] for b in (nl or {}).get("basket", [])}
            _today_s  = pd.Timestamp.now().strftime("%Y-%m-%d")
            _launch_s = (launch or {}).get("launch_date", "")
            _all_s    = _sika_s.get("dividendes", [])
            _rec_s    = [d for d in _all_s if d.get("ticker") in _basket_s
                         and d.get("date_detach") and _launch_s <= d["date_detach"] <= _today_s]
            _fut_s    = [d for d in _all_s if d.get("ticker") in _basket_s
                         and d.get("date_detach") and d["date_detach"] > _today_s]
            _pre_s    = [d for d in _all_s if d.get("ticker") in _basket_s
                         and d.get("date_detach") and d["date_detach"] < _launch_s]
            _dist_s   = _dlog_s.get("distribution_date", "2026-09-30")
            _distr_ok_s = _dlog_s.get("distribue", False)
            _dist_lbl_s = ("DISTRIBUE" if _distr_ok_s
                           else pd.Timestamp(_dist_s).strftime("%d/%m/%Y") if _dist_s else "30/09")
            _dpp_s    = _dlog_s.get("dividende_par_part_fcfa", 0) or 0
            _rend_s   = _dlog_s.get("rendement_distribution") or 0
            _cash_s   = _dlog_s.get("total_cash_fcfa", 0) or 0
            _trf_s    = _dlog_s.get("taux_rf_annuel", 0.03) * 100
            _col_s    = "#2d7a4f" if _distr_ok_s else "#b8973f"
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-card-hd">Dividendes — Distribution : <span style="color:{_col_s}">{_dist_lbl_s}</span></div>
              <div style="display:flex;flex-wrap:wrap">
                {_kc("Div. / part (estimé)", f"{_dpp_s:,.0f} FCFA" if _dpp_s else "—", color="#b8973f" if _dpp_s else None)}
                {_kc("Rendement dist.", f"{_rend_s:.2f}%" if _rend_s else "—", color="#2d7a4f" if _rend_s else None)}
                {_kc("Cash collecté", f"{_cash_s/1e6:.3f} M FCFA" if _cash_s else "—")}
                {_kc("Reçus ETF", f"{len(_rec_s)} titre(s)" if _rec_s else "—")}
                {_kc("À détacher (panier)", f"{len(_fut_s)} titre(s)", color="#c9861a" if _fut_s else None)}
                {_kc("Taux RF (UEMOA)", f"{_trf_s:.1f}%")}
              </div>
            </div>""", unsafe_allow_html=True)

            if nl and launched:
                par       = float((launch or {}).get("par_fcfa", 100000))
                nav_anch  = float((launch or {}).get("nav_index_at_launch") or 100)
                launch_dt = pd.Timestamp(launch_date) if launch_date else None

                # Charger historique intraday multi-sessions (15 min par point)
                intra_hist_path = os.path.join(HALAL_DIR, "nav_intraday_history.json")
                intra_hist = load_json(intra_hist_path) or {}

                # Charger historique de l'indice Indice Dividende officiel
                _brvm30_hist_path = os.path.join(HALAL_DIR, "brvm30_index_history.json")
                _brvm30_hist = load_json(_brvm30_hist_path) or {}
                # Valeur de référence = clôture indice Dividende le jour du lancement
                # Priorité à brvm30_index_history.json (clôture officielle) pour cohérence avec le KPI TD
                _dividende_idx_at_launch = None
                if _brvm30_hist and launch_date:
                    _v = _brvm30_hist.get(launch_date)
                    if _v:
                        _dividende_idx_at_launch = float(_v)
                if not _dividende_idx_at_launch:
                    _dividende_idx_at_launch = (launch or {}).get("etfdividende_index_at_launch")

                # Construire série : dernier point par session >= launch_date uniquement
                _launch_ts = pd.Timestamp(launch_date) if launch_date else pd.Timestamp("1900-01-01")
                all_pts = {}
                for _day, _pts in intra_hist.items():
                    if _pts and pd.Timestamp(_day) >= _launch_ts:
                        _last = _pts[-1]
                        _ts = pd.Timestamp(_day + " " + _last["time"])
                        all_pts[_ts] = float(_last["vl"])

                # Ajouter le dernier snapshot du jour courant
                intra_snaps = (intraday or {}).get("snapshots", [])
                intra_date  = (intraday or {}).get("date", "")
                snap_series = pd.Series(dtype=float)
                if intra_snaps and intra_date:
                    _last_s = intra_snaps[-1]
                    _ts = pd.Timestamp(intra_date + " " + _last_s["time"])
                    vl_s = _last_s.get("vl_live_fcfa") or (_last_s["nav_indice"] / nav_anch * par)
                    all_pts[_ts] = vl_s
                    snap_series = pd.Series({_ts: 1}, dtype=float)

                combined = pd.Series(all_pts).sort_index()
                combined = combined[~combined.index.duplicated(keep="last")]

                # Fallback si pas d'historique intraday : points journaliers
                if combined.empty and nl.get("nav_live_series"):
                    nlive = pd.DataFrame(nl["nav_live_series"], columns=["date", "value"])
                    nlive["date"] = pd.to_datetime(nlive["date"])
                    combined = nlive.set_index("date")["value"]

                # Insérer des NaN entre sessions distantes (nuit/week-end) pour couper la ligne
                def _break_sessions(s, gap_h = 3.0):
                    if len(s) < 2:
                        return s
                    diffs = pd.Series(s.index).diff().iloc[1:].values
                    threshold = pd.Timedelta(hours=gap_h)
                    gap_positions = [s.index[i+1] for i, d in enumerate(diffs) if d > threshold]
                    if not gap_positions:
                        return s
                    nan_idx = [ts - pd.Timedelta(minutes=1) for ts in gap_positions]
                    nans = pd.Series(float('nan'), index=nan_idx)
                    return pd.concat([s, nans]).sort_index()

                # ── Construction des deux séries graphiques ───────────────────
                fig_main = go.Figure()
                if not combined.empty:
                    combined_plot = _break_sessions(combined)
                    _vmin = combined.min()
                    _vmax = combined.max()
                    _pad  = (_vmax - _vmin) * 0.2 if _vmax > _vmin else par * 0.02
                    fig_main.add_trace(go.Scatter(
                        x=combined_plot.index, y=combined_plot.values,
                        name="VL par part (FCFA)",
                        mode="lines+markers",
                        line=dict(color=COLOR, width=2.5),
                        marker=dict(size=4, color=COLOR, symbol="circle"),
                        connectgaps=False,
                        hovertemplate="%{x|%d/%m %H:%M}<br><b>%{y:,.0f} FCFA</b><extra></extra>",
                    ))
                    fig_main.add_hline(y=par, line_dash="dot", line_color="#ccc5b9",
                                       annotation_text=f"Émission {par:,.0f}")
                    fig_main.update_layout(**PLOTLY_LAYOUT, height=380,
                        title=f"VL CGF ETF Dividende BRVM — depuis le {launch_date}",
                        yaxis_title="FCFA / part", hovermode="x unified",
                        yaxis_range=[_vmin - _pad, _vmax + _pad],
                        legend=dict(orientation="h", y=-0.14))
                    fig_main.update_xaxes(
                        tickformat="%d/%m %H:%M" if not snap_series.empty else "%d/%m"
                    )

                _t0 = pd.Timestamp(launch_date).normalize()
                _live_ser = nl.get("nav_live_series") or []
                _etf_pts  = {_t0: 100.0}
                for _d, _v in _live_ser:
                    _dt = pd.Timestamp(_d).normalize()
                    if _dt > _t0:
                        _etf_pts[_dt] = float(_v) / par * 100
                # Compléter avec les derniers snapshots intraday des jours passés
                for _d, _dpts in intra_hist.items():
                    _dt = pd.Timestamp(_d).normalize()
                    if _dpts and _dt > _t0:
                        _lp = _dpts[-1]
                        _vl_d = _lp.get("vl_fcfa") or _lp.get("vl")
                        if _vl_d:
                            _etf_pts[_dt] = float(_vl_d) / par * 100
                if intra_snaps:
                    _last_s = intra_snaps[-1]
                    _vl_s   = _last_s.get("vl_live_fcfa") or (_last_s["nav_indice"] / nav_anch * par)
                    _dt = pd.Timestamp(intra_date).normalize()
                    if _dt > _t0:
                        _etf_pts[_dt] = float(_vl_s) / par * 100
                _idx_pts = {}
                if _dividende_idx_at_launch:
                    _idx_pts[_t0] = 100.0
                    for _d, _bv in _brvm30_hist.items():
                        _dt = pd.Timestamp(_d).normalize()
                        if _dt > _t0 and _dt.weekday() < 5:
                            _idx_pts[_dt] = float(_bv) / _dividende_idx_at_launch * 100
                    # Fallback : jours manquants depuis le dernier snapshot intraday
                    for _d, _snaps in intra_hist.items():
                        _dt = pd.Timestamp(_d).normalize()
                        if _dt in _idx_pts or _dt <= _t0 or _dt.weekday() >= 5 or not _snaps:
                            continue
                        for _s in reversed(_snaps):
                            _v = _s.get("dividende_index")
                            if _v:
                                _idx_pts[_dt] = float(_v) / _dividende_idx_at_launch * 100
                                break
                    if intra_snaps:
                        _bv_live = intra_snaps[-1].get("dividende_index")
                        _dt = pd.Timestamp(intra_date).normalize()
                        if _bv_live and _dt > _t0:
                            _idx_pts[_dt] = float(_bv_live) / _dividende_idx_at_launch * 100
                etf_s = pd.Series(_etf_pts).sort_index()
                idx_s = pd.Series(_idx_pts).sort_index()

                fig_cmp = None
                if not etf_s.empty:
                    fig_cmp = go.Figure()
                    fig_cmp.add_trace(go.Scatter(
                        x=etf_s.index, y=etf_s.values,
                        name="CGF ETF Dividende BRVM",
                        mode="lines+markers",
                        line=dict(color=COLOR, width=2.5),
                        marker=dict(size=6, color=COLOR),
                        hovertemplate="%{x|%d/%m}<br><b>ETF : %{y:.2f}</b><extra></extra>",
                    ))
                    if not idx_s.empty:
                        fig_cmp.add_trace(go.Scatter(
                            x=idx_s.index, y=idx_s.values,
                            name="Indice Dividende",
                            mode="lines+markers",
                            line=dict(color=BENCH_COLOR, width=2, dash="dash"),
                            marker=dict(size=6, color=BENCH_COLOR),
                            hovertemplate="%{x|%d/%m}<br><b>Indice Dividende : %{y:.2f}</b><extra></extra>",
                        ))
                    fig_cmp.add_hline(y=100, line_dash="dot", line_color="#ccc5b9",
                                      annotation_text="Base 100 au lancement")
                    fig_cmp.update_layout(**PLOTLY_LAYOUT, height=380,
                        title=f"ETF vs Indice Dividende — base 100 depuis le {launch_date}",
                        yaxis_title="Base 100", hovermode="x unified",
                        legend=dict(orientation="h", y=-0.14))
                    fig_cmp.update_xaxes(tickformat="%d/%m")

                # ── Graphique ETF vs Indice Dividende pleine largeur ────────────────────
                _section("ETF vs Indice Dividende — base 100")
                if fig_cmp is not None:
                    st.plotly_chart(fig_cmp, width='stretch')
                    st.caption("Base 100 = prix d'émission le jour du lancement.")

                # ── Tableau récapitulatif (expander pleine largeur) ───────────
                if fig_cmp is not None:
                    _raw_vl  = {}
                    _raw_ni  = {}
                    _raw_vl[_t0] = par
                    _raw_ni[_t0] = _dividende_idx_at_launch if _dividende_idx_at_launch else None
                    # Historique intraday : dernier snapshot de chaque jour
                    for _d, _pts in intra_hist.items():
                        _dt = pd.Timestamp(_d).normalize()
                        if _pts and _dt > _t0:
                            _lp = _pts[-1]
                            _v  = _lp.get("vl_fcfa") or _lp.get("vl")
                            if _v: _raw_vl[_dt] = float(_v)
                    # Indice Indice Dividende officiel depuis brvm30_index_history.json (jours ouvrés uniquement)
                    for _d, _bv in _brvm30_hist.items():
                        _dt = pd.Timestamp(_d).normalize()
                        if _dt >= _t0 and _dt.weekday() < 5:
                            _raw_ni[_dt] = float(_bv)
                    # Fallback : jours manquants comblés depuis le dernier snapshot intraday
                    # (couvre le délai de ~1 jour entre clôture du marché et workflow nocturne)
                    for _d, _snaps in intra_hist.items():
                        _dt = pd.Timestamp(_d).normalize()
                        if _dt in _raw_ni or _dt < _t0 or _dt.weekday() >= 5 or not _snaps:
                            continue
                        for _s in reversed(_snaps):
                            _v = _s.get("dividende_index")
                            if _v:
                                _raw_ni[_dt] = float(_v)
                                break
                    # nav_live_series (VL de clôture calc_nav) écrase si dispo — source du graphique
                    for _d, _v in (_live_ser or []):
                        _dt = pd.Timestamp(_d).normalize()
                        if _dt > _t0:
                            _raw_vl[_dt] = float(_v)
                    # Snapshot live du jour
                    if intra_snaps:
                        _ls2 = intra_snaps[-1]
                        _dt2 = pd.Timestamp(intra_date).normalize()
                        if _dt2 > _t0:
                            _v2 = _ls2.get("vl_live_fcfa") or (_ls2.get("nav_indice", 0) / nav_anch * par)
                            _n2 = _ls2.get("dividende_index")   # indice officiel Dividende, pas nav_indice
                            if _v2: _raw_vl[_dt2] = float(_v2)
                            if _n2: _raw_ni[_dt2] = float(_n2)

                    _all_dates = sorted(set(list(_raw_vl.keys()) + list(_raw_ni.keys())))
                    _tbl_rows  = []
                    for _dt in _all_dates:
                        _vl_r = _raw_vl.get(_dt)
                        _ni_r = _raw_ni.get(_dt)
                        _b100_etf = float(_vl_r) / par * 100                   if _vl_r else None
                        _b100_idx = float(_ni_r) / _dividende_idx_at_launch * 100 if (_ni_r and _dividende_idx_at_launch) else None
                        if _dt == _t0:
                            _b100_etf = 100.0
                            _b100_idx = 100.0
                        _tbl_rows.append({
                            "Date":            _dt.strftime("%d/%m/%Y"),
                            "VL ETF (FCFA)":        f"{_vl_r:,.0f}" if _vl_r else "—",
                            "Indice Dividende (pts)":  f"{_ni_r:.2f}"  if _ni_r  else "—",
                            "ETF base 100":    f"{_b100_etf:.2f}" if _b100_etf is not None else "—",
                            "Indice Dividende base 100": f"{_b100_idx:.2f}" if _b100_idx is not None else "—",
                        })
                    if _tbl_rows:
                        with st.expander("Données brutes — VL ETF & Indice Indice Dividende", expanded=False):
                            st.dataframe(
                                pd.DataFrame(_tbl_rows).set_index("Date"),
                                width='stretch',
                            )

                # ── Écart de suivi cumulé (ETF − Indice Dividende base 100) ────────────
                if not etf_s.empty and not idx_s.empty:
                    _com_gap = etf_s.index.intersection(idx_s.index)
                    if len(_com_gap) >= 2:
                        _gap_s     = etf_s.loc[_com_gap] - idx_s.loc[_com_gap]
                        _gap_last  = float(_gap_s.iloc[-1])
                        _gap_color = POS_COLOR if _gap_last >= 0 else NEG_COLOR
                        _fill_color = "rgba(45,122,79,0.10)" if _gap_last >= 0 else "rgba(192,57,43,0.10)"
                        _section("Écart de suivi ETF / Indice Dividende")
                        fig_gap = go.Figure()
                        fig_gap.add_trace(go.Scatter(
                            x=_gap_s.index, y=[0.0] * len(_gap_s),
                            line=dict(width=0), showlegend=False, hoverinfo="skip",
                        ))
                        fig_gap.add_trace(go.Scatter(
                            x=_gap_s.index, y=_gap_s.values,
                            name="ETF − Indice Dividende (pts base 100)",
                            mode="lines",
                            line=dict(color=_gap_color, width=2.5),
                            fill="tonexty", fillcolor=_fill_color,
                            hovertemplate="%{x|%d/%m}<br><b>Écart : %{y:+.2f} pts</b><extra></extra>",
                        ))
                        fig_gap.add_hline(y=0, line_dash="dot", line_color="#cbd5e1",
                                          annotation_text="À égalité", annotation_position="right")
                        fig_gap.update_layout(**PLOTLY_LAYOUT, height=280,
                            title="ETF vs Indice Dividende — avance/retard depuis le lancement (base 100)",
                            yaxis_title="Points d'écart",
                            hovermode="x unified", showlegend=False)
                        fig_gap.update_xaxes(tickformat="%d/%m")
                        st.plotly_chart(fig_gap, width='stretch')
                        _te_str2 = f"TE annualisée : {_te:.2f}%" if _te else ""
                        st.caption(
                            f"Écart actuel : {_gap_last:+.2f} pts — "
                            + ("ETF en avance sur le Indice Dividende" if _gap_last >= 0 else "ETF en retard sur le Indice Dividende")
                            + (f"  ·  {_te_str2}" if _te_str2 else "")
                        )

            elif not launched:
                st.info("ETF non encore lancé.")

            _intra_snaps = (intraday or {}).get("snapshots", [])
            _intra_date  = (intraday or {}).get("date", today_str)
            if len(_intra_snaps) >= 1:
                times  = [s["time"] for s in _intra_snaps]
                vl_pts = [s.get("vl_live_fcfa") or s.get("vl_par_part", 0) for s in _intra_snaps]
                deltas = [s.get("change_day_pct", 0) for s in _intra_snaps]
                _title_suffix = "aujourd'hui" if today_intraday else f"dernière session ({_intra_date})"

                _section(f"iNAV intraday — {_title_suffix}")
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    _vl_min = min(vl_pts)
                    _vl_max = max(vl_pts)
                    _vl_pad = (_vl_max - _vl_min) * 0.2 if _vl_max > _vl_min else _vl_min * 0.005
                    fig_intra = go.Figure()
                    fig_intra.add_trace(go.Scatter(
                        x=times, y=[_vl_min - _vl_pad] * len(times),
                        line=dict(width=0), showlegend=False, hoverinfo="skip",
                    ))
                    fig_intra.add_trace(go.Scatter(
                        x=times, y=vl_pts, mode="lines+markers",
                        line=dict(color=COLOR, width=2.5),
                        marker=dict(size=5, color=COLOR),
                        fill="tonexty", fillcolor=ACCENT, showlegend=False,
                        hovertemplate="%{x}<br><b>%{y:,.0f} FCFA</b><extra></extra>",
                    ))
                    par_val = float((launch or {}).get("par_fcfa", vl_pts[0]))
                    fig_intra.add_hline(y=par_val, line_dash="dot", line_color="#cbd5e1",
                                        annotation_text="Émission")
                    fig_intra.update_layout(**PLOTLY_LAYOUT, height=320,
                        title=f"VL intraday (FCFA)",
                        xaxis_title="Heure (UTC)", yaxis_title="FCFA / part",
                        yaxis_range=[_vl_min - _vl_pad, _vl_max + _vl_pad],
                        showlegend=False, hovermode="x unified")
                    st.plotly_chart(fig_intra, width='stretch')
                with col_g2:
                    # Indice Indice Dividende officiel intraday (pts)
                    idx_pts_all = [s.get("dividende_index") for s in _intra_snaps]
                    idx_valid   = [(t, v) for t, v in zip(times, idx_pts_all) if v is not None]
                    if idx_valid:
                        _t_idx, _v_idx = zip(*idx_valid)
                        _idx_min = min(_v_idx)
                        _idx_max = max(_v_idx)
                        _idx_pad = (_idx_max - _idx_min) * 0.2 if _idx_max > _idx_min else _idx_min * 0.005
                        fig_idx = go.Figure()
                        fig_idx.add_trace(go.Scatter(
                            x=list(_t_idx), y=[_idx_min - _idx_pad] * len(_t_idx),
                            line=dict(width=0), showlegend=False, hoverinfo="skip",
                        ))
                        fig_idx.add_trace(go.Scatter(
                            x=list(_t_idx), y=list(_v_idx), mode="lines+markers",
                            line=dict(color=BENCH_COLOR, width=2.5),
                            marker=dict(size=5, color=BENCH_COLOR),
                            fill="tonexty", fillcolor="rgba(100,116,139,0.12)", showlegend=False,
                            hovertemplate="%{x}<br><b>%{y:.2f} pts</b><extra></extra>",
                        ))
                        fig_idx.update_layout(**PLOTLY_LAYOUT, height=320,
                            title="Indice Dividende intraday (pts)",
                            xaxis_title="Heure (UTC)", yaxis_title="Points",
                            yaxis_range=[_idx_min - _idx_pad, _idx_max + _idx_pad],
                            showlegend=False, hovermode="x unified")
                        st.plotly_chart(fig_idx, width='stretch')
                    else:
                        st.info("Pas encore de données Indice Dividende aujourd'hui.")
                # Ligne 2 : comparaison base 100 pleine largeur
                if True:
                    # Indice Dividende intraday rebalisé à 100 — base commune = premier point où ETF ET Indice Dividende ont une valeur
                    _par_intra = float((launch or {}).get("par_fcfa", 100000))
                    idx_pts = [s.get("dividende_index") for s in _intra_snaps]
                    # Trouver le premier index où les deux séries ont une valeur
                    _common_i = next((i for i, (v_idx, s) in enumerate(zip(idx_pts, _intra_snaps))
                                      if v_idx is not None and (s.get("vl_live_fcfa") or s.get("vl_par_part", 0))), None)
                    _idx_open = idx_pts[_common_i] if _common_i is not None else None
                    if _idx_open and any(v is not None for v in idx_pts):
                        # Tronquer les deux séries à partir du premier point commun
                        _snaps_c  = _intra_snaps[_common_i:]
                        _idx_c    = idx_pts[_common_i:]
                        times_c   = times[_common_i:]
                        idx_base100 = [round(v / _idx_open * 100, 4) if v is not None else None for v in _idx_c]
                        _etf_open = (_snaps_c[0].get("vl_live_fcfa") or _snaps_c[0].get("vl_par_part", 0)) or _par_intra
                        etf_base100 = [round((s.get("vl_live_fcfa") or s.get("vl_par_part", 0)) / _etf_open * 100, 4) for s in _snaps_c]
                        fig_cmp_intra = go.Figure()
                        fig_cmp_intra.add_trace(go.Scatter(
                            x=times_c, y=etf_base100, name="ETF",
                            mode="lines+markers", line=dict(color=COLOR, width=2),
                            marker=dict(size=5),
                            hovertemplate="%{x}<br><b>ETF : %{y:.3f}</b><extra></extra>",
                        ))
                        fig_cmp_intra.add_trace(go.Scatter(
                            x=times_c, y=idx_base100, name="Indice Dividende",
                            mode="lines+markers", line=dict(color=BENCH_COLOR, width=2, dash="dash"),
                            marker=dict(size=5),
                            hovertemplate="%{x}<br><b>Indice Dividende : %{y:.3f}</b><extra></extra>",
                        ))
                        star_pts   = [s.get("brvm30_star") for s in _snaps_c]
                        _star_open = next((v for v in star_pts if v is not None), None)
                        if _star_open:
                            star_base100 = [round(v / _star_open * 100, 4) if v is not None else None for v in star_pts]
                            fig_cmp_intra.add_trace(go.Scatter(
                                x=times_c, y=star_base100, name="Indice Dividende*",
                                mode="lines+markers", line=dict(color="#7c3aed", width=2, dash="dot"),
                                marker=dict(size=5),
                                hovertemplate="%{x}<br><b>Indice Dividende* : %{y:.3f}</b><extra></extra>",
                            ))
                        fig_cmp_intra.add_hline(y=100, line_dash="dot", line_color="#cbd5e1")
                        fig_cmp_intra.update_layout(**PLOTLY_LAYOUT, height=300,
                            title=f"ETF vs Indice Dividende — base 100 à {times_c[0]}",
                            xaxis_title="Heure (UTC)", yaxis_title="Base 100",
                            legend=dict(orientation="h", y=-0.2),
                            hovermode="x unified")
                        st.plotly_chart(fig_cmp_intra, width='stretch')

                        # ── Attribution par tranche de 15 min ──────────────
                        _w_brvm30_ref = {}
                        try:
                            _rd_attr = load_json(rebal_detail_path) or {}
                            _rebals_attr = [r for r in _rd_attr.get('rebalancings', []) if not r.get('skipped') and r.get('basket')]
                            if _rebals_attr:
                                for _rb in _rebals_attr[-1]['basket']:
                                    _w_brvm30_ref[_rb['ticker']] = round(_rb['w_brvm30'] * 100, 2)
                        except Exception:
                            pass

                        _POS = "#16a34a"; _NEG = "#dc2626"; _MUT = "#9ca3af"

                        def _sig_tickers(contribs, w_idx_map):
                            """Titres significatifs : ont bougé ET ont un impact sur l'ETF OU sur l'écart.
                            Inclut les titres hors ETF (w_pct=0) s'ils ont un poids Indice Dividende significatif."""
                            result = []
                            for tk, v in contribs.items():
                                r = v.get('ret_pct', 0)
                                if abs(r) < 0.05:
                                    continue
                                gc = v.get('gap_contrib_pct', 0)
                                if abs(v.get('contrib_pct', 0)) >= 0.001 or abs(gc) >= 0.0005:
                                    result.append(tk)
                            return set(result)

                        def _chips_moteurs(contribs, sig_set):
                            show = {tk: v for tk, v in contribs.items() if tk in sig_set}
                            if not show:
                                return (f'<span style="color:{_MUT};font-style:italic;font-size:12px">'
                                        f'Prix non disponibles pour cette tranche</span>')
                            parts = []
                            for tk, v in sorted(show.items(), key=lambda x: x[1]['contrib_pct']):
                                c = v['contrib_pct']; r = v['ret_pct']
                                col = _POS if c > 0 else _NEG
                                arrow = "hausse" if r > 0 else "baisse"
                                parts.append(
                                    f'<div style="display:flex;align-items:baseline;gap:5px;padding:2px 0">'
                                    f'<span style="background:{col}18;color:{col};border-radius:3px;'
                                    f'padding:1px 6px;font-weight:700;font-size:12px;min-width:42px;text-align:center">{tk}</span>'
                                    f'<span style="color:{col};font-size:12px">en {arrow} de {abs(r):.2f}%</span>'
                                    f'<span style="color:#9ca3af;font-size:11px">→ {c:+.3f}pts pour l\'ETF</span>'
                                    f'</div>'
                                )
                            return "".join(parts)

                        def _chips_ecart(contribs, w_idx_map, gap_actual, sig_set):
                            if not contribs:
                                return f'<span style="color:{_MUT}">—</span>'

                            all_items = []
                            for tk, v in contribs.items():
                                if tk not in sig_set:
                                    continue
                                we = v.get('w_pct', 0)
                                wi = v.get('w_brvm30_pct') or w_idx_map.get(tk)
                                if wi is None:
                                    continue
                                gc = v.get('gap_contrib_pct') or round(((we - wi) / 100) * v['ret_pct'], 4)
                                all_items.append((tk, we, wi, round(we - wi, 2), v['ret_pct'], gc))
                            if not all_items:
                                return f'<span style="color:{_MUT}">—</span>'
                            all_items.sort(key=lambda x: abs(x[5]), reverse=True)

                            total_expl = round(sum(x[5] for x in all_items), 4)
                            col_gap = _POS if gap_actual >= 0 else _NEG
                            gap_dir = "surperformance" if gap_actual > 0 else "sous-performance"

                            # Qualite de l'attribution
                            pct = round(abs(total_expl / gap_actual) * 100) if abs(gap_actual) >= 0.02 else None

                            # Toujours afficher le tableau des titres qui ont bougé
                            if pct is None or pct < 30:
                                # Tous les titres qui ont bougé, triés par écart de poids absolu
                                _all_w = []
                                for tk, v in contribs.items():
                                    we = v.get('w_pct', 0)
                                    wi = v.get('w_brvm30_pct') or w_idx_map.get(tk, 0)
                                    r  = v.get('ret_pct', 0)
                                    gc = v.get('gap_contrib_pct', 0)
                                    if wi is None: wi = 0
                                    if abs(r) >= 0.05:
                                        _all_w.append((tk, we, wi, round(we - wi, 2), r, gc))
                                _all_w.sort(key=lambda x: abs(x[3]), reverse=True)
                                if abs(gap_actual) < 0.02:
                                    _hdr = (
                                        f'<div style="font-size:11px;padding:4px 8px;margin-bottom:6px;'
                                        f'background:#f9fafb;border-left:3px solid #cbd5e1;border-radius:0 4px 4px 0;color:#6b7280">'
                                        f'Ecart negligeable ({gap_actual:+.3f}%). '
                                        f'Poids ETF vs Indice Dividende pour les titres qui ont bouge :'
                                        f'</div>'
                                    )
                                else:
                                    _hdr = (
                                        f'<div style="font-size:11px;padding:4px 8px;margin-bottom:6px;'
                                        f'background:#fef9f0;border-left:3px solid #f59e0b;border-radius:0 4px 4px 0;color:#92400e">'
                                        f'Attribution partielle ({total_expl:+.4f}pts sur {gap_actual:+.3f}%). '
                                        f'Poids ETF vs Indice Dividende pour les titres qui ont bouge :'
                                        f'</div>'
                                    )
                                _th = (
                                    f'<div style="display:grid;grid-template-columns:52px 52px 52px 52px 60px 60px;'
                                    f'gap:4px;padding:4px 8px;background:#f3f4f6;border-radius:4px;margin-bottom:4px;'
                                    f'font-size:10px;font-weight:600;color:#6b7280;text-transform:uppercase">'
                                    f'<span>Titre</span><span>Var%</span>'
                                    f'<span>ETF%</span><span>Indice Dividende%</span>'
                                    f'<span>Δ poids</span><span>Gap contrib</span>'
                                    f'</div>'
                                )
                                _rows_w = []
                                for tk, we, wi, dw, r, gc in _all_w:
                                    r_col  = _POS if r  >= 0 else _NEG
                                    gc_col = _POS if gc >= 0 else _NEG
                                    dw_col = _POS if dw >= 0 else _NEG
                                    _rows_w.append(
                                        f'<div style="display:grid;grid-template-columns:52px 52px 52px 52px 60px 60px;'
                                        f'gap:4px;padding:4px 8px;border-bottom:1px solid #f0f0f0;'
                                        f'font-size:11px;align-items:center">'
                                        f'<b style="color:#0c1a2e">{tk}</b>'
                                        f'<span style="color:{r_col}">{r:+.2f}%</span>'
                                        f'<span style="color:#374151">{we:.2f}%</span>'
                                        f'<span style="color:#374151">{wi:.2f}%</span>'
                                        f'<span style="color:{dw_col};font-weight:600">{dw:+.2f}%</span>'
                                        f'<span style="color:{gc_col};font-weight:600">{gc:+.4f}pts</span>'
                                        f'</div>'
                                    )
                                return (
                                    _hdr + _th +
                                    f'<div style="border:1px solid #e5e7eb;border-radius:4px;overflow:hidden">'
                                    + "".join(_rows_w) + f'</div>'
                                )

                            pct_label = f"expliquent environ {min(pct, 100)}% de cet ecart"
                            summary = (
                                f'<div style="font-size:11px;padding:4px 8px;margin-bottom:6px;'
                                f'background:#f9fafb;border-left:3px solid {col_gap};border-radius:0 4px 4px 0;color:#374151">'
                                f'L\'ETF a {gap_dir} de <b style="color:{col_gap}">{abs(gap_actual):.3f}%</b> '
                                f'vs l\'indice. Les titres ci-dessous {pct_label} :'
                                f'</div>'
                            )

                            parts = []
                            for tk, we, wi, dw, r, gc in all_items:
                                col = _POS if gc > 0 else _NEG
                                move_col = _POS if r > 0 else _NEG
                                etf_more = dw > 0
                                stock_up = r > 0
                                if etf_more and stock_up:
                                    reason = f'ETF en detient <b>plus</b> ({we:.1f}% vs {wi:.1f}%) et il a monte → ETF en a plus profite'
                                elif etf_more and not stock_up:
                                    reason = f'ETF en detient <b>plus</b> ({we:.1f}% vs {wi:.1f}%) et il a baisse → ETF en a plus souffert'
                                elif not etf_more and stock_up:
                                    reason = f'ETF en detient <b>moins</b> ({we:.1f}% vs {wi:.1f}%) et il a monte → ETF en a moins profite'
                                else:
                                    reason = f'ETF en detient <b>moins</b> ({we:.1f}% vs {wi:.1f}%) et il a baisse → ETF en a moins souffert'
                                parts.append(
                                    f'<div style="margin-bottom:5px;padding:5px 8px;'
                                    f'background:{col}08;border-radius:5px;border-left:3px solid {col}">'
                                    f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:2px">'
                                    f'<b style="color:{col};font-size:13px">{tk}</b>'
                                    f'<span style="color:{move_col};font-size:12px">{"hausse" if r>0 else "baisse"} de {abs(r):.2f}%</span>'
                                    f'<span style="margin-left:auto;color:{col};font-size:11px;font-weight:600">{gc:+.4f}pts</span>'
                                    f'</div>'
                                    f'<div style="font-size:11px;color:#6b7280;line-height:1.4">{reason}</div>'
                                    f'</div>'
                                )
                            return summary + "".join(parts)

                        _attr_data = []
                        for _ai in range(1, len(_snaps_c)):
                            _sp  = _snaps_c[_ai]
                            _t   = times_c[_ai]; _t0 = times_c[_ai - 1]
                            _etf_d = round(etf_base100[_ai] - etf_base100[_ai-1], 3)
                            # Indice Dividende officiel Sika (peut rester figé 15-30 min entre MAJ)
                            _idx_d_off = round((idx_base100[_ai] or 0) - (idx_base100[_ai-1] or 0), 3) if idx_base100[_ai] and idx_base100[_ai-1] else None
                            # Indice Dividende* estimé depuis nos propres prix (synchrone avec l'iNAV)
                            _tc_ai = _sp.get('ticker_contributions', {})
                            _idx_d_est = None
                            if _tc_ai:
                                _brv_est = sum(v.get('w_brvm30_pct', 0) / 100 * v.get('ret_pct', 0) for v in _tc_ai.values())
                                _idx_d_est = round(_brv_est * (idx_base100[_ai - 1] or 100) / 100, 3)
                            # Attribution : Indice Dividende* en principal (synchrone), officiel en note
                            _idx_d = _idx_d_est if _idx_d_est is not None else _idx_d_off
                            _gap   = round(_etf_d - _idx_d, 3) if _idx_d is not None else None
                            _attr_data.append({
                                'periode': f"{_t0}→{_t}",
                                'etf_d': _etf_d, 'idx_d': _idx_d, 'idx_d_off': _idx_d_off,
                                'gap': _gap,
                                'contribs': _tc_ai,
                            })

                        if _attr_data:
                          with st.expander("Attribution intraday — explication des mouvements", expanded=False):
                            st.caption(
                                "Cliquez sur une tranche pour voir le detail. "
                                "Ce qui a bouge l'ETF + pourquoi il ne suit pas exactement l'Indice Dividende. "
                                "Indice Dividende* = estimation synchrone calculee depuis nos prix (latence Sika ~15-30 min)."
                            )
                            _items_html = ""
                            for _i, _d in enumerate(_attr_data):
                                _ed = _d['etf_d']; _id = _d['idx_d']; _gp = _d['gap']
                                _id_est = _d.get('idx_d_est')
                                _ec = _POS if _ed >= 0 else _NEG
                                _ic = (_POS if _id >= 0 else _NEG) if _id is not None else _MUT
                                _gc = (_POS if _gp >= 0 else _NEG) if _gp is not None else _MUT
                                _sig = _sig_tickers(_d["contribs"], _w_brvm30_ref)
                                _mot_html = _chips_moteurs(_d["contribs"], _sig)
                                _eca_html = _chips_ecart(_d["contribs"], _w_brvm30_ref, _gp, _sig) if _gp is not None else f'<span style="color:{_MUT}">—</span>'
                                _has_detail = bool(_sig)
                                _border_top = "border-top:1px solid #e5e7eb;" if _i > 0 else ""
                                # Officiel Sika en note si différent de l'estimé (décalage détecté)
                                _id_off = _d.get('idx_d_off')
                                _off_note = ''
                                if _id_off is not None and (_id is None or abs(_id_off - (_id or 0)) > 0.002):
                                    _ic_off = _POS if _id_off >= 0 else _NEG
                                    _off_note = f' <span style="color:#9ca3af;font-size:10px">(officiel Sika <span style="color:{_ic_off}">{_id_off:+.3f}%</span>)</span>'
                                # Résumé compact : ligne toujours visible
                                _summary = (
                                    f'<summary style="list-style:none;display:flex;align-items:center;gap:16px;'
                                    f'padding:10px 16px;cursor:{"pointer" if _has_detail else "default"};'
                                    f'background:#fff;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;'
                                    f'font-size:13px;user-select:none;{_border_top}">'
                                    f'<span style="color:#6b7280;font-size:11px;min-width:90px">{"" if _has_detail else ""}{_d["periode"]}</span>'
                                    f'<span style="color:#9ca3af;font-size:11px">ETF</span>'
                                    f'<span style="color:{_ec};font-weight:600;min-width:55px">{_ed:+.3f}%</span>'
                                    f'<span style="color:#9ca3af;font-size:11px">Indice Dividende*</span>'
                                    f'<span style="color:{_ic};min-width:80px">{f"{_id:+.3f}%" if _id is not None else "—"}{_off_note}</span>'
                                    f'<span style="color:#9ca3af;font-size:11px">Écart</span>'
                                    f'<span style="color:{_gc};font-weight:700;min-width:55px">{f"{_gp:+.3f}%" if _gp is not None else "—"}</span>'
                                    f'</summary>'
                                )
                                if _has_detail:
                                    _detail = (
                                        f'<div style="padding:12px 16px 14px;background:#fafafa;'
                                        f'border-top:1px solid #f0f0f0;'
                                        f'display:grid;grid-template-columns:1fr 1fr;gap:20px;'
                                        f'font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif">'
                                        f'<div>'
                                        f'<div style="font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;'
                                        f'letter-spacing:.05em;margin-bottom:8px">Ce qui a fait bouger l\'ETF</div>'
                                        f'{_mot_html}'
                                        f'</div>'
                                        f'<div>'
                                        f'<div style="font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;'
                                        f'letter-spacing:.05em;margin-bottom:8px">Pourquoi l\'ETF differe de l\'indice</div>'
                                        f'{_eca_html}'
                                        f'</div>'
                                        f'</div>'
                                    )
                                    _items_html += f'<details>{_summary}{_detail}</details>'
                                else:
                                    _items_html += f'<div>{_summary}</div>'
                            st.markdown(
                                f'<div style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;margin-top:4px">'
                                f'{_items_html}</div>',
                                unsafe_allow_html=True,
                            )

                    else:
                        bar_colors = [POS_COLOR if d >= 0 else NEG_COLOR for d in deltas]
                        fig_delta  = go.Figure(go.Bar(
                            x=times, y=deltas, marker_color=bar_colors,
                            hovertemplate="%{x}<br><b>%{y:+.3f}%</b><extra></extra>",
                        ))
                        fig_delta.add_hline(y=0, line_color="#e8ecf0")
                        fig_delta.update_layout(**PLOTLY_LAYOUT, height=300,
                            title="Variation vs ouverture (%)",
                            xaxis_title="Heure (UTC)", yaxis_title="%",
                            showlegend=False, hovermode="x unified")
                        st.plotly_chart(fig_delta, width='stretch')
                if not today_intraday:
                    st.caption("Marché fermé — affichage de la dernière session enregistrée.")

                # ── Historique iNAV par séance ────────────────────────────
                _ih_hist = load_json(os.path.join(HALAL_DIR, "nav_intraday_history.json")) or {}
                _past_days = sorted([d for d in _ih_hist if d != today_str], reverse=True)
                _POS = "#16a34a"; _NEG = "#dc2626"; _MUT = "#9ca3af"
                if _past_days:
                    _section("Historique iNAV par séance")
                    st.caption("Cliquez sur une journée pour voir le détail des tranches de 15 min.")

                    def _base100_series(pts, key):
                        vals = [p.get(key) for p in pts]
                        v0 = next((v for v in vals if v), None)
                        return [round(v / v0 * 100, 4) if v and v0 else None for v in vals]

                    _days_html = ""
                    for _day in _past_days:
                        _pts = _ih_hist[_day]
                        if not _pts or len(_pts) < 2:
                            continue
                        _times_h = [p['time'] for p in _pts]
                        _nav_b100  = _base100_series(_pts, 'nav_indice')
                        _brvm_b100 = _base100_series(_pts, 'brvm30_official')

                        # Résumé journalier
                        _nav0  = next((p.get('nav_indice') for p in _pts if p.get('nav_indice')), None)
                        _nav1  = next((p.get('nav_indice') for p in reversed(_pts) if p.get('nav_indice')), None)
                        _brv0  = next((p.get('brvm30_official') for p in _pts if p.get('brvm30_official')), None)
                        _brv1  = next((p.get('brvm30_official') for p in reversed(_pts) if p.get('brvm30_official')), None)
                        _etf_j  = round((_nav1 / _nav0 - 1) * 100, 3) if _nav0 and _nav1 else None
                        _brv_j  = round((_brv1 / _brv0 - 1) * 100, 3) if _brv0 and _brv1 else None
                        _eca_j  = round(_etf_j - _brv_j, 3) if _etf_j is not None and _brv_j is not None else None
                        _ec_col = (_POS if _eca_j >= 0 else _NEG) if _eca_j is not None else _MUT
                        _etf_col = (_POS if _etf_j >= 0 else _NEG) if _etf_j is not None else _MUT
                        _brv_col = (_POS if _brv_j >= 0 else _NEG) if _brv_j is not None else _MUT

                        # Résumé dans le <summary>
                        _day_label = pd.Timestamp(_day).strftime("%-d %b %Y") if hasattr(pd.Timestamp(_day), 'day') else _day
                        try:
                            _day_label = pd.Timestamp(_day).strftime("%d %b %Y")
                        except Exception:
                            _day_label = _day
                        _day_summary = (
                            f'<summary style="list-style:none;display:flex;align-items:center;gap:16px;'
                            f'padding:10px 16px;cursor:pointer;background:#fff;'
                            f'font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;font-size:13px;">'
                            f'<span style="font-weight:600;color:#374151;min-width:100px">{_day_label}</span>'
                            f'<span style="color:#9ca3af;font-size:11px">ETF journée</span>'
                            f'<span style="color:{_etf_col};font-weight:600;min-width:55px">{f"{_etf_j:+.3f}%" if _etf_j is not None else "—"}</span>'
                            f'<span style="color:#9ca3af;font-size:11px">Indice Dividende</span>'
                            f'<span style="color:{_brv_col};min-width:55px">{f"{_brv_j:+.3f}%" if _brv_j is not None else "—"}</span>'
                            f'<span style="color:#9ca3af;font-size:11px">Écart</span>'
                            f'<span style="color:{_ec_col};font-weight:700;min-width:55px">{f"{_eca_j:+.3f}%" if _eca_j is not None else "—"}</span>'
                            f'<span style="color:#9ca3af;font-size:11px;margin-left:auto">{len(_pts)} snapshots</span>'
                            f'</summary>'
                        )

                        # Détail par tranche de 15 min
                        _periods_html = ""
                        _ecarts = []
                        for _ai in range(1, len(_pts)):
                            _t0h = _times_h[_ai - 1]; _t1h = _times_h[_ai]
                            _ed = round(_nav_b100[_ai] - _nav_b100[_ai-1], 3) if _nav_b100[_ai] and _nav_b100[_ai-1] else None
                            _id = round((_brvm_b100[_ai] or 0) - (_brvm_b100[_ai-1] or 0), 3) if _brvm_b100[_ai] and _brvm_b100[_ai-1] else None
                            _gp = round(_ed - _id, 3) if _ed is not None and _id is not None else None
                            if _gp is not None:
                                _ecarts.append(_gp)
                            _ec2 = (_POS if _ed >= 0 else _NEG) if _ed is not None else _MUT
                            _ic2 = (_POS if _id >= 0 else _NEG) if _id is not None else _MUT
                            _gc2 = (_POS if _gp >= 0 else _NEG) if _gp is not None else _MUT
                            _periods_html += (
                                f'<div style="display:flex;align-items:center;gap:12px;padding:7px 16px;'
                                f'border-bottom:1px solid #f3f4f6;font-size:12px;'
                                f'font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif">'
                                f'<span style="color:#6b7280;min-width:80px">{_t0h}→{_t1h}</span>'
                                f'<span style="color:#9ca3af;font-size:11px">ETF</span>'
                                f'<span style="color:{_ec2};font-weight:600;min-width:55px">{f"{_ed:+.3f}%" if _ed is not None else "—"}</span>'
                                f'<span style="color:#9ca3af;font-size:11px">Indice Dividende</span>'
                                f'<span style="color:{_ic2};min-width:55px">{f"{_id:+.3f}%" if _id is not None else "—"}</span>'
                                f'<span style="color:#9ca3af;font-size:11px">Écart</span>'
                                f'<span style="color:{_gc2};font-weight:700;min-width:55px">{f"{_gp:+.3f}%" if _gp is not None else "—"}</span>'
                                f'</div>'
                            )

                        # Résumé de fin de journée
                        if _ecarts:
                            _moy = round(sum(_ecarts) / len(_ecarts), 4)
                            _max_e = max(_ecarts, key=abs)
                            _moy_col = _POS if _moy >= 0 else _NEG
                            _max_col = _POS if _max_e >= 0 else _NEG
                            _periods_html += (
                                f'<div style="padding:10px 16px;background:#f9fafb;border-top:2px solid #e5e7eb;'
                                f'font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;font-size:12px">'
                                f'<b style="color:#374151">Résumé de la journée</b>'
                                f'<span style="margin-left:16px;color:#6b7280">ETF total : </span>'
                                f'<b style="color:{_etf_col}">{f"{_etf_j:+.3f}%" if _etf_j else "—"}</b>'
                                f'<span style="margin-left:12px;color:#6b7280">Indice Dividende total : </span>'
                                f'<b style="color:{_brv_col}">{f"{_brv_j:+.3f}%" if _brv_j else "—"}</b>'
                                f'<span style="margin-left:12px;color:#6b7280">Écart total : </span>'
                                f'<b style="color:{_ec_col}">{f"{_eca_j:+.3f}%" if _eca_j is not None else "—"}</b>'
                                f'<span style="margin-left:16px;color:#9ca3af">·</span>'
                                f'<span style="margin-left:12px;color:#6b7280">Écart moyen/tranche : </span>'
                                f'<b style="color:{_moy_col}">{_moy:+.4f}%</b>'
                                f'<span style="margin-left:12px;color:#6b7280">Écart max : </span>'
                                f'<b style="color:{_max_col}">{_max_e:+.3f}%</b>'
                                f'</div>'
                            )

                        _days_html += (
                            f'<details style="border-top:1px solid #e5e7eb">'
                            f'{_day_summary}'
                            f'<div style="background:#fafafa">{_periods_html}</div>'
                            f'</details>'
                        )

                    if _days_html:
                        st.markdown(
                            f'<div style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;margin-top:4px">'
                            f'{_days_html}</div>',
                            unsafe_allow_html=True,
                        )

                # ── Export CSV historique iNAV ─────────────────────────────
                _ih_dl = load_json(os.path.join(HALAL_DIR, "nav_intraday_history.json")) or {}
                if _ih_dl:
                    import io as _io_csv
                    _rows_csv = []
                    for _d_csv, _pts_csv in sorted(_ih_dl.items()):
                        # Base100 depuis le premier snapshot de la journée
                        _nav0_csv  = next((p.get('nav_indice') for p in _pts_csv if p.get('nav_indice')), None)
                        _brv0_csv  = next((p.get('brvm30_official') for p in _pts_csv if p.get('brvm30_official')), None)
                        _prev_nav  = None
                        _prev_brv  = None
                        for _pt in _pts_csv:
                            _nav  = _pt.get('nav_indice')
                            _brv  = _pt.get('brvm30_official')
                            _vl   = _pt.get('vl_fcfa') or _pt.get('vl')
                            # Δ% par tranche (vs snapshot précédent)
                            _etf_delta  = round((_nav / _prev_nav - 1) * 100, 4) if _nav and _prev_nav else None
                            _brv_delta  = round((_brv / _prev_brv - 1) * 100, 4) if _brv and _prev_brv else None
                            _ecart      = round(_etf_delta - _brv_delta, 4) if _etf_delta is not None and _brv_delta is not None else None
                            # Δ% depuis ouverture
                            _etf_vs_open  = round((_nav / _nav0_csv - 1) * 100, 4) if _nav and _nav0_csv else None
                            _brv_vs_open  = round((_brv / _brv0_csv - 1) * 100, 4) if _brv and _brv0_csv else None
                            _row = {
                                "date":                _d_csv,
                                "heure":               _pt.get("time"),
                                "vl_fcfa":             round(_vl, 0) if _vl else None,
                                "nav_indice":          _nav,
                                "brvm30_official":     _brv,
                                "etf_delta_tranche_%": _etf_delta,
                                "brvm30_delta_tranche_%": _brv_delta,
                                "ecart_tranche_%":     _ecart,
                                "etf_vs_ouverture_%":  _etf_vs_open,
                                "brvm30_vs_ouverture_%": _brv_vs_open,
                                "perf_lancement_%":    _pt.get("perf_since_launch"),
                                "var_jour_%":          _pt.get("change_day_pct"),
                                "aum_mfcfa":           _pt.get("aum_mfcfa"),
                            }
                            for _tk, _tc in sorted((_pt.get("ticker_contributions") or {}).items()):
                                _row[f"{_tk}_var_%"]       = _tc.get("ret_pct")
                                _row[f"{_tk}_w_etf_%"]     = _tc.get("w_pct")
                                _row[f"{_tk}_w_brvm30_%"]  = _tc.get("w_brvm30_pct")
                                _row[f"{_tk}_contrib_etf_%"] = _tc.get("contrib_pct")
                                _row[f"{_tk}_gap_contrib_%"] = _tc.get("gap_contrib_pct")
                            _rows_csv.append(_row)
                            _prev_nav = _nav or _prev_nav
                            _prev_brv = _brv or _prev_brv
                    _df_csv = pd.DataFrame(_rows_csv)
                    _csv_buf = _io_csv.StringIO()
                    _df_csv.to_csv(_csv_buf, index=False, sep=";", decimal=",")
                    import io as _io_csv2
                    _c1, _c2 = st.columns(2)
                    with _c1:
                        st.download_button(
                            label="Télécharger l'historique iNAV (CSV)",
                            data=_csv_buf.getvalue().encode("utf-8"),
                            file_name=f"inav_history_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                        )
                    with _c2:
                        # Export VL journalière (clôtures)
                        _vl_rows = []
                        _brvm_hist_dl = load_json(os.path.join(HALAL_DIR, "brvm30_index_history.json")) or {}
                        _par_dl = float((launch or {}).get("par_fcfa", 100000))
                        _anchor_dl = (launch or {}).get("nav_index_at_launch")
                        for _dt_vl, _vl_val in sorted((nl or {}).get("nav_live_series", [])):
                            _brv_val = _brvm_hist_dl.get(_dt_vl)
                            _perf = round((_vl_val / _par_dl - 1) * 100, 4) if _par_dl else None
                            _vl_rows.append({
                                "date":              _dt_vl,
                                "vl_par_part_fcfa":  round(_vl_val, 0),
                                "brvm30_officiel":   _brv_val,
                                "perf_lancement_%":  _perf,
                            })
                        if _vl_rows:
                            _buf_vl = _io_csv2.StringIO()
                            pd.DataFrame(_vl_rows).to_csv(_buf_vl, index=False, sep=";", decimal=",")
                            st.download_button(
                                label="Télécharger la VL journalière (CSV)",
                                data=_buf_vl.getvalue().encode("utf-8"),
                                file_name=f"vl_journaliere_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv",
                            )
            else:
                st.caption("Graphiques intraday disponibles pendant les heures de marché (09h–15h30 UTC).")

            if nl and nl.get("basket"):
                _section("Composition du portefeuille")

                df_basket = pd.DataFrame(nl["basket"])

                # Poids cibles du dernier rebalancement (capés par ADV)
                _rd_live = load_json(os.path.join(HALAL_DIR, "rebal_detail.json")) or {}
                _rebals_live = [r for r in _rd_live.get("rebalancings", []) if not r.get("skipped") and r.get("basket")]
                _last_rb_live = _rebals_live[-1] if _rebals_live else {}
                _w_cible_live = {b["ticker"]: round(b.get("w_etf", 0) * 100, 4)
                                 for b in _last_rb_live.get("basket", [])}
                _capped_live  = {b["ticker"]: bool(b.get("capped", False))
                                 for b in _last_rb_live.get("basket", [])}

                # Var. journalière via Sika — on récupère la variation officielle du jour
                sika_data = scrape_sika_open()
                if not sika_data:
                    st.info("ℹ Sika Finance indisponible — variations journalières non affichées.")

                # Poids flottants courants de l'Indice Dividende (recalculés avec prix du jour)
                # Formule : w_i(t) = w_i(rebal) × (P_i(t)/P_i(rebal)) / Σ(w_j(rebal) × P_j(t)/P_j(rebal))
                _rebal_date_live = _last_rb_live.get("date", "")
                _sh_live = load_json(os.path.join(HALAL_DIR, "sika_history.json")) or {}
                _price_now = {r["ticker"]: r["dernier_prix"] for _, r in df_basket.iterrows()}
                _interim_idx, _sum_idx = {}, 0.0
                for _b in _last_rb_live.get("basket", []):
                    _tk, _w0 = _b["ticker"], _b.get("w_brvm30", 0)
                    _p0   = (_sh_live.get(_tk, {}).get(_rebal_date_live) or {}).get("close")
                    _pnow = _price_now.get(_tk)
                    if _w0 and _p0 and _pnow:
                        _r = _w0 * _pnow / _p0
                        _interim_idx[_tk] = _r
                        _sum_idx += _r
                if _sum_idx > 0:
                    _w_brvm30_live = {tk: round(r / _sum_idx * 100, 4) for tk, r in _interim_idx.items()}
                else:
                    _w_brvm30_live = {b["ticker"]: round(b.get("w_brvm30", 0) * 100, 4)
                                      for b in _last_rb_live.get("basket", [])}
                rows = []
                for _, r in df_basket.iterrows():
                    last  = r["dernier_prix"]   # clôture veille dans nav_latest
                    ticker_upper = r["ticker"].upper()
                    sika  = sika_data.get(ticker_upper, {})
                    var_j = sika.get("variation") if isinstance(sika, dict) else None
                    w_live  = round(r["poids_pct"], 4)
                    w_cible = _w_cible_live.get(r["ticker"])
                    w_b30   = _w_brvm30_live.get(r["ticker"])
                    rows.append({
                        "Ticker":              r["ticker"],
                        "Poids live (%)":      w_live,
                        "Cible rebal (%)":     w_cible,
                        "Indice Dividende (%)": w_b30,
                        "Rend. div. moy. (%)": r.get("avg_yield_pct"),
                        "_capped":             _capped_live.get(r["ticker"], False),
                        "_excluded":           False,
                        "Clôture":             f"{int(last):,}" if last else "—",
                        "Var. J (%)":          var_j,
                        "Val. (M FCFA)":       round(r.get("pv_mfcfa") or 0, 1),
                        "Stale":               "" if r.get("prix_stale", False) else "",
                    })
                _etf_tickers_set = {r["Ticker"] for r in rows}
                for _e in sorted(_last_rb_live.get("excluded", []), key=lambda x: x.get("w_brvm30", 0), reverse=True):
                    _tk = _e["ticker"]
                    if _tk in _etf_tickers_set:
                        continue
                    _sika_e = sika_data.get(_tk.upper(), {}) if isinstance(sika_data.get(_tk.upper()), dict) else {}
                    rows.append({
                        "Ticker":              _tk,
                        "Poids live (%)":      0.0,
                        "Cible rebal (%)":     0.0,
                        "Indice Dividende (%)": round(_e.get("w_brvm30", 0) * 100, 4),
                        "Rend. div. moy. (%)": _e.get("avg_yield_pct"),
                        "_capped":             False,
                        "_excluded":           True,
                        "Clôture":             f"{int(_sika_e['dernier']):,}" if _sika_e.get("dernier") else "—",
                        "Var. J (%)":          _sika_e.get("variation"),
                        "Val. (M FCFA)":       0.0,
                        "Stale":               "",
                    })

                df_out = pd.DataFrame(rows)

                # ── Contrôle qualité données ─────────────────────────────────
                _dq_issues = []
                _dq_today  = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d")
                for _dq_r in rows:
                    _dqtk = _dq_r["Ticker"]
                    if _dq_r.get("_excluded"):
                        continue
                    _dqhist = _sh_live.get(_dqtk, {})
                    if not _dqhist:
                        _dq_issues.append(f"**{_dqtk}** : aucun historique dans sika_history.json")
                        continue
                    _dqdates = sorted(d for d in _dqhist if d <= _dq_today)[-30:]
                    if _dqdates:
                        _dqnz = sum(1 for d in _dqdates if (_dqhist[d].get("volume") or 0) == 0)
                        if _dqnz / len(_dqdates) >= 0.9:
                            _dq_issues.append(
                                f"**{_dqtk}** : volume = 0 sur {_dqnz}/{len(_dqdates)} "
                                f"jours récents — données volume suspectes"
                            )
                    _dqcloses = [_dqhist[d].get("close") for d in _dqdates[-10:]
                                 if _dqhist[d].get("close")]
                    if len(_dqcloses) >= 10 and len(set(_dqcloses)) == 1:
                        _dq_issues.append(
                            f"**{_dqtk}** : prix figé à {int(_dqcloses[0]):,} FCFA "
                            f"depuis ≥ 10 jours — vérifier suspension/données"
                        )
                    _dqvar = _dq_r.get("Var. J (%)")
                    if isinstance(_dqvar, (int, float)) and abs(_dqvar) > 15:
                        _dq_issues.append(
                            f"**{_dqtk}** : variation journalière extrême "
                            f"**{_dqvar:+.2f}%** — confirmer ou erreur de scraping"
                        )
                for _dqe in _last_rb_live.get("excluded", []):
                    _dqtk2  = _dqe["ticker"]
                    _dqadv  = _dqe.get("adv_mfcfa", 0)
                    _dqwidx = _dqe.get("w_brvm30", 0) * 100
                    if _dqwidx > 1.0 and _dqadv < 0.5:
                        _dq_issues.append(
                            f"**{_dqtk2}** exclu pour ADV={_dqadv:.2f} MFCFA/j "
                            f"mais poids indice={_dqwidx:.2f}% — vérifier données volume"
                        )
                if _dq_issues:
                    with st.expander(
                        f"⚠️ {len(_dq_issues)} alerte(s) qualité données — cliquer pour détails",
                        expanded=True,
                    ):
                        for _dqmsg in _dq_issues:
                            st.markdown(f"- {_dqmsg}")
                        st.caption(
                            "Ces alertes signalent des données potentiellement incorrectes. "
                            "Relancer scrape_sika_history.py pour corriger les volumes."
                        )

                def _color_pct(val):
                    if isinstance(val, (int, float)):
                        return f"color: {'#2d7a4f' if val > 0 else '#c0392b' if val < 0 else '#7d8fa3'}; font-weight:500"
                    return ""

                def _fmt_var(val):
                    if isinstance(val, (int, float)):
                        return f"{val:+.2f}%"
                    return "—"

                def _color_drift_live(row):
                    styles = [""] * len(row)
                    cols = list(row.index)
                    if bool(row.get("_excluded", False)):
                        return ["background-color: #f1f5f9; color: #94a3b8"] * len(styles)
                    b30   = row.get("Indice Dividende (%)")
                    # Titre capé : lu directement depuis le basket rebal_detail
                    capped = bool(row.get("_capped", False))
                    if capped:
                        for i in range(len(styles)):
                            styles[i] = "background-color: #FDEDEC"
                        if "Ticker" in cols:
                            styles[cols.index("Ticker")] = "background-color: #FDEDEC; color: #C0392B; font-weight:700"
                        if "Cible rebal (%)" in cols:
                            styles[cols.index("Cible rebal (%)")] = "background-color: #FDEDEC; color: #C0392B; font-weight:600"
                    # Dérive live vs poids flottant courant de l'indice > 1%
                    if "Poids live (%)" in cols and "Indice Indice Dividende (%)" in cols:
                        live = row["Poids live (%)"]
                        if live is not None and b30 is not None and not pd.isna(live) and not pd.isna(b30):
                            if abs(live - b30) > 1.0:
                                styles[cols.index("Poids live (%)")] = (
                                    ("background-color: #FDEDEC; " if capped else "")
                                    + "color: #C0392B; font-weight:600"
                                )
                    return styles

                df_styled = df_out.style\
                    .apply(_color_drift_live, axis=1)\
                    .hide(axis='columns', names=['_capped', '_excluded'])\
                    .map(_color_pct, subset=["Var. J (%)"])\
                    .format({
                        "Var. J (%)":        _fmt_var,
                        "Poids live (%)":    "{:.4f}%",
                        "Cible rebal (%)":   lambda x: f"{x:.4f}%" if x is not None and not (isinstance(x, float) and pd.isna(x)) else "—",
                        "Indice Indice Dividende (%)": lambda x: f"{x:.4f}%" if x is not None and not (isinstance(x, float) and pd.isna(x)) else "—",
                        "Val. (M FCFA)":     "{:.1f}",
                    })

                col_tbl, col_pie = st.columns([3, 2])
                with col_tbl:
                    st.dataframe(df_styled, width='stretch', hide_index=True,
                                 height=min(580, 44 + len(df_out) * 36))
                with col_pie:
                    # Top 10 par poids + "Autres" pour le reste
                    _pie_df = df_out[["Ticker", "Val. (M FCFA)", "Poids live (%)"]].copy()
                    _pie_df["Poids live (%)"] = _pie_df["Poids live (%)"].astype(float)
                    _pie_df = _pie_df.sort_values("Poids live (%)", ascending=False)
                    _top10      = _pie_df.iloc[:10].copy()
                    _reste      = _pie_df.iloc[10:]
                    _n_autres   = len(_reste)
                    _autres_tickers = _reste["Ticker"].tolist()
                    if _n_autres > 0:
                        _autres_row = pd.DataFrame([{
                            "Ticker": f"Autres ({_n_autres})",
                            "Val. (M FCFA)": _reste["Val. (M FCFA)"].sum(),
                            "Poids live (%)": _reste["Poids live (%)"].sum(),
                        }])
                        _pie_main = pd.concat([_top10, _autres_row], ignore_index=True)
                    else:
                        _pie_main = _top10
                    _pie_vals = _pie_main["Val. (M FCFA)"] if _pie_main["Val. (M FCFA)"].sum() > 0 else _pie_main["Poids live (%)"]
                    fig_pie = go.Figure(go.Pie(
                        labels=_pie_main["Ticker"],
                        values=_pie_vals,
                        hole=0.42,
                        textinfo="label+percent",
                        textfont=dict(size=13, color="#ffffff"),
                        textposition="auto",
                        insidetextorientation="auto",
                        outsidetextfont=dict(size=12, color="#0c1a2e"),
                        marker=dict(line=dict(color="#ffffff", width=2)),
                    ))
                    fig_pie.update_layout(**PLOTLY_LAYOUT, height=400,
                        title="Répartition par titre", showlegend=False,
                        uniformtext=dict(minsize=11, mode="hide"))
                    st.plotly_chart(fig_pie, width='stretch')
                    if _n_autres > 0:
                        _autres_str = " · ".join(
                            f"{t} ({_pie_df.loc[_pie_df['Ticker']==t, 'Poids live (%)'].values[0]:.4f}%)"
                            for t in _autres_tickers
                        )
                        st.markdown(
                            f"<p style='font-size:13px; color:#374151; line-height:1.6'>"
                            f"<b>Autres ({_n_autres}) :</b> {_autres_str}</p>",
                            unsafe_allow_html=True,
                        )

        _live_fragment()

    # ── Rebalancements ────────────────────────────────────────────────────────
    elif _lsec == "rebalancements":
        rd_data       = load_json(rebal_detail_path)
        comp_hist_raw      = load_json(os.path.join(HALAL_DIR, "brvm_composition_history.json")) or []
        _nl_rb             = load_json(nav_latest_path) or {}
        _comp_latest       = load_json(os.path.join(HALAL_DIR, "brvm_composition_latest.json")) or {}
        _verified_path     = os.path.join(HALAL_DIR, "verified_rebals.json")
        # Lire depuis GitHub si token dispo, sinon fichier local
        if "verified_gh_cache" not in st.session_state:
            _gh_data, _gh_sha = _gh_get_verified()
            if _gh_data is not None:
                st.session_state.verified_gh_cache  = _gh_data
                st.session_state.verified_gh_sha    = _gh_sha
            else:
                st.session_state.verified_gh_cache  = load_json(_verified_path) or {}
                st.session_state.verified_gh_sha    = None
        _verified_rebals = st.session_state.verified_gh_cache
        _verified_sha    = st.session_state.verified_gh_sha

        # Panier ETF actuel (sous-ensemble des 30) — utilisé dans la correction historique
        _etf_basket = {b["ticker"].upper(): b["poids_pct"] for b in _nl_rb.get("basket", [])}

        # Build official Indice Dividende composition dict indexed by date (from PDF scrapes only)
        comp_pdf = [c for c in comp_hist_raw if c.get("rebal_date") and len(c.get("composition", [])) >= 25]
        comp_pdf = sorted(comp_pdf, key=lambda x: x["rebal_date"])
        # Fallback: compute entries/exits from consecutive compositions ONLY when both are complete (n==30)
        # and the current entry has no PDF-extracted entries/exits.
        # This avoids wrong diffs when a date is missing (e.g. Jan 2024 absent → Oct23→Apr24 diff spans 2 quarters).
        for i, c in enumerate(comp_pdf):
            if not c.get("entries") and i > 0:
                prev = comp_pdf[i - 1]
                # Only diff if both compositions are complete and there's no skipped quarter
                if c.get("n_tickers", 0) == 30 and prev.get("n_tickers", 0) == 30:
                    prev_s = set(prev["composition"])
                    curr_s = set(c["composition"])
                    c["entries"] = sorted(curr_s - prev_s)
                    c["exits"]   = sorted(prev_s - curr_s)
                # If n≠30 or previous is also partial: leave entries/exits empty (shown as "données incomplètes")
        # Index by date — also build a fuzzy lookup (PDF announced a few days before effective date)
        official_by_date = {c["rebal_date"]: c for c in comp_pdf}
        def _find_official(rebal_date_str):
            """Match rebal date to PDF date with ±10-day tolerance."""
            if rebal_date_str in official_by_date:
                return official_by_date[rebal_date_str]
            try:
                dt = pd.Timestamp(rebal_date_str)
                for delta in range(-10, 11):
                    candidate = (dt + pd.Timedelta(days=delta)).strftime("%Y-%m-%d")
                    if candidate in official_by_date:
                        return official_by_date[candidate]
            except Exception:
                pass
            return None

        if not rd_data or not rd_data.get("rebalancings"):
            st.info("Aucun rebalancement enregistré.")
        else:
            rebals = rd_data["rebalancings"]

            _section("Résumé")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Rebalancements", len(rebals))
            c2.metric("Turnover moyen", f"{sum(r['turnover'] for r in rebals)/len(rebals)*100:.1f}%")
            c3.metric("Coût moyen",     f"{sum(r['cost_bps'] for r in rebals)/len(rebals):.0f} bps")
            c4.metric("Titres moy.",    f"{sum(r['basket_n'] for r in rebals)/len(rebals):.0f}")
            st.markdown("---")

            # ── Corriger / éditer une composition historique (Kanban) ────────
            with st.expander("Corriger une composition existante", expanded=False):
                st.caption("Sélectionne un rebalancement et corrige sa composition via les tickets.")

                _ed_hist_path   = os.path.join(HALAL_DIR, "brvm_composition_history.json")
                _ed_date_opts   = [r["date"] for r in rebals]
                _ed_label_map   = {r["date"]: r["date_label"] for r in rebals}

                _ed_sel = st.selectbox(
                    "Rebalancement à corriger",
                    _ed_date_opts,
                    format_func=lambda d: _ed_label_map.get(d, d),
                    key="ed_sel_date",
                )

                # Charger la composition sauvegardée pour cette date
                _ed_existing  = _find_official(_ed_sel)
                _ed_saved_comp = sorted([t.upper() for t in (_ed_existing.get("composition", []) if _ed_existing else [])])

                # Univers complet : tous les titres cotés à la BRVM
                try:
                    from scrape_brvm_composition import KNOWN_BRVM_TICKERS as _BRVM_UNIVERSE
                    _all_known = sorted(_BRVM_UNIVERSE)
                except Exception:
                    _all_known = sorted({t.upper() for c in comp_hist_raw for t in c.get("composition", [])})

                # Session state par date — se réinitialise si on change de date
                _ed_key = f"ed_{_ed_sel}"
                if st.session_state.get("_ed_loaded_date") != _ed_sel:
                    st.session_state[_ed_key + "_dans"] = _ed_saved_comp.copy() if _ed_saved_comp else []
                    st.session_state[_ed_key + "_hors"] = sorted(
                        [t for t in _all_known if t not in _ed_saved_comp]
                    )
                    st.session_state["_ed_loaded_date"] = _ed_sel

                _ed_dans = st.session_state[_ed_key + "_dans"]
                _ed_hors = st.session_state[_ed_key + "_hors"]

                # Statut scraping
                _ed_n = len(_ed_saved_comp)
                _ed_color = "#2d7a4f" if _ed_n == 30 else "#c9861a" if _ed_n >= 25 else "#c0392b"
                _ed_status = "Composition complète (30)" if _ed_n == 30 else f"OCR partiel : {_ed_n}/30 tickers extraits"
                st.markdown(f'<span style="font-size:0.85rem;color:{_ed_color};font-weight:600">{_ed_status}</span>', unsafe_allow_html=True)

                # Ajouter un ticker
                _ed_c1, _ed_c2, _ed_c3 = st.columns([2, 1, 1])
                _ed_new_tk = _ed_c1.text_input("Ajouter un ticker manquant", key="ed_new_tk",
                                               placeholder="ex: PALC").strip().upper()
                with _ed_c2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("+ Ajouter", key="ed_add_btn") and _ed_new_tk:
                        if _ed_new_tk not in _ed_dans and _ed_new_tk not in _ed_hors:
                            _ed_dans.append(_ed_new_tk)
                            st.rerun()
                with _ed_c3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("↺ Réinitialiser", key="ed_reset_btn"):
                        st.session_state[_ed_key + "_dans"] = _ed_saved_comp.copy()
                        st.session_state[_ed_key + "_hors"] = sorted(
                            [t for t in _all_known if t not in _ed_saved_comp]
                        )
                        st.rerun()

                # Noms complets des tickers BRVM
                _TICKER_NAMES = {
                    'ABJC': 'Servair Abidjan CI', 'BICB': 'BIC Bénin', 'BICC': 'BICICI',
                    'BNBC': 'Bernabé CI', 'BOAB': 'Bank of Africa Bénin',
                    'BOABF': 'Bank of Africa Burkina', 'BOAC': 'Bank of Africa CI',
                    'BOAM': 'Bank of Africa Mali', 'BOAN': 'Bank of Africa Niger',
                    'BOAS': 'Bank of Africa Sénégal', 'CABC': 'Sicable CI',
                    'CBIBF': 'Coris Bank International Burkina', 'CFAC': 'CFAO CI',
                    'CIEC': 'CIE CI', 'ECOC': 'Ecobank CI',
                    'ETIT': 'ETI TG', 'FTSC': 'Filtisac CI', 'LNBB': 'Loterie Nationale Bénin',
                    'NEIC': 'NEI-CEDA CI', 'NSBC': 'NSIA Banque CI',
                    'NTLC': 'Nestlé CI', 'ONTBF': 'ONATEL Burkina',
                    'ORAC': 'Orange CI', 'ORGT': 'Oragroup Togo',
                    'PALC': 'PalmCI', 'PRSC': 'Tractafric Motors CI',
                    'SAFC': 'SAFCA CI', 'SCRC': 'Sucrivoire CI',
                    'SDCC': 'SODECI', 'SDSC': 'Africa Global Logistics CI',
                    'SEMC': 'Eviosys Packaging Siem CI', 'SGBC': 'Société Générale CI',
                    'SHEC': 'Vivo Energy CI', 'SIBC': 'Société Ivoirienne de Banque',
                    'SICC': 'SICOR CI', 'SIVC': 'Erium CI',
                    'SLBC': 'Solibra CI', 'SMBC': 'SMB CI',
                    'SNTS': 'Sonatel', 'SOGC': 'SOGB CI',
                    'SPHC': 'SAPH CI', 'STAC': 'SETAO CI',
                    'STBC': 'SITAB CI', 'SVOC': 'Movis CI',
                    'TTLC': 'TotalEnergies CI', 'TTLS': 'TotalEnergies Sénégal',
                    'UNLC': 'Unilever CI', 'UNXC': 'Uniwax CI',
                }

                # Barre de recherche + tri
                _sr_col, _sort_col = st.columns([3, 2])
                _ed_search = _sr_col.text_input(
                    "Rechercher", key="ed_search",
                    placeholder="ticker ou nom…"
                ).strip().upper()
                _ed_sort = _sort_col.selectbox(
                    "Trier par", ["Alphabétique", "Ordre original"],
                    key="ed_sort"
                )

                def _sort_list(lst):
                    if _ed_sort == "Alphabétique":
                        return sorted(lst, key=lambda t: _TICKER_NAMES.get(t, t).lower())
                    return lst

                def _match(tk):
                    if not _ed_search:
                        return True
                    name = _TICKER_NAMES.get(tk, "").upper()
                    return _ed_search in tk or _ed_search in name

                # En-têtes Kanban
                st.markdown(
                    f'<div style="display:flex;gap:12px;margin:8px 0 4px 0">'
                    f'<div style="flex:1;text-align:center;font-weight:600;font-size:12px;'
                    f'padding:7px;background:rgba(184,151,63,0.08);border-radius:2px;color:#b8973f;letter-spacing:0.06em;text-transform:uppercase">'
                    f'Dans l\'indice ({len(_ed_dans)})</div>'
                    f'<div style="flex:1;text-align:center;font-weight:600;font-size:12px;'
                    f'padding:7px;background:#fdf2f1;border-radius:2px;color:#c0392b;letter-spacing:0.06em;text-transform:uppercase">'
                    f'Hors de l\'indice ({len(_ed_hors)})</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                _ed_col_d, _ed_col_h = st.columns(2)

                with _ed_col_d:
                    for _tk in _sort_list(list(_ed_dans)):
                        if not _match(_tk):
                            continue
                        _is_added = _tk not in _ed_saved_comp
                        _bg = "#f2f8f4" if _is_added else "rgba(184,151,63,0.07)"
                        _bd = "#2d7a4f" if _is_added else "#b8973f"
                        _fc = "#2d7a4f" if _is_added else "#b8973f"
                        _tag = "AJOUTÉ" if _is_added else ""
                        _name = _TICKER_NAMES.get(_tk, "")
                        _cc, _cb = st.columns([5, 1])
                        _cc.markdown(
                            f'<div style="background:{_bg};border-left:3px solid {_bd};'
                            f'border-radius:4px;padding:5px 10px;margin-bottom:3px">'
                            f'<b style="color:{_fc};font-size:13px">{_tk}</b>'
                            f'<span style="font-size:11px;color:#7d8fa3;margin-left:6px">{_name}</span>'
                            f'<span style="float:right;font-size:11px;color:#7d8fa3">{_tag}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        if _cb.button("→", key=f"ed_out_{_ed_sel}_{_tk}"):
                            _ed_dans.remove(_tk)
                            _ed_hors.append(_tk)
                            st.rerun()

                with _ed_col_h:
                    for _tk in _sort_list(list(_ed_hors)):
                        if not _match(_tk):
                            continue
                        _name = _TICKER_NAMES.get(_tk, "")
                        _cb2, _cc2 = st.columns([1, 5])
                        if _cb2.button("←", key=f"ed_in_{_ed_sel}_{_tk}"):
                            _ed_hors.remove(_tk)
                            _ed_dans.append(_tk)
                            st.rerun()
                        _cc2.markdown(
                            f'<div style="background:#fdf2f1;border-left:2px solid #c0392b;'
                            f'border-radius:2px;padding:5px 10px;margin-bottom:3px">'
                            f'<b style="color:#c0392b;font-size:13px">{_tk}</b>'
                            f'<span style="font-size:11px;color:#7d8fa3;margin-left:6px">{_name}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                # Résumé
                _ed_added   = [t for t in _ed_dans if t not in _ed_saved_comp]
                _ed_removed = [t for t in _ed_hors  if t in _ed_saved_comp]
                if _ed_added or _ed_removed:
                    _rs1, _rs2 = st.columns(2)
                    if _ed_added:   _rs1.success(f"**+{len(_ed_added)} ajouté(s) :** {' · '.join(_ed_added)}")
                    if _ed_removed: _rs2.error(  f"**-{len(_ed_removed)} retiré(s) :** {' · '.join(_ed_removed)}")

                # Compteur
                _ed_n_new = len(_ed_dans)
                _ed_cnt_color = "#2d7a4f" if _ed_n_new == 30 else "#c9861a" if _ed_n_new >= 25 else "#c0392b"
                st.markdown(
                    f'<span style="font-size:0.85rem;color:{_ed_cnt_color};font-weight:600">'
                    f'{_ed_n_new} tickers {"OK" if _ed_n_new == 30 else "(attendu 30)"}</span>',
                    unsafe_allow_html=True,
                )

                # Enregistrer + recalcul
                st.markdown("<br>", unsafe_allow_html=True)
                _save_col, _rerun_col = st.columns(2)
                _do_save    = _save_col.button("Enregistrer la correction", key="ed_save_btn",
                                               type="primary", disabled=_ed_n_new < 25)
                _do_rerun   = _rerun_col.button("Enregistrer + recalculer le backtest",
                                                key="ed_rerun_btn", disabled=_ed_n_new < 25)

                if _do_save or _do_rerun:
                    # Auto-calculer entries/exits vs rebalancement précédent
                    _all_hist = sorted(comp_pdf, key=lambda x: x["rebal_date"])
                    _prev_comp = set()
                    for _hh in _all_hist:
                        if _hh["rebal_date"] < _ed_sel:
                            _prev_comp = set(_hh.get("composition", []))
                    _auto_entries = sorted(set(_ed_dans) - _prev_comp) if _prev_comp else []
                    _auto_exits   = sorted(_prev_comp - set(_ed_dans))  if _prev_comp else []

                    _hist_data = load_json(_ed_hist_path) or []
                    _hist_data = [h for h in _hist_data if h.get("rebal_date") != _ed_sel]
                    _hist_data.append({
                        "rebal_date":  _ed_sel,
                        "scrape_ts":   pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                        "pdf_slug":    _ed_existing.get("pdf_slug", "manual_correction") if _ed_existing else "manual_correction",
                        "n_tickers":   _ed_n_new,
                        "composition": sorted(_ed_dans),
                        "entries":     _auto_entries,
                        "exits":       _auto_exits,
                    })
                    _hist_data = sorted(_hist_data, key=lambda x: x.get("rebal_date", ""))
                    try:
                        with open(_ed_hist_path, "w", encoding="utf-8") as _fh:
                            json.dump(_hist_data, _fh, ensure_ascii=False, indent=2)
                        _dated = [h for h in _hist_data if h.get("n_tickers", 0) >= 25]
                        if _dated:
                            with open(os.path.join(HALAL_DIR, "brvm_composition_latest.json"), "w", encoding="utf-8") as _fh:
                                json.dump(_dated[-1], _fh, ensure_ascii=False, indent=2)

                        st.success(f"Composition {_ed_label_map.get(_ed_sel, _ed_sel)} corrigée ({_ed_n_new} tickers).")

                        st.cache_data.clear()
                        st.rerun()
                    except Exception as _e:
                        st.error(f"Erreur sauvegarde : {_e}")

            st.markdown("---")

            def _color_cell(val):
                if isinstance(val, (int, float)):
                    c = "#2d7a4f" if val > 0 else "#c0392b" if val < 0 else ""
                    return f"color: {c}; font-weight: 500"
                return ""

            for i in range(len(rebals) - 1, -1, -1):
                rebal = rebals[i]
                prev  = rebals[i - 1] if i > 0 else None

                # ETF basket changes (basket-to-basket)
                curr_basket = {b["ticker"] for b in rebal.get("basket", [])}
                prev_basket = {b["ticker"] for b in prev.get("basket", [])} if prev else set()
                etf_entries = sorted(curr_basket - prev_basket)
                etf_exits   = sorted(prev_basket - curr_basket)

                # Full index at this date = basket + excluded
                curr_index = curr_basket | {e["ticker"] for e in rebal.get("excluded", [])}
                prev_index = prev_basket | {e["ticker"] for e in (prev.get("excluded", []) if prev else [])}

                # Official Indice Dividende change from PDF only — no fallback reconstruction
                official = _find_official(rebal["date"])
                if official:
                    idx_entries  = official.get("entries", [])
                    idx_exits    = official.get("exits",   [])
                    idx_n        = official.get("n_tickers", 0)
                    idx_source   = f"Avis BRVM {official.get('rebal_date', '')}"
                    idx_comp     = official.get("composition", [])
                    idx_complete = (idx_n == 30)
                else:
                    idx_entries  = []
                    idx_exits    = []
                    idx_n        = 0
                    idx_source   = None
                    idx_comp     = []
                    idx_complete = False

                # PDF deposit
                _pdf_dir  = os.path.join(HALAL_DIR, "pdfs")
                _pdf_path = os.path.join(_pdf_dir, f"rebal_{rebal['date']}.pdf")
                _pdf_exists = os.path.exists(_pdf_path)

                # Expander label — only show indice tag when we have reliable entries/exits
                idx_tag = ""
                if official and (idx_entries or idx_exits):
                    idx_tag = f"  ·  indice +{len(idx_entries)}/-{len(idx_exits)}"
                pdf_tag = "  · [PDF]" if _pdf_exists else ""
                _is_verified = _verified_rebals.get(rebal["date"], False)
                _wchk = rebal.get("weight_check", {})
                _wchk_ok = _wchk.get("ok", True)
                _wchk_sum = _wchk.get("sum_brvm30_weights", None)
                _wchk_zero = _wchk.get("tickers_w_zero", [])
                _wchk_tag = "" if _wchk_ok else "  (!)"
                exp_label = (
                    f"{rebal['date_label']}  ·  TO {rebal['turnover']*100:.1f}%  ·  {rebal['cost_bps']:.0f} bps"
                    + idx_tag + pdf_tag + _wchk_tag
                )

                _col_verif, _col_exp = st.columns([0.07, 0.93])
                with _col_verif:
                    st.markdown("<div style='margin-top:6px'>", unsafe_allow_html=True)
                    _new_verif = st.checkbox(
                        "v",
                        value=_is_verified,
                        key=f"verif_{rebal['date']}",
                        help="Cocher pour marquer ce rebalancement comme vérifié",
                        label_visibility="collapsed",
                    )
                    st.markdown("</div>", unsafe_allow_html=True)
                    if _new_verif != _is_verified:
                        _verified_rebals[rebal["date"]] = _new_verif
                        st.session_state.verified_gh_cache = _verified_rebals
                        # Sauvegarder sur GitHub (visible partout) ou en local
                        if _gh_save_verified(_verified_rebals, _verified_sha):
                            # Rafraîchir le SHA pour le prochain save
                            _, new_sha = _gh_get_verified()
                            st.session_state.verified_gh_sha = new_sha
                        else:
                            with open(_verified_path, "w", encoding="utf-8") as _vf:
                                json.dump(_verified_rebals, _vf, ensure_ascii=False, indent=2)
                        load_json_fresh.clear()
                        st.rerun()

                with _col_exp:
                    with st.expander(exp_label + (" (vérifié)" if _is_verified else ""), expanded=(i == len(rebals) - 1)):
                        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                        col_m1.metric("Turnover",   f"{rebal['turnover']*100:.1f}%")
                        col_m2.metric("Coût",       f"{rebal['cost_bps']:.0f} bps")
                        col_m3.metric("Couverture", f"{rebal.get('coverage', 0)*100:.1f}%")
                        col_m4.metric("Titres ETF", str(rebal["basket_n"]))

                        if _wchk:
                            if _wchk_ok:
                                st.success(f"Poids OK — somme Indice Dividende = {_wchk_sum:.1%}")
                            else:
                                _warn_msg = f"Somme poids = {_wchk_sum:.1%}"
                                if _wchk_zero:
                                    _warn_msg += f" · Titres sans poids : **{', '.join(_wchk_zero)}** (ajoute leur nombre de titres dans `BASE DE DONNEES BRVM.xlsm`)"
                                st.warning(_warn_msg)

                        st.markdown("---")
                        col_idx, col_etf = st.columns(2)

                        # ── Côté indice ───────────────────────────────────────────
                        with col_idx:
                            src_label = (
                                f'<span style="font-weight:400;color:#7d8fa3;text-transform:none;letter-spacing:0"> — {idx_source}</span>'
                                if idx_source else
                                '<span style="font-weight:400;color:#f59e0b;text-transform:none;letter-spacing:0"> — PDF non disponible</span>'
                            )
                            st.markdown(
                                f'<p class="cgf-section">Indice Indice Dividende{src_label}</p>',
                                unsafe_allow_html=True,
                            )
                            if not idx_source:
                                st.caption("Données officielles Indice Dividende non disponibles pour cette date. "
                                           "Utilise le panneau d'édition manuelle ci-dessus pour saisir la composition.")
                            else:
                                # Avertissement OCR partiel
                                if not idx_complete:
                                    st.markdown(
                                        f'<span style="font-size:0.75rem;color:#f59e0b">OCR partiel — {idx_n}/30 tickers extraits. '
                                        f'Les entrées/sorties ci-dessous viennent du PDF (fiables). '
                                        f'Corrige la composition via le panneau d\'édition si nécessaire.</span>',
                                        unsafe_allow_html=True,
                                    )
                                if idx_entries:
                                    st.markdown(
                                        f'<span style="color:#2d7a4f;font-size:0.8rem;font-weight:500">'
                                        f'Entrées ({len(idx_entries)})</span> &nbsp; '
                                        + " &nbsp;·&nbsp; ".join(
                                            [f'<span style="background:#f2f8f4;color:#2d7a4f;border-radius:2px;padding:1px 7px;font-size:0.74rem">{t}</span>'
                                             for t in idx_entries]
                                        ),
                                        unsafe_allow_html=True,
                                    )
                                if idx_exits:
                                    st.markdown(
                                        f'<span style="color:#c0392b;font-size:0.8rem;font-weight:500">'
                                        f'Sorties ({len(idx_exits)})</span> &nbsp; '
                                        + " &nbsp;·&nbsp; ".join(
                                            [f'<span style="background:#fdf2f1;color:#c0392b;border-radius:2px;padding:1px 7px;font-size:0.74rem">{t}</span>'
                                             for t in idx_exits]
                                        ),
                                        unsafe_allow_html=True,
                                    )
                                if not idx_entries and not idx_exits:
                                    st.markdown(
                                        '<span style="font-size:0.75rem;color:#f59e0b">Entrees/sorties non disponibles — '
                                        'l\'OCR n\'a pas trouvé les ENTRANTS/SORTANTS dans ce PDF. '
                                        'Saisis-les via le panneau d\'édition manuelle.</span>',
                                        unsafe_allow_html=True,
                                    )

                            if idx_comp:
                                st.markdown("<br>", unsafe_allow_html=True)
                                n_label = f"{len(idx_comp)}/30" if len(idx_comp) != 30 else "30"
                                st.caption(f"Composition ({n_label} titres) — bleu = dans l'ETF, gris = exclu liquidité")
                                _etf_set = curr_basket
                                _ent_set = set(idx_entries)
                                _exi_set = set(idx_exits)
                                html_comp = '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:4px">'
                                for t in sorted(idx_comp):
                                    if t in _ent_set:
                                        bg, fg = "#f2f8f4", "#2d7a4f"
                                    elif t in _exi_set:
                                        bg, fg = "#fdf2f1", "#c0392b"
                                    elif t in _etf_set:
                                        bg, fg = "rgba(184,151,63,0.1)", "#b8973f"
                                    else:
                                        bg, fg = "#f5f2ed", "#7d8fa3"
                                    html_comp += (
                                        f'<span style="background:{bg};color:{fg};border-radius:4px;'
                                        f'padding:2px 7px;font-size:0.72rem;font-weight:500">{t}</span>'
                                    )
                                html_comp += "</div>"
                                st.markdown(html_comp, unsafe_allow_html=True)

                        # ── Côté ETF ──────────────────────────────────────────────
                        with col_etf:
                            st.markdown('<p class="cgf-section">Panier ETF</p>', unsafe_allow_html=True)
                            if etf_entries:
                                st.markdown(
                                    f'<span style="color:#2d7a4f;font-size:0.8rem;font-weight:500">'
                                    f'Entrées panier ({len(etf_entries)})</span> &nbsp; '
                                    + " &nbsp;·&nbsp; ".join(
                                        [f'<span style="background:#f2f8f4;color:#2d7a4f;border-radius:2px;padding:1px 7px;font-size:0.74rem">{t}</span>'
                                         for t in etf_entries]
                                    ),
                                    unsafe_allow_html=True,
                                )
                            if etf_exits:
                                st.markdown(
                                    f'<span style="color:#c0392b;font-size:0.8rem;font-weight:500">'
                                    f'Sorties panier ({len(etf_exits)})</span> &nbsp; '
                                    + " &nbsp;·&nbsp; ".join(
                                        [f'<span style="background:#fdf2f1;color:#c0392b;border-radius:2px;padding:1px 7px;font-size:0.74rem">{t}</span>'
                                         for t in etf_exits]
                                    ),
                                    unsafe_allow_html=True,
                                )
                            if not etf_entries and not etf_exits:
                                st.caption("Pas de changement de panier.")

                            if rebal.get("excluded"):
                                excl_names = [e["ticker"] for e in rebal["excluded"]]
                                st.caption(f"{len(excl_names)} exclus liquidité : {', '.join(excl_names)}")

                            if rebal.get("basket"):
                                st.markdown("<br>", unsafe_allow_html=True)
                                df_b = pd.DataFrame(rebal["basket"])
                                df_b["w_etf"]       = (df_b["w_etf"] * 100).round(4)
                                df_b["w_brvm30"]    = (df_b.get("w_brvm30", df_b["w_etf"]) * 100).round(4)
                                df_b["delta"]       = (df_b["delta"] * 100).round(4) if "delta" in df_b.columns else 0.0
                                # Fallback : reconstruire trade_mfcfa / days_exec depuis orders si absents du basket
                                _orders_lookup = {
                                    o["ticker"]: {
                                        "trade_mfcfa": round(o.get("montant_mfcfa", 0) * (1 if o.get("sens") == "ACHETER" else -1), 1),
                                        "days_exec":   round(o.get("days_exec", 0), 1),
                                    }
                                    for o in rebal.get("orders", [])
                                }
                                if "trade_mfcfa" not in df_b.columns or df_b["trade_mfcfa"].abs().sum() == 0:
                                    df_b["trade_mfcfa"] = df_b["ticker"].map(lambda t: _orders_lookup.get(t, {}).get("trade_mfcfa", 0.0))
                                if "days_exec" not in df_b.columns or df_b["days_exec"].abs().sum() == 0:
                                    df_b["days_exec"]   = df_b["ticker"].map(lambda t: _orders_lookup.get(t, {}).get("days_exec", 0.0))
                                if "force"       not in df_b.columns: df_b["force"]       = False
                                if "force_otc"   not in df_b.columns: df_b["force_otc"]   = False
                                df_b["trade_mfcfa"] = df_b["trade_mfcfa"].round(1)
                                df_b["force"]       = df_b.apply(
                                    lambda r: "OTC" if (r.get("force_otc") or r.get("force")) else "", axis=1
                                )
                                # Ajouter les exits (w_new=0) présents dans orders mais pas dans basket
                                _basket_tickers = set(df_b["ticker"].tolist())
                                _exit_rows = [
                                    {
                                        "ticker":      o["ticker"],
                                        "w_etf":       0.0,
                                        "w_brvm30":    0.0,
                                        "delta":       round(o.get("delta_pct", 0), 4),
                                        "trade_mfcfa": round(o.get("montant_mfcfa", 0) * -1, 1),
                                        "days_exec":   round(o.get("days_exec", 0), 1),
                                        "force":       "",
                                        "force_otc":   False,
                                    }
                                    for o in rebal.get("orders", [])
                                    if o.get("w_new_pct", -1) == 0 and o["ticker"] not in _basket_tickers
                                ]
                                if _exit_rows:
                                    df_b = pd.concat([df_b, pd.DataFrame(_exit_rows)], ignore_index=True)
                                _esnap = set(etf_entries)
                                _xsnap = set(etf_exits)
                                df_b["mvt"] = df_b["ticker"].map(
                                    lambda t: "+" if t in _esnap else ("-" if t in _xsnap else "")
                                )
                                st.dataframe(
                                    df_b.rename(columns={
                                        "ticker": "Ticker", "w_etf": "Poids %",
                                        "w_brvm30": "Indice Dividende %", "delta": "Delta %",
                                        "trade_mfcfa": "Trade (MFCFA)", "days_exec": "J.",
                                        "force": "OTC", "mvt": "Mvt",
                                    }).style.map(_color_cell, subset=["Trade (MFCFA)"]),
                                    width='stretch', hide_index=True,
                                    height=min(400, 44 + len(df_b) * 36),
                                    column_order=["Ticker", "OTC", "Poids %", "Indice Dividende %",
                                                  "Trade (MFCFA)", "J.", "Mvt"],
                                )
                                total_buy  = df_b["trade_mfcfa"].clip(lower=0).sum()
                                total_sell = df_b["trade_mfcfa"].clip(upper=0).sum()
                                tc1, tc2, tc3 = st.columns(3)
                                tc1.metric("Achats", f"+{total_buy:,.1f} MFCFA")
                                tc2.metric("Ventes", f"{total_sell:,.1f} MFCFA")
                                tc3.metric("Net",    f"{total_buy + total_sell:,.1f} MFCFA")

                        # ── PDF officiel BRVM ─────────────────────────────────────
                        st.markdown("---")
                        _pdf_col1, _pdf_col2 = st.columns([3, 2])
                        with _pdf_col1:
                            st.markdown('<p class="cgf-section" style="margin-bottom:6px">Avis officiel BRVM (PDF)</p>', unsafe_allow_html=True)
                            if _pdf_exists:
                                with open(_pdf_path, "rb") as _pf:
                                    st.download_button(
                                        "Telecharger PDF",
                                        data=_pf.read(),
                                        file_name=f"Indice Dividende_rebal_{rebal['date']}.pdf",
                                        mime="application/pdf",
                                        key=f"dl_pdf_{rebal['date']}",
                                    )
                                _sz = os.path.getsize(_pdf_path) // 1024
                                st.caption(f"Deposé · {_sz} Ko · {rebal['date']}")
                            elif official and official.get("pdf_url"):
                                st.caption(f"Source BRVM.org : {official['pdf_url']}")
                            else:
                                st.caption("Aucun PDF déposé pour ce rebalancement.")
                        with _pdf_col2:
                            _up_label = "Remplacer le PDF" if _pdf_exists else "Déposer le PDF officiel"
                            _uploaded = st.file_uploader(
                                _up_label, type=["pdf"],
                                key=f"up_pdf_{rebal['date']}",
                                label_visibility="visible",
                            )
                            if _uploaded is not None:
                                os.makedirs(_pdf_dir, exist_ok=True)
                                with open(_pdf_path, "wb") as _pf:
                                    _pf.write(_uploaded.getbuffer())
                                st.success("PDF enregistré.")
                                st.cache_data.clear()
                                st.rerun()


    # ── Prochain rebalancement (panneau d'action) ─────────────────────────────
    elif _lsec == "rebalancement_action":
        _nl_reb    = load_json_fresh(nav_latest_path) or {}
        _sh_reb    = load_json(os.path.join(HALAL_DIR, "sika_history.json")) or {}
        _bch_reb   = load_json(os.path.join(HALAL_DIR, "brvm_composition_history.json")) or []

        _last_rebal_str = _nl_reb.get("last_rebal_date", "N/A")
        _aum_reb        = float(_nl_reb.get("aum_mfcfa", 5000))

        # Calcul prochain rebalancement
        _rebal_months = {1, 4, 7, 10}
        _today_ts = pd.Timestamp.now()

        def _next_rebal_date(from_ts):
            # Si le mois courant est un mois de rebal ET que le dernier rebal
            # était dans le trimestre précédent → le rebal est aujourd'hui
            if from_ts.month in _rebal_months:
                this_rebal = pd.Timestamp(from_ts.year, from_ts.month, 1) + pd.offsets.BDay(0)
                last_done  = pd.Timestamp(_last_rebal_str) if _last_rebal_str and _last_rebal_str != "N/A" else None
                if last_done is None or last_done < this_rebal:
                    return this_rebal
            for m in range(1, 5):
                cm = ((from_ts.month - 1 + m) % 12) + 1
                cy = from_ts.year + ((from_ts.month - 1 + m) // 12)
                if cm in _rebal_months:
                    first = pd.Timestamp(cy, cm, 1)
                    return first + pd.offsets.BDay(0)
            return None

        _next_rebal_ts  = _next_rebal_date(_today_ts)
        _next_rebal_str = _next_rebal_ts.strftime("%Y-%m-%d") if _next_rebal_ts else "N/A"
        _days_left      = int((_next_rebal_ts - _today_ts).days) if _next_rebal_ts else 999

        # Lire rebal_pending.json pour pré-remplir la date si un rebal est en attente
        _pending_rebal_date = None
        _pending_path = os.path.join(BASE, "data", "rebal_pending.json")
        if os.path.exists(_pending_path):
            try:
                _pending_data = json.load(open(_pending_path, encoding="utf-8"))
                if _pending_data.get("status") == "pending":
                    _pending_rebal_date = _pending_data.get("proposed_rebal_date")
            except Exception:
                pass
        _default_rebal_date = _pending_rebal_date or _next_rebal_str

        st.markdown("<br>", unsafe_allow_html=True)
        _section("Prochain rebalancement annuel")

        _mc1, _mc2, _mc3 = st.columns(3)
        _mc1.metric("Dernier rebalancement", _last_rebal_str)
        _mc2.metric("Prochain rebalancement", _next_rebal_str)
        _mc3.metric("Jours restants", f"{max(0, _days_left)} j")

        st.markdown("---")

        # ── Étape 1 : Prévisualisation ─────────────────────────────────────
        st.markdown("#### Étape 1 — Prévisualisation des ordres")
        st.caption("Calcule le nouveau panier sans modifier aucun fichier.")

        _prev_date_input = st.text_input(
            "Date du rebalancement",
            value=_default_rebal_date,
            key="rebal_date_input",
            help="Format YYYY-MM-DD. Par défaut : date du rebal en attente ou prochain jour ouvré de trimestre.",
        )

        if st.button("Calculer le nouveau panier (dry-run)", key="btn_rebal_preview"):
            with st.spinner("Calcul en cours…"):
                _script_path = os.path.join(BASE, "scripts", "rebalance_live.py")
                _res_prev = subprocess.run(
                    [sys.executable, _script_path, "--dry-run", "--force",
                     "--date", _prev_date_input],
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                )
                st.session_state["rebal_preview_out"]  = _res_prev.stdout
                st.session_state["rebal_preview_err"]  = _res_prev.stderr
                st.session_state["rebal_preview_date"] = _prev_date_input
                st.session_state["rebal_applied"]      = False

        if st.session_state.get("rebal_preview_out"):
            _raw_out = st.session_state["rebal_preview_out"]
            _JSON_MARKER = "### JSON_ORDERS ###"
            if _JSON_MARKER in _raw_out:
                _text_part, _json_part = _raw_out.split(_JSON_MARKER, 1)
            else:
                _text_part, _json_part = _raw_out, ""
            with st.expander("Détails du calcul (texte brut)", expanded=False):
                st.code(_text_part.strip(), language="text")

            if _json_part.strip():
                try:
                    _orders = json.loads(_json_part.strip())
                    _df_full = pd.DataFrame(_orders)

                    # Masques couleur depuis le df complet (OTC/CAP/section)
                    _m_otc     = _df_full.get('otc',     pd.Series([False]*len(_df_full))).fillna(False).astype(bool).values
                    _m_cap     = _df_full.get('capped',  pd.Series([False]*len(_df_full))).fillna(False).astype(bool).values
                    _m_section = _df_full.get('section', pd.Series(['']*len(_df_full))).fillna('').values

                    # Colonnes affichées (sans flags booléens)
                    _col_map = {
                        'section': 'Section', 'ticker': 'Ticker', 'sens': 'Sens',
                        'delta_pct': 'Delta %', 'montant_mfcfa': 'Montant (M)',
                        'w_old_pct': 'Ancien %', 'w_new_pct': 'Nouveau %',
                        'w_brvm30_pct': 'Indice %',
                        'adv_mfcfa': 'ADV (M)', 'days_exec': 'Jours',
                    }
                    _display_cols = [k for k in _col_map if k in _df_full.columns]
                    _df_display = _df_full[_display_cols].rename(columns=_col_map).reset_index(drop=True)

                    def _color_row(row):
                        i = row.name
                        n = len(row)
                        if _m_otc[i]:
                            return ['background-color: #ffcc80'] * n   # orange
                        if _m_cap[i]:
                            return ['background-color: #ce93d8'] * n   # violet
                        if _m_section[i] == 'Sortant':
                            return ['background-color: #ef9a9a'] * n   # rouge
                        if _m_section[i] == 'Entrant':
                            return ['background-color: #a5d6a7'] * n   # vert
                        return [''] * n

                    _styled = (
                        _df_display.style
                        .apply(_color_row, axis=1)
                        .format({'Delta %': '{:+.2f}', 'Montant (M)': '{:.1f}',
                                 'Ancien %': '{:.2f}', 'Nouveau %': '{:.2f}',
                                 'Indice %': '{:.2f}', 'ADV (M)': '{:.1f}',
                                 'Jours': '{:.1f}'})
                    )
                    st.markdown("**Légende :** 🟠 OTC (bloc négocié)  🟣 CAP (limité par ADV)  🔴 Sortant  🟢 Entrant")
                    st.dataframe(_styled, hide_index=True, use_container_width=True)
                except Exception as _e:
                    st.warning(f"Impossible d'afficher le tableau coloré : {_e}")

            if st.session_state.get("rebal_preview_err"):
                with st.expander("Erreurs / avertissements"):
                    st.code(st.session_state["rebal_preview_err"], language="text")

            # ── Étape 2 : Application ──────────────────────────────────────
            st.markdown("---")
            st.markdown("#### Étape 2 — Appliquer le rebalancement")

            if st.session_state.get("rebal_applied"):
                st.success("Rebalancement déjà appliqué dans cette session.")
            else:
                st.warning(
                    "**Action irréversible.** Vérifiez les ordres ci-dessus "
                    "avant de confirmer. Les fichiers `nav_latest.json`, "
                    "`dashboard_data.json` et `rebal_detail.json` seront mis à jour "
                    "et un commit sera poussé sur GitHub."
                )

                _confirm_val = st.text_input(
                    "Tapez **CONFIRMER** pour activer le bouton",
                    key="rebal_confirm_text",
                    placeholder="CONFIRMER",
                )
                _btn_disabled = (_confirm_val.strip() != "CONFIRMER")

                if st.button(
                    "Appliquer le rebalancement",
                    key="btn_rebal_apply",
                    type="primary",
                    disabled=_btn_disabled,
                ):
                    _apply_date = st.session_state.get("rebal_preview_date") or _pending_rebal_date or _next_rebal_str
                    st.info(f"Date du rebalancement : **{_apply_date}** — relance le dry-run si incorrect.")
                    with st.spinner(f"Application du rebalancement {_apply_date}…"):
                        _script_path = os.path.join(BASE, "scripts", "rebalance_live.py")
                        _res_apply = subprocess.run(
                            [sys.executable, _script_path, "--apply", "--force",
                             "--date", _apply_date],
                            capture_output=True, text=True, encoding="utf-8", errors="replace",
                        )

                    if _res_apply.returncode != 0:
                        st.error("Erreur lors de l'application du rebalancement.")
                        st.code(_res_apply.stdout + "\n" + _res_apply.stderr, language="text")
                    else:
                        st.success(f"Rebalancement {_apply_date} appliqué.")
                        st.code(_res_apply.stdout, language="text")
                        st.session_state["rebal_applied"] = True

                        # ── Commit + push Git ──────────────────────────────
                        with st.spinner("Commit et push Git…"):
                            _git_add = subprocess.run(
                                ["git", "-C", BASE, "add",
                                 "data/nav_latest.json",
                                 "data/dashboard_data.json",
                                 "data/rebal_detail.json",
                                 "data/sika_history.json"],
                                capture_output=True, text=True,
                            )
                            _git_commit = subprocess.run(
                                ["git", "-C", BASE, "commit", "-m",
                                 f"rebal: rebalancement annuel {_apply_date}"],
                                capture_output=True, text=True,
                            )
                            _git_pull = subprocess.run(
                                ["git", "-C", BASE, "pull", "--no-rebase", "--no-edit", "origin", "main"],
                                capture_output=True, text=True,
                            )
                            _git_push = subprocess.run(
                                ["git", "-C", BASE, "push", "origin", "main"],
                                capture_output=True, text=True,
                            )
                        _push_ok = _git_push.returncode == 0
                        if _push_ok:
                            st.success("Pushé sur GitHub — le dashboard se mettra à jour.")
                        else:
                            st.warning("Rebalancement appliqué localement mais push échoué.")
                            st.code(_git_push.stdout + _git_push.stderr)

                        st.cache_data.clear()
                        st.rerun()

    # ── AP ────────────────────────────────────────────────────────────────────
    elif _lsec == "ap":
        st.markdown("<br>", unsafe_allow_html=True)
        _section("Simulateur AP — Opportunité d'arbitrage")

        _nl_ap   = load_json_fresh(nav_latest_path) or {}
        _bask_ap = _nl_ap.get("basket", [])
        _inav_ap = float(_nl_ap.get("vl_par_part_fcfa") or 0)
        _n_total_ap = int(_launch_data.get("n_parts", 50000))

        if not _inav_ap or not _bask_ap:
            st.warning("Données iNAV indisponibles — impossible de simuler.")
        else:
            # ── Paramètres ────────────────────────────────────────────────
            _apc1, _apc2, _apc3 = st.columns([2, 1, 1])
            with _apc1:
                _ap_etf_px = st.number_input(
                    "Prix de marché ETF (FCFA/part)",
                    min_value=float(_inav_ap * 0.70),
                    max_value=float(_inav_ap * 1.30),
                    value=float(_inav_ap),
                    step=100.0,
                    format="%.0f",
                    key="ap_etf_px",
                    help="Prix coté sur le marché secondaire BRVM",
                )
            with _apc2:
                _ap_cout = st.number_input(
                    "Coûts aller-retour (%)",
                    min_value=0.0, max_value=5.0,
                    value=1.2,
                    step=0.1,
                    format="%.2f",
                    key="ap_cout",
                    help="Total frais achat + vente (courtage + taxes BRVM)",
                )
            with _apc3:
                _ap_unit = st.number_input(
                    "Taille unité AP (parts)",
                    min_value=1000, max_value=_n_total_ap,
                    value=min(5000, _n_total_ap),
                    step=1000,
                    key="ap_unit",
                )

            _ap_cout_dec  = _ap_cout / 100.0
            _ap_cout_demi = _ap_cout_dec / 2.0
            _ap_prem_pct  = (_ap_etf_px - _inav_ap) / _inav_ap * 100
            _ap_notionnel = _inav_ap * _ap_unit

            # Création : AP achète panier → livre au fonds → reçoit ETF → vend ETF
            _ap_profit_c = (
                (_ap_etf_px - _inav_ap) * _ap_unit
                - (_inav_ap + _ap_etf_px) * _ap_unit * _ap_cout_demi
            )
            # Rachat : AP achète ETF → livre au fonds → reçoit panier → vend panier
            _ap_profit_r = (
                (_inav_ap - _ap_etf_px) * _ap_unit
                - (_inav_ap + _ap_etf_px) * _ap_unit * _ap_cout_demi
            )

            _ap_breakeven = _ap_cout_dec * 100  # ≈ prime minimale pour couvrir les frais

            if abs(_ap_prem_pct) <= _ap_breakeven / 2:
                _ap_reco, _ap_reco_col, _ap_reco_bg = "NEUTRE", "#6b7280", "#f3f4f6"
            elif _ap_prem_pct > 0:
                _ap_reco, _ap_reco_col, _ap_reco_bg = "CRÉER", POS_COLOR, "#f0fdf4"
            else:
                _ap_reco, _ap_reco_col, _ap_reco_bg = "RACHETER", NEG_COLOR, "#fdf2f2"

            _ap_best_profit = _ap_profit_c if _ap_prem_pct >= 0 else _ap_profit_r
            _ap_sign = "+" if _ap_prem_pct >= 0 else ""

            # ── KPIs ──────────────────────────────────────────────────────
            _kpi_html(
                ("iNAV (FCFA/part)",  f"{_inav_ap:,.0f}"),
                ("Prix marché ETF",   f"{_ap_etf_px:,.0f}"),
                ("Prime / Décote",    f"{_ap_sign}{_ap_prem_pct:.3f}%"),
                ("Seuil rentabilité", f"±{_ap_breakeven:.2f}%"),
            )

            # ── Recommandation + P&L ──────────────────────────────────────
            _ap_rcol, _ap_plcol = st.columns(2)
            with _ap_rcol:
                st.markdown(f"""
                <div style="border-radius:10px;background:{_ap_reco_bg};border:2px solid {_ap_reco_col};
                            padding:22px;text-align:center;margin-top:10px">
                  <div style="font-size:12px;color:#6b7280;letter-spacing:.05em;margin-bottom:6px">RECOMMANDATION AP</div>
                  <div style="font-size:32px;font-weight:800;color:{_ap_reco_col}">{_ap_reco}</div>
                  <div style="font-size:12px;color:#9ca3af;margin-top:6px">{_ap_unit:,} parts · {_ap_cout:.2f}% de coûts</div>
                </div>""", unsafe_allow_html=True)
            with _ap_plcol:
                _ap_pl_col = POS_COLOR if _ap_best_profit > 0 else (NEG_COLOR if _ap_best_profit < 0 else "#6b7280")
                _ap_pl_pct = _ap_best_profit / _ap_notionnel * 100 if _ap_notionnel else 0
                st.markdown(f"""
                <div style="border-radius:10px;background:#f9fafb;border:1px solid #e5e7eb;
                            padding:22px;text-align:center;margin-top:10px">
                  <div style="font-size:12px;color:#6b7280;letter-spacing:.05em;margin-bottom:6px">P&L NET ESTIMÉ</div>
                  <div style="font-size:32px;font-weight:800;color:{_ap_pl_col}">{_ap_best_profit:+,.0f} FCFA</div>
                  <div style="font-size:12px;color:#9ca3af;margin-top:6px">{_ap_pl_pct:+.4f}% du notionnel</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Graphique P&L selon prime ─────────────────────────────────
            _section("Profit AP en fonction de la prime / décote")
            import numpy as _np_ap
            _ap_px_arr   = _np_ap.linspace(_inav_ap * 0.92, _inav_ap * 1.08, 200)
            _ap_prem_arr = (_ap_px_arr - _inav_ap) / _inav_ap * 100
            _ap_plc_arr  = (_ap_px_arr - _inav_ap) * _ap_unit - (_inav_ap + _ap_px_arr) * _ap_unit * _ap_cout_demi
            _ap_plr_arr  = (_inav_ap - _ap_px_arr) * _ap_unit - (_inav_ap + _ap_px_arr) * _ap_unit * _ap_cout_demi

            fig_ap = go.Figure()
            fig_ap.add_trace(go.Scatter(
                x=_ap_prem_arr, y=_ap_plc_arr, name="Création",
                line=dict(color=POS_COLOR, width=2),
                hovertemplate="Prime: %{x:.3f}%<br>P&L: %{y:+,.0f} FCFA<extra>Création</extra>",
            ))
            fig_ap.add_trace(go.Scatter(
                x=_ap_prem_arr, y=_ap_plr_arr, name="Rachat",
                line=dict(color=NEG_COLOR, width=2),
                hovertemplate="Prime: %{x:.3f}%<br>P&L: %{y:+,.0f} FCFA<extra>Rachat</extra>",
            ))
            fig_ap.add_hline(y=0, line_dash="dash", line_color="#9ca3af", line_width=1)
            fig_ap.add_vline(
                x=float(_ap_prem_pct),
                line_dash="dot", line_color=COLOR, line_width=2,
                annotation_text=f" Actuel ({_ap_sign}{_ap_prem_pct:.3f}%)",
                annotation_font_color=COLOR,
            )
            fig_ap.update_layout(
                **PLOTLY_LAYOUT, height=300,
                xaxis_title="Prime / Décote (%)",
                yaxis_title="P&L (FCFA)",
                title=f"P&L AP · {_ap_unit:,} parts · {_ap_cout:.2f}% coûts aller-retour",
                legend=dict(orientation="h", x=0.5, xanchor="center", y=1.12),
            )
            st.plotly_chart(fig_ap, width='stretch')

            # ── Tableau des trades — Création ────────────────────────────
            _section("Trades à exécuter — Création (achat du panier)")
            _ap_rows = []
            _ap_total_m = 0.0
            _ap_total_com = 0.0
            for _it in _bask_ap:
                _tk   = _it["ticker"]
                _w    = _it["poids_pct"] / 100.0
                _px_s = float(_it.get("dernier_prix") or 0)
                if not _px_s:
                    continue
                _ap_val    = _w * _inav_ap * _ap_unit
                _ap_qty_th = _ap_val / _px_s
                _ap_qty_rd = round(_ap_qty_th)
                _ap_mont   = _ap_qty_rd * _px_s
                _ap_com    = _ap_mont * _ap_cout_demi
                _ap_total_m   += _ap_mont
                _ap_total_com += _ap_com
                _ap_rows.append({
                    "Titre":          _tk,
                    "Poids ETF (%)":  round(_it["poids_pct"], 2),
                    "Prix (FCFA)":    int(_px_s),
                    "Qté théorique":  round(_ap_qty_th, 2),
                    "Qté entière":    _ap_qty_rd,
                    "Montant (FCFA)": int(_ap_mont),
                    "Commission":     int(_ap_com),
                })

            if _ap_rows:
                _df_ap = pd.DataFrame(_ap_rows).sort_values("Poids ETF (%)", ascending=False)
                st.dataframe(_df_ap, hide_index=True, use_container_width=True, height=400)
                _ap_ecart = abs(_ap_total_m - _ap_notionnel) / _ap_notionnel * 100
                st.caption(
                    f"Coût total panier : {_ap_total_m:,.0f} FCFA  ·  "
                    f"Commission achat : {_ap_total_com:,.0f} FCFA  ·  "
                    f"Valeur ETF reçue : {_ap_etf_px * _ap_unit:,.0f} FCFA  ·  "
                    f"Écart arrondi : {_ap_ecart:.3f}%"
                )
                st.markdown(f"""
                <div style="margin-top:12px;padding:12px 16px;background:#f9fafb;border-left:3px solid #e5e7eb;
                            border-radius:0 8px 8px 0;font-size:12px;color:#6b7280">
                  <b>Hypothèses</b> : coûts aller-retour {_ap_cout:.2f}% répartis moitié achat / moitié vente.
                  Quantités arrondies au titre entier (résidu ±{_ap_ecart:.3f}%).
                  Prix du panier = derniers cours disponibles (iNAV {_inav_ap:,.0f} FCFA/part).
                </div>""", unsafe_allow_html=True)

    # ── Analyse approfondie ───────────────────────────────────────────────────
    elif _lsec == "analyse":
        nl_mgmt    = load_json_fresh(nav_latest_path)
        rd_data    = load_json(rebal_detail_path)
        bm_data    = load_json(bm_path) or {}
        launch     = load_json(os.path.join(HALAL_DIR, "launch_state.json")) or {}
        basket_now = (nl_mgmt or {}).get("basket", [])
        rebals_an  = [r for r in (rd_data or {}).get("rebalancings", []) if not r.get("skipped", False)]
        last_rb    = rebals_an[-1] if rebals_an else {}
        launch_date = launch.get("launch_date")
        rh_path    = os.path.join(HALAL_DIR, "sika_history.json")
        rh         = load_json(rh_path) or {}

        # ── 1. Composition du panier ──────────────────────────────────────────
        if basket_now:
            _section("Composition du panier")
            df_bask = pd.DataFrame(basket_now)
            _sec_file = load_json(os.path.join(BASE, "data", "sector_map.json")) or {}
            _sec_map  = _sec_file.get("sectors", {})
            df_bask["secteur"] = df_bask["ticker"].map(lambda t: _sec_map.get(t, "Autre"))
            sec_grp = df_bask.groupby("secteur")["poids_pct"].sum().sort_values(ascending=False).reset_index()
            sec_grp.columns = ["Secteur", "Poids (%)"]
            col_pie, col_bar = st.columns(2)
            with col_pie:
                fig_pie = go.Figure(go.Pie(
                    labels=sec_grp["Secteur"], values=sec_grp["Poids (%)"],
                    hole=0.42,
                    textinfo="percent",
                    textfont=dict(size=12),
                    textposition="inside",
                    hovertemplate="<b>%{label}</b><br>%{value:.2f}%<extra></extra>",
                ))
                _pie_layout = {k: v for k, v in PLOTLY_LAYOUT.items() if k != 'margin'}
                fig_pie.update_layout(**_pie_layout, height=380,
                    title="Répartition sectorielle",
                    showlegend=True,
                    legend=dict(orientation="v", x=1.02, y=0.5, xanchor="left", font=dict(size=12)),
                    margin=dict(l=10, r=160, t=40, b=10),
                )
                st.plotly_chart(fig_pie, width='stretch')
            with col_bar:
                _w_cible_bar = {b["ticker"]: b.get("w_etf", 0) * 100 for b in last_rb.get("basket", [])}
                df_bs = df_bask.sort_values("poids_pct", ascending=True).copy()
                df_bs["cible_pct"] = df_bs["ticker"].map(lambda t: _w_cible_bar.get(t, 0))
                fig_bw = go.Figure()
                fig_bw.add_trace(go.Bar(
                    x=df_bs["poids_pct"], y=df_bs["ticker"], orientation="h",
                    name="Poids live", marker_color=COLOR,
                    hovertemplate="%{y}<br>Live : <b>%{x:.2f}%</b><extra></extra>",
                ))
                fig_bw.add_trace(go.Scatter(
                    x=df_bs["cible_pct"], y=df_bs["ticker"], mode="markers",
                    name="Cible rebal", marker=dict(symbol="line-ns", size=10, color="#c0392b", line=dict(width=2, color="#c0392b")),
                    hovertemplate="%{y}<br>Cible : <b>%{x:.2f}%</b><extra></extra>",
                ))
                _bar_h = max(380, len(df_bs) * 22)
                fig_bw.update_layout(**PLOTLY_LAYOUT, height=_bar_h,
                    title="Poids par titre — live vs cible rebalancement",
                    xaxis_title="%", showlegend=True,
                    legend=dict(orientation="h", y=-0.08))
                st.plotly_chart(fig_bw, width='stretch')
            top5  = df_bask.nlargest(5,  "poids_pct")["poids_pct"].sum()
            top10 = df_bask.nlargest(10, "poids_pct")["poids_pct"].sum()
            _kpi_html(
                ("Top 5 titres",  f"{top5:.1f}%"),
                ("Top 10 titres", f"{top10:.1f}%"),
                ("Nb titres", str(len(df_bask))),
            )

            # Répartition par pays
            def _pays(tk):
                if tk.endswith("BF"): return "Burkina Faso"
                return {"C": "Côte d'Ivoire", "B": "Burkina Faso", "T": "Togo",
                        "S": "Sénégal", "N": "Niger", "M": "Mali",
                        "G": "Guinée-Bissau"}.get(tk[-1], "Autre")
            df_bask["pays"] = df_bask["ticker"].map(_pays)
            pays_grp = df_bask.groupby("pays")["poids_pct"].sum().sort_values(ascending=False).reset_index()
            pays_grp.columns = ["Pays", "Poids (%)"]
            col_pp1, col_pp2 = st.columns(2)
            with col_pp1:
                fig_pays = go.Figure(go.Pie(
                    labels=pays_grp["Pays"], values=pays_grp["Poids (%)"],
                    hole=0.42,
                    textinfo="percent",
                    textfont=dict(size=12),
                    textposition="inside",
                    hovertemplate="<b>%{label}</b><br>%{value:.2f}%<extra></extra>",
                ))
                _pays_layout = {k: v for k, v in PLOTLY_LAYOUT.items() if k != 'margin'}
                fig_pays.update_layout(**_pays_layout, height=320,
                    title="Répartition par pays",
                    showlegend=True,
                    legend=dict(orientation="v", x=1.02, y=0.5, xanchor="left", font=dict(size=12)),
                    margin=dict(l=10, r=160, t=40, b=10),
                )
                st.plotly_chart(fig_pays, width='stretch')
            with col_pp2:
                fig_pays_bar = go.Figure(go.Bar(
                    x=pays_grp["Poids (%)"], y=pays_grp["Pays"], orientation="h",
                    marker_color=COLOR2,
                    hovertemplate="%{y}<br><b>%{x:.2f}%</b><extra></extra>",
                ))
                fig_pays_bar.update_layout(**PLOTLY_LAYOUT, height=300,
                    title="Poids par pays (%)", xaxis_title="%", showlegend=False)
                st.plotly_chart(fig_pays_bar, width='stretch')

        # ── 2. Poids ETF vs Indice Dividende (live + hier) ─────────────────────────────
        intra_data  = load_json_fresh(os.path.join(HALAL_DIR, "intraday_nav.json")) or {}
        intra_hist  = load_json(os.path.join(HALAL_DIR, "nav_intraday_history.json")) or {}
        snaps_today = intra_data.get("snapshots", [])
        last_snap   = snaps_today[-1] if snaps_today else None
        snap_time   = last_snap.get("time", "—") if last_snap else "—"

        # Contributions live du dernier snapshot
        tc_live = {}
        if last_snap:
            tc = last_snap.get("ticker_contributions", {})
            tc_live = tc if isinstance(tc, dict) else {}

        # Poids Indice Dividende d'hier (dernier snapshot de la veille)
        tc_hier = {}
        date_today = intra_data.get("date", "")
        if isinstance(intra_hist, dict) and intra_hist:
            dates_av = sorted([d for d in intra_hist if d < date_today]) if date_today else []
            if dates_av:
                snaps_h = intra_hist[dates_av[-1]]
                if isinstance(snaps_h, list) and snaps_h:
                    th = snaps_h[-1].get("ticker_contributions", {})
                    tc_hier = th if isinstance(th, dict) else {}

        if basket_now and last_rb.get("basket"):
            st.markdown("---")
            _section(f"Poids ETF vs Indice Dividende — {snap_time} UTC (live) | rebalancement {last_rb.get('date_label','—')}")

            w_brvm_rebal      = {b["ticker"]: b.get("w_brvm30", 0) * 100 for b in last_rb["basket"]}
            w_etf_cible       = {b["ticker"]: b.get("w_etf",   0) * 100 for b in last_rb["basket"]}
            excluded          = last_rb.get("excluded", [])
            w_brvm_rebal_excl = {e["ticker"]: e.get("w_brvm30", 0) * 100 for e in excluded}

            rows_cmp = []
            # Titres dans l'ETF
            for item in sorted(basket_now, key=lambda x: x.get("poids_pct", 0), reverse=True):
                tk       = item["ticker"]
                w_etf    = item.get("poids_pct", 0)
                w_live   = tc_live.get(tk, {}).get("w_brvm30_pct") if tc_live else None
                w_hier   = tc_hier.get(tk, {}).get("w_brvm30_pct") if tc_hier else None
                w_rebal  = w_brvm_rebal.get(tk)
                w_cible  = w_etf_cible.get(tk)
                delta    = round(w_etf - w_live, 2) if w_live is not None else None
                rows_cmp.append({
                    "Ticker":           tk,
                    "Dans ETF":         "oui",
                    "ETF % (live)":     round(w_etf, 2),
                    "Cible rebal %":    round(w_cible, 2) if w_cible is not None else None,
                    "Indice Dividende live %":    round(w_live, 2) if w_live is not None else None,
                    "Indice Dividende rebal %":   round(w_rebal, 2) if w_rebal is not None else None,
                    "Écart (ETF-live)": delta,
                })
            # Titres exclus de l'ETF (poids Indice Dividende > 0, poids ETF = 0)
            for excl in sorted(excluded, key=lambda x: x.get("w_brvm30", 0), reverse=True):
                tk      = excl["ticker"]
                w_live  = tc_live.get(tk, {}).get("w_brvm30_pct") if tc_live else None
                w_hier  = tc_hier.get(tk, {}).get("w_brvm30_pct") if tc_hier else None
                w_rebal = w_brvm_rebal_excl.get(tk)
                delta   = round(0 - w_live, 2) if w_live is not None else (
                          round(-w_rebal, 2) if w_rebal else None)
                rows_cmp.append({
                    "Ticker":           tk,
                    "Dans ETF":         "exclu",
                    "ETF % (live)":     0.0,
                    "Cible rebal %":    0.0,
                    "Indice Dividende live %":    round(w_live, 2) if w_live is not None else None,
                    "Indice Dividende rebal %":   round(w_rebal, 2) if w_rebal else None,
                    "Écart (ETF-live)": delta,
                })

            df_cmp = pd.DataFrame(rows_cmp)

            def _color_delta(val):
                if val is None or pd.isna(val): return ""
                if val > 0.5:  return "color: #1A7A4A; font-weight:600"
                if val < -0.5: return "color: #C0392B; font-weight:600"
                return "color: #888"

            def _color_drift(row):
                styles = [""] * len(row)
                cols = list(row.index)
                cible  = row.get("Cible rebal %")
                b30_rb = row.get("Indice Dividende rebal %")
                # Titre capé par ADV : cible rebal < poids Indice Dividende rebal - seuil
                capped = (cible is not None and b30_rb is not None
                          and not pd.isna(cible) and not pd.isna(b30_rb)
                          and b30_rb > 0 and cible < b30_rb - 0.05
                          and row.get("Dans ETF") == "oui")
                if capped:
                    for i in range(len(styles)):
                        styles[i] = "background-color: #FDEDEC"
                    if "Ticker" in cols:
                        styles[cols.index("Ticker")] = "background-color: #FDEDEC; color: #C0392B; font-weight:700"
                    if "Cible rebal %" in cols:
                        styles[cols.index("Cible rebal %")] = "background-color: #FDEDEC; color: #C0392B; font-weight:600"
                # Dérive live vs cible > 1%
                if "ETF % (live)" in cols and "Cible rebal %" in cols:
                    live = row["ETF % (live)"]
                    if live is not None and cible is not None and not pd.isna(live) and not pd.isna(cible):
                        if abs(live - cible) > 1.0:
                            styles[cols.index("ETF % (live)")] = (
                                ("background-color: #FDEDEC; " if capped else "")
                                + "color: #C0392B; font-weight:600"
                            )
                return styles

            fmt_pct = lambda x: f"{x:.2f}%" if x is not None and not (isinstance(x, float) and pd.isna(x)) else "—"
            st.dataframe(
                df_cmp.style
                    .format({
                        "ETF % (live)":     fmt_pct,
                        "Cible rebal %":    fmt_pct,
                        "Indice Dividende live %":    fmt_pct,
                        "Indice Dividende rebal %":   fmt_pct,
                        "Écart (ETF-live)": lambda x: f"{x:+.2f}%" if x is not None and not (isinstance(x, float) and pd.isna(x)) else "—",
                    })
                    .apply(_color_drift, axis=1)
                    .map(_color_delta, subset=["Écart (ETF-live)"]),
                use_container_width=True, hide_index=True,
            )

        # ── Calendrier d'exécution jour par jour ─────────────────────────────
        orders_last = last_rb.get("orders", [])
        if orders_last:
            from datetime import datetime as _dt, timedelta as _td
            st.markdown("---")
            rebal_date_str = last_rb.get("date", "")
            rebal_dt = _dt.strptime(rebal_date_str, "%Y-%m-%d") if rebal_date_str else _dt(2026, 7, 1)
            today_dt = _dt.now().replace(hour=0, minute=0, second=0, microsecond=0)
            _section(f"Calendrier d'exécution — rebalancement du {rebal_date_str}")

            # T+3 BRVM : ventes démarrent J0, achats démarrent J+3 jours ouvrés
            # Tous les jours d'exécution sont des jours ouvrés (pas de weekend)
            T3 = 3
            _rebal_ts     = pd.Timestamp(rebal_dt)
            _buy_start_ts = _rebal_ts + pd.offsets.BDay(T3)

            def _bday_range(start_ts, n):
                """Retourne n dates de jours ouvrés à partir de start_ts."""
                return [(start_ts + pd.offsets.BDay(k)).strftime("%Y-%m-%d") for k in range(n)]

            # Construire le détail jour par jour
            # daily_detail[date] = {'achats': [(ticker, montant)], 'ventes': [(ticker, montant)]}
            _MAX_LARGE, _MAX_SMALL, _LARGE_THR = 40, 20, 3.0
            daily_detail = {}
            for o in orders_last:
                _is_exit = (o.get("w_new_pct", -1) == 0 and o.get("sens") == "VENDRE")
                _max_d = 999 if _is_exit else (_MAX_LARGE if o.get("w_brvm30_pct", 0) >= _LARGE_THR else _MAX_SMALL)
                d_ex  = max(min(int(o.get("days_exec", 0)), _max_d), 1)
                daily = o["montant_mfcfa"] / d_ex
                start_ts = _buy_start_ts if o["sens"] == "ACHETER" else _rebal_ts
                for dt_key in _bday_range(start_ts, d_ex):
                    if dt_key not in daily_detail:
                        daily_detail[dt_key] = {"achats": [], "ventes": []}
                    if o["sens"] == "ACHETER":
                        daily_detail[dt_key]["achats"].append((o["ticker"], daily))
                    else:
                        daily_detail[dt_key]["ventes"].append((o["ticker"], daily))

            all_days_sorted = sorted(daily_detail.keys())

            # ── Graphique timeline : une couleur par ticker ───────────────────
            import plotly.colors as _pc

            _palette = (_pc.qualitative.Plotly + _pc.qualitative.D3
                        + _pc.qualitative.G10 + _pc.qualitative.Pastel)
            all_tickers_ord = sorted(set(o["ticker"] for o in orders_last))
            ticker_clr = {tk: _palette[i % len(_palette)]
                          for i, tk in enumerate(all_tickers_ord)}

            def _hex_to_rgba(hex_c, alpha):
                h = hex_c.lstrip("#")
                r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
                return f"rgba({r},{g},{b},{alpha})"

            fig_cal = go.Figure()
            for tk in all_tickers_ord:
                x_r, y_r, x_p, y_p = [], [], [], []
                for d in all_days_sorted:
                    ach = sum(v for t, v in daily_detail[d]["achats"] if t == tk)
                    ven = sum(v for t, v in daily_detail[d]["ventes"] if t == tk)
                    val = ach - ven
                    if val == 0:
                        continue
                    is_past = _dt.strptime(d, "%Y-%m-%d") < today_dt
                    if is_past:
                        x_r.append(d); y_r.append(val)
                    else:
                        x_p.append(d); y_p.append(val)

                clr = ticker_clr[tk]
                if x_r:
                    fig_cal.add_trace(go.Bar(
                        x=x_r, y=y_r, name=tk,
                        marker_color=clr, legendgroup=tk,
                        hovertemplate=f"<b>{tk}</b><br>%{{x}}<br>%{{y:.1f}} M FCFA<extra></extra>",
                    ))
                if x_p:
                    fig_cal.add_trace(go.Bar(
                        x=x_p, y=y_p, name=tk,
                        marker_color=_hex_to_rgba(clr if clr.startswith("#") else "#888888", 0.35),
                        legendgroup=tk, showlegend=False,
                        hovertemplate=f"<b>{tk}</b> (prévu)<br>%{{x}}<br>%{{y:.1f}} M FCFA<extra></extra>",
                    ))

            fig_cal.add_vline(x=today_dt.strftime("%Y-%m-%d"), line_dash="dash",
                              line_color="#b8922f", annotation_text="Aujourd'hui",
                              annotation_position="top right")
            fig_cal.update_layout(
                **PLOTLY_LAYOUT, height=420, barmode="relative",
                title="Volume journalier lissé par titre (M FCFA) — ventes J0 / achats J+3 (T+3 BRVM) — plein=réalisé, transparent=prévu",
                yaxis_title="M FCFA",
                legend=dict(orientation="h", y=1.06, font=dict(size=10)),
            )
            fig_cal.update_xaxes(type="date")
            st.plotly_chart(fig_cal, width='stretch')

            # ── Tableau jour par jour ─────────────────────────────────────────
            rows_cal = []
            for d in all_days_sorted:
                dt = _dt.strptime(d, "%Y-%m-%d")
                is_past = dt < today_dt
                statut  = "✅ Réalisé" if is_past else "🔵 Prévu"
                ach = daily_detail[d]["achats"]
                ven = daily_detail[d]["ventes"]
                total_ach = sum(v for _, v in ach)
                total_ven = sum(v for _, v in ven)
                ach_detail = ", ".join(f"{tk} ({v:.1f}M)" for tk, v in sorted(ach, key=lambda x: -x[1]))
                ven_detail = ", ".join(f"{tk} ({v:.1f}M)" for tk, v in sorted(ven, key=lambda x: -x[1]))
                rows_cal.append({
                    "Date":           d,
                    "Statut":         statut,
                    "Achats (M)":     round(total_ach, 1) if total_ach else None,
                    "Tickers achetés":  ach_detail or "—",
                    "Ventes (M)":     round(total_ven, 1) if total_ven else None,
                    "Tickers vendus":   ven_detail or "—",
                })

            df_cal = pd.DataFrame(rows_cal)
            st.dataframe(
                df_cal.style.apply(
                    lambda row: ["background-color:#f0f4f8"] * len(row)
                    if "Réalisé" in str(row["Statut"]) else [""] * len(row),
                    axis=1
                ),
                use_container_width=True, hide_index=True, height=400,
            )

        # ── Analyse quantitative (3 onglets) ─────────────────────────────────
        st.markdown("---")
        _section("Analyse quantitative")
        _tab_liq, _tab_attr, _tab_rsk = st.tabs(["  Liquidité  ", "  Attribution  ", "  Risque  "])

        # ── Onglet Liquidité ──────────────────────────────────────────────────
        with _tab_liq:
            if basket_now:
                # Calcul live depuis sika_history (63 jours ouvrés = 3 mois)
                _sh_liq = load_json(rh_path) or {}
                import datetime as _dt
                _today  = _dt.datetime.utcnow().strftime("%Y-%m-%d")
                _aum    = (nl_mgmt or {}).get("aum_mfcfa") or 5000.0

                def _live_adv(ticker):
                    hist  = _sh_liq.get(ticker, {})
                    dates = sorted(d for d in hist if d < _today)[-63:]
                    vals  = [(hist[d].get("volume") or 0) * (hist[d].get("close") or 0) / 1e6
                             for d in dates]
                    return float(sum(vals) / len(dates)) if dates else 0.0

                _liq_rows = []
                for b in basket_now:
                    tk       = b["ticker"]
                    pv       = b.get("pv_mfcfa") or b.get("poids_pct", 0) / 100 * _aum
                    adv      = _live_adv(tk)
                    days     = round(pv / adv if adv > 0 else 0.0, 1)
                    liq_r    = round(pv / adv if adv > 0 else 0.0, 2)
                    _liq_rows.append({
                        "ticker":      tk,
                        "adv_mfcfa":   round(adv, 1),
                        "trade_mfcfa": round(pv, 1),
                        "days_exec":   days,
                        "liq_ratio":   liq_r,
                    })

                df_liq   = pd.DataFrame(_liq_rows)
                df_liq_s = df_liq.sort_values("days_exec", ascending=False)
                n_illiq    = int((df_liq["days_exec"] > 5).sum())
                avg_days   = float(df_liq["days_exec"].mean())
                max_idx    = df_liq["days_exec"].idxmax()
                max_days   = float(df_liq.loc[max_idx, "days_exec"])
                max_ticker = df_liq.loc[max_idx, "ticker"]
                _liq_alert_col = "#c0392b" if n_illiq > 0 else "#2d7a4f"
                _kpi_html(
                    ("Rebalancement", last_rb.get("date_label", "—")),
                    ("J. d'exec. moyen", f"{avg_days:.1f}j"),
                    ("Plus illiquide", f"{max_ticker} — {max_days:.1f}j"),
                    ("Titres > 5j", f"{n_illiq} / {len(df_liq)}", _liq_alert_col),
                )
                col_liq1, col_liq2 = st.columns([3, 2])
                with col_liq1:
                    _colors_liq = [NEG_COLOR if v > 5 else COLOR if v > 1 else POS_COLOR
                                   for v in df_liq_s["days_exec"]]
                    fig_liq = go.Figure(go.Bar(
                        x=df_liq_s["days_exec"], y=df_liq_s["ticker"], orientation="h",
                        marker_color=_colors_liq,
                        hovertemplate="%{y}<br><b>%{x:.1f} j</b><extra></extra>",
                    ))
                    fig_liq.add_vline(x=1,  line_dash="dot",   line_color="#cbd5e1", annotation_text="1j")
                    fig_liq.add_vline(x=5,  line_dash="dot",   line_color=NEG_COLOR, annotation_text="5j")
                    fig_liq.add_vline(x=35, line_dash="solid", line_color=NEG_COLOR, line_width=2,
                                      annotation_text="Cap 35j", annotation_font_color=NEG_COLOR)
                    _liq_h = max(440, len(df_liq_s) * 26 + 60)
                    fig_liq.update_layout(**PLOTLY_LAYOUT, height=_liq_h,
                        title="Jours d'exécution estimés", xaxis_title="Jours", showlegend=False)
                    st.plotly_chart(fig_liq, width='stretch')
                with col_liq2:
                    st.dataframe(
                        df_liq_s[["ticker","adv_mfcfa","trade_mfcfa","days_exec","liq_ratio"]],
                        column_config={
                            "ticker":      st.column_config.TextColumn("Ticker", width="small"),
                            "adv_mfcfa":   st.column_config.NumberColumn("ADV (MF)", format="%.1f"),
                            "trade_mfcfa": st.column_config.NumberColumn("Trade (MF)", format="%.1f"),
                            "days_exec":   st.column_config.NumberColumn("J. exec.", format="%.1f"),
                            "liq_ratio":   st.column_config.NumberColumn("Ratio liq.", format="%.2f"),
                        },
                        hide_index=True, height=_liq_h, use_container_width=True
                    )
            else:
                st.info("Données de rebalancement non disponibles.")

        # ── Onglet Attribution ────────────────────────────────────────────────
        with _tab_attr:
            if basket_now and launch_date and rh:
                _w_cible_attr = {b["ticker"]: round(b.get("w_etf", 0) * 100, 2) for b in last_rb.get("basket", [])}
                attr_rows = []
                for item in basket_now:
                    tk      = item["ticker"]
                    w       = item["poids_pct"] / 100
                    px_hist = rh.get(tk, rh.get(tk.upper(), {}))
                    if not px_hist: continue
                    d_before = [d for d in px_hist if d <= launch_date]
                    if not d_before: continue
                    def _px(v):
                        return float(v['close'] if isinstance(v, dict) else v)
                    px_launch = _px(px_hist[max(d_before)])
                    px_now    = _px(px_hist[max(px_hist)])
                    ret_pct   = (px_now / px_launch - 1) * 100 if px_launch > 0 else 0.0
                    attr_rows.append({
                        "ticker": tk, "poids": round(w * 100, 2),
                        "cible": _w_cible_attr.get(tk),
                        "ret_pct": round(ret_pct, 2),
                        "contrib_pct": round(w * ret_pct, 3),
                    })
                if attr_rows:
                    df_attr = pd.DataFrame(attr_rows).sort_values("contrib_pct", ascending=False)
                    total_attr = df_attr["contrib_pct"].sum()
                    n_pos = int((df_attr["contrib_pct"] >= 0).sum())
                    n_neg = int((df_attr["contrib_pct"] < 0).sum())
                    _lbl_at = pd.Timestamp(launch_date).strftime("%d/%m/%Y")
                    _perf_col = "#2d7a4f" if total_attr >= 0 else "#c0392b"
                    _kpi_html(
                        ("Depuis le lancement", _lbl_at),
                        ("Perf. totale attribuée", f"{total_attr:+.2f}%", _perf_col),
                        ("Meilleur contributeur", f"{df_attr.iloc[0]['ticker']} — {df_attr.iloc[0]['contrib_pct']:+.3f} pts", "#2d7a4f"),
                        ("Plus grand détracteur", f"{df_attr.iloc[-1]['ticker']} — {df_attr.iloc[-1]['contrib_pct']:+.3f} pts", "#c0392b"),
                    )
                    col_at1, col_at2 = st.columns([3, 2])
                    with col_at1:
                        fig_attr = go.Figure(go.Bar(
                            x=df_attr["contrib_pct"], y=df_attr["ticker"], orientation="h",
                            marker_color=[POS_COLOR if v >= 0 else NEG_COLOR for v in df_attr["contrib_pct"]],
                            hovertemplate="%{y}<br>Contribution : <b>%{x:+.3f} pts</b><extra></extra>",
                        ))
                        fig_attr.add_vline(x=0, line_color="#cbd5e1")
                        fig_attr.update_layout(**PLOTLY_LAYOUT, height=480,
                            title=f"Contribution à la performance — base 100 au {_lbl_at}",
                            xaxis_title="pts %", showlegend=False)
                        st.plotly_chart(fig_attr, width='stretch')
                    with col_at2:
                        _max_poids = float(df_attr["poids"].max()) + 2
                        st.dataframe(
                            df_attr.rename(columns={"ticker":"Ticker","poids":"Poids live %",
                                "cible":"Cible rebal %","ret_pct":"Perf. %","contrib_pct":"Contrib. pts"}),
                            column_config={
                                "Ticker":          st.column_config.TextColumn("Ticker", width="small"),
                                "Poids live %":    st.column_config.ProgressColumn("Poids live %", format="%.2f%%",
                                                       min_value=0, max_value=_max_poids),
                                "Cible rebal %":   st.column_config.NumberColumn("Cible rebal %", format="%.2f%%"),
                                "Perf. %":         st.column_config.NumberColumn("Perf. %", format="%+.2f%%"),
                                "Contrib. pts":    st.column_config.NumberColumn("Contrib. pts", format="%+.3f"),
                            },
                            hide_index=True, height=480, use_container_width=True
                        )
                else:
                    st.info("Pas assez de données historiques pour calculer l'attribution.")
            else:
                st.info("Données insuffisantes pour l'attribution.")

        # ── Onglet Risque ─────────────────────────────────────────────────────
        with _tab_rsk:
            if basket_now and rh:
                _w_cible_rsk = {b["ticker"]: round(b.get("w_etf", 0) * 100, 2) for b in last_rb.get("basket", [])}
                risk_rows = []
                for item in basket_now:
                    tk      = item["ticker"]
                    w       = item["poids_pct"] / 100
                    px_hist = rh.get(tk, rh.get(tk.upper(), {}))
                    if not px_hist or len(px_hist) < 10: continue
                    _px_vals = {}
                    for _d, _v in px_hist.items():
                        try:
                            _px_vals[_d] = float(_v['close'] if isinstance(_v, dict) else _v)
                        except (TypeError, ValueError, KeyError):
                            pass
                    if len(_px_vals) < 10: continue
                    prices = pd.Series(_px_vals).sort_index().iloc[-252:]
                    rets   = prices.pct_change().dropna()
                    if len(rets) < 5: continue
                    vol_ann   = float(rets.std() * np.sqrt(252) * 100)
                    roll_max  = prices.cummax()
                    max_dd    = float(((prices - roll_max) / roll_max * 100).min())
                    risk_rows.append({"ticker": tk, "poids": round(w*100,2),
                                       "cible": _w_cible_rsk.get(tk),
                                       "vol_ann": round(vol_ann,2), "max_dd": round(max_dd,2)})
                if risk_rows:
                    df_risk = pd.DataFrame(risk_rows).sort_values("vol_ann", ascending=False)
                    wgt_vol  = float((df_risk["vol_ann"] * df_risk["poids"] / 100).sum())
                    worst_dd = df_risk.loc[df_risk["max_dd"].idxmin()]
                    n_high   = int((df_risk["vol_ann"] > 30).sum())
                    _vol_col = "#c0392b" if wgt_vol > 30 else "#c9861a" if wgt_vol > 15 else "#2d7a4f"
                    _kpi_html(
                        ("Vol. pond. portefeuille", f"{wgt_vol:.1f}%", _vol_col),
                        ("Vol. max (titre)", f"{df_risk.iloc[0]['ticker']} — {df_risk.iloc[0]['vol_ann']:.1f}%"),
                        ("Max DD (titre)", f"{worst_dd['ticker']} — {worst_dd['max_dd']:.1f}%", "#c0392b"),
                        ("Titres vol > 30%", str(n_high), "#c0392b" if n_high > 0 else "#2d7a4f"),
                    )
                    col_rk1, col_rk2 = st.columns([3, 2])
                    with col_rk1:
                        fig_vol = go.Figure(go.Bar(
                            x=df_risk["vol_ann"], y=df_risk["ticker"], orientation="h",
                            marker_color=[NEG_COLOR if v > 30 else COLOR if v > 15 else POS_COLOR
                                          for v in df_risk["vol_ann"]],
                            hovertemplate="%{y}<br>Vol : <b>%{x:.1f}%</b><extra></extra>",
                        ))
                        fig_vol.update_layout(**PLOTLY_LAYOUT, height=480,
                            title="Volatilité annualisée par titre — 252 séances",
                            xaxis_title="%", showlegend=False)
                        st.plotly_chart(fig_vol, width='stretch')
                    with col_rk2:
                        _max_poids_r = float(df_risk["poids"].max()) + 2
                        st.dataframe(
                            df_risk.rename(columns={"ticker":"Ticker","poids":"Poids live %",
                                "cible":"Cible rebal %","vol_ann":"Vol. ann. %","max_dd":"Max DD %"}),
                            column_config={
                                "Cible rebal %": st.column_config.NumberColumn("Cible rebal %", format="%.2f%%"),
                                "Ticker":    st.column_config.TextColumn("Ticker", width="small"),
                                "Poids %":   st.column_config.ProgressColumn("Poids %", format="%.2f%%",
                                                 min_value=0, max_value=_max_poids_r),
                                "Vol. ann. %": st.column_config.NumberColumn("Vol. ann. %", format="%.2f%%"),
                                "Max DD %":    st.column_config.NumberColumn("Max DD %", format="%.2f%%"),
                            },
                            hide_index=True, height=480, use_container_width=True
                        )
                else:
                    st.info("Historique insuffisant pour calculer le risque.")

        # ── 5. Suivi des coûts (backtest uniquement) ─────────────────────────
        if bm_data.get("annual") and _page != "live":
            st.markdown("---")
            _section("Suivi des coûts et du tracking")
            df_costs = pd.DataFrame(bm_data["annual"])
            df_costs["te_pct"]       = (df_costs["te"]       * 100).round(3)
            df_costs["td_pct"]       = (df_costs["td"]       * 100).round(3)
            df_costs["cost_tx_pct"]  = (df_costs["cost_tx"]  * 100).round(3)
            df_costs["mgmt_fee_pct"] = (df_costs["mgmt_fee"] * 100).round(3)
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                fig_te = go.Figure()
                fig_te.add_trace(go.Bar(x=df_costs["year"].astype(str), y=df_costs["te_pct"],
                    name="TE (%)", marker_color=COLOR,
                    hovertemplate="%{x}<br>TE : <b>%{y:.3f}%</b><extra></extra>"))
                fig_te.add_trace(go.Scatter(x=df_costs["year"].astype(str), y=df_costs["td_pct"],
                    name="TD (%)", mode="lines+markers",
                    line=dict(color=BENCH_COLOR, width=2),
                    hovertemplate="%{x}<br>TD : <b>%{y:+.3f}%</b><extra></extra>"))
                fig_te.update_layout(**PLOTLY_LAYOUT, height=300,
                    title="Tracking Error & Tracking Difference par année",
                    yaxis_title="%", legend=dict(orientation="h", y=-0.2))
                st.plotly_chart(fig_te, width='stretch')
            with col_c2:
                fig_cost = go.Figure()
                fig_cost.add_trace(go.Bar(x=df_costs["year"].astype(str), y=df_costs["cost_tx_pct"],
                    name="Coûts tx", marker_color=NEG_COLOR,
                    hovertemplate="%{x}<br>Coûts : <b>%{y:.3f}%</b><extra></extra>"))
                fig_cost.add_trace(go.Bar(x=df_costs["year"].astype(str), y=df_costs["mgmt_fee_pct"],
                    name="Frais gestion", marker_color=COLOR2,
                    hovertemplate="%{x}<br>Frais : <b>%{y:.3f}%</b><extra></extra>"))
                fig_cost.update_layout(**PLOTLY_LAYOUT, height=300, barmode="stack",
                    title="Coûts annuels (transactions + gestion)", yaxis_title="%",
                    legend=dict(orientation="h", y=-0.2))
                st.plotly_chart(fig_cost, width='stretch')
            ck1, ck2, ck3, ck4 = st.columns(4)
            ck1.metric("TE full période",       f"{bm_data.get('te_full',0)*100:.2f}%")
            ck2.metric("TD full période",        f"{bm_data.get('td_full',0)*100:+.2f}%")
            ck3.metric("Coûts tx cumulés",      f"{bm_data.get('cost_tx_cumul',0)*100:.2f}%")
            ck4.metric("Frais gestion cumulés",  f"{bm_data.get('mgmt_fee_cumul',0)*100:.2f}%")
            st.dataframe(
                df_costs[["year","te_pct","td_pct","cost_tx_pct","mgmt_fee_pct"]].rename(columns={
                    "year":"Année","te_pct":"TE (%)","td_pct":"TD (%)",
                    "cost_tx_pct":"Coûts tx (%)","mgmt_fee_pct":"Frais gest. (%)"}),
                width='stretch', hide_index=True)

        # ── 6. Performance & Tracking LIVE ───────────────────────────────────
        _nl_an     = load_json(nav_latest_path) or {}
        _idx_hist  = load_json(os.path.join(HALAL_DIR, "brvm30_index_history.json")) or {}
        _par_fcfa  = float(launch.get("par_fcfa", 100000))
        _idx_launch_v = float(_idx_hist.get(launch_date, 0)) if launch_date and launch_date in _idx_hist else 0

        # Construire nav_live_series depuis intraday history (dernier snapshot de chaque jour)
        _ih_live = load_json(os.path.join(HALAL_DIR, "nav_intraday_history.json")) or {}
        _ls_series = _nl_an.get("nav_live_series", [])
        if not _ls_series and _ih_live and launch_date:
            _ls_series = []
            for _d in sorted(_ih_live.keys()):
                if _d < launch_date:
                    continue
                _pts = _ih_live[_d]
                if not _pts:
                    continue
                _last_pt = _pts[-1]
                _vl = _last_pt.get("vl_fcfa") or _last_pt.get("vl")
                if _vl:
                    _ls_series.append([_d, float(_vl)])

        if len(_ls_series) >= 2 and _idx_launch_v > 0:
            st.markdown("---")
            _lbl_launch = pd.Timestamp(launch_date).strftime("%d/%m/%Y") if launch_date else "—"
            _section(f"Performance & Tracking live — depuis le {_lbl_launch}")

            # Séries normalisées base 100
            _df_etf = pd.DataFrame(_ls_series, columns=["date","vl_fcfa"])
            _df_etf.index = pd.to_datetime(_df_etf["date"]); _df_etf = _df_etf.drop(columns="date")
            _df_etf["etf"] = _df_etf["vl_fcfa"] / _par_fcfa * 100

            _idx_rows = [(d, float(v)) for d, v in _idx_hist.items() if d >= launch_date]
            _df_idx = pd.DataFrame(_idx_rows, columns=["date","brvm30"])
            _df_idx.index = pd.to_datetime(_df_idx["date"]); _df_idx = _df_idx.drop(columns="date")
            _df_idx["idx"] = _df_idx["brvm30"] / _idx_launch_v * 100

            _df_m = _df_etf[["etf"]].join(_df_idx[["idx"]], how="inner").sort_index()
            _n_pts = len(_df_m)

            # Drawdown + TD cumulatif
            _etf_dd = ((_df_m["etf"] - _df_m["etf"].cummax()) / _df_m["etf"].cummax() * 100)
            _idx_dd = ((_df_m["idx"] - _df_m["idx"].cummax()) / _df_m["idx"].cummax() * 100)
            _td_cum = (_df_m["etf"] - _df_m["idx"])  # base 100 diff = %

            col_lv1, col_lv2 = st.columns(2)

            # ── Graphique 2 : Drawdown ETF vs Indice Dividende ──────────────────────────
            with col_lv1:
                fig_lv_dd = go.Figure()
                fig_lv_dd.add_trace(go.Scatter(
                    x=_df_m.index, y=_etf_dd, name="ETF",
                    fill="tozeroy", fillcolor="rgba(184,151,63,0.12)",
                    line=dict(color=COLOR, width=1.5),
                    hovertemplate="%{x|%d/%m/%Y}<br>DD ETF : <b>%{y:.2f}%</b><extra></extra>"))
                fig_lv_dd.add_trace(go.Scatter(
                    x=_df_m.index, y=_idx_dd, name="Indice Dividende",
                    line=dict(color=BENCH_COLOR, width=1.5, dash="dot"),
                    hovertemplate="%{x|%d/%m/%Y}<br>DD Indice Dividende : <b>%{y:.2f}%</b><extra></extra>"))
                fig_lv_dd.update_layout(**PLOTLY_LAYOUT, height=300,
                    title="Drawdown — ETF vs Indice Dividende",
                    yaxis_title="%", legend=dict(orientation="h", y=-0.2))
                st.plotly_chart(fig_lv_dd, width='stretch')

            # ── Graphique 3 : TD cumulatif ────────────────────────────────────
            with col_lv2:
                _td_color = COLOR2 if float(_td_cum.iloc[-1]) >= 0 else NEG_COLOR
                _td_fill  = "rgba(74,127,165,0.10)" if float(_td_cum.iloc[-1]) >= 0 else "rgba(192,57,43,0.08)"
                fig_lv_td = go.Figure(go.Scatter(
                    x=_df_m.index, y=_td_cum,
                    fill="tozeroy", fillcolor=_td_fill,
                    line=dict(color=_td_color, width=1.5),
                    hovertemplate="%{x|%d/%m/%Y}<br>TD : <b>%{y:+.3f} pts</b><extra></extra>"))
                fig_lv_td.add_hline(y=0, line_dash="dash", line_color="#e0dbd2")
                fig_lv_td.update_layout(**PLOTLY_LAYOUT, height=300,
                    title="Tracking Difference cumulée (ETF − Indice Dividende Price Return, base 100)",
                    yaxis_title="pts")
                fig_lv_td.add_annotation(
                    text="TD+ attendue en mars–sept. : l'ETF capture les dividendes, l'indice PR ne les intègre pas",
                    xref="paper", yref="paper", x=0.01, y=0.97,
                    showarrow=False, font=dict(size=9, color="#7d8fa3"), align="left")
                st.plotly_chart(fig_lv_td, width='stretch')

            # Rendements journaliers
            if _n_pts >= 2:
                _etf_rets = _df_m["etf"].pct_change().dropna() * 100
                _idx_rets = _df_m["idx"].pct_change().dropna() * 100
                _active   = (_etf_rets - _idx_rets)

                col_lv3, col_lv4 = st.columns(2)

                # ── Graphique 4 : Rendements journaliers ──────────────────────
                with col_lv3:
                    fig_lv_r = go.Figure()
                    fig_lv_r.add_trace(go.Bar(
                        x=_etf_rets.index, y=_etf_rets, name="ETF",
                        marker_color=[POS_COLOR if v >= 0 else NEG_COLOR for v in _etf_rets],
                        hovertemplate="%{x|%d/%m/%Y}<br>ETF : <b>%{y:+.3f}%</b><extra></extra>"))
                    fig_lv_r.add_trace(go.Scatter(
                        x=_idx_rets.index, y=_idx_rets, name="Indice Dividende",
                        mode="markers", marker=dict(color=BENCH_COLOR, size=7, symbol="diamond"),
                        hovertemplate="%{x|%d/%m/%Y}<br>Indice Dividende : <b>%{y:+.3f}%</b><extra></extra>"))
                    fig_lv_r.add_hline(y=0, line_color="#e0dbd2")
                    fig_lv_r.update_layout(**PLOTLY_LAYOUT, height=300,
                        title="Rendements journaliers",
                        yaxis_title="%", legend=dict(orientation="h", y=-0.2))
                    st.plotly_chart(fig_lv_r, width='stretch')

                # ── Graphique 5 : Rendement actif (ETF − Indice Dividende) ──────────────
                with col_lv4:
                    fig_lv_act = go.Figure(go.Bar(
                        x=_active.index, y=_active,
                        marker_color=[POS_COLOR if v >= 0 else NEG_COLOR for v in _active],
                        hovertemplate="%{x|%d/%m/%Y}<br>Actif : <b>%{y:+.3f}%</b><extra></extra>"))
                    fig_lv_act.add_hline(y=0, line_color="#e0dbd2")
                    fig_lv_act.update_layout(**PLOTLY_LAYOUT, height=300,
                        title="Rendement actif journalier (ETF − Indice Dividende)",
                        yaxis_title="%")
                    st.plotly_chart(fig_lv_act, width='stretch')

                # ── Graphique 6 : TE glissante (dès 5 points) ─────────────────
                if len(_active) >= 5:
                    _win = min(20, len(_active))
                    _te_roll = (_active.rolling(_win).std() * (252**0.5) * 100).dropna()
                    if len(_te_roll) >= 2:
                        fig_lv_te = go.Figure(go.Scatter(
                            x=_te_roll.index, y=_te_roll,
                            fill="tozeroy", fillcolor="rgba(184,151,63,0.10)",
                            line=dict(color=COLOR, width=2),
                            hovertemplate="%{x|%d/%m/%Y}<br>TE : <b>%{y:.2f}%</b><extra></extra>"))
                        fig_lv_te.add_hline(y=2.5, line_dash="dash", line_color="#c0392b",
                            annotation_text="Seuil alerte 2.5%",
                            annotation_font=dict(color="#c0392b", size=11))
                        fig_lv_te.update_layout(**PLOTLY_LAYOUT, height=300,
                            title=f"Tracking Error glissante ({_win}j) — annualisée",
                            yaxis_title="%")
                        st.plotly_chart(fig_lv_te, width='stretch')

            _n_jours = _n_pts
            if _n_jours < 30:
                st.caption(f"Données live : {_n_jours} jour(s) de cotation. "
                           f"TE et Sharpe fiables à partir de 30 jours — les graphiques s'enrichiront automatiquement.")
        else:
            st.info("Graphiques disponibles dès le 2ème jour de cotation.")

        # ── Dividendes & Distribution ─────────────────────────────────────────
        st.markdown("---")
        _section("Dividendes & Distribution")

        _dlog_a  = load_json(os.path.join(HALAL_DIR, "dividend_log.json")) or {}
        _sika_a  = load_json(os.path.join(HALAL_DIR, "sika_dividendes.json")) or {}
        _dhist_a = load_json(os.path.join(HALAL_DIR, "dividend_history.json")) or {}
        _bask_a  = {b["ticker"] for b in basket_now}
        _today_a = pd.Timestamp.now().strftime("%Y-%m-%d")
        _trf_a   = _dlog_a.get("taux_rf_annuel", 0.03)
        _annee_a = _dlog_a.get("annee", pd.Timestamp.now().year)
        _dist_dt_a   = pd.Timestamp(_dlog_a.get("distribution_date", f"{_annee_a}-09-30"))
        _dist_str_a  = _dist_dt_a.strftime("%d/%m/%Y")
        _distribue_a = _dlog_a.get("distribue", False)
        _dpp_a       = _dlog_a.get("dividende_par_part_fcfa", 0) or 0
        _rend_a      = _dlog_a.get("rendement_distribution") or 0
        _cash_a      = _dlog_a.get("total_cash_fcfa", 0) or 0
        _nparts_a    = _dlog_a.get("n_parts", 0) or 0
        _events_etf  = _dlog_a.get("evenements", [])
        _launch_a    = launch.get("launch_date", "")

        _stat_a = "DISTRIBUE" if _distribue_a else f"Distribution le {_dist_str_a}"
        _c_stat = "#2d7a4f" if _distribue_a else "#b8973f"
        _kpi_html(
            ("Statut distribution",  _stat_a,                                           _c_stat),
            ("Dividende / part",     f"{_dpp_a:,.0f} FCFA" if _dpp_a else "En attente"),
            ("Rendement distribué",  f"{_rend_a:.2f}%" if _rend_a else "—",             "#2d7a4f" if _rend_a else None),
            ("Cash collecté",        f"{_cash_a/1e6:.3f} M FCFA" if _cash_a else "—"),
            ("Parts émises",         f"{_nparts_a:,}" if _nparts_a else "—"),
            ("Taux RF UEMOA",        f"{_trf_a*100:.1f}%"),
        )


        _tab_ex, _tab_cal, _tab_hist_d = st.tabs([
            f"Exercice {_annee_a} — vue ETF",
            "Calendrier BRVM complet",
            "Historique dividendes BRVM (2022–)",
        ])

        # ── Tab 1 : Exercice en cours ─────────────────────────────────────────
        with _tab_ex:
            _divs_all_a = sorted(_sika_a.get("dividendes", []),
                                 key=lambda x: x.get("date_detach") or "9999")
            # Normalisation tickers sika_dividendes → tickers basket
            _DIV_TK_MAP = {
                "":     "NSBC",   # NSIA Banque : ticker absent dans le scraping
                "TOTC": "TTLC",   # TotalEnergies CI : Sika=TOTC, basket=TTLC
                "VIVC": "SHEC",   # Vivo Energy CI : Sika=VIVC, basket=SHEC
            }
            rows_ex = []
            for _d in _divs_all_a:
                _tk_raw = _d.get("ticker") or ""
                _tk     = _DIV_TK_MAP.get(_tk_raw, _tk_raw) or _tk_raw
                _dt  = _d.get("date_detach")
                _mt  = _d.get("montant", 0)
                _rnd = _d.get("rendement")
                _in_b = _tk in _bask_a if _tk else False
                if not _dt:
                    _st, _sc = "Date à préciser", "#9e9e9e"
                elif _launch_a and _dt < _launch_a:
                    _st, _sc = "Avant lancement ETF", "#9e9e9e"
                elif _dt <= _today_a:
                    _recv = any(e.get("ticker") == _tk for e in _events_etf)
                    if _recv:
                        _st, _sc = "Recu", "#2d7a4f"
                    elif _in_b:
                        _st, _sc = "Détaché — en attente paiement", "#c9861a"
                    else:
                        _st, _sc = "Détaché — hors panier", "#9e9e9e"
                else:
                    _jj = (pd.Timestamp(_dt) - pd.Timestamp(_today_a)).days
                    _st, _sc = f"Dans {_jj}j", "#c9861a"
                _cash_ev = next((e.get("cash_total_fcfa") for e in _events_etf if e.get("ticker") == _tk), None)
                rows_ex.append({
                    "Ticker":          _tk or "—",
                    "Société":         _d.get("nom_sika") or _TICKER_NAMES.get(_tk, "—"),
                    "Détachement":     _dt or "—",
                    "Montant (FCFA)":  _mt,
                    "Rend. Sika (%)":  _rnd,
                    "Panier ETF":      "OUI" if _in_b else "—",
                    "Statut":          _st,
                    "Cash ETF (FCFA)": int(_cash_ev) if _cash_ev else None,
                })
            if rows_ex:
                _df_ex = pd.DataFrame(rows_ex)
                _n_bask_ex  = sum(1 for r in rows_ex if r["Panier ETF"] == "OUI")
                _n_recu_ex  = sum(1 for r in rows_ex if r["Statut"] == "Recu")
                _n_attex    = sum(1 for r in rows_ex if r["Statut"] == "Détaché — en attente paiement")
                _n_fut_ex   = sum(1 for r in rows_ex if r["Statut"].startswith("Dans "))
                _n_prec_ex  = sum(1 for r in rows_ex if r["Statut"] == "Date à préciser")
                col_e1, col_e2, col_e3, col_e4 = st.columns(4)
                col_e1.metric("Dans le panier", _n_bask_ex)
                col_e2.metric("Reçus par l'ETF", _n_recu_ex,
                              help="Cash effectivement reçu sur la poche distribution (date de paiement atteinte)")
                col_e3.metric("En attente paiement", _n_attex,
                              help="Titre du panier détaché (ex-date passée) — cash attendu à la date de paiement BRVM")
                col_e4.metric("À venir", _n_fut_ex, help="Dates connues, pas encore détachés")
                st.dataframe(_df_ex, use_container_width=True, hide_index=True,
                             column_config={
                                 "Montant (FCFA)":  st.column_config.NumberColumn(format="%.2f"),
                                 "Rend. Sika (%)":  st.column_config.NumberColumn(format="%.2f"),
                                 "Cash ETF (FCFA)": st.column_config.NumberColumn(format="%.0f"),
                             })
                # Graphique : dividendes du panier
                _df_b_ex = _df_ex[_df_ex["Panier ETF"] == "OUI"].copy()
                if not _df_b_ex.empty:
                    _colors_ex = [
                        COLOR if s == "Recu"
                        else (BENCH_COLOR if s.startswith("Dans ") else "#bdbdbd")
                        for s in _df_b_ex["Statut"]
                    ]
                    fig_ex = go.Figure(go.Bar(
                        x=_df_b_ex["Ticker"], y=_df_b_ex["Montant (FCFA)"],
                        marker_color=_colors_ex,
                        text=_df_b_ex["Détachement"], textposition="outside",
                        hovertemplate="%{x} — %{text}<br><b>%{y:,.0f} FCFA/action</b><extra></extra>",
                    ))
                    fig_ex.update_layout(**PLOTLY_LAYOUT, height=320,
                        title=f"Dividendes {_annee_a} — panier ETF (FCFA/action)",
                        yaxis_title="FCFA / action")
                    fig_ex.add_annotation(
                        text="Vert = reçu par l'ETF · Doré = à venir · Gris = hors fenêtre",
                        xref="paper", yref="paper", x=0.01, y=1.08,
                        showarrow=False, font=dict(size=10, color="#7d8fa3"))
                    st.plotly_chart(fig_ex, width='stretch')
                    # Tableau cash détaillé si des événements existent
                    if _events_etf:
                        st.caption("Détail des dividendes reçus par l'ETF :")
                        _df_ev = pd.DataFrame(_events_etf)[[
                            "ticker","date_detach","date_paiement","montant_par_action","nb_actions_etf",
                            "cash_brut_fcfa","jours_placement","interets_fcfa","cash_total_fcfa"
                        ]].rename(columns={
                            "ticker":              "Ticker",
                            "date_detach":         "Ex-date",
                            "date_paiement":       "Paiement (ex+30j)",
                            "montant_par_action":  "Montant/action",
                            "nb_actions_etf":      "Nb actions ETF",
                            "cash_brut_fcfa":      "Cash brut (FCFA)",
                            "jours_placement":     "Jours RF",
                            "interets_fcfa":       "Intérêts RF (FCFA)",
                            "cash_total_fcfa":     "Cash total (FCFA)",
                        })
                        st.dataframe(_df_ev, use_container_width=True, hide_index=True,
                                     column_config={
                                         "Montant/action":   st.column_config.NumberColumn(format="%.2f"),
                                         "Nb actions ETF":   st.column_config.NumberColumn(format="%.2f"),
                                         "Cash brut (FCFA)": st.column_config.NumberColumn(format="%.0f"),
                                         "Intérêts RF (FCFA)": st.column_config.NumberColumn(format="%.0f"),
                                         "Cash total (FCFA)": st.column_config.NumberColumn(format="%.0f"),
                                     })
                        st.caption(f"Placement du cash au taux RF {_trf_a*100:.1f}% (BCEAO UEMOA) jusqu'au {_dist_str_a}")
                    else:
                        st.info(f"Aucun dividende reçu par l'ETF pour l'instant. "
                                f"Les prochains détachements dans le panier : "
                                + ", ".join(f"{r['Ticker']} le {r['Détachement']}"
                                            for _, r in _df_b_ex.iterrows()
                                            if r['Statut'].startswith('Dans ')))
            else:
                st.info("Aucune donnée dividendes — relancer scrape_sika_dividendes.py")

        # ── Tab 2 : Calendrier BRVM complet ──────────────────────────────────
        with _tab_cal:
            _divs_cal = sorted(_sika_a.get("dividendes", []),
                               key=lambda x: x.get("date_detach") or "9999")
            rows_cal = []
            for _d in _divs_cal:
                _tk_raw = _d.get("ticker") or ""
                _tk     = _DIV_TK_MAP.get(_tk_raw, _tk_raw) or _tk_raw
                _dt  = _d.get("date_detach")
                _mt  = _d.get("montant", 0)
                _rnd = _d.get("rendement")
                _in_b = "OUI" if (_tk and _tk in _bask_a) else "—"
                if not _dt:       _st_c = "À préciser"
                elif _dt < _today_a: _st_c = "Passé"
                else:             _st_c = "À venir"
                rows_cal.append({
                    "Ticker":         _tk or "—",
                    "Société":        _d.get("nom_sika") or _TICKER_NAMES.get(_tk, "—"),
                    "Détachement":    _dt or "—",
                    "Montant (FCFA)": _mt,
                    "Rend. (%)":      _rnd,
                    "Panier ETF":     _in_b,
                    "Statut":         _st_c,
                })
            if rows_cal:
                _df_cal = pd.DataFrame(rows_cal)
                col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                col_c1.metric("Dividendes BRVM",     len(rows_cal))
                col_c2.metric("Déjà détachés",       sum(1 for r in rows_cal if r["Statut"] == "Passé"))
                col_c3.metric("À venir",             sum(1 for r in rows_cal if r["Statut"] == "À venir"))
                col_c4.metric("Dans le panier ETF",  sum(1 for r in rows_cal if r["Panier ETF"] == "OUI"))
                st.dataframe(_df_cal, use_container_width=True, hide_index=True,
                             column_config={
                                 "Montant (FCFA)": st.column_config.NumberColumn(format="%.2f"),
                                 "Rend. (%)":      st.column_config.NumberColumn(format="%.2f"),
                             })
                # Yield chart : tous les tickers avec rendement connu
                _df_rnd = _df_cal[_df_cal["Rend. (%)"].notna()].sort_values("Rend. (%)", ascending=True)
                if not _df_rnd.empty:
                    fig_cal = go.Figure(go.Bar(
                        x=_df_rnd["Rend. (%)"], y=_df_rnd["Ticker"], orientation="h",
                        marker_color=[COLOR if p == "OUI" else "#bdbdbd" for p in _df_rnd["Panier ETF"]],
                        hovertemplate="%{y}<br>Rendement : <b>%{x:.2f}%</b><extra></extra>",
                    ))
                    fig_cal.update_layout(**PLOTLY_LAYOUT, height=420,
                        title=f"Rendement dividende {_annee_a} — marché BRVM (vert = dans le panier ETF)",
                        xaxis_title="Rendement (%)")
                    st.plotly_chart(fig_cal, width='stretch')

        # ── Tab 3 : Historique multi-années ──────────────────────────────────
        with _tab_hist_d:
            _hist_d = _dhist_a.get("history", {})
            if _hist_d:
                _years_h = sorted({yr for yrs in _hist_d.values() for yr in yrs})
                rows_h = []
                for _tk_raw, _yrs in sorted(_hist_d.items()):
                    _tk = _DIV_TK_MAP.get(_tk_raw, _tk_raw)
                    row = {"Ticker": _tk, "Panier ETF": "OUI" if _tk in _bask_a else "—"}
                    for _yr in _years_h:
                        row[_yr] = _yrs.get(_yr)
                    rows_h.append(row)
                _df_h = pd.DataFrame(rows_h)
                _df_h = pd.concat([
                    _df_h[_df_h["Panier ETF"] == "OUI"],
                    _df_h[_df_h["Panier ETF"] == "—"],
                ]).reset_index(drop=True)
                st.caption(f"Source : sikafinance.com — {len(_hist_d)} tickers · "
                           f"Mis à jour : {_dhist_a.get('updated_at','—')}")
                st.dataframe(_df_h, use_container_width=True, hide_index=True,
                             column_config={yr: st.column_config.NumberColumn(yr, format="%.0f")
                                            for yr in _years_h})
                # Graphique évolution par titre (panier seulement)
                _df_bh = _df_h[_df_h["Panier ETF"] == "OUI"]
                if not _df_bh.empty and len(_years_h) >= 2:
                    fig_hev = go.Figure()
                    for _, _r in _df_bh.iterrows():
                        _ys = [_r.get(_y) for _y in _years_h]
                        if any(v is not None and v == v for v in _ys):
                            fig_hev.add_trace(go.Scatter(
                                x=_years_h, y=_ys, name=_r["Ticker"],
                                mode="lines+markers",
                                connectgaps=True,
                                hovertemplate=f"{_r['Ticker']}<br>%{{x}} : <b>%{{y:,.0f}} FCFA</b><extra></extra>",
                            ))
                    fig_hev.update_layout(**PLOTLY_LAYOUT, height=400,
                        title="Évolution dividende / action — titres du panier (FCFA)",
                        yaxis_title="FCFA / action", xaxis_title="Année",
                        legend=dict(orientation="h", y=-0.2, x=0))
                    st.plotly_chart(fig_hev, width='stretch')
            else:
                st.info("Historique non disponible — relancer scrape_sika_dividendes.py")

        logs_dir = os.path.join(HALAL_DIR, "logs")
        if os.path.isdir(logs_dir):
            log_files = sorted([f for f in os.listdir(logs_dir) if f.startswith("daily_")], reverse=True)
            if log_files:
                with st.expander(f"Log pipeline — {log_files[0]}", expanded=False):
                    try:
                        with open(os.path.join(logs_dir, log_files[0]), encoding="utf-8", errors="replace") as lf:
                            st.code(lf.read(), language=None)
                    except Exception: st.caption("Log illisible.")

        # ── Alertes email ─────────────────────────────────────────────────────
        st.markdown("---")
        _section("Alertes email automatiques")
        _alert_cfg_path = os.path.join(HALAL_DIR, "alert_config.json")
        try:
            _alert_cfg = load_json(_alert_cfg_path) or {}
        except Exception:
            _alert_cfg = {}
        _enabled        = _alert_cfg.get("enabled", False)
        _badge          = "Activées" if _enabled else "Désactivées"
        st.caption(f"Statut : **{_badge}** — fichier : `alert_config.json`")

        with st.expander("Configurer les seuils d'alerte", expanded=False):
            _thr = _alert_cfg.get("thresholds", {})
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                _te_thr  = st.number_input("Tracking Error seuil (%)", value=float(_thr.get("tracking_error_pct", 2.0)), step=0.1, min_value=0.1)
                _td_thr  = st.number_input("Tracking Difference seuil (%)", value=float(_thr.get("tracking_diff_pct", 0.5)), step=0.1, min_value=0.0)
            with col_a2:
                _vl_thr  = st.number_input("Variation VL seuil (%)", value=float(_thr.get("vl_change_1d_pct", 3.0)), step=0.5, min_value=0.0)
                _age_thr = st.number_input("Données obsolètes (jours ouvrés)", value=int(_thr.get("data_age_biz_days", 2)), step=1, min_value=1)
            _smtp_user = st.text_input("Expéditeur SMTP (Gmail)", value=_alert_cfg.get("smtp_user", ""))
            _smtp_pwd  = st.text_input("App Password Gmail", type="password", value="",
                                       help="Générer sur myaccount.google.com > Sécurité > Mots de passe d'application")
            _recipients_raw = st.text_input("Destinataires (virgules)", value=", ".join(_alert_cfg.get("recipients", [])))
            _col_s1, _col_s2, _col_s3 = st.columns(3)
            with _col_s1:
                if st.button("Sauvegarder config", width='stretch'):
                    _new_cfg = {
                        "enabled":       True,
                        "smtp_host":     "smtp.gmail.com",
                        "smtp_port":     587,
                        "smtp_user":     _smtp_user,
                        "smtp_password": _smtp_pwd if _smtp_pwd else _alert_cfg.get("smtp_password", ""),
                        "recipients":    [r.strip() for r in _recipients_raw.split(",") if r.strip()],
                        "thresholds": {
                            "tracking_error_pct":  _te_thr,
                            "tracking_diff_pct":   _td_thr,
                            "vl_change_1d_pct":    _vl_thr,
                            "data_age_biz_days":   int(_age_thr),
                        },
                    }
                    try:
                        with open(_alert_cfg_path, "w", encoding="utf-8") as _af:
                            import json as _json_al
                            _json_al.dump(_new_cfg, _af, ensure_ascii=False, indent=2)
                        load_json.clear()
                        st.success("Configuration sauvegardée.")
                    except Exception as _ae:
                        st.error(f"Erreur : {_ae}")
            with _col_s3:
                if st.button("Désactiver alertes", width='stretch'):
                    if _alert_cfg:
                        _alert_cfg["enabled"] = False
                        try:
                            with open(_alert_cfg_path, "w", encoding="utf-8") as _af:
                                import json as _json_al2
                                _json_al2.dump(_alert_cfg, _af, ensure_ascii=False, indent=2)
                            load_json.clear()
                            st.success("Alertes désactivées.")
                        except Exception as _ae2:
                            st.error(str(_ae2))

        if nl_mgmt:
            st.markdown("---")
            _section("Situation actuelle")
            age = nl_mgmt.get("data_age_biz_days", 0)
            if age and age > 1:
                st.warning(f"Données vieilles de {age} jour(s). Dernier scraping : {nl_mgmt.get('calc_date', '—')}")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("VL par part",           f"{nl_mgmt.get('vl_par_part_fcfa', 0):,.0f} FCFA")
            c2.metric("AUM",                   f"{nl_mgmt.get('aum_mfcfa', 0):,.0f} MFCFA")
            c3.metric("Depuis lancement",      f"{nl_mgmt.get('perf_since_launch', 0):+.2f}%")
            c4.metric("Dernier rebal.",         nl_mgmt.get("last_rebal_date", "—"))
            c5.metric("Titres en portefeuille", str(nl_mgmt.get("n_basket", "—")))
            st.caption(f"VL officielle calculée sur prix de clôture BRVM — mise à jour automatique chaque jour à 16h00 après clôture (15h30 UTC). Dernière mise à jour : {nl_mgmt.get('calc_date', '—')}. Pour la VL indicative en temps réel, voir la section iNAV.")

        # ── Rendement Dividende & Total Return ───────────────────────────────
        st.markdown("---")
        _section("Rendement Dividende & Total Return")
        _sika_div_tr  = load_json(os.path.join(BASE, "data", "sika_dividendes.json")) or {}
        _divs_tr      = _sika_div_tr.get("dividendes", [])
        _today_tr     = pd.Timestamp.now().strftime("%Y-%m-%d")
        _launch_tr    = (load_json(os.path.join(HALAL_DIR, "launch_state.json")) or {}).get("launch_date", "")

        # Construire index basket ETF et Indice Dividende
        _bask_tr  = {b["ticker"]: b for b in basket_now}
        _b30_tr   = {b["ticker"]: b.get("w_brvm30", 0) for b in last_rb.get("basket", [])}

        # Normalisation tickers Sika → basket
        _TK_MAP_TR = {"": "NSBC", "TOTC": "TTLC", "VIVC": "SHEC"}

        _etf_div_yield  = 0.0
        _b30_div_yield  = 0.0
        _rows_div_tr    = []

        for _d in _divs_tr:
            _dt = _d.get("date_detach") or ""
            if not _dt or _dt > _today_tr:
                continue
            if _launch_tr and _dt < _launch_tr:
                continue
            _tk_raw = _d.get("ticker") or ""
            _tk     = _TK_MAP_TR.get(_tk_raw, _tk_raw)
            _rend   = float(_d.get("rendement") or 0) / 100  # Sika donne en %

            _w_etf = (_bask_tr[_tk]["poids_pct"] / 100) if _tk in _bask_tr else 0.0
            _w_b30 = _b30_tr.get(_tk, 0.0)

            _contrib_etf = _w_etf * _rend * 100
            _contrib_b30 = _w_b30 * _rend * 100

            _etf_div_yield += _contrib_etf
            _b30_div_yield += _contrib_b30

            if _w_etf > 0 or _w_b30 > 0:
                _rows_div_tr.append({
                    "Ticker":           _tk or _tk_raw or "—",
                    "Ex-date":          _dt,
                    "Rend. Sika (%)":   round(_rend * 100, 2),
                    "Poids ETF (%)":    round(_w_etf * 100, 3),
                    "Contrib ETF (bp)": round(_contrib_etf * 100, 1),
                    "Poids Indice Dividende (%)": round(_w_b30 * 100, 3),
                    "Contrib B30 (bp)": round(_contrib_b30 * 100, 1),
                })

        # Perf Price Return depuis lancement
        _ls_tr       = load_json(os.path.join(HALAL_DIR, "launch_state.json")) or {}
        _nav_now_tr  = (load_json_fresh(nav_latest_path) or {}).get("nav_indice", 0)
        _nav_anc_tr  = float(_ls_tr.get("nav_index_at_launch") or _nav_now_tr or 1)
        _pr_etf      = (_nav_now_tr / _nav_anc_tr - 1) * 100 if _nav_anc_tr else 0.0
        _pr_b30      = _pr_etf  # même base indice — PR identique par construction

        _tr_etf = _pr_etf + _etf_div_yield
        _tr_b30 = _pr_b30 + _b30_div_yield
        _ecart_div = _etf_div_yield - _b30_div_yield

        _td1, _td2, _td3, _td4, _td5 = st.columns(5)
        _td1.metric("Rend. Div. ETF (YTD)",   f"{_etf_div_yield:.2f}%",
                    help="Dividendes captés par l'ETF pondérés par les poids du panier")
        _td2.metric("Rend. Div. Indice Dividende (YTD)", f"{_b30_div_yield:.2f}%",
                    help="Dividendes théoriques de l'indice pondérés par les poids Indice Dividende")
        _td3.metric("Total Return ETF",        f"{_tr_etf:+.2f}%",
                    help="Price Return ETF + Rendement Dividende ETF")
        _td4.metric("Total Return Indice Dividende",     f"{_tr_b30:+.2f}%",
                    help="Price Return Indice Dividende + Rendement Dividende Indice Dividende")
        _td5.metric("Écart Div. ETF vs B30",   f"{_ecart_div:+.2f}%",
                    delta=round(_ecart_div, 2),
                    help="Positif = ETF a capté plus de dividendes que l'indice (bonne capture)")

        if _rows_div_tr:
            _df_div_tr = pd.DataFrame(_rows_div_tr).sort_values("Contrib ETF (bp)", ascending=False)
            _fig_div = go.Figure()
            _fig_div.add_trace(go.Bar(
                x=_df_div_tr["Ticker"], y=_df_div_tr["Contrib ETF (bp)"],
                name="Contribution ETF (bp)", marker_color=COLOR,
                hovertemplate="%{x}<br>ETF : <b>%{y:.1f} bp</b><extra></extra>",
            ))
            _fig_div.add_trace(go.Bar(
                x=_df_div_tr["Ticker"], y=_df_div_tr["Contrib B30 (bp)"],
                name="Contribution Indice Dividende (bp)", marker_color=BENCH_COLOR,
                hovertemplate="%{x}<br>Indice Dividende : <b>%{y:.1f} bp</b><extra></extra>",
            ))
            _fig_div.update_layout(**PLOTLY_LAYOUT, height=300, barmode="group",
                title="Contribution dividende par titre — ETF vs Indice Dividende (points de base)",
                yaxis_title="bp", legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(_fig_div, width='stretch')

            with st.expander("Détail par titre"):
                st.dataframe(_df_div_tr, use_container_width=True, hide_index=True,
                             column_config={
                                 "Rend. Sika (%)":   st.column_config.NumberColumn(format="%.2f"),
                                 "Poids ETF (%)":    st.column_config.NumberColumn(format="%.3f"),
                                 "Contrib ETF (bp)": st.column_config.NumberColumn(format="%.1f"),
                                 "Poids Indice Dividende (%)": st.column_config.NumberColumn(format="%.3f"),
                                 "Contrib B30 (bp)": st.column_config.NumberColumn(format="%.1f"),
                             })
        else:
            st.info("Aucun dividende détaché depuis le lancement de l'ETF.")

        # ── Comptabilité Dividend Settlement Gap ──────────────────────────────
        st.markdown("---")
        _section("Dividend Settlement Gap — Comptabilité")
        _acct_dsg    = load_json(os.path.join(BASE, "data", "dividend_accounting.json")) or {}
        _events_dsg  = _acct_dsg.get("evenements", [])
        _recv_dsg    = _acct_dsg.get("dividend_receivable_fcfa", 0) or 0
        _payable_dsg = _acct_dsg.get("distribution_payable_fcfa", 0) or 0
        _poche_dsg   = _acct_dsg.get("poche_distribution_fcfa", 0) or 0

        _dc1, _dc2, _dc3 = st.columns(3)
        _dc1.metric("Dividend Receivable (actif)",
                    f"{_recv_dsg:,.0f} FCFA",
                    help="Créance sur dividendes détachés — cash pas encore reçu de la BRVM")
        _dc2.metric("Distribution Payable (passif)",
                    f"{_payable_dsg:,.0f} FCFA",
                    help="Dette envers les porteurs — montant à reverser")
        _dc3.metric("Poche Distribution (cantonnée)",
                    f"{_poche_dsg:,.0f} FCFA",
                    help="Cash reçu routé vers la poche dépositaire — ne transite pas par la NAV")

        if _events_dsg:
            _rows_dsg = []
            for _ev in _events_dsg:
                _rows_dsg.append({
                    "Ticker":          _ev.get("ticker", "—"),
                    "Ex-date":         _ev.get("ex_date", "—"),
                    "Montant/action":  _ev.get("montant_par_action_fcfa", 0),
                    "Nb titres (ETF)": int(_ev.get("nb_titres_etf", 0) or 0),
                    "Total FCFA":      int(_ev.get("montant_total_fcfa", 0) or 0),
                    "Par part FCFA":   round(_ev.get("montant_par_part_fcfa", 0) or 0, 4),
                    "Paiement":        _ev.get("payment_date") or "En attente",
                    "Distribution":    _ev.get("distribution_date", "—"),
                    "Statut":          _ev.get("status", "—").upper(),
                })
            st.dataframe(
                pd.DataFrame(_rows_dsg),
                use_container_width=True, hide_index=True,
                column_config={
                    "Montant/action": st.column_config.NumberColumn(format="%.2f"),
                    "Total FCFA":     st.column_config.NumberColumn(format="%d"),
                    "Par part FCFA":  st.column_config.NumberColumn(format="%.4f"),
                }
            )

            with st.expander("Journal comptable détaillé"):
                for _ev in _events_dsg:
                    st.caption(f"**{_ev['ticker']}** — ex-date {_ev['ex_date']}")
                    for _je in _ev.get("journal", []):
                        _col = {"ACCRUAL": "#c9861a", "PAYMENT": "#1565c0",
                                "DISTRIBUTION": "#2d7a4f"}.get(_je.get("type"), "#555")
                        st.markdown(
                            f"<span style='color:{_col}'><b>{_je['type']}</b></span> "
                            f"{_je['date']} — Débit : {_je['debit']} / Crédit : {_je['credit']} "
                            f"— {int(_je.get('montant_fcfa', 0) or 0):,} FCFA",
                            unsafe_allow_html=True,
                        )
        else:
            st.info("Aucun dividende provisionné pour le moment. "
                    "Le provisionnement automatique se déclenche chaque matin à l'ex-date "
                    "via check_corporate_actions.py.")

        # Actions manuelles
        _accrued_dsg  = [e for e in _events_dsg if e.get("status") == "accrued"]
        _received_dsg = [e for e in _events_dsg if e.get("status") == "received"]
        if _accrued_dsg:
            st.caption("Enregistrer la réception du cash (quand la BRVM verse le dividende) :")
            for _ev_btn in _accrued_dsg:
                _btn_lbl = (f"Marquer reçu — {_ev_btn['ticker']} "
                            f"({int(_ev_btn.get('montant_total_fcfa', 0) or 0):,} FCFA)")
                if st.button(_btn_lbl, key=f"dsg_recv_{_ev_btn['id']}"):
                    _scripts = os.path.join(BASE, "scripts")
                    if _scripts not in sys.path:
                        sys.path.insert(0, _scripts)
                    from check_corporate_actions import CorporateActionsChecker as _CAC
                    _CAC().record_payment_received(_ev_btn["ticker"], _ev_btn["ex_date"])
                    load_json.clear()
                    st.rerun()
        if _received_dsg:
            _total_dsg = sum(e.get("montant_total_fcfa", 0) or 0 for e in _received_dsg)
            if st.button(f"Distribuer aux porteurs — {_total_dsg:,.0f} FCFA",
                         key="dsg_distribuer", type="primary"):
                _scripts = os.path.join(BASE, "scripts")
                if _scripts not in sys.path:
                    sys.path.insert(0, _scripts)
                from check_corporate_actions import CorporateActionsChecker as _CAC
                _CAC().record_distribution()
                load_json.clear()
                st.rerun()



# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD — Point d'entrée OOP
# ══════════════════════════════════════════════════════════════════════════════
class Dashboard:
    """
    Dashboard CGF ETF Dividende BRVM — structure orientée objet.

    Chaque section est une méthode dédiée pour faciliter la navigation et
    la maintenance du code par l'équipe.

    Structure :
      run()              — routing principal (délègue selon _page)
      render_landing()   — page d'accueil (cartes, téléchargements)
      render_backtest()  — backtest simulation 2023–2026
      render_live()      — live ETF : iNAV, rebalancements, AP, analyse

    Ajouter une nouvelle section :
      1. Définir la fonction _render_xxx() au-dessus de cette classe
      2. Ajouter render_xxx = staticmethod(_render_xxx) ici
      3. Ajouter l'appel dans run()
    """

    render_landing  = staticmethod(_render_landing)
    render_backtest = staticmethod(_render_backtest)
    render_live     = staticmethod(_render_live)

    def run(self):
        """Point d'entrée principal — routing par valeur de ?page=."""
        if _page == "landing":
            self.render_landing()
        elif _page == "backtest":
            self.render_backtest()
        elif _page == "live":
            self.render_live()


Dashboard().run()
