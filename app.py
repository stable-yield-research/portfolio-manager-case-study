"""
Streamlit case study dashboard.

Run locally:   streamlit run app.py
Configure:     project_config.py (title, pages, events, data files)
"""

import importlib

import streamlit as st

import project_config as cfg

st.set_page_config(page_title=cfg.PROJECT_TITLE, layout="wide", initial_sidebar_state="expanded")

# ── CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Sans:wght@300;400;500&family=Barlow+Condensed:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,300;8..60,400&display=swap');

    :root { --ink:#1C1C1C; --cream:#FFFEF8; --panel:#262323; --navy:#1E3B70; --teal:#00736B; --teal2:#00BBA0; --rule:#DCEFEB; --muted:#57585B; }

    html, body, .main, .block-container, p, span, li, td, th, label, a,
    [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p, [data-testid="stText"] {
        font-family: 'Fira Sans', 'Helvetica Neue', sans-serif; font-weight: 300; color: var(--ink);
    }
    strong, b { font-weight: 500; }
    .block-container { max-width: 1180px; padding-top: 2.5rem; }

    h1, [data-testid="stHeading"] h1 {
        font-family: 'Source Serif 4', Georgia, serif !important; font-weight: 300 !important;
        font-size: 2.6rem !important; letter-spacing: -0.01em; color: var(--ink) !important; line-height: 1.15;
    }
    h1 span, h1 div, [data-testid="stHeading"] h1 * { font-family: 'Source Serif 4', Georgia, serif !important; font-weight: 300 !important; }
    h2, h3, h4, [data-testid="stHeading"] h2, [data-testid="stHeading"] h3 {
        font-family: 'Barlow Condensed', 'Arial Narrow', sans-serif !important; font-weight: 600 !important;
        text-transform: uppercase; letter-spacing: 0.08em; color: var(--navy) !important;
    }
    h2 { font-size: 1.35rem !important; border-bottom: 1px solid var(--rule); padding-bottom: .35rem; margin-top: 1.6rem; }
    h3 { font-size: 1.1rem !important; }

    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { color: var(--muted) !important; font-size: .82rem; }

    [data-testid="stMetric"] { background: #FFFFFF; border: 1px solid #E6E1D6; border-top: 3px solid var(--teal2); border-radius: 2px; padding: 12px 16px; }
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {
        font-family: 'Barlow Condensed', sans-serif !important; text-transform: uppercase; letter-spacing: .06em;
        font-size: .82rem !important; color: var(--muted) !important; font-weight: 500 !important;
    }
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
        font-family: 'Source Serif 4', Georgia, serif !important; font-weight: 400 !important; font-size: 1.7rem !important; color: var(--ink) !important;
    }

    .eyebrow { font-family: 'Barlow Condensed', sans-serif; text-transform: uppercase; letter-spacing: .12em; color: var(--teal2); font-weight: 500; font-size: .9rem; }
    .panel { background: var(--panel); color: #FCF8F3; padding: 1.4rem 1.6rem; border-radius: 3px; margin: .6rem 0 1.2rem 0; }
    .panel p, .panel li, .panel span, .panel strong { color: #FCF8F3 !important; }
    .panel .lead { font-family: 'Source Serif 4', Georgia, serif; font-weight: 300; font-size: 1.35rem; line-height: 1.45; }
    .rule { border-top: 1px solid var(--rule); margin: 1.4rem 0; }
    .section-divider { border-top: 1px solid var(--rule); margin: 1.5rem 0; }
    .tag-ok { color: var(--teal); font-weight: 500; } .tag-watch { color: #B45309; font-weight: 500; } .tag-no { color: #B91C1C; font-weight: 500; }

    [data-testid="stSidebar"] { background-color: var(--panel); border-right: none; }
    [data-testid="stSidebar"] * { color: #D9D5CE !important; }
    [data-testid="stSidebarNav"] a span { font-family: 'Fira Sans', sans-serif; font-weight: 300; }
    [data-testid="stSidebarNav"] [data-testid="stNavSectionHeader"], [data-testid="stSidebarNavSeparator"] + div span {
        font-family: 'Barlow Condensed', sans-serif !important; text-transform: uppercase; letter-spacing: .12em; color: var(--teal2) !important;
    }
    [data-testid="stDataFrame"] { border: 1px solid #E6E1D6; border-radius: 2px; }
    .stAlert, [data-testid="stAlert"] > div { border-radius: 2px; background: #EEF6F3 !important; border-left: 3px solid var(--teal2); }
    [data-testid="stAlert"] * { color: var(--ink) !important; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Navigation (built from project_config.PAGES) ────────────────
groups: dict[str, list] = {}
page_objs: dict[str, object] = {}
for p in cfg.PAGES:
    module = importlib.import_module(f"sections.{p['module']}")
    page_objs[p["url"]] = st.Page(module.render, title=p["title"], url_path=p["url"], default=p.get("default", False))
    groups.setdefault(p["group"], []).append(page_objs[p["url"]])
nav = st.navigation(groups, expanded=True)

# ── Sidebar ─────────────────────────────────────────────────────
with st.sidebar:
    # Re-scroll to a #section link once the page has finished rendering (charts and tables load after the first scroll).
    st.iframe("""<script>
      const go = () => { const h = window.parent.location.hash.slice(1);
        if (h) { const e = window.parent.document.getElementById(h); if (e) e.scrollIntoView({block: "start"}); } };
      setTimeout(go, 1500); setTimeout(go, 4000);
    </script>""", height=1)
    st.markdown('<div class="eyebrow">Investment Committee</div>', unsafe_allow_html=True)
    st.caption(cfg.PROJECT_SUBTITLE)
    st.divider()

    st.divider()
    st.caption(cfg.SIDEBAR_FOOTER)

    from utils.data_loader import show_data_warnings
    show_data_warnings()

nav.run()
