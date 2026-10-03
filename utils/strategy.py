"""
Strategy math. Every page computes its numbers here, from the CSVs in data/.

C21 (Proposal 1): USD1 carry on Dolomite, two positions, USDC equity.
  Position A: USDC collateral, USD1 debt.  Position B: USD1 collateral, USDC debt (recycled into A).
  Leverage L = total collateral / equity. Both positions held at the same health.
C5 (Proposal 2): reUSD/scrvUSD LP on Stake DAO, funded with reUSD borrowed on Resupply.
"""

import numpy as np
import pandas as pd

LT = 0.9                      # Dolomite stable e-mode: liquidation at 90% of collateral value
DOLOMITE_RATIO = 1.17647058823529413   # DolomiteMargin liquidationRatio (default markets)
WL_SYMS = ("WLFI", "WLFIcx")


# ── C21: structure ──────────────────────────────────────────────
def legs(L: float):
    """Per unit of equity: USDC supplied (a), USD1 supplied = USD1 borrowed (d1), USDC borrowed (d2), health."""
    if L <= 1:
        return 1.0, 0.0, 0.0, float("inf")
    k = 1 - 1 / L
    return 1 / (1 - k * k), k / (1 - k * k), k * k / (1 - k * k), LT / k


def c21_components(L: float, r: dict) -> dict:
    """Annual % on equity, split by source. r: usd1_supply_base, usd1_borrow, usdc_supply_base, usdc_borrow,
    usd1_wlfi_reward, usdc_wlfi_reward (all %)."""
    a, d1, d2, _ = legs(L)
    return {
        "USDC lending (base)": a * r["usdc_supply_base"],
        "USD1 lending (base)": d1 * r["usd1_supply_base"],
        "USD1 borrow cost": -d1 * r["usd1_borrow"],
        "USDC borrow cost": -d2 * r["usdc_borrow"],
        "WLFI rewards on USDC": a * r["usdc_wlfi_reward"],
        "WLFI rewards on USD1": d1 * r["usd1_wlfi_reward"],
    }


def c21_net(L: float, r: dict) -> float:
    return sum(c21_components(L, r).values())


RATE_COLS = ["usd1_supply_base", "usd1_borrow", "usdc_supply_base", "usdc_borrow", "usd1_wlfi_reward", "usdc_wlfi_reward"]


def window_rates(rates: pd.DataFrame, days: int) -> dict:
    """Average of daily realized rates over the last `days` days."""
    return rates.tail(days)[RATE_COLS].mean().to_dict()


def c21_daily_net(rates: pd.DataFrame, L: float) -> pd.Series:
    return rates.apply(lambda row: c21_net(L, row), axis=1)


def c21_guardrail_backtest(rates: pd.DataFrame, wlfi: pd.DataFrame, base_L: float, liq_price: float,
                           start: str = "2026-04-22") -> tuple[pd.DataFrame, list]:
    """Daily net APR with guardrails. T1: WLFI 7-day fall > 20% -> 1.5x for 7 days.
    T2: WLFI close < 1.6x liq_price -> 1x until back above 1.8x."""
    df = rates[rates["date"] >= start].merge(wlfi[["date", "close"]], on="date").reset_index(drop=True)
    cut_until, unwound, events, levs = None, False, [], []
    for i, row in df.iterrows():
        c = row["close"]
        wk = df.loc[i - 7, "close"] if i >= 7 else c
        if c / wk - 1 < -0.20 and not unwound:
            cut_until = df.loc[min(i + 7, len(df) - 1), "date"]
            events.append((row["date"], "T1: cut to 1.5x", f"WLFI {c / wk - 1:+.1%} over 7 days"))
        if not unwound and c < 1.6 * liq_price:
            unwound = True
            events.append((row["date"], "T2: net to 1x", f"WLFI ${c:.4f}"))
        if unwound and c > 1.8 * liq_price:
            unwound = False
            events.append((row["date"], "T2: re-enter", f"WLFI ${c:.4f}"))
        levs.append(1.0 if unwound else (1.5 if cut_until is not None and row["date"] <= cut_until else base_L))
    df["leverage"] = levs
    df["net_plain"] = df.apply(lambda r: c21_net(base_L, r), axis=1)
    df["net_guarded"] = df.apply(lambda r: c21_net(r["leverage"], r), axis=1)
    return df, events


