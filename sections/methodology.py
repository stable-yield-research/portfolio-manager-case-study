"""
Data & Methodology: provenance, freshness, and a pipeline runner.

Reviewers trust numbers they can trace. This page says where each headline
figure comes from and whether it is pinned or live.
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from utils.text import T

import project_config as cfg
from utils.data_loader import data_file_status

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNNER = REPO_ROOT / "queries" / "runner.py"
TIMEOUT_S = 1800  # slow API blocks need this; 600 was not enough last time


def _run(blocks: list[str], log):
    cmd = [sys.executable, "-u", str(RUNNER)] + blocks   # -u: unbuffered, lines stream live
    buf = []
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1, cwd=str(REPO_ROOT))
    try:
        for line in proc.stdout:
            buf.append(line.rstrip("\n"))
            log.code("\n".join(buf[-80:]), language="text")
        proc.wait(timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        proc.kill()
        buf.append(f"Timed out after {TIMEOUT_S // 60} minutes.")
        log.code("\n".join(buf[-80:]), language="text")
        return False
    return proc.returncode == 0


def render():
    st.markdown('<div class="eyebrow">Process</div>', unsafe_allow_html=True)
    st.title("Data Sources and Methods")
    st.subheader("Data sources")
    st.markdown(T("method.sources"))
    st.caption(T("method.files_note"))

    st.subheader("Disclosure")
    st.markdown(T("report.disclosure"))

    st.subheader("Assumptions")
    st.markdown(T("method.assumptions"))

    st.subheader("AI use")
    st.markdown(T("method.ai_use"))

    st.subheader("Data freshness")
    st.info(T("method.freshness"))
    st.dataframe(pd.DataFrame([x for x in cfg.METRIC_SOURCES if x["source"].startswith(("current", "editorial"))]).rename(columns=str.title),
                 hide_index=True, width="stretch")

    st.subheader("Data files")
    st.dataframe(data_file_status()[lambda d: d.iloc[:, 0].astype(str).str.contains("current|candidates|gates|pipeline|risk_controls|monitoring|ai_use", regex=True)], hide_index=True, width="stretch")

    st.subheader("Data refresh")
    st.caption("Runs the query scripts and rewrites the data files. On Streamlit Cloud, refreshed files last until the app restarts.")
    blocks = st.multiselect("Blocks", ["current"], default=["current"])
    if st.button("Run", type="primary"):
        log = st.empty()
        ok = _run(blocks, log)
        st.cache_data.clear()
        (st.success if ok else st.error)("Pipeline finished." if ok else "Pipeline failed. See log.")
