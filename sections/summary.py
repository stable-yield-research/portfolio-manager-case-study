"""
Investment Summary: the one-minute read. Prose from content/report.md; numbers computed from data/.
"""

import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.refresh import refresh_control

import project_config as cfg
from utils.charts import GREY, NAVY, TEAL, apply_layout, format_usd
from utils.data_loader import (latest_data_date, load_c21_rates, load_current, load_current_snapshot, load_dolomite_snapshot,
                               load_editorial, load_positions, load_wlfi)
from utils.strategy import (c21_guardrail_backtest, cur_components, cur_costs, cur_daily, cur_legs, cur_liq_levels, monthly_apr,
                            nearest_large_liquidation)
from utils.text import T


@st.cache_data(show_spinner=False)
def numbers():
    cur, snap = load_current(), load_current_snapshot().iloc[-1]
    L, E = cfg.CUR_LEVERAGE, cfg.EQUITY / 1e6
    d = pd.DataFrame({"date": cur["date"], "net": cur_daily(cur, L, E).values, "zero": cur_daily(cur, L, 0.0).values})
    m = monthly_apr(d, "net")
    days = d.assign(month=d["date"].astype(str).str[:7]).groupby("month").size()
    m = m[m["month"].map(lambda x: days.get(x, 0) >= 14)].reset_index(drop=True)
    sep = d[d["date"].astype(str).str.startswith("2026-09")]
    c = cur_costs(snap, L, E)
    up, dn = cur_liq_levels(L)
    e1, e2, a, d1, d2 = cur_legs(L)
    comp = cur_components(cur.tail(30).mean(numeric_only=True).to_dict(), L, E)
    by_month = dict(zip(m["month"], m["apr"]))
    return {"comp": comp, "aug": by_month.get("2026-08"), "sep_m": by_month.get("2026-09"), "net30": d["net"].tail(30).mean(), "sep": sep["net"].mean(), "sep_min": sep["net"].min(),
            "months": m, "months_ok": int((m["apr"] >= 12).sum()), "zero_avg": d["zero"].mean(),
            "costs": c, "up": up, "dn": dn, "share_usdsui": d1 * E / (snap["usdsui_supplied"] + d1 * E)}


