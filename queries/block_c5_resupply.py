"""Block: Proposal 2 history from DefiLlama. Stake DAO reUSD/scrvUSD vault, Curve pool TVL, Resupply crvUSD lending
(WBTC market), reUSD price. Writes c5_daily.csv."""
import time
import pandas as pd
import requests
from graphql_client import save_csv

REUSD = "0x57aB1E0003F623289CD798B1824Be09a793e4Bec"


def chart(pid):
    return pd.DataFrame(requests.get(f"https://yields.llama.fi/chart/{pid}", timeout=90).json()["data"]).assign(
        date=lambda d: d["timestamp"].str[:10])


lp = chart("321b0f91-21ca-438b-966e-78946e275589")[["date", "apyBase", "apyReward", "tvlUsd"]].rename(
    columns={"apyBase": "lp_base", "apyReward": "lp_reward", "tvlUsd": "stakedao_tvl"})
pool = chart("5c4940c7-c193-440d-b95e-9148d017e12c")[["date", "tvlUsd"]].rename(columns={"tvlUsd": "pool_tvl"})
col = chart("15a38ed8-75f4-4487-8825-7622ba82fb45")[["date", "apy"]].rename(columns={"apy": "collateral_lend_apy"})
start = int(time.time()) - 366 * 86400
pts = requests.get(f"https://coins.llama.fi/chart/ethereum:{REUSD}?start={start}&span=366&period=1d", timeout=90).json()
px = pd.DataFrame(pts["coins"][f"ethereum:{REUSD}"]["prices"])
px["date"] = px["timestamp"].apply(lambda t: time.strftime("%Y-%m-%d", time.gmtime(t)))
out = lp.merge(pool, on="date").merge(col, on="date").merge(px[["date", "price"]].rename(columns={"price": "reusd_price"}), on="date")
save_csv(out.fillna(0), "c5_daily.csv")
