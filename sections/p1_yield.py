"""
USD1 carry: structure and yield.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import project_config as cfg
from utils.charts import ACCENT, GREEN, GREY, RED, apply_layout, event_lines
from utils.data_loader import load_c21_rates
from utils.strategy import c21_components, c21_net, legs, window_rates
from utils.text import T


def render(embedded=False):
    if not embedded:
        st.markdown('<div class="eyebrow">On hold · USD1 carry</div>', unsafe_allow_html=True)
        st.title("USD1 Carry · Structure and Yield")
        st.warning(T("s1.hold"))
    st.caption(f"Realized rates from interest indexes, as of {cfg.PIN_LABEL}.")
    rates = load_c21_rates()
    if rates.empty:
        st.info("c21_rates_daily.csv missing.")
        return

    st.subheader("Structure")
    st.markdown(T("s1.structure"))

    L = st.slider("Leverage for this page (total collateral / equity)", 1.5, 4.0, cfg.C21_LEVERAGE, 0.5)
    r30 = window_rates(rates, 30)
    comp = c21_components(L, r30)
    df = pd.DataFrame({"source": list(comp), "apr": list(comp.values())})
    fig = go.Figure(go.Waterfall(x=df["source"], y=df["apr"], measure=["relative"] * len(df),
                                 increasing=dict(marker_color=GREEN), decreasing=dict(marker_color=RED)))
    fig.add_hline(y=cfg.HURDLE_APR, line_dash="dash", line_color=GREY, annotation_text="12% hurdle")
    st.plotly_chart(apply_layout(fig, title=f"Yield by source at {L:.1f}x, last 30 days: net {c21_net(L, r30):.1f}%",
                                 height=380, show_legend=False), width="stretch")
    base = sum(v for k, v in comp.items() if "WLFI" not in k)
    rew = sum(v for k, v in comp.items() if "WLFI" in k)
    st.markdown(f"Base lending spread: **{base:+.1f}%**. WLFI rewards: **{rew:+.1f}%**. " + T("s1.yield_note"))

    st.subheader("Net APR by leverage")
    windows = {"Last 30 days": 30, "Last 90 days": 90, "Since 22 Apr": len(rates[rates["date"] >= cfg.WINDOW_START])}
    rows = []
    for name, d in windows.items():
        r = window_rates(rates, d)
        rows.append([name] + [f"{c21_net(x, r):.1f}%" for x in (2, 2.5, 3, 3.5, 4)])
    r = window_rates(rates, 30)
    for label, mult in (("30 days, WLFI rewards -50%", 0.5), ("30 days, no WLFI rewards", 0.0)):
        rr = {**r, "usd1_wlfi_reward": r["usd1_wlfi_reward"] * mult, "usdc_wlfi_reward": r["usdc_wlfi_reward"] * mult}
        rows.append([label] + [f"{c21_net(x, rr):.1f}%" for x in (2, 2.5, 3, 3.5, 4)])
    rows.append(["Health, both positions"] + [f"{legs(x)[3]:.2f}" for x in (2, 2.5, 3, 3.5, 4)])
    rows.append(["USD1 fall that liquidates B"] + [f"{1 - 1 / legs(x)[3]:.0%}" for x in (2, 2.5, 3, 3.5, 4)])
    rows.append(["USD1 rise that liquidates A"] + [f"{legs(x)[3] - 1:.0%}" for x in (2, 2.5, 3, 3.5, 4)])
    st.dataframe(pd.DataFrame(rows, columns=["", "2x", "2.5x", "3x", "3.5x", "4x"]), hide_index=True, width="stretch")

    st.subheader("Historical returns")
    h = rates[rates["date"] >= cfg.WINDOW_START].copy()
    h["date"] = pd.to_datetime(h["date"])
    fig2 = go.Figure()
    for x, color, width in ((2.5, GREY, 1.5), (3.0, ACCENT, 2.5), (3.5, "#1E3A8A", 1.5)):
        s = h.apply(lambda row: c21_net(x, row), axis=1).rolling(7, min_periods=1).mean()
        fig2.add_trace(go.Scatter(x=h["date"], y=s, name=f"{x}x", line=dict(color=color, width=width)))
    fig2.add_hline(y=cfg.HURDLE_APR, line_dash="dash", line_color=GREY)
    st.plotly_chart(event_lines(apply_layout(fig2, title="Net APR, 7-day average (%)", height=380)), width="stretch")

    st.subheader("Yield decomposition over time")
    all_ = rates.copy()
    all_["date"] = pd.to_datetime(all_["date"])
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=all_["date"], y=(all_["usd1_supply_base"] - all_["usd1_borrow"]).rolling(7, min_periods=1).mean(),
                              name="USD1 supply minus borrow (base)", line=dict(color=RED)))
    fig3.add_trace(go.Scatter(x=all_["date"], y=all_["usd1_wlfi_reward"].rolling(7, min_periods=1).mean(),
                              name="WLFI reward on USD1 supply", line=dict(color=GREEN)))
    fig3.add_trace(go.Scatter(x=all_["date"], y=all_["usdc_wlfi_reward"].rolling(7, min_periods=1).mean(),
                              name="WLFI reward on USDC supply", line=dict(color=ACCENT)))
    st.plotly_chart(event_lines(apply_layout(fig3, title="7-day average, %", height=360)), width="stretch")
    st.caption("Open item: reward value actually claimed against the rate shown, from the pilot wallet.")
