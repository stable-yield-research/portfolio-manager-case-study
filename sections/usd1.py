"""On hold: USD1 carry on Dolomite. One page: overview and the full technical analysis in tabs."""

import streamlit as st

import project_config as cfg
from sections import p1_audit_liquidity, p1_ops, p1_risk, p1_yield
from utils.data_loader import load_c21_rates, load_positions, load_wlfi
from utils.strategy import c21_guardrail_backtest, c21_net, nearest_large_liquidation, window_rates
from utils.text import T


def render():
    st.markdown('<div class="eyebrow">On hold · strategy 2</div>', unsafe_allow_html=True)
    st.title("USD1 Carry on Dolomite")
    rates, wlfi, pos = load_c21_rates(), load_wlfi(), load_positions()
    if rates.empty or wlfi.empty or pos.empty:
        st.info("Data missing.")
        return
    _, liq = nearest_large_liquidation(pos, float(wlfi["close"].iloc[-1]))
    bt, _ = c21_guardrail_backtest(rates, wlfi, cfg.C21_LEVERAGE, liq, cfg.WINDOW_START)
    c1, c2, c3 = st.columns(3)
    c1.metric("Net at 3x since rewards began", f"{bt['net_guarded'].mean():.1f}%")
    c2.metric("Net at 3x, last 30 days", f"{c21_net(cfg.C21_LEVERAGE, window_rates(rates, 30)):.1f}%")
    c3.metric("Status", "On hold")
    st.markdown(T("s1.overview", usd1_window=f"{bt['net_guarded'].mean():.1f}%"))
    st.warning(T("s1.hold"))
    tabs = st.tabs(["Structure and yield", "Track record and liquidity", "Risk, WLFI stress and controls", "Monitoring, team and sizing"])
    with tabs[0]:
        p1_yield.render(embedded=True)
    with tabs[1]:
        p1_audit_liquidity.render(embedded=True)
    with tabs[2]:
        p1_risk.render(embedded=True)
    with tabs[3]:
        p1_ops.render(embedded=True)
    st.markdown(T("s1.method"))
