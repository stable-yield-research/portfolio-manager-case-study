"""
Shared GraphQL client for query blocks.

  gql(query, variables)         -> data dict, retries on 429 / 5xx
  paginate(query, path, ...)    -> all items across first/skip pages
  save_csv(df, name, gzip=None) -> data/<name>[.gz]; auto-gzips files over 50 MB
"""

import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
import project_config as cfg  # noqa: E402

DATA_DIR = REPO_ROOT / "data"
API_URL = os.environ.get("GRAPHQL_URL", cfg.API_URL)
REQUEST_DELAY = float(os.environ.get("REQUEST_DELAY", "0.3"))
GZIP_THRESHOLD_BYTES = 50 * 1024 * 1024


def gql(query: str, variables: dict | None = None, retries: int = 5) -> dict:
    for attempt in range(retries):
        try:
            r = requests.post(API_URL, json={"query": query, "variables": variables or {}}, timeout=60)
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"HTTP {r.status_code}")
            body = r.json()
            if body.get("errors"):
                raise RuntimeError(body["errors"][0].get("message", body["errors"]))
            time.sleep(REQUEST_DELAY)
            return body["data"]
        except (requests.RequestException, requests.HTTPError) as e:
            wait = 2 ** attempt
            print(f"  retry {attempt + 1}/{retries} in {wait}s ({e})", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"GraphQL request failed after {retries} attempts")


def paginate(query: str, path: list[str], variables: dict | None = None,
             page_size: int = 100, max_pages: int = 200) -> list[dict]:
    """path = keys to the list container, e.g. ["markets"]; expects .items and .pageInfo."""
    items, skip = [], 0
    for _ in range(max_pages):
        data = gql(query, {**(variables or {}), "first": page_size, "skip": skip})
        node = data
        for k in path:
            node = node[k]
        batch = node.get("items") or []
        items.extend(batch)
        total = (node.get("pageInfo") or {}).get("countTotal")
        skip += page_size
        if not batch or (total is not None and skip >= total):
            break
    return items


def save_csv(df: pd.DataFrame, name: str, gzip: bool | None = None) -> Path:
    """Write to data/. Removes the stale twin (.csv vs .csv.gz) so the loader never reads old data."""
    DATA_DIR.mkdir(exist_ok=True)
    name = name.removesuffix(".gz")
    plain, gz = DATA_DIR / name, DATA_DIR / (name + ".gz")
    if gzip is None:
        gzip = df.memory_usage(deep=True).sum() > GZIP_THRESHOLD_BYTES
    target, stale = (gz, plain) if gzip else (plain, gz)
    df.to_csv(target, index=False, compression="gzip" if gzip else None)
    stale.unlink(missing_ok=True)
    print(f"  wrote {target.relative_to(REPO_ROOT)} ({len(df):,} rows)", flush=True)
    return target
