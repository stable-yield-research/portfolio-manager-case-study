"""
Audit the text export for the problems that kept recurring last project.

    cd <repo> && python3 utils/audit_export.py [data/dashboard_full_text.md]

Checks: em/en dashes, raw floats in tables, nan/None leaks, leftover icon names,
lowercase chain names, double periods, and how often each $ figure appears
(same metric, different values across pages = inconsistency to investigate).
"""

import re
import sys
from collections import Counter
from pathlib import Path

path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/dashboard_full_text.md")
text = path.read_text(encoding="utf-8")
lines = text.splitlines()

CHECKS = {
    "em dash (\u2014)": lambda l: "\u2014" in l,
    "en dash (\u2013)": lambda l: "\u2013" in l,
    "raw float in table": lambda l: l.startswith("|") and re.search(r"\|\s*-?\d+\.\d{4,}\s*\|", l),
    "nan / None leak": lambda l: re.search(r"(\|\s*(nan|None|NaN)\s*\|)|\bnan\b", l),
    "icon name leak": lambda l: re.search(r"keyboard_arrow|expand_more|chevron_right", l),
    "lowercase chain": lambda l: re.search(r"\|\s*(ethereum|arbitrum|base|plume|optimism|polygon)\s*\|", l),
    "double period": lambda l: re.search(r"[a-z]\.\.(\s|$)", l),
    "LaTeX artifact": lambda l: re.search(r"\\\$|\$\$", l),
}

total = 0
for name, fn in CHECKS.items():
    hits = [(i, l) for i, l in enumerate(lines, 1) if fn(l)]
    total += len(hits)
    status = "OK " if not hits else "FIX"
    print(f"[{status}] {name}: {len(hits)}")
    for i, l in hits[:5]:
        print(f"       line {i}: {l.strip()[:110]}")

print("\nDollar figures by frequency (check each headline metric has ONE value everywhere):")
for fig, n in Counter(re.findall(r"\$\d[\d,.]*[KMB]?", text)).most_common(25):
    print(f"  {fig:>12}  x{n}")

print(f"\n{total} issue(s) found in {path} ({len(lines):,} lines)")
sys.exit(1 if total else 0)
