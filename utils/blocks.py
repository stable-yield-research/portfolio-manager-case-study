"""
Shared blocks rendered on several pages: monitoring checks, stablecoin facts and admin findings, filtered by strategy.
"""

import pandas as pd
import streamlit as st

import project_config as cfg
from utils.data_loader import (load_c21_rates, load_c5, load_csv, load_current, load_current_snapshot,
                               load_dolomite_snapshot, load_positions, load_resupply_snapshot, load_wlfi)
from utils.strategy import c21_net, cur_daily, cur_liq_levels, legs, nearest_large_liquidation, window_rates

ICON = {"OK": "🟢 OK", "WARN": "🟠 WARN", "ACT": "🔴 ACT", "NO DATA": "⚪ NO DATA"}


def status(value, warn, act, higher_is_bad=True):
    if value is None:
        return "NO DATA"
    if higher_is_bad:
        return "ACT" if value >= act else "WARN" if value >= warn else "OK"
    return "ACT" if value <= act else "WARN" if value <= warn else "OK"


def rows_current():
    cur, cs = load_current(), load_current_snapshot()
    if cur.empty or cs.empty:
        return []
    lc, s0 = cur.iloc[-1], cs.iloc[-1]
    ratio = float(lc["s_tokenPrice"] / lc["c_tokenPrice"])   # USDSUI/USDC on Current Finance's price feed, latest day
    net14 = cur_daily(cur.tail(14), cfg.CUR_LEVERAGE, cfg.EQUITY / 1e6).mean()
    health = 0.85 / ((cfg.CUR_LEVERAGE - 1) / cfg.CUR_LEVERAGE)
    return [
        ("K1", "USDSUI/USDC on Current Finance's feed", f"{ratio:.5f}", "ACT" if abs(ratio - 1) > 0.02 else "WARN" if abs(ratio - 1) > 0.005 else "OK"),
        ("K2", f"Vault health at {cfg.CUR_LEVERAGE:g}x (target)", f"{health:.2f}", status(health, 1.15, 1.10, False)),
        ("K3", "USDSUI utilization", f"{lc['s_utilization']:.1%}", status(lc["s_utilization"], 0.85, 0.90)),
        ("K3", "USDSUI borrow cap used", f"{s0['usdsui_borrowed'] / s0['usdsui_borrow_cap']:.0%}",
         status(s0["usdsui_borrowed"] / s0["usdsui_borrow_cap"], 0.85, 0.95)),
        ("K4", f"Net yield at {cfg.CUR_LEVERAGE:g}x on $1.5M, 14 days", f"{net14:.1f}%", status(net14, 13.0, 12.0, False)),
        ("K5", "Unclaimed or unhedged SUI rewards", "no live position", "NO DATA"),
        ("K7", f"USDSUI independent rating / early-warning score", f"{s0['usdsui_grade']} / {int(s0['usdsui_dews'])}", status(s0["usdsui_dews"], 20, 30)),
        ("K7", "USDSUI supply change, 1 day", f"{s0['usdsui_supply_1d']:+.1%}", status(s0["usdsui_supply_1d"], 0.03, 0.05)),
        ("K7", f"USDC independent rating / early-warning score", f"{s0['usdc_grade']} / {int(s0['usdc_dews'])}", status(s0["usdc_dews"], 20, 30)),
        ("K8", "SUI reward APR on USDC vs 30-day average", f"{lc['c_reward'] / cur.tail(30)['c_reward'].mean() - 1:+.1%}",
         status(-(lc["c_reward"] / cur.tail(30)["c_reward"].mean() - 1), 0.10, 0.15)),
        ("K8", "SUI reward APR on USDSUI vs 30-day average", f"{lc['s_reward'] / cur.tail(30)['s_reward'].mean() - 1:+.1%}",
         status(-(lc["s_reward"] / cur.tail(30)["s_reward"].mean() - 1), 0.10, 0.15)),
        ("K9", "Exit capacity: quoted cost of a $1M USDSUI swap", f"{s0['buy_usdsui_1m']:.3%}", status(s0["buy_usdsui_1m"], 0.001, 0.003)),
        ("K3", "USDC borrow cap room", f"${s0['usdc_borrow_cap'] - s0['usdc_borrowed']:.1f}M", status(s0["usdc_borrow_cap"] - s0["usdc_borrowed"], 2.0, 1.0, False)),
        ("K6", "Admin, upgrade or capability actions", "no event feed yet", "NO DATA"),
    ]


