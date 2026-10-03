"""
Sourcing and screening: how candidates were found, the criteria, and why each one was kept or dropped.
"""

import plotly.graph_objects as go
import streamlit as st

from utils.charts import apply_layout
from utils.data_loader import load_editorial
from utils.text import T



def render():
    st.markdown('<div class="eyebrow">Process</div>', unsafe_allow_html=True)
    st.title("Sourcing and Screening")
    st.caption(T("screen.date"))

    cands, gates = load_editorial("candidates"), load_editorial("gates")
    if cands.empty:
        st.info("candidates.csv missing.")
        return

    st.markdown(T("screen.intro"))

    cands = cands[~cands["status"].fillna("").str.startswith("On hold")].reset_index(drop=True)
    st_ = cands["status"].fillna("")
    groups = {"Rejected": st_.str.startswith("Rejected").sum(), "Requires automation": (st_ == "Requires automation").sum(),
              "Needs data, monitoring or team discussion": st_.isin(["Needs data or monitoring", "Team discussion"]).sum(),
              "Selected": st_.str.startswith("Selected").sum()}
    proposals = int(groups["Selected"])
    cols = st.columns(len(groups))
    for col, (k, v) in zip(cols, groups.items()):
        col.metric(k, int(v))
    stages = ["Screened", "Passed yield and capacity", "Passed income-source test", "Selected"]
    passed_yield = len(cands) - int(cands["deciding_issue"].str.contains("C3|C1|C4").sum())
    passed_g6 = passed_yield - int(cands["deciding_issue"].str.contains("C6").sum())
    fig = go.Figure(go.Funnel(y=stages, x=[len(cands), passed_yield, max(passed_g6, proposals), proposals],
                              marker_color=["#9CA3AF", "#9CA3AF", "#9CA3AF", "#2470FF"]))
    st.plotly_chart(apply_layout(fig, title="Screening funnel (approximate: some candidates fail several gates)", height=300,
                                 show_legend=False), width="stretch")

    st.subheader("Investment criteria")
    st.dataframe(gates.rename(columns=str.title), hide_index=True, width="stretch")
    st.markdown(T("screen.income_test"))

    st.subheader("Candidates screened")
    status = st.multiselect("Filter by status", sorted(cands["status"].unique()), default=[])
    view = cands if not status else cands[cands["status"].isin(status)]
    st.dataframe(view.rename(columns=lambda c: c.replace("_", " ").title()), hide_index=True, width="stretch", height=560)


    st.subheader("Repeatable process")
    st.markdown(T("screen.repeat"))

    st.subheader("Pipeline")
    st.caption(T("screen.pipeline_note"))
    p = load_editorial("pipeline")
    if not p.empty:
        st.dataframe(p.rename(columns={"name": "Idea", "link": "Link", "mechanism": "Mechanism", "yield": "Yield",
                                       "why_not_now": "Why not now"}), hide_index=True, width="stretch",
                     column_config={"Link": st.column_config.LinkColumn("Link", display_text="open")})
    st.caption(T("screen.open_item"))
