"""
Centralized data loading.

Rules that saved time last project:
  * Every page loads through here. Never pd.read_csv inside a section.
  * .csv.gz is read transparently (GitHub rejects files over 100 MB).
  * Normalization happens once, at load time (chain names, column aliases).
  * Missing file -> empty DataFrame. Sections must handle empty data.
  * No fake or generated data. Editorial files (timeline) are the only exception.
"""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

import project_config as cfg

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Column aliases: different query scripts sometimes name the same field differently
COLUMN_ALIASES = {
    "blockchain": "chain",
    "network": "chain",
}


def _resolve(filename: str) -> Path | None:
    """Return the existing path for filename, preferring .csv.gz."""
    gz = DATA_DIR / (filename if filename.endswith(".gz") else filename + ".gz")
    plain = DATA_DIR / filename.removesuffix(".gz")
    if gz.exists():
        return gz
    if plain.exists():
        return plain
    return None


def _read(filename: str) -> pd.DataFrame:
    path = _resolve(filename)
    if path is None:
        return pd.DataFrame()
    df = pd.read_csv(path, compression="gzip" if path.suffix == ".gz" else None)

    for old, new in COLUMN_ALIASES.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})
    if "chain" in df.columns:
        df["chain"] = df["chain"].astype(str).str.title()
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def load_csv(filename: str) -> pd.DataFrame:
    return _read(filename)


def show_data_warnings():
    missing = [f for f in cfg.EXPECTED_FILES if _resolve(f) is None]
    if missing:
        st.sidebar.warning(
            f"Missing data files: {', '.join(missing)}. "
            "Run the query pipeline on the Data & Methodology page."
        )


def data_file_status() -> pd.DataFrame:
    """One row per expected file: present, size, last modified."""
    rows = []
    for f in cfg.EXPECTED_FILES:
        p = _resolve(f)
        if p is None:
            rows.append({"file": f, "status": "missing", "size": "-", "modified": "-"})
            continue
        mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        rows.append({
            "file": p.name,
            "status": "ok",
            "size": f"{p.stat().st_size / 1024:,.0f} KB",
            "modified": mtime.strftime("%Y-%m-%d %H:%M UTC"),
        })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════
#  Loaders: one per logical dataset. Add yours below.
# ═══════════════════════════════════════════════════════════════

def load_markets_snapshot() -> pd.DataFrame:
    """CURRENT state. Drifts between runs."""
    df = load_csv("block1_markets_snapshot.csv")
    if df.empty:
        return df
    df["market_label"] = df["collateral_symbol"].fillna("?") + "/" + df["loan_symbol"].fillna("?")
    return df


def load_market_history() -> pd.DataFrame:
    """Daily history. Use for PINNED figures."""
    df = load_csv("block1_market_history.csv")
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["timestamp"], unit="s", utc=True).dt.tz_localize(None)
    return df


def load_value_at_pin(df: pd.DataFrame, value_col: str, key_col: str = "market_id") -> pd.DataFrame:
    """Latest row at or before PIN_TIMESTAMP, per key. The standard way to pin a figure."""
    if df.empty:
        return df
    before = df[df["timestamp"] <= cfg.PIN_TIMESTAMP]
    return before.sort_values("timestamp").groupby(key_col, as_index=False).last()[[key_col, value_col]]


def load_timeline() -> pd.DataFrame:
    """Editorial, hand-written."""
    df = load_csv("timeline_events.csv")
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


# ── Case study loaders ──────────────────────────────────────────
def load_c21_rates() -> pd.DataFrame:
    """Daily realized Dolomite rates (%) and WLFI reward APR (%). PINNED history."""
    return load_csv("c21_rates_daily.csv")


def load_wlfi() -> pd.DataFrame:
    return load_csv("wlfi_price_daily.csv")


def load_positions() -> pd.DataFrame:
    return load_csv("c21_wlfi_positions.csv")


def load_dolomite_snapshot() -> pd.DataFrame:
    return load_csv("dolomite_markets_snapshot.csv")


def load_c5() -> pd.DataFrame:
    return load_csv("c5_daily.csv")


def load_editorial(name: str) -> pd.DataFrame:
    """candidates, gates, risk_map_c21, risk_map_c5, monitoring_triggers, pipeline, ai_use_log."""
    return load_csv(f"{name}.csv")


def load_resupply_snapshot() -> pd.DataFrame:
    return load_csv("resupply_curve_snapshot.csv")


def load_wlfi_venues() -> pd.DataFrame:
    return load_csv("wlfi_liquidity_venues.csv")


def load_current() -> pd.DataFrame:
    """Current Main Market daily history (USDC c_, USDSUI s_): rates %, utilization, supplied/borrowed $M, SUI rewards %."""
    d = load_csv("current_daily.csv")
    if not d.empty:
        d = d.rename(columns={d.columns[0]: "date"})
        d = d[d["date"] >= "2026-04-16"].reset_index(drop=True)
    return d


def load_current_snapshot() -> pd.DataFrame:
    return load_csv("current_snapshot.csv")


def latest_data_date() -> str:
    """Last day in the Current Finance history, formatted like '2 October 2026'."""
    import pandas as pd
    try:
        d = pd.read_csv(Path(__file__).resolve().parent.parent / "data" / "current_daily.csv", usecols=[0])
        return pd.to_datetime(d.iloc[-1, 0]).strftime("%-d %B %Y")
    except Exception:
        return "the latest refresh"
