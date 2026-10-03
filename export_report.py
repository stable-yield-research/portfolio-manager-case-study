"""Export every page of the app, as rendered, to one Markdown file (and optionally a PDF).

Usage (from the repo root):
    Markdown only:  uv run --with-requirements requirements.txt --with tabulate python export_report.py
    Markdown + PDF: uv run --with-requirements requirements.txt --with tabulate --with markdown --with playwright python export_report.py --pdf
                    (first time only: uv run --with playwright playwright install chromium)
Output: export/stablecoin_carry_report_full.md, export/stablecoin_carry_report_full.pdf
"""

import json
import os
import re
import sys
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import project_config as cfg  # noqa: E402

OUT = ROOT / "export"
OUT.mkdir(exist_ok=True)


def clean(text: str) -> str:
    text = str(text).replace("\\$", "$")
    text = re.sub(r"<div[^>]*>(.*?)</div>", r"\1", text, flags=re.S)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def table_md(df: pd.DataFrame) -> str:
    df = df.copy()
    df.columns = [clean(c) for c in df.columns]
    for c in df.columns:
        df[c] = df[c].map(lambda v: clean(v).replace("\n", " ") if isinstance(v, str) else v)
    return df.to_markdown(index=False)


def _decode(v):
    """Plotly 6 stores numeric arrays as {'dtype', 'bdata'} (base64)."""
    if isinstance(v, dict) and "bdata" in v:
        import base64
        import numpy as np
        arr = np.frombuffer(base64.b64decode(v["bdata"]), dtype=np.dtype(v.get("dtype", "f8")))
        if "shape" in v:
            arr = arr.reshape([int(x) for x in str(v["shape"]).split(",")])
        return arr.tolist()
    return v


def chart_md(proto) -> str:
    try:
        spec = json.loads(proto.spec)
    except Exception:
        return "_Chart (data not readable)_"
    layout = spec.get("layout", {})
    title = layout.get("title", {})
    title = title.get("text") if isinstance(title, dict) else title
    lines = [f"**Chart: {clean(title or 'untitled')}**"]
    for tr in spec.get("data", []):
        name = tr.get("name") or tr.get("type", "series")
        x, y = _decode(tr.get("x")), _decode(tr.get("y"))
        if tr.get("type") == "histogram" and isinstance(x, list) and y is None:
            vals = sorted(v for v in x if isinstance(v, (int, float)))
            q = lambda p: round(vals[int(p * (len(vals) - 1))], 2)
            lines.append(f"- {name}: distribution of {len(vals)} values; min {q(0)}, 5th percentile {q(0.05)}, median {q(0.5)}, "
                         f"95th percentile {q(0.95)}, max {q(1)}")
            continue
        if y is not None and x is None:
            x = list(range(len(y)))
        if isinstance(x, dict) or isinstance(y, dict) or x is None or y is None:
            lines.append(f"- {name}: data in binary form, not shown")
            continue
        if len(x) <= 40:
            pts = ", ".join(f"{a}: {round(b, 3) if isinstance(b, (int, float)) else b}" for a, b in zip(x, y))
            lines.append(f"- {name}: {pts}")
        else:
            ys = [v for v in y if isinstance(v, (int, float))]
            lines.append(f"- {name}: {len(x)} points from {str(x[0])[:10]} to {str(x[-1])[:10]}; first {round(ys[0], 3)}, last {round(ys[-1], 3)}, "
                         f"min {round(min(ys), 3)}, max {round(max(ys), 3)}, mean {round(sum(ys) / len(ys), 3)}")
    return lines[0] + "\n\n" + "\n".join(lines[1:])


def walk(node, out, depth=0):
    """Walk the rendered element tree in on-screen order."""
    t = getattr(node, "type", None)
    if t in ("main", "sidebar", "vertical", "horizontal", "column", "container", "expander", "form", "flex_container") \
            or t is None and hasattr(node, "children"):
        if t == "expander":
            out.append(f"\n**{clean(getattr(node, 'label', ''))}**\n")
        for child in node.children.values():
            walk(child, out, depth)
        return
    if t == "tab_container":
        for tab in node.children.values():
            out.append(f"\n#### Tab: {clean(tab.label)}\n")
            for child in tab.children.values():
                walk(child, out, depth)
        return
    if t == "tab":
        out.append(f"\n#### Tab: {clean(node.label)}\n")
        for child in node.children.values():
            walk(child, out, depth)
        return
    try:
        if t == "title":
            out.append(f"\n# {clean(node.value)}\n")
        elif t == "header":
            out.append(f"\n## {clean(node.value)}\n")
        elif t == "subheader":
            out.append(f"\n### {clean(node.value)}\n")
        elif t == "markdown":
            v = clean(node.value)
            if v:
                out.append(v + "\n")
        elif t == "caption":
            out.append(f"_{clean(node.value)}_\n")
        elif t in ("info", "warning", "error", "success"):
            out.append(f"> {clean(node.value)}\n")
        elif t == "metric":
            out.append(f"- **{clean(node.label)}:** {clean(node.value)}"
                       + (f" ({clean(node.proto.help)})" if node.proto.help else "") + "\n")
        elif t in ("arrow_data_frame", "dataframe", "table", "arrow_table"):
            out.append(table_md(node.value) + "\n")
        elif t == "plotly_chart":
            out.append(chart_md(node.proto) + "\n")
        elif t in ("slider", "select_slider", "selectbox", "radio", "number_input", "multiselect", "checkbox", "toggle", "text_input"):
            out.append(f"_Control: {clean(node.label)} = {node.value} (default)_\n")
        elif t == "button":
            pass
        elif hasattr(node, "children"):
            for child in node.children.values():
                walk(child, out, depth)
    except Exception as e:  # keep going on any odd element
        out.append(f"_({t} not exported: {e})_\n")


