"""
PM case study. Edit this file first; navigation, sidebar, event lines and methodology read from it.
"""

# ── Identity ────────────────────────────────────────────────────
PROJECT_TITLE = "Stablecoin Carry on Current Finance: Allocation Proposal"
PROJECT_SUBTITLE = "Investment memorandum, October 2026"
SIDEBAR_FOOTER = "Data: Current Finance API, Sui GraphQL, Pharos, Cetus, CoinGecko, Hyperliquid. DefiLlama for reward history only."
AUTHOR = "Juan"

API_URL = "https://api.goldsky.com/api/public/project_clyuw4gvq4d5801tegx0aafpu/subgraphs/dolomite-ethereum/latest/gn"
DATA_SOURCES = "Current Finance's chart API and Sui GraphQL, the Dolomite Ethereum subgraph and contracts, DefiLlama, Curve, Resupply (hippo.army) and the Hyperliquid info API"

# Every pinned figure refers to this moment.
PIN_TIMESTAMP = 1790726400            # 2026-09-29 00:00 UTC
PIN_LABEL = "29 September 2026"
PIN_DATE = "2026-09-29"

WINDOW_START = "2026-04-22"           # WLFI rewards live on Dolomite
WINDOW_END = "2026-09-29"

# Case study thresholds
HURDLE_APR = 12.0                     # net APY required by the brief
EQUITY = 1_500_000                    # capacity test size
C21_LEVERAGE = 3.0                    # USD1 carry (on hold)
CUR_LEVERAGE = 3.5                    # Current carry, starting leverage
C5_BORROW_RATE = 2.9                  # reUSD borrow on Resupply, 29 Sep (no free history)

# ── Event markers on time-series charts ─────────────────────────
EVENT_MARKERS = [
    ("2026-04-09", "WLF loan in the news (Apr 9)", "#DC2626"),
    ("2026-04-22", "WLFI rewards start (Apr 22)", "#16A34A"),
]

# ── Pages (module = file in sections/, must expose render()) ────
PAGES = [
    {"group": "Report", "module": "contents", "title": "Contents and Search", "url": "contents",
     "desc": "Search the whole report, and a clickable list of every page and section"},
    {"group": "Report", "module": "summary", "title": "Investment Summary", "url": "summary", "default": True,
     "desc": "The recommendation, how the position works, its returns, the main risks and how I would run it"},
    {"group": "Technical appendix", "module": "cur_yield", "title": "Structure and Yield", "url": "current-yield",
     "desc": "How the two positions fit together, where the return comes from, and how interest rates respond to size"},
    {"group": "Technical appendix", "module": "cur_record", "title": "Track Record, Capacity and Costs",
     "url": "current-record", "desc": "Monthly returns since April, room within Current Finance's limits, entry, exit and their costs"},
    {"group": "Technical appendix", "module": "cur_risk", "title": "Risk and Leverage", "url": "current-risk",
     "desc": "Why 3.5 times, when a position would be liquidated, the two stablecoins, SUI reward exposure and the risk map"},
    {"group": "Technical appendix", "module": "cur_controls", "title": "Controls and Security", "url": "current-controls",
     "desc": "Audits, who controls the platform and its code, price feeds, limits and the insurance quote"},
    {"group": "Technical appendix", "module": "cur_ops", "title": "Monitoring and Operations", "url": "current-ops",
     "desc": "The nine alarms, the monitoring screen, response steps, custody, team support and the pre-mortem"},
    {"group": "Technical appendix", "module": "cur_controls_matrix", "title": "Risk Controls and Stress Tests", "url": "current-controls-matrix",
     "desc": "The 57 controls checked against standard risk lists, and how the return holds up under stress"},
    {"group": "Technical appendix", "module": "allocation", "title": "Allocation Tool", "url": "allocation",
     "desc": "Interactive sizing: leverage, return, liquidation levels and costs"},
    {"group": "Process", "module": "sourcing", "title": "Sourcing and Screening", "url": "sourcing",
     "desc": "How the opportunity was found, the investment tests and every candidate considered"},
    {"group": "Process", "module": "methodology", "title": "Data Sources and Methods", "url": "methodology",
     "desc": "Where every number comes from, the assumptions, the disclosure and how AI tools were used"},
    {"group": "On hold", "module": "usd1", "title": "USD1 Carry (Dolomite)", "url": "usd1",
     "desc": "A second strategy, fully researched and on hold, with the conditions for revisiting it"},
    {"group": "On hold", "module": "p2_reusd", "title": "reUSD Liquidity (Resupply)", "url": "reusd",
     "desc": "A third strategy, fully researched and on hold, with the conditions for revisiting it"},
]

EXPECTED_FILES = [
    "c21_rates_daily.csv", "wlfi_price_daily.csv", "c21_wlfi_positions.csv", "dolomite_markets_snapshot.csv",
    "c5_daily.csv", "candidates.csv", "gates.csv", "risk_map_c21.csv", "risk_map_c5.csv",
    "monitoring_triggers.csv", "pipeline.csv", "timeline_events.csv", "ai_use_log.csv",
    "resupply_curve_snapshot.csv", "wlfi_liquidity_venues.csv", "lp_venues.csv", "admin_map.csv", "rewards_snapshot.csv", "current_daily.csv", "current_snapshot.csv", "risk_map_current.csv", "risk_controls_matrix.csv",
]

QUERY_BLOCKS = {
    "current": "block_current.py",
    "c21_dolomite": "block_c21_dolomite.py",
    "wlfi_price": "block_wlfi_price.py",
    "c5_resupply": "block_c5_resupply.py",
}

METRIC_SOURCES = [
    {"metric": "Current Finance USDC / USDSUI rates, utilization, supply, borrow, price", "source": "current_daily.csv", "type": "PINNED",
     "note": "Current Finance chart API, hourly, averaged daily. SUI reward rates: Current Finance reward API for today, and DefiLlama's daily record of the same figures for the history"},
    {"metric": "Current Finance live rates, supply, borrow, caps, reward rates", "source": "current_snapshot.csv", "type": "CURRENT", "note": "Current Finance market and reward APIs, refreshed with the data block. Daily limits from the reserve pages, swap quotes from Cetus"},
    {"metric": "USD1 / USDC realized supply and borrow APR", "source": "c21_rates_daily.csv", "type": "PINNED",
     "note": "Index ratios from the Dolomite Ethereum subgraph, one row per UTC day"},
    {"metric": "WLFI reward APR", "source": "c21_rates_daily.csv", "type": "PINNED",
     "note": "DefiLlama apyReward for the Dolomite USD1 and USDC pools"},
    {"metric": "WLFI price", "source": "wlfi_price_daily.csv", "type": "PINNED", "note": "Hyperliquid WLFI perp, daily close and low"},
    {"metric": "WLFI-backed positions", "source": "c21_wlfi_positions.csv", "type": "CURRENT",
     "note": f"Subgraph par balances x on-chain prices and indexes, {PIN_LABEL}"},
    {"metric": "Pool supply, borrow, utilization", "source": "dolomite_markets_snapshot.csv", "type": "CURRENT",
     "note": f"Subgraph total par x on-chain index and price, {PIN_LABEL}"},
    {"metric": "reUSD/scrvUSD LP APY, pool TVL, reUSD price, Resupply lending APY", "source": "c5_daily.csv",
     "type": "PINNED", "note": "DefiLlama yields and coins APIs"},
    {"metric": "Candidates, risk maps, triggers, pipeline, AI log", "source": "editorial CSVs", "type": "EDITORIAL",
     "note": "Hand-written from the research workbook"},
]
