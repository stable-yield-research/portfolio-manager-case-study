"""Current Finance carry: track record, capacity, entry and exit, costs."""

import pandas as pd
import streamlit as st

from utils.refresh import refresh_control

import project_config as cfg
from utils.charts import format_usd
from utils.data_loader import load_current, load_current_snapshot
from utils.strategy import cur_costs, cur_daily, cur_legs, monthly_apr
from utils.text import T


def render():
    st.markdown('<div class="eyebrow">Current Finance carry · technical analysis</div>', unsafe_allow_html=True)
    st.title("Track Record, Capacity and Costs")
    refresh_control("record")
    cur, snap = load_current(), load_current_snapshot()
    if cur.empty or snap.empty:
        st.info("Data missing.")
        return
    s = snap.iloc[-1]
    L, E = cfg.CUR_LEVERAGE, cfg.EQUITY / 1e6
    st.subheader("Track record")
    st.markdown(T("cur.record"))
    d = pd.DataFrame({"date": cur["date"], "net": cur_daily(cur, L, E).values})
    m = monthly_apr(d, "net")
    days = d.assign(month=d["date"].astype(str).str[:7]).groupby("month").size()
    m = m[m["month"].map(lambda x: days.get(x, 0) >= 14)].reset_index(drop=True)
    pools = cur.assign(month=cur["date"].str[:7]).groupby("month")[["c_supply_usd", "s_supply_usd"]].mean().reset_index()
    m = m.merge(pools, on="month")
    st.dataframe(pd.DataFrame({"month": m["month"], f"net at {L:g}x, $1.5M": m["apr"].map(lambda v: f"{v:.1f}%"),
                               "meets 12%": m["apr"].map(lambda v: "yes" if v >= 12 else "no"),
                               "USDC supplied": m["c_supply_usd"].map(lambda v: f"${v:.1f}M"),
                               "USDSUI supplied": m["s_supply_usd"].map(lambda v: f"${v:.1f}M")}), hide_index=True, width="stretch")
    k1, k2, k3 = st.columns(3)
    k1.metric("Net, last 30 days", f"{d['net'].tail(30).mean():.1f}%")
    k2.metric("Net, September", f"{d[d['date'].astype(str).str.startswith('2026-09')]['net'].mean():.1f}%")
    k3.metric("Lowest day, September", f"{d[d['date'].astype(str).str.startswith('2026-09')]['net'].min():.1f}%")

    st.subheader("Capacity")
    e1, e2, a, d1, d2 = cur_legs(L)
    need = {"USDC supply": a * E, "USDC borrow": d2 * E, "USDSUI supply": d1 * E, "USDSUI borrow": d1 * E}
    room = {"USDC supply": s["usdc_supply_cap"] - s["usdc_supplied"], "USDC borrow": s["usdc_borrow_cap"] - s["usdc_borrowed"],
            "USDSUI supply": s["usdsui_supply_cap"] - s["usdsui_supplied"], "USDSUI borrow": s["usdsui_borrow_cap"] - s["usdsui_borrowed"]}
    base = {"USDC supply": s["usdc_supplied"], "USDC borrow": s["usdc_borrowed"], "USDSUI supply": s["usdsui_supplied"],
            "USDSUI borrow": s["usdsui_borrowed"]}
    st.dataframe(pd.DataFrame({"market": list(need), "fund needs": [f"${v:.2f}M" for v in need.values()],
                               "room under cap": [f"${v:.2f}M" for v in room.values()],
                               "fund share after entry": [f"{need[k] / (base[k] + need[k]):.1%}" for k in need]}),
                 hide_index=True, width="stretch")
    st.caption(f"Daily caps, shared by all users: new borrowing \\${s['usdc_daily_borrow_cap']:.1f}M of USDC and \\${s['usdsui_daily_borrow_cap']:.1f}M of USDSUI, "
               f"withdrawals \\${s['usdc_daily_withdraw_cap']:.1f}M of USDC and \\${s['usdsui_daily_withdraw_cap']:.1f}M of USDSUI.")

    st.subheader("Position build")
    st.markdown(T("cur.build"))
    st.subheader("Exit")
    st.markdown(T("cur.exit"))
    st.subheader("Exit capacity")
    st.markdown(T("cur.exit_capacity"))
    st.subheader("Limitations of the exit plan")
    st.markdown(T("cur.exit_limits"))
    st.subheader("Execution costs")
    st.markdown(T("cur.costs"))
    c = cur_costs(s, L, E)
    eq = cfg.EQUITY
    daily = d["net"].tail(30).mean() / 100 / 365 * eq
    st.dataframe(pd.DataFrame([
        ["Leveraged size (Multiply fee base)", format_usd(c["size"]), ""],
        ["Swapped each way at entry", format_usd(c["swap_each_way"]), ""],
        ["Entry in tranches", format_usd(c["entry"]), f"{c['entry'] / eq:.3%} of equity, earned back in {c['entry'] / daily:.1f} days"],
        ["Normal round trip", format_usd(c["round_trip"]), f"{c['round_trip'] / eq:.3%}"],
        ["Fast exit at today's prices", format_usd(c["exit_fast"]), f"{c['exit_fast'] / eq:.3%}"],
        ["Exit provision in the fund's accounts (0.028% x leverage)", format_usd(c["exit_provision"]), f"{c['exit_provision'] / eq:.3%}"],
        ["Stressed exit (0.2% slippage on every swap)", format_usd(c["exit_stress"]), f"{c['exit_stress'] / eq:.3%}. One month's yield is {d['net'].tail(30).mean() / 12:.2f}%"],
    ], columns=["item", "amount", "note"]), hide_index=True, width="stretch")
