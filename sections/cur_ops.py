"""Current Finance carry: triggers, monitoring console, runbook, team support, edge, pre-mortem."""

import streamlit as st

from utils.refresh import refresh_control

import project_config as cfg
from utils.blocks import console, rows_current
from utils.data_loader import load_editorial
from utils.text import T


def render():
    st.markdown('<div class="eyebrow">Current Finance carry · technical analysis</div>', unsafe_allow_html=True)
    st.title("Monitoring and Operations")
    refresh_control("ops")
    st.subheader("Exit triggers")
    st.caption(T("cur.triggers_note"))
    t = load_editorial("monitoring_triggers")
    if not t.empty:
        st.dataframe(t[t["proposal"] == "C26"].drop(columns=["proposal"]).rename(columns=str.title), hide_index=True, width="stretch")
    st.subheader("Monitoring console")
    st.caption(T("cur.console_note"))
    console(rows_current())
    st.subheader("Runbook")
    st.markdown(T("cur.runbook"))
    st.subheader("Custody and signing")
    st.markdown(T("cur.custody"))

    st.subheader("Team support")
    st.markdown(T("cur.team"))
    st.subheader("Opportunity rationale")
    st.markdown(T("cur.why"))
    st.subheader("Pre-mortem")
    st.markdown(T("cur.premortem"))
