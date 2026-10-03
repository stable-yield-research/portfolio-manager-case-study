"""Current Finance carry: risk controls matrix and stress tests."""

import streamlit as st

from utils.refresh import refresh_control

import project_config as cfg
from utils.data_loader import load_csv, load_current, load_current_snapshot
from utils.strategy import cur_stress
from utils.text import T


def render():
    st.markdown('<div class="eyebrow">Current Finance carry · technical analysis</div>', unsafe_allow_html=True)
    st.title("Risk Controls and Stress Tests")
    refresh_control("matrix")
    st.markdown(T("cur.controls_intro"))
    cur, cs = load_current(), load_current_snapshot()
    if not cur.empty and not cs.empty:
        st.subheader("Stress tests")
        st.dataframe(cur_stress(cur, cs.iloc[-1], cfg.CUR_LEVERAGE, cfg.EQUITY / 1e6), hide_index=True, width="stretch")
    m = load_csv("risk_controls_matrix.csv")
    if m.empty:
        return
    st.subheader("Controls matrix")
    st.markdown(T("cur.matrix_legend"))
    c1, c2 = st.columns(2)
    status = m["status"].map(lambda v: "In place" if v.startswith("In place") else ("Partly in place" if v.startswith("Partly") else "To build"))
    pick_s = c1.multiselect("Status", sorted(status.unique()), default=[])
    pick_p = c2.multiselect("Priority", sorted(m["priority"].unique()), default=[])
    mask = status.isin(pick_s) if pick_s else status.notna()
    if pick_p:
        mask &= m["priority"].isin(pick_p)
    view = m[mask]
    k1, k2, k3 = st.columns(3)
    k1.metric("In place", int((status == "In place").sum()))
    k2.metric("Partly in place", int((status == "Partly in place").sum()))
    k3.metric("To build", int((status == "To build").sum()))
    st.dataframe(view.rename(columns=lambda c: c.replace("_", " ").title()), hide_index=True, width="stretch", height=560)