# ── C21: WLFI stress on Dolomite ────────────────────────────────
def position_health(pos: pd.DataFrame, shock: float) -> pd.DataFrame:
    """Health and raw values of WLFI-backed positions after a WLFI price move `shock` (e.g. -0.5)."""
    p = pos.copy()
    p["adj_supply"] = p["adj_wlfi"] * (1 + shock) + p["adj_other"]
    p["health"] = p["adj_supply"] / (p["adj_debt"] * DOLOMITE_RATIO)
    p["raw_collateral"] = (p["wlfi_collateral_usd"] + p["wlfics_collateral_usd"]) * (1 + shock) + p["other_collateral_usd"]
    p["raw_debt"] = p["usd1_debt_usd"] + p["usdc_debt_usd"] + p["other_debt_usd"]
    p["shortfall"] = (p["raw_debt"] - p["raw_collateral"]).clip(lower=0)
    share = p["shortfall"] / p["raw_debt"].where(p["raw_debt"] > 0, 1)
    p["shortfall_usd1"] = share * p["usd1_debt_usd"]
    p["shortfall_usdc"] = share * p["usdc_debt_usd"]
    return p


def threshold_shock(row: pd.Series, kind: str) -> float | None:
    """WLFI move at which one position becomes liquidatable ('liq') or insolvent ('insolvent')."""
    for s in np.arange(0, -1.0005, -0.001):
        adj = row["adj_wlfi"] * (1 + s) + row["adj_other"]
        raw = (row["wlfi_collateral_usd"] + row["wlfics_collateral_usd"]) * (1 + s) + row["other_collateral_usd"]
        debt = row["usd1_debt_usd"] + row["usdc_debt_usd"] + row["other_debt_usd"]
        if kind == "liq" and adj < row["adj_debt"] * DOLOMITE_RATIO:
            return s
        if kind == "insolvent" and raw < debt:
            return s
    return None


def stress_table(pos: pd.DataFrame, snap: pd.DataFrame, L: float, equity: float, shocks) -> pd.DataFrame:
    usd1_supply = float(snap.loc[snap.symbol == "USD1", "supply_usd"].iloc[0])
    usdc_supply = float(snap.loc[snap.symbol == "USDC", "supply_usd"].iloc[0])
    a, d1, _, _ = legs(L)
    rows = []
    for s in shocks:
        p = position_health(pos, s)
        sf1, sfc = p["shortfall_usd1"].sum(), p["shortfall_usdc"].sum()
        loss1, lossc = sf1 / usd1_supply, sfc / usdc_supply
        our = equity * (d1 * loss1 + a * lossc)
        rows.append({"shock": s, "liquidatable": int((p["health"] < 1).sum()),
                     "debt_liquidatable": p.loc[p["health"] < 1, "raw_debt"].sum(),
                     "shortfall_usd1": sf1, "shortfall_usdc": sfc, "pool_loss_usd1": loss1, "pool_loss_usdc": lossc,
                     "our_loss": our, "our_loss_pct": our / equity, "our_loss_netted": equity * lossc,
                     "our_loss_netted_pct": lossc})
    return pd.DataFrame(rows)


