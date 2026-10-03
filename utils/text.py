"""All report prose comes from content/report.md. T("key", **numbers) returns the block with {placeholders} filled."""

from pathlib import Path

import streamlit as st

PATH = Path(__file__).resolve().parent.parent / "content" / "report.md"


@st.cache_data(show_spinner=False)
def _blocks(mtime: float) -> dict:
    text = PATH.read_text(encoding="utf-8")
    if "-->" in text:
        text = text.split("-->", 1)[1]
    out, key, buf = {}, None, []
    for line in text.splitlines():
        if line.startswith("## "):
            if key:
                out[key] = "\n".join(buf).strip()
            key, buf = line[3:].strip(), []
        else:
            buf.append(line)
    if key:
        out[key] = "\n".join(buf).strip()
    return out


class _Safe(dict):
    def __missing__(self, k):
        return "{" + k + "}"


def T(key: str, **nums) -> str:
    blocks = _blocks(PATH.stat().st_mtime)
    s = blocks.get(key, f"[missing text: {key}]")
    return s.format_map(_Safe(nums)) if nums else s