def slug(text: str) -> str:
    """Same anchor rule Streamlit uses for headings."""
    return re.sub(r"[^a-z0-9]+", "-", clean(text).lower()).strip("-")


def plain(md: str) -> str:
    t = re.sub(r"<[^>]+>", " ", md)
    t = re.sub(r"[*_`#>|]", " ", t)
    t = re.sub(r":?-{3,}:?", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def main():
    index, toc, pages_md = [], [], []
    group = None
    for p in cfg.PAGES:
        if p["module"] == "contents":
            continue
        at = AppTest.from_string(
            f"import sys,os; sys.path.insert(0,{str(ROOT)!r}); os.chdir({str(ROOT)!r})\n"
            f"from sections.{p['module']} import render\nrender()", default_timeout=300)
        at.run()
        out = []
        walk(at.main, out)
        page_md = "\n".join(out)
        # split into sections at subheadings (### ) and tabs (#### Tab:)
        sections, cur = [], {"section": "Overview", "anchor": None, "lines": []}
        lines_out = []
        for line in page_md.split("\n"):
            m = re.match(r"^(###|####) (Tab: )?(.+)$", line)
            if m and not line.startswith("# "):
                sections.append(cur)
                name = (m.group(2) or "") + m.group(3).strip()
                anchor = None if m.group(2) else slug(m.group(3))
                cur = {"section": name, "anchor": anchor, "lines": []}
                lines_out.append(f'<a id="{p["url"]}--{slug(name)}"></a>')
            cur["lines"].append(line)
            lines_out.append(line)
        sections.append(cur)
        for sec in sections:
            text = plain("\n".join(sec["lines"]))
            if len(text) > 20:
                index.append({"group": p["group"], "page": p["title"], "url": p["url"], "section": sec["section"],
                              "anchor": sec["anchor"], "text": text})
        if p["group"] != group:
            group = p["group"]
            toc.append(f"\n**{group}**\n")
            pages_md.append(f"\n---\n\n# Section: {group}\n")
        toc.append(f"- [{p['title']}](#{p['url']}) - {p.get('desc', '')}")
        for sec in sections[1:]:
            toc.append(f"    - [{sec['section']}](#{p['url']}--{slug(sec['section'])})")
        pages_md.append(f'\n---\n\n<a id="{p["url"]}"></a>\n' + "\n".join(lines_out))
        print("exported", p["module"])
    head = ["# Stablecoin Carry on Current Finance: full report\n",
            "Full text export of the interactive report: every page, table, metric and chart data series, in page order. "
            "Interactive controls are shown at their default values.\n", "## Contents\n", "\n".join(toc)]
    md = re.sub(r"\n{3,}", "\n\n", "\n".join(head + pages_md))
    (OUT / "stablecoin_carry_report_full.md").write_text(md)
    (ROOT / "data" / "search_index.json").write_text(json.dumps(index, ensure_ascii=False))
    print("written", OUT / "stablecoin_carry_report_full.md", len(md), "characters;", len(index), "searchable sections")


def to_pdf():
    """Render the Markdown export to a PDF (landscape A4) with headless Chromium."""
    import asyncio

    import markdown
    from playwright.async_api import async_playwright

    md = (OUT / "stablecoin_carry_report_full.md").read_text()
    body = markdown.markdown(md, extensions=["tables", "sane_lists"])
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
      @page {{ size: A4 landscape; margin: 14mm 12mm; }}
      body {{ font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; font-size: 9.5pt; line-height: 1.45; color: #1d1d1f; }}
      h1 {{ font-size: 17pt; margin: 18px 0 6px; }} h2 {{ font-size: 13pt; }} h3 {{ font-size: 11pt; margin: 14px 0 4px; text-transform: uppercase;
      letter-spacing: .04em; color: #0b3d5c; }} h4 {{ font-size: 10pt; margin: 12px 0 4px; color: #0b3d5c; }}
      table {{ border-collapse: collapse; width: 100%; margin: 6px 0 10px; font-size: 8pt; }}
      th, td {{ border: 1px solid #d0d4d9; padding: 3px 5px; vertical-align: top; text-align: left; word-break: break-word; }}
      th {{ background: #eef2f5; }} blockquote {{ border-left: 3px solid #0b3d5c; margin: 6px 0; padding: 2px 10px; background: #f5f8fa; }}
      hr {{ border: 0; border-top: 1px solid #c8cdd2; margin: 18px 0; }} em {{ color: #555; }}
    </style></head><body>{body}</body></html>"""
    (OUT / "stablecoin_carry_report_full.html").write_text(html)

    async def run():
        async with async_playwright() as p:
            b = await p.chromium.launch()
            pg = await b.new_page()
            await pg.goto((OUT / "stablecoin_carry_report_full.html").as_uri())
            await pg.pdf(path=str(OUT / "stablecoin_carry_report_full.pdf"), format="A4", landscape=True, print_background=True,
                         margin={"top": "14mm", "bottom": "14mm", "left": "12mm", "right": "12mm"})
            await b.close()

    asyncio.run(run())
    print("written", OUT / "stablecoin_carry_report_full.pdf")


if __name__ == "__main__":
    main()
    if "--pdf" in sys.argv:
        to_pdf()
