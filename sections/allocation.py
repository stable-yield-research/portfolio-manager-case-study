"""
Allocation Dashboard. Size = the smallest of: capacity, loss budget / stressed loss, and each concentration limit.
"""

import pandas as pd
import streamlit as st
from utils.text import T

from utils.refresh import refresh_control

import project_config as cfg
from utils.charts import format_usd, md_usd
from utils.data_loader import latest_data_date, load_current, load_current_snapshot
from utils.strategy import cur_costs, cur_daily, cur_legs, cur_liq_levels

FUND_NAV = 35_000_000


def fund_limits():
    st.subheader("Fund limits")
    cols = st.columns(3)
    loss_budget = cols[0].number_input("Stressed-loss budget, % of NAV", 0.1, 5.0, 0.5, 0.1) / 100
    max_protocol = cols[1].number_input("Max % NAV per protocol", 1.0, 30.0, 8.0, 1.0) / 100
    max_pool_share = cols[2].number_input("Max share of a pool", 0.5, 20.0, 2.0, 0.5) / 100
    return loss_budget, max_protocol, max_pool_share


def render_current(loss_budget, max_protocol, max_pool_share):
    cur, cs = load_current(), load_current_snapshot()
    if cur.empty or cs.empty:
        st.info("Current Finance data missing.")
    else:
        snap0 = cs.iloc[-1]
        c1, c2, c3 = st.columns(3)
        Lc = c1.slider("Leverage of each vault", 2.0, 4.8, cfg.CUR_LEVERAGE, 0.5, key="curL")
        Ec = c2.number_input("Equity, $M", 0.25, 5.0, cfg.EQUITY / 1e6, 0.25, key="curE")
        win = c3.selectbox("Rates", ["September", "Last 30 days", "Since rewards began"], key="curW")
        sub = cur[cur["date"].astype(str).str.startswith("2026-09")] if win == "September" else (cur.tail(30) if win == "Last 30 days" else cur)
        net = cur_daily(sub, Lc, Ec).mean()
        costs = cur_costs(snap0, Lc, Ec)
        up, dn = cur_liq_levels(Lc)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Net yield before costs", f"{net:.1f}%", delta=f"{net - cfg.HURDLE_APR:+.1f} vs hurdle")
        m2.metric("After a round trip, 12 months", f"{net - costs['round_trip'] / (Ec * 1e6) * 100:.1f}%")
        m3.metric("Liquidation at USDSUI/USDC", f"{dn:.3f} / {up:.3f}")
        m4.metric("Distance vs widest USDSUI move", f"{min(up - 1, 1 - dn) / 0.013:.0f}x", help="USDSUI's widest recorded moves: +1.30% / -0.63%.")
        e1, e2, a, d1, d2 = cur_legs(Lc)
        room_borrow = snap0["usdsui_borrow_cap"] - snap0["usdsui_borrowed"]
        room_usdc_b = snap0["usdc_borrow_cap"] - snap0["usdc_borrowed"]
        cap_eq = min(room_borrow / d1, room_usdc_b / d2) * 1e6
        pool_eq = snap0["usdsui_supplied"] * max_pool_share * 5 / d1 * 1e6
        st.dataframe(pd.DataFrame([
            ["Room under USDSUI and USDC borrow caps", format_usd(cap_eq)],
            [f"Protocol limit: {max_protocol:.0%} of NAV on Current Finance", format_usd(FUND_NAV * max_protocol)],
            [f"Pool share: {max_pool_share * 5:.0%} of the USDSUI market (5x the general pool-share limit)", format_usd(pool_eq)],
        ], columns=["limit", "max equity"]), hide_index=True, width="stretch")
        limit = min(cap_eq, FUND_NAV * max_protocol, pool_eq)
        size = min(cfg.EQUITY, limit)
        room = (f" The limits above would allow up to {md_usd(limit)}." if limit > cfg.EQUITY
                else " The limits above bind before the \\$1.5M allocation.")
        st.info(f"**Recommended size: {md_usd(size)}** at {Lc:g}x, against a \\$1.5M allocation.{room} "
                f"Vault 1 holds {e1:.0%} of equity and vault 2 holds {e2:.0%}.")
        eqd = Ec * 1e6
        st.dataframe(pd.DataFrame([
            ["Entry in tranches", format_usd(costs["entry"]), f"{costs['entry'] / eqd:.3%}"],
            ["Normal round trip", format_usd(costs["round_trip"]), f"{costs['round_trip'] / eqd:.3%}"],
            ["Exit provision (0.028% x leverage)", format_usd(costs["exit_provision"]), f"{costs['exit_provision'] / eqd:.3%}"],
            ["Stressed exit (0.2% on every swap)", format_usd(costs["exit_stress"]), f"{costs['exit_stress'] / eqd:.3%}"],
        ], columns=["cost", "amount", "share of equity"]), hide_index=True, width="stretch")




def render():
    st.markdown('<div class="eyebrow">Current Finance carry · technical analysis</div>', unsafe_allow_html=True)
    st.title("Allocation Tool")
    refresh_control("alloc")
    st.caption(T("alloc.intro", data_date=latest_data_date()))
    lb, mp, mps = fund_limits()
    render_current(lb, mp, mps)
