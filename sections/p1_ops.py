"""On hold, USD1 carry: monitoring, operations, team, edge, pre-mortem and sizing."""

import streamlit as st
import pandas as pd

from utils.charts import format_usd, md_usd
from utils.data_loader import load_c21_rates, load_dolomite_snapshot, load_positions, load_wlfi
from utils.strategy import c21_net, expected_shortfall, legs, nearest_large_liquidation, stress_table, window_rates

import project_config as cfg
from utils.blocks import console, rows_usd1
from utils.data_loader import load_c21_rates, load_dolomite_snapshot, load_editorial, load_positions
from utils.strategy import c21_net, stress_table, window_rates
from utils.text import T

FUND_NAV = 35_000_000


def render(embedded=False):
    if not embedded:
        st.markdown('<div class="eyebrow">On hold · USD1 carry</div>', unsafe_allow_html=True)
        st.title("Monitoring, Team and Sizing")
        st.warning(T("s1.hold"))
    st.subheader("Exit triggers")
    st.caption("At the warning level I investigate and prepare the exit. At the action level I act without waiting for a meeting.")
    trig = load_editorial("monitoring_triggers")
    t = trig[trig["proposal"] == "C21"].drop(columns=["proposal"])
    st.dataframe(t.rename(columns=str.title), hide_index=True, width="stretch", height=470)

    st.subheader("Trigger coverage")
    st.markdown(
        "| Triggers | What they watch |\n| --- | --- |\n"
        "| T1, T2, T3 | The WLFI tail. Leverage comes down before large positions get close to liquidation. |\n"
        "| T4, T5 | A pool freeze. Utilization and the largest USDC supplier give the early signs. |\n"
        "| T6, T12 | The yield itself. Rotate when the carry no longer pays for the risk. |\n"
        "| T7 | The WLFI price between claim and sale. |\n"
        "| T8, T9, T11 | The USD1 peg, position health and the oracle. |\n"
        "| T10 | Admin or governance changes on the markets used. |"
    )

    st.subheader("Monitoring tools")
    st.markdown(
        "| Area | Tool |\n| --- | --- |\n"
        "| Dolomite | Subgraph for positions and pool totals, DolomiteMargin reads for rates, indexes and health, polled every 5 minutes |\n"
        "| Prices | Hyperliquid WLFI perpetual, Chainlink USD1, DEX quotes |\n"
        "| Rewards | Merkl API for accrual and claims |\n"
        "| Events | Contract event subscriptions for parameter changes, plus news and governance feeds |\n"
        "| Alerts | Telegram and email for warnings, a pager for actions |"
    )

    st.subheader("Runbook")
    st.markdown(
        "1. On a warning, check the cause, confirm the data and prepare the unwind transactions.\n"
        "2. If T1 reaches its action level, cut to 1.5x by repaying USD1 in A with USD1 moved from B, then USDC in B.\n"
        "3. If T2 or T5 reaches its action level, net both positions to 1x on Dolomite's ledger and withdraw equity as USDC frees up.\n"
        "4. If T6 reaches its action level, unwind over one to two days and rotate.\n"
        "5. Log each event with the trigger, time, size, cost and outcome."
    )

    st.subheader("Review cadence")
    st.markdown(
        "| How often | What |\n| --- | --- |\n"
        "| Daily | Trigger review, position health, WLFI claims |\n"
        "| Weekly | WLFI sale, reward rate against the base spread, change in WLFI-backed debt, stress refresh |\n"
        "| Monthly | Net APR against the hurdle, re-underwriting |\n"
        "| Quarterly | Full review of the thesis and limits |"
    )

    st.subheader("Monitoring console")
    st.caption(f"This is a mock-up. Each check runs on the {cfg.PIN_LABEL} snapshot.")
    console(rows_usd1())
    rates, pos, snap = load_c21_rates(), load_positions(), load_dolomite_snapshot()
    if rates.empty or pos.empty or snap.empty:
        st.info("Data missing.")
        return
    base = c21_net(cfg.C21_LEVERAGE, {**window_rates(rates, 30), "usd1_wlfi_reward": 0, "usdc_wlfi_reward": 0})
    share = pos["usd1_debt_usd"].sum() / snap.set_index("symbol").loc["USD1", "borrow_usd"]
    t = stress_table(pos, snap, cfg.C21_LEVERAGE, cfg.EQUITY, [-0.9]).iloc[0]
    fmt = {"wl_share": f"{share:.0%}", "base_only": f"{base:+.1f}%", "loss90": f"{t['our_loss_pct']:.0%}",
           "loss90_net": f"{t['our_loss_netted_pct']:.0%}"}

    st.subheader("Team support")
    st.markdown(T("s1.team"))
    st.subheader("Opportunity rationale")
    st.markdown(T("s1.why", **fmt))
    st.subheader("Pre-mortem")
    st.markdown(T("s1.premortem", **fmt))

    st.subheader("Sizing")
    lb, mp, mps, shock = fund_limits(stress=True)
    render_usd1(lb, mp, mps, shock)


