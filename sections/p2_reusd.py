"""
reUSD liquidity strategy: structure, yield, depeg behaviour, insurance pool, record, liquidity, risk, monitoring.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import project_config as cfg
from utils.charts import GREY, NAVY, ORANGE, TEAL, apply_layout, format_usd
from utils.data_loader import load_c5, load_editorial, load_resupply_snapshot
from utils.strategy import (C5_RE_SHARE, INTERFACE_BORROW_REWARDS, c5_backtest, c5_inputs, depeg_table, loss_thresholds,
                            interface_reward_scale, monthly_apr)
from utils.text import T
from utils.blocks import admin_table, console, rows_reusd, stablecoin_table

SEV = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}


def render():
    st.markdown('<div class="eyebrow">On hold · strategy 3</div>', unsafe_allow_html=True)
    st.title("reUSD Liquidity on Curve, Funded through Resupply")
    st.warning(T("s2.hold"))
    st.caption(f"Reconstructed from pool, Resupply pair and lending history, as of {cfg.PIN_LABEL}.")
    c5, rs = load_c5(), load_resupply_snapshot()
    if c5.empty or rs.empty:
        st.info("Data missing.")
        return
    snap = rs.iloc[-1]

    s1, s2 = st.columns(2)
    ltv = s1.slider("Share of the deposit borrowed as reUSD", 0.5, 0.9, 0.8, 0.05)
    src = s2.radio("Borrow rewards", [f"Interface level (about {INTERFACE_BORROW_REWARDS:.1f}%)", "Pair history as recorded"],
                   horizontal=True)
    inp = c5_inputs(c5)
    hist_rw = inp.tail(30)["borrow_rewards"].mean()
    scale = interface_reward_scale(c5) if src.startswith("Interface") else 1.0
    h = c5_backtest(c5, cfg.EQUITY, ltv, True, scale)
    u = c5_backtest(c5, cfg.EQUITY, ltv, False)
    ex = h[h["exact"]]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Net yield, last 30 days", f"{h.tail(30)['apr_day'].mean():.1f}%")
    c2.metric("Since structure launched", f"{ex['apr_day'].mean():.1f}%", help=f"{len(ex)} days from {ex['date'].min()}")
    c3.metric("Unhedged LP, last 30 days", f"{u.tail(30)['apr_day'].mean():.1f}%")
    c4.metric("reUSD price", f"{c5['reusd_price'].iloc[-1]:.4f}")

    tabs = st.tabs(["Structure and yield", "Depeg and exit rules", "Insurance pool and record", "Liquidity", "Risk",
                    "Monitoring", "Sourcing and pre-mortem", "Stablecoins and controls"])
    with tabs[0]:
        st.markdown(T("s2.structure", re_share=f"{C5_RE_SHARE:.0%}"))
        st.markdown(T("s2.lp_yield"))
        st.markdown(T("s2.variants"))
        half = h.copy()
        half["apr_day"] = (h["apr_day"] + u["apr_day"]) / 2
        since = h.index[h["exact"]].min()
        var = []
        for name, d in (("Plain LP (buy reUSD and scrvUSD)", u), ("Funded through Resupply", h), ("Half and half", half)):
            mm = monthly_apr(d, "apr_day")
            var.append([name, f"{d.tail(30)['apr_day'].mean():.1f}%", f"{d.loc[since:, 'apr_day'].mean():.1f}%",
                        f"{d['apr_day'].mean():.1f}%", f"{int((mm['apr'] >= cfg.HURDLE_APR).sum())} of {len(mm)}"])
        st.dataframe(pd.DataFrame(var, columns=["variant", "last 30 days", "since 31 Jul", "last 12 months", "months at 12%+"]),
                     hide_index=True, width="stretch")
        st.markdown(T("s2.venues"))
        last = h.tail(30)
        comp = pd.DataFrame({"source": ["LP fees and CRV (Stake DAO, after dilution)", "crvUSD lending", "Borrow rewards (CRV, RSUP, CVX)",
                                        "reUSD borrow cost", "reUSD price effect"],
                             "apr": [last[c].mean() * 365 / cfg.EQUITY * 100 for c in
                                     ("inc_lp", "inc_collateral", "inc_borrow_rewards", "inc_borrow_cost", "inc_price")]})
        fig = go.Figure(go.Bar(x=comp["source"], y=comp["apr"], marker_color=[NAVY, NAVY, TEAL, GREY, GREY]))
        st.plotly_chart(apply_layout(fig, title=f"Yield by source, last 30 days, % of equity (net {comp['apr'].sum():.1f}%)",
                                     height=320, show_legend=False), width="stretch")
        st.markdown(T("s2.rewards_note", hist_rewards=f"{hist_rw:.2f}%"))
        m = monthly_apr(h, "apr_day").merge(monthly_apr(u, "apr_day").rename(columns={"apr": "unhedged"}), on="month")
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=m["month"], y=m["apr"], name="funded with borrowed reUSD", marker_color=NAVY))
        fig2.add_trace(go.Bar(x=m["month"], y=m["unhedged"], name="plain LP", marker_color=GREY))
        fig2.add_hline(y=cfg.HURDLE_APR, line_dash="dash", line_color=GREY)
        st.plotly_chart(apply_layout(fig2, title="Monthly net yield at $1.5M, % a year (before Aug: closest proxy pair)",
                                     height=340), width="stretch")

    with tabs[1]:
        st.markdown(T("s2.depeg"))
        pool = {"A": snap["A"], "reusd_balance": snap["reusd_balance"], "scrvusd_balance": snap["scrvusd_balance"],
                "scrvusd_rate": snap["scrvusd_rate"]}
        lp = cfg.EQUITY * ltv
        full, p0 = depeg_table(pool, lp, 1.0)
        neut, _ = depeg_table(pool, lp, C5_RE_SHARE)
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=full["price"], y=full["funded_pnl"] / cfg.EQUITY * 100, name="funded structure (all reUSD borrowed)",
                                  line=dict(color=NAVY, width=2.5)))
        fig3.add_trace(go.Scatter(x=neut["price"], y=neut["funded_pnl"] / cfg.EQUITY * 100, name=f"borrow only the pool's reUSD share ({C5_RE_SHARE:.0%})",
                                  line=dict(color=TEAL)))
        fig3.add_trace(go.Scatter(x=full["price"], y=full["plain_lp_pnl"] / cfg.EQUITY * 100, name="plain LP, no borrowing",
                                  line=dict(color=GREY, dash="dot")))
        fig3.add_vline(x=p0, line_dash="dash", line_color=GREY, annotation_text=f"today {p0:.3f}")
        fig3.update_xaxes(autorange="reversed", title_text="reUSD price")
        fig3.update_yaxes(title_text="P&L, % of equity")
        st.plotly_chart(apply_layout(fig3, title=f"Position value if reUSD moves (StableSwap A={int(snap['A'])}, \\$1.5M equity)",
                                     height=360), width="stretch")
        show = full.assign(neutral=neut["funded_pnl"])
        st.dataframe(pd.DataFrame({
            "reUSD price": show["price"].map(lambda v: f"{v:.3f}"),
            "reUSD share of pool": show["reusd_share"].map(lambda v: f"{v:.0%}"),
            "pool IL vs holding": show["il_vs_hold"].map(lambda v: f"{v:.2%}"),
            "reUSD in the LP": show["lp_reusd_tokens"].map(lambda v: f"{v:,.0f}"),
            "funded structure": show["funded_pnl"].apply(format_usd),
            "share-neutral borrow": show["neutral"].apply(format_usd),
            "plain LP": show["plain_lp_pnl"].apply(format_usd),
        }), hide_index=True, width="stretch")
        st.markdown(T("s2.il"))
        st.caption("reUSD price at which each setup has lost 0.1%, 0.2% and 0.3% of equity.")
        at_par = {"A": snap["A"], "reusd_balance": 7.13e6, "scrvusd_balance": 7.13e6 / snap["scrvusd_rate"],
                  "scrvusd_rate": snap["scrvusd_rate"]}
        rows = []
        for case, pl in (("Entered today (pool 76% reUSD, price 0.990)", pool), ("Entered after a repeg (balanced pool, price 1.00)", at_par)):
            for label, bsh in (("plain LP", 0.0), ("borrow the pool's reUSD share", None), ("borrow all (funded structure)", 1.0)):
                b = bsh if bsh is not None else pl["reusd_balance"] / (pl["reusd_balance"] + pl["scrvusd_balance"] * pl["scrvusd_rate"])
                _, th = loss_thresholds(pl, lp, b, cfg.EQUITY)
                def fmt_t(t):
                    if t["up"] and t["down"]:
                        return f"above {t['up']} or below {t['down']}"
                    return f"above {t['up']}" if t["up"] else (f"below {t['down']}" if t["down"] else "none")
                rows.append([case, label] + [fmt_t(t) for t in th])
        st.dataframe(pd.DataFrame(rows, columns=["entry", "setup", "loss 0.1%", "loss 0.2%", "loss 0.3%"]), hide_index=True,
                     width="stretch")
        st.markdown(T("s2.exit_rules"))

    with tabs[2]:
        cov = snap["ip_reusd"] / snap["reusd_supply"]
        k1, k2, k3 = st.columns(3)
        k1.metric("Insurance pool", f"{snap['ip_reusd'] / 1e6:.1f}M reUSD")
        k2.metric("reUSD supply", f"{snap['reusd_supply'] / 1e6:.1f}M")
        k3.metric("Coverage", f"{cov:.1%}", help=f"Before the 2025 exploit: {snap['ip_pre_exploit'] / 1e6:.1f}M reUSD")
        st.markdown(T("s2.insurance", ip_reusd=f"{snap['ip_reusd'] / 1e6:.1f}M", reusd_supply=f"{snap['reusd_supply'] / 1e6:.1f}M",
                      ip_cov=f"{cov:.1%}"))
        st.markdown(T("s2.reputation"))
    with tabs[3]:
        st.markdown(T("s2.audit"))
        st.dataframe(pd.DataFrame([
            ["Curve pool TVL", format_usd(c5["pool_tvl"].iloc[-1])],
            ["LP size at $1.5M equity", format_usd(cfg.EQUITY * ltv)],
            ["Share of the pool", f"{cfg.EQUITY * ltv / c5['pool_tvl'].iloc[-1]:.1%}"],
            ["reUSD borrowed by all users in this pair", format_usd(inp['v2_debt'].dropna().iloc[-1])],
            ["Pool fee", f"{snap['fee']:.2%}, up to {snap['offpeg_fee_multiplier']:.0f}x when off peg"],
        ], columns=["item", "value"]), hide_index=True, width="stretch")
        st.markdown(T("s2.exit"))
        st.caption("Open item: Curve withdrawal quotes at \\$0.5M, \\$1M and \\$1.2M.")
    with tabs[4]:
        r = load_editorial("risk_map_c5")
        if not r.empty:
            r["impact"] = r["impact"].map(lambda v: f"{SEV.get(v, '')} {v}")
            r["likelihood"] = r["likelihood"].map(lambda v: f"{SEV.get(v, '')} {v}")
            st.dataframe(r.rename(columns=str.title), hide_index=True, width="stretch")
        st.caption("Open item: loss budget for a Resupply incident on the collateral side.")
    with tabs[5]:
        t = load_editorial("monitoring_triggers")
        if not t.empty:
            st.dataframe(t[t["proposal"] == "C5"].drop(columns=["proposal"]).rename(columns=str.title), hide_index=True,
                         width="stretch")
        console(rows_reusd())
    with tabs[6]:
        st.markdown(T("s2.found"))
        st.markdown(T("s2.ic"))
    with tabs[7]:
        stablecoin_table(["reUSD", "scrvUSD"])
        st.markdown(T("stable.reusd", ip_cov=f"{snap['ip_reusd'] / snap['reusd_supply']:.1%}"))
        st.markdown(T("stable.scrvusd"))
        st.markdown(T("s2.controls"))
        admin_table(["reUSD liquidity"])
        st.markdown(T("durability.crv"))
        st.markdown(T("s2.method"))