def expected_shortfall(wlfi: pd.DataFrame, pos: pd.DataFrame, snap: pd.DataFrame, L: float, horizon: int = 30,
                       q: float = 0.95) -> dict:
    """Historical-simulation loss on equity from WLFI moves over `horizon` days (close to later low), no liquidations
    filled, pro-rata pool shortfall. Returns VaR and ES at q, plus the worst case."""
    c, lo = wlfi["close"].to_numpy(), wlfi["low"].to_numpy()
    moves = [lo[i + 1:i + horizon + 1].min() / c[i] - 1 for i in range(len(c) - horizon)]
    grid = np.round(np.arange(0, -1.0001, -0.01), 2)
    st = stress_table(pos, snap, L, 1.0, grid).set_index("shock")["our_loss_pct"]
    losses = np.array([np.interp(m, grid[::-1], st.to_numpy()[::-1]) for m in moves])
    var = np.quantile(losses, q)
    tail = losses[losses >= var]
    return {"n": len(moves), "var": var, "es": tail.mean() if len(tail) else var, "worst_move": min(moves),
            "worst_loss": losses.max(), "moves": np.array(moves), "losses": losses}


# ── C5 ──────────────────────────────────────────────────────────
C5_LTV, C5_RE_SHARE = 0.8, 0.77
SD_BOOST, SD_FEES = 2.38, 0.155   # Stake DAO boost on this gauge and total fees on CRV (30 Sep 2026)


def c5_inputs(c5: pd.DataFrame) -> pd.DataFrame:
    """Daily inputs for Proposal 2. Exact structure (Resupply crvUSD/sfrxUSD v2 pair) where history exists; before that,
    the closest proxies: Curve Lend sfrxUSD v1 lending base and the Resupply crvUSD/sUSDe pair's borrow cost and rewards."""
    d = c5.copy()
    d["exact"] = d["v2_borrow_cost"].notna() & d["col_base_v2"].notna()
    d["col_base"] = d["col_base_v2"].fillna(d["col_base_v1"]).fillna(d["collateral_lend_apy"]).fillna(0)
    d["borrow_cost"] = d["v2_borrow_cost"].fillna(d["proxy_borrow_cost"]).fillna(2.9)
    for t in ("crv", "rsup", "cvx"):
        d[f"rw_{t}"] = d[f"v2_rw_{t}"].fillna(d[f"proxy_rw_{t}"]).fillna(0)
    d["borrow_rewards"] = d["rw_crv"] + d["rw_rsup"] + d["rw_cvx"]
    # LP yield on Stake DAO: Curve trading fees + unboosted CRV x Stake DAO boost, net of Stake DAO fees.
    if "curve_crv_min" in d:
        d["lp_fee"] = d["curve_base"].fillna(d["lp_base"])
        d["lp_crv"] = (d["curve_crv_min"] * SD_BOOST * (1 - SD_FEES)).fillna(d["lp_reward"])
    else:
        d["lp_fee"], d["lp_crv"] = d["lp_base"], d["lp_reward"]
    return d


def c5_backtest(c5: pd.DataFrame, equity: float, ltv: float = C5_LTV, hedged: bool = True,
                reward_scale: float = 1.0) -> pd.DataFrame:
    """Daily income on equity.
    Hedged: deposit crvUSD in Resupply (lent in Curve Lend, earns col_base), borrow reUSD at `ltv` (pays borrow_cost,
    earns borrow rewards in CRV/RSUP/CVX), LP the reUSD on Stake DAO. Unhedged: equity straight into the LP.
    The LP reward part is diluted by our size vs pool TVL; reward_scale scales the borrow rewards (sensitivity)."""
    d = c5_inputs(c5).reset_index(drop=True)
    size = equity * ltv if hedged else equity
    dil = d["pool_tvl"] / (d["pool_tvl"] + size)
    lp = (d["lp_fee"] + d["lp_crv"] * dil) / 100 / 365 * size
    dp = d["reusd_price"].diff().fillna(0) / d["reusd_price"].shift(1).fillna(d["reusd_price"])
    d["inc_lp"] = lp
    if hedged:
        d["inc_collateral"] = d["col_base"] / 100 / 365 * equity
        d["inc_borrow_cost"] = -d["borrow_cost"] / 100 / 365 * size
        d["inc_borrow_rewards"] = d["borrow_rewards"] * reward_scale / 100 / 365 * size
        d["inc_price"] = -(1 - C5_RE_SHARE) * size * dp
        d["income"] = d["inc_lp"] + d["inc_collateral"] + d["inc_borrow_cost"] + d["inc_borrow_rewards"] + d["inc_price"]
    else:
        d["inc_price"] = C5_RE_SHARE * size * dp
        d["income"] = d["inc_lp"] + d["inc_price"]
    d["apr_day"] = d["income"] / equity * 365 * 100
    return d