def fund_limits(stress=False):
    st.subheader("Fund limits")
    cols = st.columns(4 if stress else 3)
    loss_budget = cols[0].number_input("Stressed-loss budget, % of NAV", 0.1, 5.0, 0.5, 0.1) / 100
    max_protocol = cols[1].number_input("Max % NAV per protocol", 1.0, 30.0, 8.0, 1.0) / 100
    max_pool_share = cols[2].number_input("Max share of a pool", 0.5, 20.0, 2.0, 0.5) / 100
    stress_shock = (cols[3].selectbox("Stress scenario, WLFI move", [-0.7, -0.8, -0.9, -1.0], index=1, format_func=lambda x: f"{x:.0%}")
                    if stress else -0.8)
    return loss_budget, max_protocol, max_pool_share, stress_shock


def render_usd1(loss_budget, max_protocol, max_pool_share, stress_shock):
    rates, wlfi, pos, snap = load_c21_rates(), load_wlfi(), load_positions(), load_dolomite_snapshot()
    if rates.empty or snap.empty:
        st.info("Data missing.")
        return
    c1, c2, c3 = st.columns(3)
    L = c1.slider("Leverage (total collateral / equity)", 1.0, 4.0, cfg.C21_LEVERAGE, 0.1)
    window = c2.selectbox("Rates", ["Last 30 days", "Last 90 days", "Since rewards began"], index=0)
    netted = c3.toggle("Assume the position is netted to 1x before bad debt lands", value=False)
    days = {"Last 30 days": 30, "Last 90 days": 90, "Since rewards began": len(rates[rates["date"] >= cfg.WINDOW_START])}[window]
    r = window_rates(rates, days)
    a, d1, d2, h = legs(L)
    net = c21_net(L, r)
    s = stress_table(pos, snap, L, 1.0, [stress_shock]).iloc[0]
    loss_pct = s["our_loss_netted_pct"] if netted else s["our_loss_pct"]
    es = expected_shortfall(wlfi, pos, snap, L)

    usd1 = snap.set_index("symbol").loc["USD1"]
    usdc = snap.set_index("symbol").loc["USDC"]
    cap_capacity = (usd1["supply_usd"] - usd1["borrow_usd"]) * 0.10 / max(d1, 1e-9)   # use at most 10% of free USD1
    cap_loss = FUND_NAV * loss_budget / loss_pct if loss_pct > 0 else float("inf")
    cap_protocol = FUND_NAV * max_protocol
    cap_pool = min(usd1["supply_usd"] * max_pool_share / max(d1, 1e-9), usdc["supply_usd"] * max_pool_share / a)
    size = min(cap_capacity, cap_loss, cap_protocol, cap_pool)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Net APR", f"{net:.1f}%", delta=f"{net - cfg.HURDLE_APR:+.1f} vs hurdle")
    m2.metric("Health, both positions", f"{h:.2f}" if h != float("inf") else "n/a")
    m3.metric(f"Loss at WLFI {stress_shock:.0%}", f"{loss_pct:.1%} of equity")
    m4.metric("30-day expected shortfall (95%)", f"{es['es']:.2%}")

    st.subheader("Size limits")
    lim = pd.DataFrame([
        ["Capacity: at most 10% of free USD1 borrow", cap_capacity],
        [f"Loss budget: {loss_budget:.1%} of NAV / loss at {stress_shock:.0%}", cap_loss],
        [f"Protocol limit: {max_protocol:.0%} of NAV on Dolomite", cap_protocol],
        [f"Pool share: {max_pool_share:.1%} of the USD1 or USDC pool", cap_pool],
    ], columns=["limit", "max equity"])
    lim["max equity"] = lim["max equity"].apply(format_usd)
    st.dataframe(lim, hide_index=True, width="stretch")
    verdict = "clears" if size >= cfg.EQUITY and net >= cfg.HURDLE_APR else "does not clear"
    st.info(f"**Recommended size: {md_usd(size)}** (the smallest limit). At {L:.1f}x this {verdict} the target "
            f"of \\$1.5M at {cfg.HURDLE_APR:.0f}% net.")

    st.subheader("Position legs per \\$1 of equity")
    st.dataframe(pd.DataFrame({"leg": ["USDC supplied (A)", "USD1 borrowed (A) = USD1 supplied (B)", "USDC borrowed (B)"],
                               "per $1": [f"{a:.2f}", f"{d1:.2f}", f"{d2:.2f}"],
                               "at recommended size": [format_usd(a * size), format_usd(d1 * size), format_usd(d2 * size)]}),
                 hide_index=True, width="stretch")



