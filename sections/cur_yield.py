"""Current Finance carry: structure, yield by source, rate curve, history."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.refresh import refresh_control

import project_config as cfg
from utils.charts import GREEN, GREY, NAVY, RED, TEAL, apply_layout
from utils.data_loader import load_current
from utils.strategy import cur_components_avg, cur_curve, cur_daily, cur_legs, monthly_apr
from utils.text import T


def render():
    st.markdown('<div class="eyebrow">Current Finance carry · technical analysis</div>', unsafe_allow_html=True)
    st.title("Structure and Yield")
    refresh_control("yield")
    cur = load_current()
    if cur.empty:
        st.info("current_daily.csv missing.")
        return
    L = st.slider("Leverage of each vault", 2.0, 4.8, cfg.CUR_LEVERAGE, 0.5)
    e1, e2, a, d1, d2 = cur_legs(L)
    st.subheader("Structure")
    st.markdown(T("cur.structure", L=f"{L:g}", e1=f"{e1:.0%}", e2=f"{e2:.0%}"))
    st.dataframe(pd.DataFrame({"per $1 of equity": ["USDC supplied", "USDSUI borrowed (vault 1) = held (vault 2)", "USDC borrowed (vault 2)"],
                               "amount": [f"{a:.2f}", f"{d1:.2f}", f"{d2:.2f}"]}), hide_index=True, width="stretch")

    st.subheader("Rationale for two vaults")
    st.markdown(T("cur.two_vaults"))

    st.subheader("Yield decomposition")
    comp = cur_components_avg(cur.tail(30), L, cfg.EQUITY / 1e6)
    df = pd.DataFrame({"source": list(comp), "apr": list(comp.values())})
    fig = go.Figure(go.Waterfall(x=df["source"], y=df["apr"], measure=["relative"] * len(df),
                                 increasing=dict(marker_color=GREEN), decreasing=dict(marker_color=RED)))
    fig.add_hline(y=cfg.HURDLE_APR, line_dash="dash", line_color=GREY, annotation_text="12%")
    st.plotly_chart(apply_layout(fig, title=f"Yield by source at {L:g}x on $1.5M, last 30 days: net {sum(comp.values()):.1f}%",
                                 height=380, show_legend=False), width="stretch")
    st.caption(T("cur.yield_note"))

    st.subheader("Interest rate model")
    st.markdown(T("cur.curve"))
    u = np.linspace(0, 0.9, 91)
    fig2 = go.Figure(go.Scatter(x=u * 100, y=cur_curve(u), line=dict(color=NAVY, width=2.5), name="borrow APR"))
    fig2.add_trace(go.Scatter(x=cur["s_utilization"] * 100, y=cur["s_borrowAPY"], mode="markers", name="USDSUI, daily",
                              marker=dict(color=TEAL, size=5)))
    fig2.add_trace(go.Scatter(x=cur["c_utilization"] * 100, y=cur["c_borrowAPY"], mode="markers", name="USDC, daily",
                              marker=dict(color=GREY, size=5)))
    fig2.update_xaxes(title_text="utilization, %")
    st.plotly_chart(apply_layout(fig2, title="Borrow APR vs utilization (%)", height=340), width="stretch")

    st.subheader("Historical returns")
    rows = []
    d = pd.DataFrame({"date": cur["date"]})
    for lev in (3.0, 3.5, 4.5):
        d[f"{lev}x zero"] = cur_daily(cur, lev, 0.0).values
        d[f"{lev}x $1.5M"] = cur_daily(cur, lev, cfg.EQUITY / 1e6).values
    m = None
    for col in [c for c in d.columns if c != "date"]:
        mm = monthly_apr(d, col).rename(columns={"apr": col})
        m = mm if m is None else m.merge(mm, on="month")
    st.dataframe(m.round(1), hide_index=True, width="stretch")
    fig3 = go.Figure()
    dd = d.copy(); dd["date"] = pd.to_datetime(dd["date"])
    fig3.add_trace(go.Scatter(x=dd["date"], y=dd["3.5x $1.5M"].rolling(7, min_periods=1).mean(), name="3.5x at $1.5M", line=dict(color=NAVY, width=2.5)))
    fig3.add_trace(go.Scatter(x=dd["date"], y=dd["3.5x zero"].rolling(7, min_periods=1).mean(), name="3.5x, zero size", line=dict(color=GREY)))
    fig3.add_hline(y=cfg.HURDLE_APR, line_dash="dash", line_color=GREY)
    st.plotly_chart(apply_layout(fig3, title="Net yield, 7-day average (%)", height=340), width="stretch")
