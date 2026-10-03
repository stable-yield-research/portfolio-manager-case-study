"""Refresh control for pages that show live Current Finance data."""

import subprocess
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent


def _last_date():
    try:
        d = pd.read_csv(ROOT / "data" / "current_daily.csv", usecols=[0])
        return str(d.iloc[-1, 0])[:10]
    except Exception:
        return "unknown"


def refresh_control(key: str):
    """A compact 'Refresh live data' button with the data date beside it."""
    c1, c2 = st.columns([5, 2])
    c1.caption(f"Live rates from Current Finance's API, latest day: {_last_date()}")
    if c2.button("Refresh live data", key=f"refresh_{key}", icon=":material/refresh:", type="secondary",
                 help="Pulls the latest rates, utilization and supply from Current Finance (about 15 seconds).",
                 width="stretch"):
        with st.spinner("Pulling the latest data from Current Finance..."):
            r = subprocess.run([sys.executable, str(ROOT / "queries" / "runner.py"), "current"], cwd=ROOT,
                               capture_output=True, text=True, timeout=180)
        if r.returncode == 0:
            st.cache_data.clear()
            st.toast("Live data updated.", icon=":material/check_circle:")
            st.rerun()
        else:
            st.error("Refresh failed; the pinned data is still shown. " + (r.stderr or r.stdout)[-300:])