def rows_usd1():
    rates, wlfi, pos, snap = load_c21_rates(), load_wlfi(), load_positions(), load_dolomite_snapshot()
    if rates.empty or wlfi.empty or snap.empty:
        return []
    s = snap.set_index("symbol")
    px = wlfi["close"].to_numpy()
    wk = px[-1] / px[-8] - 1
    nearest, _ = nearest_large_liquidation(pos, float(px[-1]))
    ratio = 1 / (1 + nearest) if nearest is not None else None
    net7 = c21_net(cfg.C21_LEVERAGE, window_rates(rates, 7))
    h = legs(cfg.C21_LEVERAGE)[3]
    rows = [
        ("T1", "WLFI 7-day change", f"{wk:+.1%}", status(-wk, 0.15, 0.20)),
        ("T2", "WLFI / nearest large-position liquidation price (debt 1M+)", f"{ratio:.2f}x" if ratio else "-", status(ratio, 2.0, 1.6, False)),
        ("T3", "WLFI-backed debt, weekly change", "needs two snapshots", "NO DATA"),
        ("T4", "USD1 pool utilization", f"{s.loc['USD1', 'utilization']:.1%}", status(s.loc['USD1', 'utilization'], 0.85, 0.92)),
        ("T4", "USDC pool utilization", f"{s.loc['USDC', 'utilization']:.1%}", status(s.loc['USDC', 'utilization'], 0.85, 0.92)),
        ("T5", "USDC pool supply, 1-day change", "needs two snapshots", "NO DATA"),
        ("T6", "Net APR at 3x, last 7 days", f"{net7:.1f}%", status(net7, 13.0, 12.0, False)),
        ("T7", "Unsold WLFI rewards", "no live position", "NO DATA"),
        ("T8", "USD1 price (oracle)", f"{s.loc['USD1', 'price']:.4f}", status(s.loc['USD1', 'price'], 0.995, 0.985, False)),
        ("T9", "Health, positions A and B (target)", f"{h:.2f}", status(h, 1.25, 1.15, False)),
        ("T10", "Dolomite admin / parameter events", "no event feed yet", "NO DATA"),
        ("T12", "Merkl accrual vs expected", "no live position", "NO DATA"),
    ]
    rw = load_csv("rewards_snapshot.csv")
    if not rw.empty:
        r0 = rw.iloc[-1]
        runway = r0["funder_wlfi_balance"] / r0["wlfi_campaign_weekly"]
        rows += [("T13", f"WLFI campaign runway (current ends {r0['wlfi_campaign_end']})", f"{runway:.1f} weeks", status(runway, 2.0, 0.0, False)),
                 ("T14", "Access-control events (Dolomite roles, USD1 mint/freeze, oracles)", "no event feed yet", "NO DATA")]
    return rows


def rows_reusd():
    c5, rs, rw = load_c5(), load_resupply_snapshot(), load_csv("rewards_snapshot.csv")
    if c5.empty:
        return []
    last = c5.iloc[-1]
    lp = last["lp_base"] + last["lp_reward"]
    px5 = last["reusd_price"]
    r1 = "ACT" if (px5 > 1.003 or px5 < 0.93) else "WARN" if (px5 > 0.998 or px5 < 0.95) else "OK"
    rows = [("R1", "reUSD price", f"{px5:.4f}", r1),
            ("R2", "LP APY before dilution", f"{lp:.1f}%", status(lp, 14.0, 12.0, False)),
            ("R3", "Resupply reUSD borrow cost", f"{last['v2_borrow_cost']:.2f}%", status(last["v2_borrow_cost"], 4.0, 6.0))]
    if not rs.empty:
        s0 = rs.iloc[-1]
        share = s0["reusd_balance"] / (s0["reusd_balance"] + s0["scrvusd_balance"] * s0["scrvusd_rate"])
        cov = s0["ip_reusd"] / s0["reusd_supply"]
        rows += [("R4", "reUSD share of the Curve pool", f"{share:.1%}", status(share, 0.85, 0.90)),
                 ("R7", "Insurance pool coverage", f"{cov:.1%}", status(cov, 0.05, 0.03, False)),
                 ("R8", "Redemptions against the fund's pair", "no live position", "NO DATA")]
    if not rw.empty:
        r0 = rw.iloc[-1]
        chg = r0["gauge_weight_next_week"] / r0["gauge_weight_this_week"] - 1
        rows += [("R9", "Curve gauge weight, next week vs this week", f"{chg:+.1%}", status(-chg, 0.30, 0.50)),
                 ("R10", "Resupply guardian and upgrade actions", "no event feed yet", "NO DATA")]
    return rows


def console(rows, height=None):
    df = pd.DataFrame(rows, columns=["trigger", "check", "value", "status"])
    counts = df["status"].value_counts()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("OK", int(counts.get("OK", 0)))
    c2.metric("Warn", int(counts.get("WARN", 0)))
    c3.metric("Act", int(counts.get("ACT", 0)))
    c4.metric("No data yet", int(counts.get("NO DATA", 0)))
    df["status"] = df["status"].map(ICON)
    st.dataframe(df, hide_index=True, width="stretch", height=height or (38 + 35 * len(df)))