def monthly_apr(df: pd.DataFrame, col: str, date_col: str = "date") -> pd.DataFrame:
    m = df.assign(month=pd.to_datetime(df[date_col]).dt.strftime("%Y-%m")).groupby("month")[col].mean()
    return m.reset_index().rename(columns={col: "apr"})


LARGE_DEBT = 1_000_000   # a "large" WLFI-backed position for trigger T2


def nearest_large_liquidation(pos: pd.DataFrame, wlfi_now: float, min_debt: float = LARGE_DEBT):
    """WLFI move and price at which the first large WLFI-backed position becomes liquidatable."""
    big = pos[(pos["usd1_debt_usd"] + pos["usdc_debt_usd"]) >= min_debt]
    moves = [m for m in (threshold_shock(r, "liq") for _, r in big.iterrows()) if m is not None]
    if not moves:
        return None, None
    m = max(moves)
    return m, wlfi_now * (1 + m)


# ── C21: stress with a liquidation capacity ─────────────────────
LIQ_BONUS = 0.15   # WLFI liquidation reward (1.05 x (1 + liquidationRewardPremium 2.0) spread)


def stress_with_capacity(pos: pd.DataFrame, snap: pd.DataFrame, L: float, equity: float, shock: float,
                         capacity: float) -> dict:
    """WLFI falls to `shock`. Positions become liquidatable in order of their threshold; liquidators can sell up to
    `capacity` USD of WLFI in total during the fall. A liquidated position leaves no shortfall; the rest are marked at
    the terminal shock."""
    p = pos.copy()
    p["liq_at"] = [threshold_shock(r, "liq") for _, r in p.iterrows()]
    p["debt"] = p["usd1_debt_usd"] + p["usdc_debt_usd"] + p["other_debt_usd"]
    left, liquidated = capacity, set()
    for i, r in p[p["liq_at"].notna()].sort_values("liq_at", ascending=False).iterrows():
        if r["liq_at"] < shock:
            continue
        need = r["debt"] * (1 + LIQ_BONUS)
        if need <= left:
            left -= need
            liquidated.add(i)
    rest = position_health(p.drop(index=list(liquidated)), shock)
    usd1_supply = float(snap.loc[snap.symbol == "USD1", "supply_usd"].iloc[0])
    usdc_supply = float(snap.loc[snap.symbol == "USDC", "supply_usd"].iloc[0])
    sf1, sfc = rest["shortfall_usd1"].sum(), rest["shortfall_usdc"].sum()
    a, d1, _, _ = legs(L)
    return {"liquidated": len(liquidated), "shortfall": sf1 + sfc, "our_loss_pct": d1 * sf1 / usd1_supply + a * sfc / usdc_supply,
            "our_loss_netted_pct": sfc / usdc_supply}


# ── C5: StableSwap depeg model (reUSD/scrvUSD, Curve NG) ────────
def _ss_D(x, y, Ann):
    S, D = x + y, x + y
    for _ in range(255):
        Dp = D ** 3 / (4 * x * y)
        Dn = (Ann * S + 2 * Dp) * D / ((Ann - 1) * D + 3 * Dp)
        if abs(Dn - D) < 1e-9:
            return Dn
        D = Dn
    return D


def _ss_y(x, D, Ann):
    c, b, y = D ** 3 / (4 * x * Ann), x + D / Ann, D
    for _ in range(255):
        yn = (y * y + c) / (2 * y + b - D)
        if abs(yn - y) < 1e-9:
            return yn
        y = yn
    return y


