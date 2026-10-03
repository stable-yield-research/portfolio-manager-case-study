"""
USD1 carry: risk and stress.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import project_config as cfg
from utils.charts import ACCENT, GREY, ORANGE, RED, apply_layout, event_lines, format_usd
from utils.data_loader import load_dolomite_snapshot, load_editorial, load_positions, load_wlfi, load_wlfi_venues
from utils.text import T
from utils.blocks import admin_table, stablecoin_table
from utils.strategy import stress_with_capacity, LARGE_DEBT, expected_shortfall, position_health, stress_table, threshold_shock

SEV = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}


def render(embedded=False):
    if not embedded:
        st.markdown('<div class="eyebrow">On hold · USD1 carry</div>', unsafe_allow_html=True)
        st.title("USD1 Carry · Risk, WLFI Stress and Controls")
        st.warning(T("s1.hold"))
    st.caption(f"Positions and pools as of {cfg.PIN_LABEL}, with WLFI price history since listing.")
    pos, snap, wlfi, rmap = load_positions(), load_dolomite_snapshot(), load_wlfi(), load_editorial("risk_map_c21")
    if pos.empty or snap.empty or wlfi.empty:
        st.info("Data missing.")
        return

    st.subheader("Risk map")
    if not rmap.empty:
        view = rmap.copy()
        view["impact"] = view["impact"].map(lambda v: f"{SEV.get(v, '')} {v}")
        view["likelihood"] = view["likelihood"].map(lambda v: f"{SEV.get(v, '')} {v}")
        st.dataframe(view.rename(columns=str.title), hide_index=True, width="stretch", height=460)
        st.caption("Categories follow the EEA DeFi risk taxonomy with TradFi credit additions. Trigger IDs refer to the monitoring page.")

    st.subheader("WLFI-backed borrowers")
    usd1 = snap.set_index("symbol").loc["USD1"]
    wl = pos["wlfi_collateral_usd"].sum() + pos["wlfics_collateral_usd"].sum()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("WLFI-backed positions", len(pos))
    c2.metric("WLFI collateral", format_usd(wl))
    c3.metric("Their debt", format_usd(pos["usd1_debt_usd"].sum() + pos["usdc_debt_usd"].sum()))
    c4.metric("Share of all USD1 borrowed", f"{pos['usd1_debt_usd'].sum() / usd1['borrow_usd']:.0%}")

    top = pos.assign(debt=pos["usd1_debt_usd"] + pos["usdc_debt_usd"]).sort_values("debt", ascending=False).head(6).copy()
    top["health"] = position_health(top, 0)["health"]
    top["liquidatable at"] = top.apply(lambda r: threshold_shock(r, "liq"), axis=1)
    top["insolvent at"] = top.apply(lambda r: threshold_shock(r, "insolvent"), axis=1)
    show = pd.DataFrame({
        "owner": top["owner"].str[:6] + "..." + top["owner"].str[-4:],
        "WLFI collateral": (top["wlfi_collateral_usd"] + top["wlfics_collateral_usd"]).apply(format_usd),
        "other collateral": top["other_collateral_usd"].apply(format_usd),
        "USD1 debt": top["usd1_debt_usd"].apply(format_usd), "USDC debt": top["usdc_debt_usd"].apply(format_usd),
        "health": top["health"].map(lambda v: f"{v:.2f}"),
        "liquidatable at WLFI": top["liquidatable at"].map(lambda v: "not from WLFI alone" if v is None else f"{v:.0%}"),
        "insolvent at WLFI": top["insolvent at"].map(lambda v: "not from WLFI alone" if v is None else f"{v:.0%}"),
    })
    st.dataframe(show, hide_index=True, width="stretch")

    st.subheader("WLFI stress test")
    L = st.slider("Fund leverage", 1.0, 4.0, cfg.C21_LEVERAGE, 0.5)
    shocks = [-0.5, -0.6, -0.7, -0.75, -0.8, -0.85, -0.9]
    t = stress_table(pos, snap, L, cfg.EQUITY, shocks)
    st.dataframe(pd.DataFrame({
        "WLFI move": t["shock"].map(lambda v: f"{v:.0%}"),
        "positions liquidatable": t["liquidatable"],
        "debt in them": t["debt_liquidatable"].apply(format_usd),
        "shortfall USD1 pool": t["shortfall_usd1"].apply(format_usd),
        "shortfall USDC pool": t["shortfall_usdc"].apply(format_usd),
        "fund loss, not netted": t.apply(lambda r: f"{format_usd(r['our_loss'])} ({r['our_loss_pct']:.1%})", axis=1),
        "fund loss, netted to 1x": t.apply(lambda r: f"{format_usd(r['our_loss_netted'])} ({r['our_loss_netted_pct']:.1%})", axis=1),
    }), hide_index=True, width="stretch")
    st.caption(T("s1.stress_note"))

    st.subheader("Expected shortfall")
    es = expected_shortfall(wlfi, pos, snap, L)
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("30-day windows", es["n"])
    e2.metric("Worst 30-day WLFI move", f"{es['worst_move']:.0%}")
    e3.metric("VaR 95%, loss on equity", f"{es['var']:.2%}")
    e4.metric("Expected shortfall 95%", f"{es['es']:.2%}")
    fig = go.Figure(go.Histogram(x=es["moves"] * 100, nbinsx=40, marker_color=GREY))
    first = t.loc[t["shortfall_usd1"] + t["shortfall_usdc"] > 1e6, "shock"]
    if len(first):
        fig.add_vline(x=first.iloc[0] * 100, line_color=RED, line_dash="dash", annotation_text="bad debt above $1M")
    st.plotly_chart(apply_layout(fig, title="Worst WLFI move within 30 days of each day since listing (%)", height=320,
                                 show_legend=False), width="stretch")
    st.caption("Historical simulation over every 30-day window since August 2025, measured from the close to the lowest low in each "
               "window. WLFI has heavy tails: it fell 70% in a week in October 2025, so the stress table above includes a jump scenario.")

    st.subheader("Distance to liquidation")
    w = wlfi.copy()
    w["date"] = pd.to_datetime(w["date"])
    liq_levels = top.loc[(top["usd1_debt_usd"] + top["usdc_debt_usd"]) >= LARGE_DEBT, "liquidatable at"].dropna()
    fig2 = go.Figure(go.Scatter(x=w["date"], y=w["close"], name="WLFI close", line=dict(color=ACCENT)))
    now = float(w["close"].iloc[-1])
    for v in sorted(liq_levels.unique())[-2:]:
        fig2.add_hline(y=now * (1 + v), line_dash="dot", line_color=ORANGE, annotation_text=f"liquidation at {v:.0%}")
    st.plotly_chart(event_lines(apply_layout(fig2, title="WLFI price (USD) and large-position liquidation levels today",
                                             height=340)), width="stretch")

    st.subheader("Liquidation capacity")
    st.markdown(T("s1.liquidators"))
    v = load_wlfi_venues()
    if not v.empty:
        k1, k2, k3, k4 = st.columns(4)
        spot = v[v["kind"] == "CEX spot"]
        perp = v[v["kind"] == "Perpetual"]
        k1.metric("Spot bids within 2%", format_usd(spot["depth_2pct_usd"].sum()))
        k2.metric("Spot volume, 24h", format_usd(spot["vol24h_usd"].sum()))
        k3.metric("Perpetual open interest", format_usd(perp["open_interest_usd"].sum()))
        k4.metric("Perpetual volume, 24h", format_usd(perp["vol24h_usd"].sum()))
        st.caption("Loss under different liquidation capacities, in USD of WLFI that liquidators can sell during the fall.")
        caps = [(0, "none fill"), (20e6, "$20M: spot and on-chain"), (50e6, "$50M: plus perpetual-hedged arbitrage"),
                (100e6, "$100M: deep, orderly market")]
        rows = []
        for c, label in caps:
            r80 = stress_with_capacity(pos, snap, L, cfg.EQUITY, -0.8, c)
            r90 = stress_with_capacity(pos, snap, L, cfg.EQUITY, -0.9, c)
            rows.append([label, format_usd(r80["shortfall"]), f"{r80['our_loss_pct']:.1%}",
                         format_usd(r90["shortfall"]), f"{r90['our_loss_pct']:.1%}", f"{r90['our_loss_netted_pct']:.1%}"])
        st.dataframe(pd.DataFrame(rows, columns=["capacity", "pool shortfall, WLFI -80%", "fund loss, -80%",
                                                 "pool shortfall, WLFI -90%", "fund loss, -90%", "fund loss, -90%, netted"]),
                     hide_index=True, width="stretch")

    st.subheader("Protocol history")
    st.markdown(T("s1.record"))

    st.subheader("Stablecoin analysis")
    stablecoin_table(["USD1"])
    st.markdown(T("stable.usd1"))
    st.subheader("Admin and upgrade controls")
    st.markdown(T("s1.controls"))
    admin_table(["USD1 carry"])
    st.subheader("Reward durability")
    st.markdown(T("durability.wlfi"))
