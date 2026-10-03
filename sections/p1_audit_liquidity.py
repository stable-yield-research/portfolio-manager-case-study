"""
USD1 carry: track record and liquidity.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import project_config as cfg
from utils.charts import ACCENT, GREY, ORANGE, apply_layout, event_lines, format_usd, md_usd
from utils.data_loader import load_c21_rates, load_dolomite_snapshot, load_positions, load_wlfi
from utils.strategy import c21_guardrail_backtest, legs, monthly_apr, nearest_large_liquidation
from utils.text import T


def render(embedded=False):
    if not embedded:
        st.markdown('<div class="eyebrow">On hold · USD1 carry</div>', unsafe_allow_html=True)
        st.title("USD1 Carry · Track Record and Liquidity")
        st.warning(T("s1.hold"))
    st.caption(f"Reconstructed from public on-chain data, as of {cfg.PIN_LABEL}.")
    rates, wlfi, snap = load_c21_rates(), load_wlfi(), load_dolomite_snapshot()
    if rates.empty or wlfi.empty or snap.empty:
        st.info("Data missing.")
        return

    st.subheader("Track record")
    st.markdown(T("s1.audit"))
    st.dataframe(pd.DataFrame([
        ["Supply and borrow interest", "Dolomite interest indexes, Ethereum subgraph (Goldsky), USD1 market 1, USDC market 2",
         "Index ratio over each day: exact growth a lender or borrower received"],
        ["Live rate cross-check", "DolomiteMargin 0x003C...2b97D: getMarketInterestRate, getMarketTotalPar, getMarketCurrentIndex",
         "Matches the subgraph to the second decimal"],
        ["WLFI rewards", "DefiLlama apyReward for the Dolomite USD1 and USDC pools, and the Merkl campaign page",
         "Paid since 22 Apr 2026 with no gaps"],
        ["WLFI price", "Hyperliquid WLFI perp daily candles", "Used for guardrails and stress"],
        ["Live pilot", "Two-position pilot, $100, 29 Sep", "Confirmed full USD1 supply earns WLFI"],
    ], columns=["what", "source", "note"]), hide_index=True, width="stretch")

    L = cfg.C21_LEVERAGE
    _, liq = nearest_large_liquidation(load_positions(), float(wlfi["close"].iloc[-1]))
    bt, events = c21_guardrail_backtest(rates, wlfi, L, liq, cfg.WINDOW_START)
    bt["date"] = pd.to_datetime(bt["date"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Net APR with guardrails", f"{bt['net_guarded'].mean():.1f}%", help="PINNED. 22 Apr to 29 Sep, 3x.")
    c2.metric("Without guardrails", f"{bt['net_plain'].mean():.1f}%")
    c3.metric("Days at reduced leverage", int((bt["leverage"] < L).sum()))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bt["date"], y=bt["net_plain"].rolling(7, min_periods=1).mean(), name="3x, no guardrails",
                             line=dict(color=GREY)))
    fig.add_trace(go.Scatter(x=bt["date"], y=bt["net_guarded"].rolling(7, min_periods=1).mean(), name="3x with guardrails",
                             line=dict(color=ACCENT, width=2.5)))
    fig.add_hline(y=cfg.HURDLE_APR, line_dash="dash", line_color=GREY)
    st.plotly_chart(event_lines(apply_layout(fig, title="Reconstructed net APR, 7-day average (%)", height=360)), width="stretch")

    m = monthly_apr(bt, "net_guarded").merge(monthly_apr(bt, "net_plain").rename(columns={"apr": "plain"}), on="month")
    m["guarded"] = m["apr"].map(lambda v: f"{v:.1f}%")
    m["plain"] = m["plain"].map(lambda v: f"{v:.1f}%")
    m["meets 12%"] = m["apr"].map(lambda v: "yes" if v >= cfg.HURDLE_APR else "no")
    st.dataframe(m[["month", "guarded", "plain", "meets 12%"]], hide_index=True, width="stretch")
    if events:
        st.subheader("Guardrail events")
        st.dataframe(pd.DataFrame(events, columns=["date", "action", "reason"]), hide_index=True, width="stretch")

    st.subheader("Live pilot")
    st.dataframe(pd.DataFrame([
        ["A", "USDC $196.21", "USD1 $154.72", "1.14"],
        ["B", "USD1 $154.72", "USDC $96.22", "1.44"],
    ], columns=["position", "collateral", "debt", "health"]), hide_index=True, width="stretch")
    st.caption("Open item: reward accrual from the pilot wallet, and a wallet-level P&L export.")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.subheader("Entry and exit")
    s = snap.set_index("symbol")
    free1 = s.loc["USD1", "supply_usd"] - s.loc["USD1", "borrow_usd"]
    freec = s.loc["USDC", "supply_usd"] - s.loc["USDC", "borrow_usd"]
    a, d1, d2, _ = legs(L)
    eq = cfg.EQUITY
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Free USD1 to borrow", format_usd(free1), help=f"CURRENT, utilization {s.loc['USD1', 'utilization']:.0%}")
    k2.metric("Free USDC", format_usd(freec), help=f"CURRENT, utilization {s.loc['USDC', 'utilization']:.0%}")
    k3.metric("Fund USD1 borrow at 3x", format_usd(d1 * eq), help=f"{d1 * eq / free1:.1%} of free USD1")
    k4.metric("Equity to withdraw on exit", format_usd(eq), help=f"{eq / freec:.1%} of free USDC today")

    st.markdown(T("s1.entry"))
    st.dataframe(pd.DataFrame([
        ["Normal", "Repay and withdraw in reverse order", "Hours", "Gas only"],
        ["Stressed (utilization 90% to 97%)", "Net USD1 supply against USD1 debt between the two positions, then withdraw equity as USDC frees up",
         "Hours to days", "Gas, plus a higher borrow rate while waiting"],
        ["Frozen pool (100% utilization, as in Apr 2026)", "Net internally first, so only equity waits for repayments or new supply",
         "Days", "Carry keeps accruing, with exposure to a shortfall on equity only"],
        ["WLFI crash with bad debt", "Net to 1x at trigger T2, before insolvency levels", "Hours if triggers fire first",
         "Share of any shortfall on the remaining USDC"],
    ], columns=["scenario", "action", "time", "cost"]), hide_index=True, width="stretch")
    st.caption(T("s1.liquidity_note"))
