"""Contents and search across every page of the report."""

import json
import re
from pathlib import Path

import streamlit as st

import project_config as cfg

INDEX_PATH = Path(__file__).resolve().parent.parent / "data" / "search_index.json"


@st.cache_data
def load_index():
    try:
        return json.loads(INDEX_PATH.read_text())
    except Exception:
        return []


def link(entry):
    return f"/{entry['url']}#{entry['anchor']}" if entry.get("anchor") else f"/{entry['url']}"


def a(href, label, bold=False):
    """Same-tab link. Streamlit opens Markdown links in a new tab, so plain HTML is used."""
    label = f"<b>{label}</b>" if bold else label
    return f'<a href="{href}" target="_self">{label}</a>'


def snippet(text, words, width=110):
    low = text.lower()
    pos = min((low.find(w) for w in words if low.find(w) >= 0), default=0)
    start, end = max(0, pos - width), min(len(text), pos + width)
    s = ("…" if start else "") + text[start:end] + ("…" if end < len(text) else "")
    s = s.replace("$", "\\$")
    for w in sorted(words, key=len, reverse=True):
        s = re.sub(f"({re.escape(w)})", r"**\1**", s, flags=re.I)
    return s


def render():
    st.markdown('<div class="eyebrow">Report</div>', unsafe_allow_html=True)
    st.title("Contents and Search")
    index = load_index()

    query = st.text_input("Search the whole report", placeholder="For example: liquidation, Nexus, daily cap, oracle, rebalance")
    words = [w for w in re.findall(r"[\w.%$-]+", query.lower()) if len(w) > 1]
    if words:
        hits = []
        for e in index:
            hay = (e["section"] + " " + e["text"]).lower()
            if all(w in hay for w in words):
                score = sum(hay.count(w) for w in words) + 5 * sum(w in e["section"].lower() for w in words)
                hits.append((score, e))
        hits.sort(key=lambda h: -h[0])
        st.caption(f"{len(hits)} sections match" + (" (showing the first 30)" if len(hits) > 30 else ""))
        for _, e in hits[:30]:
            st.markdown(a(link(e), f"{e['page']} › {e['section']}", bold=True) + "  \n" + snippet(e["text"], words),
                        unsafe_allow_html=True)
        if not hits:
            st.info("No section contains all of those words. Try fewer or shorter words.")
        st.divider()

    st.subheader("Contents")
    st.caption("Click a page or a section to go straight to it.")
    by_url = {}
    for e in index:
        by_url.setdefault(e["url"], []).append(e)
    group = None
    for p in cfg.PAGES:
        if p["module"] == "contents":
            continue
        if p["group"] != group:
            group = p["group"]
            st.markdown(f'<div class="eyebrow" style="margin-top:1.1rem">{group}</div>', unsafe_allow_html=True)
        secs = [e for e in by_url.get(p["url"], []) if e["section"] != "Overview"]
        lines = [a(f"/{p['url']}", p["title"], bold=True) + f": {p.get('desc', '')}"]
        if secs:
            lines.append("  \n" + " · ".join(a(link(e), e["section"]) for e in secs))
        st.markdown("".join(lines), unsafe_allow_html=True)
    if not index:
        st.warning("The search index is missing. Run export_report.py to build it.")