def depeg_table(pool: dict, lp_usd: float, borrowed_share: float = 1.0, prices=None) -> pd.DataFrame:
    """pool: A, reusd_balance, scrvusd_balance, scrvusd_rate. We deploy lp_usd into the pool and borrow
    borrowed_share x lp_usd of reUSD (1.0 = the whole LP is funded in reUSD). Arbitrage moves the pool to the market
    price p. Returns P&L of the plain LP and of our funded position, vs today, in USD, plus reUSD share of the pool."""
    Ann = pool["A"] * 2
    x0, y0 = pool["reusd_balance"], pool["scrvusd_balance"] * pool["scrvusd_rate"]
    D0 = _ss_D(x0, y0, Ann)
    price = lambda x: _ss_y(x, D0, Ann) - _ss_y(x + 1, D0, Ann)
    p0 = price(x0)

    def state(p):
        lo, hi = 1.0, D0 * 50
        for _ in range(200):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if price(mid) > p else (lo, mid)
        x = (lo + hi) / 2
        return x, _ss_y(x, D0, Ann)

    share = lp_usd / (x0 * p0 + y0)
    debt_tok = lp_usd * borrowed_share / p0
    rows = []
    for p in prices or [1.01, 1.0, 0.995, round(p0, 4), 0.985, 0.98, 0.97, 0.96, 0.95, 0.93, 0.90, 0.85, 0.80]:
        x, y = state(p)
        lp_pnl = share * (x * p + y) - lp_usd
        hold = share * (x0 * p + y0)
        rows.append({"price": p, "reusd_share": x * p / (x * p + y), "plain_lp_pnl": lp_pnl,
                     "funded_pnl": lp_pnl - debt_tok * (p - p0), "net_reusd_tokens": share * x - debt_tok,
                     "il_vs_hold": share * (x * p + y) / hold - 1, "lp_reusd_tokens": share * x})
    return pd.DataFrame(rows), p0


def loss_thresholds(pool: dict, lp_usd: float, borrowed_share: float, equity: float, limits=(0.001, 0.002, 0.003)):
    """reUSD price, above and below today's, at which the position has lost each limit (share of equity)."""
    Ann = pool["A"] * 2
    x0, y0 = pool["reusd_balance"], pool["scrvusd_balance"] * pool["scrvusd_rate"]
    D0 = _ss_D(x0, y0, Ann)
    price = lambda x: _ss_y(x, D0, Ann) - _ss_y(x + 1, D0, Ann)
    p0 = price(x0)
    share, debt = lp_usd / (x0 * p0 + y0), lp_usd * borrowed_share / p0

    def pnl(p):
        lo, hi = 1.0, D0 * 50
        for _ in range(120):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if price(mid) > p else (lo, mid)
        x = (lo + hi) / 2
        return (share * (x * p + _ss_y(x, D0, Ann)) - lp_usd - debt * (p - p0)) / equity

    out = []
    for lim in limits:
        up = next((round(p, 4) for p in np.arange(p0, 1.04, 0.0002) if pnl(p) <= -lim), None)
        dn = next((round(p, 4) for p in np.arange(p0, 0.70, -0.0005) if pnl(p) <= -lim), None)
        out.append({"limit": lim, "up": up, "down": dn})
    return p0, out


INTERFACE_BORROW_REWARDS = 4.21   # Resupply interface, crvUSD/sfrxUSD v2 pair, 30 Sep 2026


def interface_reward_scale(c5: pd.DataFrame, level: float = INTERFACE_BORROW_REWARDS) -> float:
    """Scale that lifts the pair's reward history so its last 30 days average `level`."""
    hist = c5_inputs(c5).tail(30)["borrow_rewards"].mean()
    return level / hist if hist > 0 else 1.0


