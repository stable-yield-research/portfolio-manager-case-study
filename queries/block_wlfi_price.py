"""Block: WLFI daily close and low from the Hyperliquid info API. Writes wlfi_price_daily.csv."""
import time
import pandas as pd
import requests
from graphql_client import save_csv

c = requests.post("https://api.hyperliquid.xyz/info", json={"type": "candleSnapshot", "req": {
    "coin": "WLFI", "interval": "1d", "startTime": int((time.time() - 500 * 86400) * 1000), "endTime": int(time.time() * 1000)}},
    timeout=60).json()
save_csv(pd.DataFrame([{"date": time.strftime("%Y-%m-%d", time.gmtime(x["t"] / 1000)), "close": float(x["c"]), "low": float(x["l"])}
                       for x in c]), "wlfi_price_daily.csv")
