"""Current Finance carry: controls, security and risk partners, insurance."""

import streamlit as st

from utils.blocks import admin_table
from utils.text import T


def render():
    st.markdown('<div class="eyebrow">Current Finance carry · technical analysis</div>', unsafe_allow_html=True)
    st.title("Controls and Security")
    st.subheader("Audits and security partners")
    st.markdown(T("cur.partners"))
    st.subheader("On-chain review")
    st.markdown(T("cur.controls"))
    st.subheader("Admin and upgrade controls")
    admin_table(["Current carry"])
    st.caption(T("cur.controls_note"))

    st.subheader("Insurance")
    st.markdown(T("cur.insurance"))