# ── Current: USDC / USDSUI carry through two Multiply vaults ─────
CUR_LIQ_LTV = 0.85
CUR_RF = 0.20


def cur_curve(u):
    """Borrow APR (%) vs utilization, fitted from Current Finance's hourly history (both markets share it)."""
    u = np.asarray(u, dtype=float)
    return np.where(u <= 0.8, 0.5 + 5.6 * u, 0.5 + 5.6 * 0.8 + (u - 0.8) * 90)


def cur_legs(L: float):
    """Vault 1 (USDC collateral, USDSUI debt) and vault 2 (USDSUI collateral, USDC debt), both at leverage L,
    sized so net USDSUI is zero. Per unit of equity: split e1/e2, USDC supplied a, USDSUI borrowed = supplied d1,
    USDC borrowed d2."""
    e1, e2 = L / (2 * L - 1), (L - 1) / (2 * L - 1)
    return e1, e2, L * e1, (L - 1) * e1, (L - 1) * e2


def cur_liq_levels(L: float):
    """USDSUI/USDC ratio at which vault 1 (rise) and vault 2 (fall) reach the liquidation LTV."""
    return CUR_LIQ_LTV * L / (L - 1), (L - 1) / L / CUR_LIQ_LTV


def cur_components(r: dict, L: float, E: float) -> dict:
    """Annual % on equity by source at leverage L and equity E ($M). r: c_/s_ supplied and borrowed ($M), base supply,
    borrow and SUI reward APR (%). Our size moves utilization along the fitted curve and dilutes the rewards."""
    _, _, a, d1, d2 = cur_legs(L)
    cS, cB, sS, sB = r["c_supply_usd"], r["c_borrow_usd"], r["s_supply_usd"], r["s_borrow_usd"]
    uc0, us0 = cB / cS, sB / sS
    uc1, us1 = (cB + d2 * E) / (cS + a * E), (sB + d1 * E) / (sS + d1 * E)
    bc = r["c_borrowAPY"] + float(cur_curve(uc1) - cur_curve(uc0))
    bs = r["s_borrowAPY"] + float(cur_curve(us1) - cur_curve(us0))
    c_base, s_base = uc1 * bc * (1 - CUR_RF), us1 * bs * (1 - CUR_RF)
    c_rew = r["c_reward"] * cS / (cS + a * E)
    s_rew = r["s_reward"] * sS / (sS + d1 * E)
    return {"USDC lending (base)": a * c_base, "SUI rewards on USDC": a * c_rew,
            "USDSUI lending (base)": d1 * s_base, "SUI rewards on USDSUI": d1 * s_rew,
            "USDSUI borrow cost": -d1 * bs, "USDC borrow cost": -d2 * bc}


def cur_net(r: dict, L: float, E: float) -> float:
    return sum(cur_components(r, L, E).values())


def cur_daily(cur: pd.DataFrame, L: float, E: float) -> pd.Series:
    return cur.apply(lambda row: cur_net(row, L, E), axis=1)


def _interp_cost(size, pts):
    xs, ys = zip(*sorted(pts.items()))
    return float(np.interp(size, xs, ys))


