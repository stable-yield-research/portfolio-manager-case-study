"""Block: Current Finance (Sui) Main Market history for USDC and USDSUI, plus SUI reward rates from DefiLlama.
Writes current_daily.csv (rates %, utilization, supplied/borrowed $M, rewards %)."""
import json, time, urllib.parse, urllib.request
from pathlib import Path
import pandas as pd
from graphql_client import save_csv

BASE = "https://api.current.finance/chart/"
MARKET = "fe1d8929d13b00aaecd7642dec1c6d41cab82882a1b139efa46bf61dfd6380bf::market_type::MainMarket"
TOKENS = {"c_": "dba34672e30cb065b1f93e3ab55318768fd6fef66c15942c9f7cb846e2f900e7::usdc::USDC",
          "s_": "44f838219cf67b058f3b37907b655f226153c18e33dfcd0da559a844fea9b1c1::usdsui::USDSUI"}
LLAMA = {"c_": "a0860ad8-ba2a-4ff8-8a13-348788864f23", "s_": "1438fc47-2b15-47ac-8514-1ae7b7246cac"}
CHARTS = ["getBorrowAPYHistoryChart", "getSupplyAPYHistoryChart", "getUtilizationHistoryChart", "getSupplyHistoryChart",
          "getBorrowHistoryChart", "getTokenPriceHistoryChart"]


def get(chart, token, frm, to):
    p = urllib.parse.urlencode({"from": frm, "to": to, "marketType": MARKET, "tokenAddress": token}, safe=":")
    r = urllib.request.Request(BASE + chart + "?" + p, headers={"user-agent": "Mozilla/5.0"})
    return json.load(urllib.request.urlopen(r, timeout=60)).get("data") or []


now = int(time.time() * 1000); frm = now - 400 * 86400 * 1000
frames = []
for pre, tok in TOKENS.items():
    parts = []
    for ch in CHARTS:
        df = pd.DataFrame(get(ch, tok, frm, now)).drop(columns=["id", "marketType", "token"], errors="ignore").set_index("t")
        parts.append(df)
    f = pd.concat(parts, axis=1); f = f.loc[:, ~f.columns.duplicated()]
    f.index = pd.to_datetime(f.index, unit="ms", utc=True)
    d = f[["borrowAPY", "supplyAPY", "utilization", "totalSupply", "totalBorrow", "tokenPrice"]].resample("1D").mean()
    d[["borrowAPY", "supplyAPY"]] *= 100
    d["supply_usd"] = d["totalSupply"] * d["tokenPrice"] / 1e12      # 6 decimals -> $M
    d["borrow_usd"] = d["totalBorrow"] * d["tokenPrice"] / 1e12
    rw = pd.DataFrame(json.load(urllib.request.urlopen(f"https://yields.llama.fi/chart/{LLAMA[pre]}", timeout=60))["data"])
    rw["date"] = rw["timestamp"].str[:10]
    d.index = d.index.strftime("%Y-%m-%d")
    d = d.join(rw.set_index("date")["apyReward"].rename("reward"), how="left").fillna({"reward": 0})
    frames.append(d.add_prefix(pre))
out = frames[0].join(frames[1], how="inner")
out["month"] = out.index.str[:7]
save_csv(out.reset_index().rename(columns={"index": "t"}), "current_daily.csv")


# ── Live figures straight from Current Finance's API (overrides the DefiLlama record for today) ──
def _get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"user-agent": "Mozilla/5.0"}), timeout=60))


markets = _get("https://api.current.finance/market/getMarketList?marketType=MainMarket&page=1&size=100")["data"]["content"]
config = _get("https://api.current.finance/pebbleWeb3Config/getAllMarketConfig")["data"]
mid = markets[0]["marketID"]
live = {}
for pre, tok in TOKENS.items():
    p = next(m for m in markets if m["token"] == tok)
    dec = int(p["tokenInfo"]["decimals"])
    rew = sum(r["apr"] * 100 for m in config if m["marketID"] == mid for sm in m["summaries"]
              if sm["reserveCoinType"] == tok and sm["rewardType"] == 0 for r in sm["rewards"])
    live[pre] = dict(supplied=p["totalSupply"] / 10 ** dec / 1e6, borrowed=p["totalBorrow"] / 10 ** dec / 1e6,
                     supply_cap=p["supplyCap"] / 10 ** dec / 1e6, borrow_cap=p["borrowCap"] / 10 ** dec / 1e6,
                     base=p["supplyAPY"] * 100, borrow=p["borrowAPY"] * 100, reward=rew,
                     max_ltv=p["maxLTV"], liq_ltv=p["liqLTV"])
    out.loc[out.index[-1], pre + "reward"] = rew          # today's reward rate from Current Finance itself
save_csv(out.reset_index().rename(columns={"index": "t"}), "current_daily.csv")

snap_path = Path(__file__).resolve().parent.parent / "data" / "current_snapshot.csv"
snap = pd.read_csv(snap_path)
for pre, name in (("c_", "usdc"), ("s_", "usdsui")):
    L = live[pre]
    snap.loc[0, f"{name}_supplied"] = round(L["supplied"], 2)
    snap.loc[0, f"{name}_borrowed"] = round(L["borrowed"], 2)
    snap.loc[0, f"{name}_supply_cap"] = round(L["supply_cap"], 2)
    snap.loc[0, f"{name}_borrow_cap"] = round(L["borrow_cap"], 2)
    snap.loc[0, f"{name}_base"] = round(L["base"], 3)
    snap.loc[0, f"{name}_borrow"] = round(L["borrow"], 3)
    snap.loc[0, f"{name}_reward"] = round(L["reward"], 3)
snap.loc[0, "date"] = pd.Timestamp.now("UTC").strftime("%Y-%m-%d")
snap.loc[0, "source_live"] = "api.current.finance (market list, reward config)"
snap.to_csv(snap_path, index=False)
print("  live from Current Finance:", {k: round(v["reward"], 2) for k, v in live.items()})
