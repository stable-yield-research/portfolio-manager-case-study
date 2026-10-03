"""Block: Dolomite Ethereum. Daily realized USD1/USDC rates (index ratios), WLFI reward APR (DefiLlama),
WLFI-backed borrow positions and pool snapshot. Writes c21_rates_daily.csv, c21_wlfi_positions.csv,
dolomite_markets_snapshot.csv."""
import json, time
import pandas as pd
import requests
from graphql_client import save_csv

SG = "https://api.goldsky.com/api/public/project_clyuw4gvq4d5801tegx0aafpu/subgraphs/dolomite-ethereum/latest/gn"
RPC = "https://ethereum-rpc.publicnode.com"
DM = "0x003Ca23Fd5F0ca87D01F6eC6CD14A8AE60c2b97D"
H = {"content-type": "application/json", "user-agent": "curl/8.0"}
YEAR = 365 * 86400
LLAMA = {"USD1": "86e18974-35ca-4948-9c82-694facf9d082", "USDC": "20e45c3e-7de7-4d34-89e7-20858ecdf252"}
SEL = {"price": "0x8928378e", "index": "0x56ea84b2"}   # getMarketPrice(uint256), getMarketCurrentIndex(uint256)
WL = {"WLFI", "WLFIcx"}
RATIO = 1.17647058823529413


def gql(q):
    d = requests.post(SG, json={"query": q}, headers=H, timeout=90).json()
    if "errors" in d:
        raise RuntimeError(d["errors"])
    return d["data"]


def call(sel, arg):
    r = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                                 "params": [{"to": DM, "data": sel + hex(arg)[2:].zfill(64)}, "latest"]}, headers=H, timeout=60).json()["result"][2:]
    return [int(r[i:i + 64], 16) for i in range(0, len(r), 64)]


def snapshots(token, since):
    out, last = [], since
    while True:
        page = gql('{ interestIndexSnapshots(first:1000, orderBy:updateTimestamp, orderDirection:asc, where:{token:"%s", updateTimestamp_gt:%d}) { updateTimestamp supplyIndex borrowIndex } }' % (token, last))["interestIndexSnapshots"]
        out += page
        if len(page) < 1000:
            return out
        last = int(page[-1]["updateTimestamp"])