def render():
    n = numbers()
    eq = cfg.EQUITY
    c = n["costs"]
    cur_after = n["sep"] - c["round_trip"] / eq * 100
    fmt = {"liq_up_plain": f"{(n['up'] - 1):.0%}", "liq_dn_plain": f"{(1 - n['dn']):.0%}", "pin_label": cfg.PIN_LABEL, "data_date": latest_data_date(), "n_screened": int((~load_editorial("candidates")["status"].fillna("").str.startswith("On hold")).sum()),
           "liq_up": f"{(n['up'] - 1):.0%}", "liq_dn": f"{(1 - n['dn']):.0%}",
           "exit_prov": f"{c['exit_provision'] / eq:.2%} of the money invested", "exit_stress": f"{c['exit_stress'] / eq:.2%}",
           "cur_sep": f"{cur_after:.1f}%"}

    st.markdown('<div class="eyebrow">Investment memorandum</div>', unsafe_allow_html=True)
    st.title(T("report.title"))
    refresh_control("summary")
    st.caption(T("report.subtitle", **fmt))
    lead = T("summary.lead", **fmt).replace(chr(92) + "$", "$")
    lead_html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", lead).replace("\n\n", "<br><br>")
    st.markdown(f'<div class="panel"><div class="lead">{lead_html}</div></div>', unsafe_allow_html=True)
    st.markdown(T("summary.positioning", **fmt))

    st.subheader("Strategy")
    st.markdown(T("summary.s1.oneliner"))
    a, b, c1, d = st.columns(4)
    a.metric("Return, September", f"{n['sep']:.1f}%", help="At $1.5M and 3.5x, before costs. Lowest day %.1f%%." % n["sep_min"])
    b.metric("Return after costs, one year", f"{cur_after:.1f}%", help=f"Round trip {format_usd(c['round_trip'])}.")
    c1.metric("USDSUI move before forced sale", f"+{(n['up'] - 1):.0%} / -{(1 - n['dn']):.0%}", help="Move in USDSUI against USDC that would liquidate the first / second position.")
    d.metric("Entry cost, earned back in", f"{c['entry'] / (n['net30'] / 100 / 365 * eq):.1f} days", help=f"{format_usd(c['entry'])} entry in tranches.")

    st.subheader("Assessment")
    st.markdown(T("summary.take", **fmt))

    st.subheader("Returns")
    m = n["months"]
    fig = go.Figure(go.Bar(x=m["month"], y=m["apr"], marker_color=[NAVY if v >= 12 else GREY for v in m["apr"]],
                           name="net at $1.5M"))
    fig.add_hline(y=cfg.HURDLE_APR, line_dash="dash", line_color=GREY, annotation_text="12%")
    st.plotly_chart(apply_layout(fig, title=f"Monthly return at {cfg.CUR_LEVERAGE:g} times leverage and $1.5M", height=300, show_legend=False),
                    width="stretch")
    st.caption(T("summary.returns_note"))
    sc = pd.DataFrame([
        ["Return of 12% or more after costs", f"{cur_after:.1f}% at $1.5M in September conditions"],
        ["Held for at least a month", "Above 12% at $1.5M in August and September, and every month since May at small size"],
        ["Takes $1.5M without falling below 12%", f"Within all of Current Finance's limits, about {n['share_usdsui']:.0%} of the USDSUI pool"],
        ["Can be exited at full size", f"Exit in batches over about two days, with costs set aside at {c['exit_provision'] / eq:.2%} of the money invested"],
        ["Income from on-chain lending and paid rewards", "Lending spread and SUI rewards, claimable at any time"],
        ["No reliance on token prices", "The USDSUI owed equals the USDSUI held, and SUI is sold daily"],
        ["Every part of the return can be traced", "Hourly rates and reward rates from Current Finance's own data"],
        ["Protocol maturity", "Live since March 2026, which is the main open point"],
    ], columns=["Investment criterion", "Current Finance carry"])
    st.dataframe(sc, hide_index=True, width="stretch")

    st.subheader("Risks")
    st.markdown(T("summary.risk", **fmt))
    st.subheader("Execution")
    st.markdown(T("summary.run", **fmt))
    st.subheader("Opportunity rationale")
    st.markdown(T("summary.why", **fmt))
    st.subheader("Alternatives")
    st.markdown(T("summary.alternatives", **fmt))
    st.markdown(T("summary.hold_box"))
    st.subheader("Conclusion")
    st.markdown(T("summary.verdict", **fmt))

    comp = n["comp"]
    lend = comp["USDC lending (base)"] + comp["USDSUI lending (base)"]
    rew = comp["SUI rewards on USDC"] + comp["SUI rewards on USDSUI"]
    bor = comp["USDSUI borrow cost"] + comp["USDC borrow cost"]
    sfmt = dict(fmt, aug=f"{n['aug']:.1f}%", sep=f"{n['sep_m']:.1f}%", entry=f"\\${c['entry']:,.0f}",
                lend=f"{lend:.1f}%", rew=f"{rew:.1f}%", borrow=f"{bor:.1f}%", net=f"{lend + rew + bor:.1f}%")
    st.subheader("Case study scope")
    st.markdown(T("scope.intro"))
    items = [("01", "Sourcing", "sourcing"), ("02", "Auditability", "current-record"), ("03", "Liquidity", "current-record"),
             ("04", "Yield decomposition", "current-yield"), ("05", "Risk map", "current-controls-matrix"),
             ("06", "Monitoring", "current-ops"), ("07", "Team support", "current-ops"), ("08", "Sanity check", "current-ops"),
             ("09", "Pre-mortem", "current-ops")]
    rows = ["| | Item | Answer | Section |", "| --- | --- | --- | --- |"]
    for num, name, url in items:
        rows.append(f"| {num} | {name} | {T('scope.' + num, **sfmt)} | [open]({url}) |")
    st.markdown("\n".join(rows))
    st.caption(T("report.disclosure"))