STABLE = {
    "USDC": {"Issuer / mechanism": "Circle, 1:1 fiat-backed", "Backing": "Cash and short-dated T-bills (reserve fund managed by BlackRock)",
             "Reserve evidence": "Monthly attestations", "Holder exit": "Redemption through Circle, deep markets everywhere",
             "Freeze or seizure": "Yes, issuer can freeze", "Peg record": "Fell to 0.877 in March 2023 (bank failure), recovered within days",
             "Independent rating": "A+ (90/100)", "Backing / exit / control": "89 / 100 / 84", "Reserve assurance": "Monthly Deloitte examinations", "Exit capacity": "77% of $25M executable immediately at 5 bps", "Mint and upgrade control": "Circle (issuer-controlled)", "Peg incidents on record": "3 (incl. March 2023)", "Early-warning score": "15/100, calm", "Role": "The fund's equity and the collateral of vault 1"},
    "USDSUI": {"Issuer / mechanism": "Bridge (a Stripe company), 1:1 fiat-backed, Open Issuance",
               "Backing": "T-bills, repos, government money-market funds, cash (Lead Bank, BlackRock, Fidelity)",
               "Reserve evidence": "Issuer proof of reserves", "Holder exit": "Redemption for Bridge customers, DEX otherwise",
               "Freeze or seizure": "Yes, issuer can freeze", "Peg record": "Widest moves +1.30% / -0.63%, and within 0.25% of USDC on Current Finance's feed since April",
               "Independent rating": "C- (50/100)", "Backing / exit / control": "59 / 41 / 53", "Reserve assurance": "Self-reported, no independent attestation", "Exit capacity": "Institutional redemption in 1 to 7 days, about $1.5M of effective DEX depth within $8M of pool liquidity", "Mint and upgrade control": "Single-key Bridge addresses (minter, upgrade)", "Peg incidents on record": "0", "Early-warning score": "7/100, calm", "Role": "Owed in vault 1 and held in vault 2, in equal amounts"},
    "USD1": {"Issuer / mechanism": "BitGo Trust Company, 1:1 fiat-backed", "Backing": "T-bills, government money-market funds, bank deposits",
             "Reserve evidence": "Monthly attestations, real-time proof of reserve", "Holder exit": "Redemption through the issuer only",
             "Freeze or seizure": "Yes, issuer can freeze", "Peg record": "Near par for over a year",
             "Independent rating": "C+ (61/100)", "Backing / exit / control": "-", "Reserve assurance": "Monthly attestations, KPMG examination (July 2026)", "Exit capacity": "Redemption through the issuer only", "Mint and upgrade control": "3-of-6 Safe admin, one single-key minter and freezer", "Peg incidents on record": "Near par for over a year", "Early-warning score": "-", "Role": "Held and owed in equal amounts"},
    "reUSD": {"Issuer / mechanism": "Resupply, crypto-collateralized debt position", "Backing": "crvUSD and frxUSD lending-vault deposits",
              "Reserve evidence": "On-chain collateral ratio ~1.08 (July)", "Holder exit": "1% communal redemption fee sets a floor near 0.99",
              "Freeze or seizure": "No", "Peg record": "Below par since 6 Aug 2026, printed 0.82 in April",
              "Independent rating": "D (44/100)", "Backing / exit / control": "64 / 51 / 55", "Reserve assurance": "On-chain collateral", "Exit capacity": "23% of $10M executable immediately at 200 bps", "Mint and upgrade control": "On-chain governance (7-day vote)", "Peg incidents on record": "101 incidents, below par since 6 Aug", "Early-warning score": "28/100, watch", "Role": "About three-quarters of the LP"},
    "scrvUSD": {"Issuer / mechanism": "Curve savings vault over crvUSD", "Backing": "crvUSD (crypto-collateralized, soft liquidation)",
                "Reserve evidence": "On-chain vault accounting", "Holder exit": "Withdraw from the vault, crvUSD via Curve pools",
                "Freeze or seizure": "No (only through upstream collateral)", "Peg record": "Tracks crvUSD, value rises with the savings rate",
                "Independent rating": "B (72/100)", "Backing / exit / control": "-", "Reserve assurance": "On-chain vault accounting", "Exit capacity": "Withdraw to crvUSD, Curve pools", "Mint and upgrade control": "No privileged mint", "Peg incidents on record": "Tracks crvUSD", "Early-warning score": "-", "Role": "About one-quarter of the LP"},
}


def stablecoin_table(coins):
    rows = list(STABLE["USDC"].keys())
    st.dataframe(pd.DataFrame({"": rows, **{c: [STABLE[c].get(r, "-") for r in rows] for c in coins}}), hide_index=True,
                 width="stretch", height=38 + 35 * len(rows))
    st.caption("Independent rating, pillar scores, reserve assurance, exit capacity, controls and early-warning score: Pharos "
               "(pharos.watch), 1 October 2026. Other rows: issuer disclosures and on-chain checks.")


def admin_table(strategies):
    m = load_csv("admin_map.csv")
    if m.empty:
        return
    m = m[m["strategy"].isin(strategies)].drop(columns=["strategy"])
    st.dataframe(m.rename(columns=lambda c: c.replace("_", " ").title()), hide_index=True, width="stretch")
