# Stablecoin Carry on Current Finance: Allocation Proposal

Interactive investment memorandum for a USDC / USDSUI carry on Current Finance (Sui), with two further strategies researched and on hold (a USD1 carry on Dolomite and a reUSD liquidity position on Curve).

Performance figures are reconstructed from public on-chain and protocol data at the stated position sizes; they are not the record of a live book.

## Run locally

```bash
uv run --with-requirements requirements.txt streamlit run app.py
```

## Structure

| Path | Contents |
| --- | --- |
| `app.py`, `project_config.py` | Entry point, page list, thresholds, data sources |
| `content/report.md` | All report text, one block per `## key` |
| `sections/` | One file per page |
| `utils/strategy.py` | Strategy calculations (yield, rate curves, stress, costs) |
| `queries/` | Data refresh scripts (public APIs, no keys) |
| `data/` | Pinned data used by the pages, plus editorial tables |

## Refresh data

```bash
python queries/runner.py
```

Pulls live and historical data from Current Finance's own APIs (chart, market and reward endpoints). DefiLlama is used only for the daily record of past reward rates. The on-hold strategies also use the Dolomite subgraph and contracts, Curve, Resupply (hippo.army) and the Hyperliquid info API.

## Read it

- Live dashboard: https://portfolio-manager-case-study.streamlit.app/
- Full text of every page, for offline reading or AI agents: [REPORT_FULL.md](REPORT_FULL.md)