def daily(snaps):
    df = pd.DataFrame(snaps).astype(float)
    df["day"] = (df["updateTimestamp"] // 86400).astype(int)
    last = df.groupby("day").last()
    out = []
    for d in range(int(last.index.min()) + 1, int(last.index.max()) + 1):
        prev = last[last.index < d]
        cur = last[last.index <= d]
        if prev.empty:
            continue
        a, z = prev.iloc[-1], cur.iloc[-1]
        dt = z["updateTimestamp"] - a["updateTimestamp"]
        if dt <= 0:
            continue
        out.append({"date": time.strftime("%Y-%m-%d", time.gmtime(d * 86400)),
                    "s": (z["supplyIndex"] / a["supplyIndex"] - 1) * YEAR / dt * 100,
                    "b": (z["borrowIndex"] / a["borrowIndex"] - 1) * YEAR / dt * 100})
    return pd.DataFrame(out)


def main():
    toks = gql("{ tokens(first:100){ id symbol decimals marketId riskInfo{ marginPremium liquidationRewardPremium } totalPar{ supplyPar borrowPar } } }")["tokens"]
    by_sym = {t["symbol"]: t for t in toks}
    since = int(time.time()) - 400 * 86400
    frames = {}
    for sym in ("USD1", "USDC"):
        frames[sym] = daily(snapshots(by_sym[sym]["id"], since)).rename(columns={"s": f"{sym.lower()}_supply_base", "b": f"{sym.lower()}_borrow"})
        print(f"  {sym}: {len(frames[sym])} days", flush=True)
    rates = frames["USD1"].merge(frames["USDC"], on="date")
    for sym, pid in LLAMA.items():
        rows = requests.get(f"https://yields.llama.fi/chart/{pid}", timeout=90).json()["data"]
        rw = pd.DataFrame([{"date": r["timestamp"][:10], f"{sym.lower()}_wlfi_reward": r.get("apyReward") or 0,
                            f"{sym.lower()}_tvl_defillama": r.get("tvlUsd")} for r in rows])
        rates = rates.merge(rw, on="date", how="left")
    rates = rates.fillna({"usd1_wlfi_reward": 0, "usdc_wlfi_reward": 0})
    save_csv(rates, "c21_rates_daily.csv")

    mk = {}
    for t in toks:
        m, d = int(t["marketId"]), int(t["decimals"])
        price = call(SEL["price"], m)[0] / 10 ** (36 - d)
        bi, si = [x / 1e18 for x in call(SEL["index"], m)[:2]]
        mk[m] = dict(sym=t["symbol"], price=price, bi=bi, si=si, prem=float((t["riskInfo"] or {}).get("marginPremium") or 0),
                     liqprem=float((t["riskInfo"] or {}).get("liquidationRewardPremium") or 0), tp=t["totalPar"] or {})
    snap = []
    for m, v in mk.items():
        if v["sym"] not in ("USD1", "USDC", "WLFI", "WLFIcx", "WETH"):
            continue
        sup = float(v["tp"].get("supplyPar") or 0) * v["si"] * v["price"]
        bor = float(v["tp"].get("borrowPar") or 0) * v["bi"] * v["price"]
        snap.append(dict(market_id=m, symbol=v["sym"], price=v["price"], supply_usd=sup, borrow_usd=bor,
                         utilization=bor / sup if sup else 0, margin_premium=v["prem"], liq_reward_premium=v["liqprem"]))
    save_csv(pd.DataFrame(snap), "dolomite_markets_snapshot.csv")

    accs, last = [], ""
    while True:
        page = gql('{ marginAccounts(first:1000, orderBy:id, where:{hasBorrowValue:true, id_gt:"%s"}){ id effectiveUser{id} tokenValues(first:32){ token{marketId} valuePar } } }' % last)["marginAccounts"]
        accs += page
        if len(page) < 1000:
            break
        last = page[-1]["id"]
    rows = []
    for a in accs:
        sup, bor = {}, {}
        for tv in a["tokenValues"]:
            m, par = int(tv["token"]["marketId"]), float(tv["valuePar"])
            if par > 0:
                sup[m] = par * mk[m]["si"] * mk[m]["price"]
            elif par < 0:
                bor[m] = -par * mk[m]["bi"] * mk[m]["price"]
        s_sym = {mk[m]["sym"]: v for m, v in sup.items()}
        if not bor or not (s_sym.get("WLFI", 0) + s_sym.get("WLFIcx", 0)):
            continue
        b_sym = {mk[m]["sym"]: v for m, v in bor.items()}
        rows.append(dict(owner=a["effectiveUser"]["id"], account=a["id"],
                         wlfi_collateral_usd=s_sym.get("WLFI", 0), wlfics_collateral_usd=s_sym.get("WLFIcx", 0),
                         other_collateral_usd=sum(v for k, v in s_sym.items() if k not in WL),
                         usd1_debt_usd=b_sym.get("USD1", 0), usdc_debt_usd=b_sym.get("USDC", 0),
                         other_debt_usd=sum(v for k, v in b_sym.items() if k not in ("USD1", "USDC")),
                         adj_wlfi=sum(v / (1 + mk[m]["prem"]) for m, v in sup.items() if mk[m]["sym"] in WL),
                         adj_other=sum(v / (1 + mk[m]["prem"]) for m, v in sup.items() if mk[m]["sym"] not in WL),
                         adj_debt=sum(v * (1 + mk[m]["prem"]) for m, v in bor.items())))
    save_csv(pd.DataFrame(rows).sort_values("usd1_debt_usd", ascending=False), "c21_wlfi_positions.csv")


if __name__ == "__main__":
    main()
