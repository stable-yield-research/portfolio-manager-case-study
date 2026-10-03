"""Current Finance carry: leverage policy, liquidation levels, stablecoins, SUI exposure, risk map."""

import pandas as pd
import streamlit as st

import project_config as cfg
from utils.blocks import stablecoin_table
from utils.data_loader import load_current, load_editorial
from utils.strategy import cur_daily, cur_liq_levels
from utils.text import T

SEV = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}
WIDEST = 0.013          # USDSUI's widest recorded move from par


def render():
    st.markdown('<div class="eyebrow">Current Finance carry · technical analysis</div>', unsafe_allow_html=True)
    st.title("Risk and Leverage")
    cur = load_current()
    if cur.empty:
        st.info("Data missing.")
        return
    st.subheader("Leverage policy")
    st.markdown(T("cur.leverage"))
    sep = cur[cur["date"].astype(str).str.startswith("2026-09")]
    rows = []
    for L in (3.0, 3.5, 4.0, 4.5, 4.8):
        up, dn = cur_liq_levels(L)
        dist = min(up - 1, 1 - dn)
        rows.append([f"{L:g}x", f"{up:.3f} (+{(up - 1) * 100:.1f}%)", f"{dn:.3f} (-{(1 - dn) * 100:.1f}%)",
                     f"{dist / WIDEST:.0f}x", "yes" if dist > 0.05 else "no", f"{cur_daily(sep, L, cfg.EQUITY / 1e6).mean():.1f}%",
                     {3.5: "start", 4.5: "maximum, after conditions", 4.8: "protocol maximum"}.get(L, "")])
    st.dataframe(pd.DataFrame(rows, columns=["leverage", "vault 1 liquidated at USDSUI/USDC", "vault 2 liquidated at",
                                             "distance vs widest USDSUI move", "beyond the ±5% oracle band",
                                             "net at $1.5M, September", "policy"]), hide_index=True, width="stretch")
    st.caption(T("cur.price_note"))

    st.subheader("Stablecoin analysis")
    stablecoin_table(["USDC", "USDSUI"])
    st.markdown(T("stable.usdsui"))

    st.subheader("Reward token exposure")
    st.markdown(T("cur.sui"))
    st.markdown(T("cur.sui_liquidity"))

    st.subheader("Risk map")
    r = load_editorial("risk_map_current")
    if not r.empty:
        r["impact"] = r["impact"].map(lambda v: f"{SEV.get(v, '')} {v}")
        r["likelihood"] = r["likelihood"].map(lambda v: f"{SEV.get(v, '')} {v}")
        st.dataframe(r.rename(columns=str.title), hide_index=True, width="stretch", height=430)
        st.caption(T("cur.riskmap_note"))
