"""
Export rendered dashboard text: everything a visitor sees, minus graphics.

Why: reviewing one text file catches wrong numbers, raw floats, em dashes,
lowercase labels and cross-page inconsistencies far faster than clicking around.

Usage (dashboard must be running):
    cd <repo> && uv run --with playwright python -m playwright install chromium
    cd <repo> && uv run --with playwright python utils/export_dashboard_text.py
Then:
    cd <repo> && python3 utils/audit_export.py

Output: data/dashboard_full_text.md
"""

import asyncio
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import project_config as cfg  # noqa: E402

BASE_URL = os.environ.get("DASHBOARD_URL", "http://localhost:8501")
PAGES = [(p["title"], "/" + p["url"]) for p in cfg.PAGES]
OUTPUT_FILE = "data/dashboard_full_text.md"


# ── Helper: extract structured content from a Streamlit page ──────────────
EXTRACT_JS = """
() => {
    const result = { sections: [], metrics: [], charts: [], tables: [] };

    // Target ONLY the main content block (excludes sidebar nav)
    const main = document.querySelector('[data-testid="stMainBlockContainer"]')
                 || document.querySelector('[data-testid="stAppViewContainer"]');
    if (!main) return result;

    // Material icon names to skip
    const iconNames = new Set([
        'keyboard_arrow_down', 'keyboard_arrow_up', 'keyboard_arrow_right',
        'keyboard_arrow_left', 'expand_more', 'expand_less', 'chevron_right',
        'check_circle', 'info', 'warning', 'error', 'close', 'menu'
    ]);

    // ── 1. Structured text: headings, paragraphs, captions, alerts ──
    // Process captions/containers BEFORE their children to avoid duplication.
    // Mark parent text as seen, so individual child items are skipped.
    const textSelectors = [
        'h1', 'h2', 'h3', 'h4',
        '[data-testid="stCaptionContainer"]',
        '[data-testid="stAlert"] p',
        '[data-testid="stExpander"] summary',
        '[data-testid="stMarkdown"] p',
        '[data-testid="stMarkdown"] li',
        '[data-testid="stMarkdown"] blockquote',
        '[data-testid="stExpander"] [data-testid="stMarkdown"] p',
    ];
    const seen = new Set();
    // Track parent elements to skip their children
    const capturedParents = [];
    for (const sel of textSelectors) {
        main.querySelectorAll(sel).forEach(el => {
            // Skip elements not visible
            const rect = el.getBoundingClientRect();
            if (rect.width === 0 && rect.height === 0) return;

            // Skip if this element is a child of an already-captured container
            if (capturedParents.some(p => p.contains(el) && p !== el)) return;

            let text = el.innerText?.trim();
            if (!text || text.length < 2) return;
            // Strip leading material icon names (they appear as text prefix in expander summaries)
            for (const icon of iconNames) {
                if (text.toLowerCase().startsWith(icon)) {
                    text = text.substring(icon.length).trim();
                    break;
                }
            }
            // Skip if nothing remains after stripping icon
            if (!text || text.length < 2) return;
            // Deduplicate (use full text for short items, prefix for long)
            const key = text.length < 120 ? text : text.substring(0, 80);
            if (seen.has(key)) return;
            seen.add(key);

            // Track this element so we skip its children later
            if (el.matches('[data-testid="stCaptionContainer"]')) {
                capturedParents.push(el);
            }

            const tag = el.tagName?.toLowerCase() || '';
            let type = 'text';
            if (tag.startsWith('h')) type = tag;
            else if (el.closest('[data-testid="stCaptionContainer"]')) type = 'caption';
            else if (el.closest('[data-testid="stAlert"]')) type = 'alert';

            result.sections.push({ type, text });
        });
    }

    // ── 2. Metric cards ──
    main.querySelectorAll('[data-testid="stMetric"]').forEach(m => {
        const label = m.querySelector('[data-testid="stMetricLabel"]')?.innerText?.trim() || '';
        const value = m.querySelector('[data-testid="stMetricValue"]')?.innerText?.trim() || '';
        const delta = m.querySelector('[data-testid="stMetricDelta"]')?.innerText?.trim() || '';
        if (label || value) {
            result.metrics.push({ label, value, delta });
        }
    });

    // ── 3. Chart titles (Plotly) - deduplicated ──
    const chartSeen = new Set();
    main.querySelectorAll('.gtitle, .g-gtitle').forEach(el => {
        const t = el.textContent?.trim();
        if (t && !chartSeen.has(t)) {
            chartSeen.add(t);
            result.charts.push(t);
        }
    });

    // ── 4. Dataframe tables: read visible header + rows ──
    main.querySelectorAll('[data-testid="stDataFrame"]').forEach((df, idx) => {
        const table = { index: idx + 1, headers: [], rows: [] };

        // Headers: Streamlit uses role="columnheader"
        df.querySelectorAll('[role="columnheader"]').forEach(h => {
            const t = h.innerText?.trim();
            if (t) table.headers.push(t);
        });

        // Rows: Streamlit uses role="row" with role="gridcell"
        df.querySelectorAll('[role="row"]').forEach(row => {
            const cells = [];
            row.querySelectorAll('[role="gridcell"]').forEach(cell => {
                cells.push(cell.innerText?.trim() || '');
            });
            if (cells.length > 0 && cells.some(c => c.length > 0)) {
                table.rows.push(cells);
            }
        });

        // Cap at 30 rows to avoid massive output
        if (table.rows.length > 30) {
            table.rows = table.rows.slice(0, 30);
            table.truncated = true;
        }

        if (table.headers.length > 0 || table.rows.length > 0) {
            result.tables.push(table);
        }
    });

    return result;
}
"""