def cur_costs(snap: pd.Series, L: float, E: float, tranche: float = 0.25) -> dict:
    """Entry, normal round trip, fast exit and stressed exit costs ($) for both vaults at leverage L, equity E ($M).
    Buying USDSUI costs more than selling it (it trades a hair above par). Tranche size in $M for staged entry."""
    e1, e2, a, d1, d2 = cur_legs(L)
    buy = {0.05: snap["buy_usdsui_50k"], 0.1: snap["buy_usdsui_100k"], 1.0: snap["buy_usdsui_1m"]}
    sell = {0.05: snap["sell_usdsui_50k"], 0.1: snap["sell_usdsui_100k"], 1.0: snap["sell_usdsui_1m"]}
    size = (a + d1) * E * 1e6                      # leveraged size of both vaults (Multiply fee base)
    v2_buy = L * e2 * E * 1e6                      # vault 2 buys USDSUI at entry
    v1_sell = (L - 1) * e1 * E * 1e6               # vault 1 sells borrowed USDSUI at entry
    fee = size * snap["multiply_fee"]
    entry = fee + v2_buy * _interp_cost(tranche, buy) + v1_sell * _interp_cost(tranche, sell)
    exit_staged = fee + v1_sell * _interp_cost(tranche, buy) + v2_buy * _interp_cost(tranche, sell)
    exit_fast = fee + v1_sell * _interp_cost(1.0, buy) + v2_buy * _interp_cost(1.0, sell)
    exit_stress = fee + (v1_sell + v2_buy) * 0.002
    return {"size": size, "swap_each_way": v2_buy, "entry": entry, "round_trip": entry + exit_staged,
            "exit_fast": exit_fast, "exit_provision": 0.00028 * L * E * 1e6, "exit_stress": exit_stress}



def cur_stress(cur: pd.DataFrame, snap: pd.Series, L: float, E: float) -> pd.DataFrame:
    """Stress scenarios for the Current Finance carry: each shock is applied to every September day and averaged,
    the same way the September net yield is computed elsewhere. E in $M."""
    sep_rows = [r for _, r in cur[cur["date"].astype(str).str.startswith("2026-09")].iterrows()]

    def shocked(**kw):
        vals = []
        for row in sep_rows:
            r = row.to_dict()
            for k, v in kw.items():
                r[k] = r[k] * v if k.endswith("reward") else r[k] + v
            vals.append(cur_net(r, L, E))
        return sum(vals) / len(vals)

    base = shocked()

    lo, hi = 0.0, 1.0
    for _ in range(40):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if shocked(c_reward=1 - m, s_reward=1 - m) > 12 else (lo, m)
    _, _, a, d1, _ = cur_legs(L)
    our_usdc = a * E
    pool = snap["usdc_supplied"] + our_usdc
    room = snap["usdc_borrow_cap"] - snap["usdc_borrowed"]
    day = min(snap["usdc_daily_borrow_cap"], room)
    up, dn = cur_liq_levels(L)
    rows = [
        ("Base, September conditions", f"{base:.1f}%", ""),
        (f"SUI rewards -{lo:.0%} (break-even)", "12.0%", "the tightest limit: trigger K8"),
        ("SUI rewards -30%", f"{shocked(c_reward=0.7, s_reward=0.7):.1f}%", ""),
        ("SUI rewards -50%", f"{shocked(c_reward=0.5, s_reward=0.5):.1f}%", ""),
        ("SUI rewards end", f"{shocked(c_reward=0.0, s_reward=0.0):.1f}%", "rotate"),
        ("USDSUI borrow +300 bps", f"{shocked(s_borrowAPY=3.0):.1f}%", ""),
        ("Both borrow rates +300 bps", f"{shocked(s_borrowAPY=3.0, c_borrowAPY=3.0):.1f}%", ""),
        ("USDSUI ±5% against USDC", "no liquidation", f"vaults liquidate at {dn:.3f} / {up:.3f}"),
        ("Oracle stale or rejected", "no forced loss", "Current Finance blocks new borrowing, while repayment and exits stay open"),
        ("USDSUI unbacked mint, one day", f"-${day * our_usdc / pool * 1e3:,.0f}k ({day * our_usdc / pool / E:.1%} of equity)",
         f"${day:.1f}M daily USDC borrow cap, fund share of the USDC pool {our_usdc / pool:.1%}"),
        ("USDSUI unbacked mint, full cap", f"-${room * our_usdc / pool * 1e3:,.0f}k ({room * our_usdc / pool / E:.1%} of equity)",
         f"${room:.1f}M room under the USDC borrow cap"),
        ("No liquidator bids", "protocol auto-deleveraging", "exit on activation (K6)"),
    ]
    return pd.DataFrame(rows, columns=["scenario", "net yield or loss", "note"])
