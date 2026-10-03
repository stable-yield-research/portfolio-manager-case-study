"""
Chart helpers and number formatting.

Rules that saved time last project:
  * Every chart goes through apply_layout() so the look is consistent.
  * Every time series gets event_lines() so readers see the event on every chart.
  * Use md_usd() inside st.markdown / st.info / st.error: a bare "$" pair renders as LaTeX.
  * Pre-format table columns as strings before st.dataframe: no raw floats in tables.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import project_config as cfg

BG = "#FFFEF8"
GRID = "rgba(30,59,112,0.08)"
TEXT = "#1C1C1C"
ACCENT = "#1E3B70"
RED = "#B91C1C"
GREEN = "#00736B"
ORANGE = "#B45309"
GREY = "#A8A9AB"
TEAL = "#00BBA0"
NAVY = "#1E3B70"
FONT = "Fira Sans, Helvetica Neue, sans-serif"


def apply_layout(fig, title=None, height=400, show_legend=True):
    fig.update_layout(
        title=dict(text=title or "", font=dict(size=15, color=NAVY, family="Barlow Condensed, Arial Narrow, sans-serif")),
        colorway=[NAVY, TEAL, GREY, "#00736B", "#B45309"],
        plot_bgcolor=BG, paper_bgcolor=BG,
        font=dict(color=TEXT, size=11, family=FONT),
        height=height,
        margin=dict(l=40, r=20, t=48 if title else 20, b=60),
        showlegend=show_legend,
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="top", y=-0.12, x=0),
        xaxis=dict(gridcolor=GRID, zeroline=False),
        yaxis=dict(gridcolor=GRID, zeroline=False),
    )
    return fig


def event_lines(fig):
    """Dashed vertical line + label for each entry in cfg.EVENT_MARKERS."""
    for i, (date, label, color) in enumerate(cfg.EVENT_MARKERS):
        x = pd.Timestamp(date)
        fig.add_vline(x=x, line_dash="dash", line_color=color, opacity=0.5)
        fig.add_annotation(x=x, y=1, yref="paper", text=label, showarrow=False,
                           font=dict(size=10, color=color), yshift=14 - 20 * (i % 2))
    return fig


def time_series(df, x, y, color=None, title=None, height=400):
    fig = px.line(df, x=x, y=y, color=color)
    return event_lines(apply_layout(fig, title=title, height=height))


def bar_chart(df, x, y, color=None, title=None, height=400, horizontal=False, text=None):
    if horizontal:
        fig = px.bar(df, y=x, x=y, color=color, orientation="h", text=text)
    else:
        fig = px.bar(df, x=x, y=y, color=color, text=text)
    fig = apply_layout(fig, title=title, height=height)
    if text:
        fig.update_traces(textposition="outside", textfont_size=10)
    return fig


def donut_chart(values, names, title=None, height=350, colors=None):
    fig = go.Figure(go.Pie(values=values, labels=names, hole=0.55, marker_colors=colors,
                           textinfo="label+percent", textposition="outside"))
    return apply_layout(fig, title=title, height=height, show_legend=False)


# ── Number formatting ───────────────────────────────────────────

def format_usd(value) -> str:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "-"
    if abs(v) >= 1_000_000_000:
        return f"${v / 1_000_000_000:,.1f}B"
    if abs(v) >= 1_000_000:
        return f"${v / 1_000_000:,.1f}M"
    if abs(v) >= 1_000:
        return f"${v / 1_000:,.1f}K"
    return f"${v:,.2f}"


def md_usd(value) -> str:
    """format_usd with escaped $ for st.markdown, st.info, st.warning, st.error."""
    return format_usd(value).replace("$", r"\$")


def format_pct(value, decimals=1) -> str:
    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except (TypeError, ValueError):
        return "-"


def fmt_cols(df: pd.DataFrame, usd=(), pct=(), title_case=()) -> pd.DataFrame:
    """Return a display copy with columns pre-formatted as strings."""
    out = df.copy()
    for c in usd:
        if c in out:
            out[c] = pd.to_numeric(out[c], errors="coerce").apply(format_usd)
    for c in pct:
        if c in out:
            out[c] = pd.to_numeric(out[c], errors="coerce").apply(format_pct)
    for c in title_case:
        if c in out:
            out[c] = out[c].astype(str).str.title()
    return out