def format_page_content(data: dict) -> str:
    """Convert extracted structured data into clean markdown."""
    lines = []

    # Metrics as a clean block
    if data.get("metrics"):
        lines.append("### Key Metrics")
        for m in data["metrics"]:
            delta_str = f" ({m['delta']})" if m.get("delta") else ""
            lines.append(f"  **{m['label']}**: {m['value']}{delta_str}")
        lines.append("")

    # Main content sections
    if data.get("sections"):
        for s in data["sections"]:
            t = s["type"]
            text = s["text"]
            if t == "h1":
                lines.append(f"\n# {text}")
            elif t == "h2":
                lines.append(f"\n## {text}")
            elif t == "h3":
                lines.append(f"\n### {text}")
            elif t == "h4":
                lines.append(f"\n#### {text}")
            elif t == "caption":
                lines.append(f"_{text}_")
            elif t == "alert":
                lines.append(f"> **{text}**")
            else:
                lines.append(text)
            lines.append("")

    # Charts
    if data.get("charts"):
        lines.append("### Charts on this page")
        for c in data["charts"]:
            lines.append(f"  📊 {c}")
        lines.append("")

    # Tables
    if data.get("tables"):
        for t in data["tables"]:
            lines.append(f"### Table {t['index']}")
            if t.get("headers"):
                lines.append("| " + " | ".join(t["headers"]) + " |")
                lines.append("| " + " | ".join(["---"] * len(t["headers"])) + " |")
            for row in t.get("rows", []):
                lines.append("| " + " | ".join(row) + " |")
            if t.get("truncated"):
                lines.append(f"_...truncated (showing 30 of many rows)_")
            lines.append("")

    return "\n".join(lines)


async def extract_page(page, url, title, idx):
    """Navigate to page, expand everything, extract visible content only."""
    lines = []
    lines.append(f"\n{'='*80}")
    lines.append(f"PAGE {idx}: {title}")
    lines.append(f"URL: {url}")
    lines.append(f"{'='*80}\n")

    try:
        await page.goto(url, wait_until="networkidle", timeout=45000)
        await page.wait_for_timeout(4000)

        # Expand all expanders
        for _ in range(3):
            expanders = await page.query_selector_all(
                '[data-testid="stExpander"] summary'
            )
            for exp in expanders:
                try:
                    is_open = await exp.evaluate(
                        'el => el.closest("details")?.open'
                    )
                    if not is_open:
                        await exp.click()
                        await page.wait_for_timeout(300)
                except Exception:
                    pass

        # Scroll to bottom to trigger lazy loading
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(500)

        # Extract default tab content first
        data = await page.evaluate(EXTRACT_JS)
        default_content = format_page_content(data)
        lines.append(default_content)

        # Collect set of already-seen table signatures to avoid duplication
        default_table_sigs = set()
        for t in data.get("tables", []):
            sig = "|".join(t.get("headers", [])) + "||" + str(len(t.get("rows", [])))
            default_table_sigs.add(sig)

        # Click through additional tabs and capture ONLY new content
        tab_buttons = await page.query_selector_all('[role="tab"]')
        if len(tab_buttons) > 1:
            for i, tab in enumerate(tab_buttons):
                try:
                    label = (await tab.inner_text()).strip()
                    is_selected = await tab.get_attribute("aria-selected")
                    if is_selected == "true":
                        continue  # Already captured above

                    await tab.click()
                    await page.wait_for_timeout(1500)

                    # Extract full page again but only keep NEW tables
                    tab_data = await page.evaluate(EXTRACT_JS)
                    new_tables = []
                    for t in tab_data.get("tables", []):
                        sig = "|".join(t.get("headers", [])) + "||" + str(len(t.get("rows", [])))
                        if sig not in default_table_sigs:
                            new_tables.append(t)
                            default_table_sigs.add(sig)

                    if new_tables:
                        lines.append(f"\n--- TAB: {label} ---\n")
                        tab_only = {"sections": [], "metrics": [], "charts": [], "tables": new_tables}
                        lines.append(format_page_content(tab_only))
                except Exception:
                    pass

    except Exception as e:
        lines.append(f"ERROR loading page: {e}")

    return "\n".join(lines)


async def main():
    from playwright.async_api import async_playwright

    t0 = time.time()
    all_text = []
    all_text.append(f"# {cfg.PROJECT_TITLE.upper()}: FULL DASHBOARD TEXT EXPORT")
    all_text.append(f"# Exported: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}")
    all_text.append(f"# Source: {BASE_URL}")
    all_text.append(f"# Pages: {len(PAGES)}")
    all_text.append("")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        for idx, (title, path) in enumerate(PAGES):
            url = f"{BASE_URL}{path}"
            print(f"📄 [{idx}] {title} → {url}")
            text = await extract_page(page, url, title, idx)
            all_text.append(text)
            print(f"   ✅ {len(text)} chars")

        await browser.close()

    output = "\n".join(all_text)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(output)

    elapsed = time.time() - t0
    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"\n🎉 Done: {OUTPUT_FILE} ({size_kb:.0f} KB, {elapsed:.0f}s)")
    print(f"   Upload this file for review.")


if __name__ == "__main__":
    asyncio.run(main())
