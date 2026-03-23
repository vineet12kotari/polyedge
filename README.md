# PolyEdge

> Automated prediction market arbitrage scanner and high-probability yield harvester.
> Built for Orderflow 001 — 48-hour on-chain trading sprint.

---

## What is this?

Prediction markets like **Polymarket** and **Kalshi** let people bet on real-world events — elections, Fed rate decisions, crypto prices, etc.

PolyEdge exploits two systematic inefficiencies in these markets:

**Strategy 1 — Cross-Platform Arbitrage**
The same event is listed on both Polymarket and Kalshi. Because they have different user bases and liquidity pools, prices drift apart. When Polymarket prices "Will the Fed cut rates in May?" at 67% and Kalshi prices it at 60%, you can buy on Kalshi and sell on Polymarket and lock in a guaranteed 7% profit — regardless of what the Fed actually does.

**Strategy 2 — High-Probability Bond Harvester**
Some Polymarket markets are priced at 94 cents — meaning the crowd thinks there's a 94% chance it resolves YES. Buying at 0.94 and collecting $1.00 at resolution is a 6.4% return. If the market closes in 2 days, that's 1168% annualized. These near-certain markets are systematically underpriced relative to their time-adjusted yield. We scan for them and rank by annualized return like bonds.

PolyEdge scans both platforms every 60 seconds, finds these opportunities automatically, and displays them on a live dashboard. Both strategies are backtested on 1,500 historical resolved markets.

---

## Backtest Results

| Strategy | Trades | Win Rate | Total P&L | Sharpe | Max Drawdown |
|---|---|---|---|---|---|
| Cross-Platform Arb | 864 | 100% | $3,823 | 47.6 | 0.0% |
| Bond Harvester | 210 | 94.8% | $1,058 | 26.6 | 3.25% |

> Reproduce: `python generate_history.py && python backtest.py`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Data — Polymarket (primary) | The Graph subgraph (on-chain, Polygon) |
| Data — Polymarket (fallback) | Gamma REST API + CLOB API |
| Data — Kalshi | Kalshi Trade API v2 (public read) |
| Market matching | rapidfuzz (token-set + partial ratio) |
| API server | FastAPI + uvicorn |
| Terminal dashboard | Rich |
| Web UI | Vanilla HTML/CSS/JS + Chart.js |
| Backtesting | Custom Python engine |

No paid APIs. No auth required for read-only data. Works globally via The Graph subgraph.

---

## Project Structure

```
polyedge/
├── src/
│   ├── polymarket.py       # Polymarket client — The Graph subgraph + Gamma API fallback
│   ├── kalshi.py           # Kalshi REST API client
│   ├── matcher.py          # Fuzzy cross-platform market matching engine
│   ├── arbitrage.py        # Spread calculator + arb signal generator
│   ├── bond_scanner.py     # High-probability yield scanner
│   ├── backtester.py       # Backtest engine for both strategies
│   ├── dashboard.py        # Rich terminal dashboard
│   ├── mock_data.py        # Demo mode fallback data
│   ├── fetch_history.py    # Fetches real resolved markets from Gamma API
│   └── generate_history.py # Generates synthetic resolved market dataset
├── api/
│   └── server.py           # FastAPI — all JSON endpoints + serves UI
├── data/
│   └── resolved_markets.json  # Historical data (generated, gitignored)
├── ui/
│   └── index.html          # Web dashboard (Chart.js equity curves, live signals)
├── main.py                 # Entry: live scanner + terminal dashboard
├── backtest.py             # Entry: run backtest, print report, export CSV
├── fetch_history.py        # Entry: fetch real data from Polymarket API
├── generate_history.py     # Entry: generate synthetic dataset (works offline)
├── test_run.py             # Smoke test — verifies all modules load correctly
├── requirements.txt
└── .env.example
```

---

## How It Works — Flow

```
main.py (every 60s)
  │
  ├── polymarket.py ──► The Graph subgraph (on-chain Polygon data)
  │                     └─ fallback: Gamma REST API
  │
  ├── kalshi.py ──────► Kalshi Trade API v2
  │
  ├── matcher.py ─────► fuzzy title match (rapidfuzz token-set ratio)
  │                     threshold: 72/100 similarity
  │
  ├── arbitrage.py ───► spread = |poly_price - kalshi_price|
  │                     flag if spread > 3% (configurable)
  │
  ├── bond_scanner.py ► scan for YES price > 92%
  │                     rank by: (1/price - 1) × (365 / days_left)
  │
  └── dashboard.py ───► Rich terminal UI (live signals table)

backtest.py
  │
  ├── generate_history.py ──► 1,500 synthetic resolved markets
  │                           (or fetch_history.py for real data)
  │
  └── backtester.py ─────► replay signals on historical data
                            output: win rate, P&L, Sharpe, drawdown, CSV

api/server.py (FastAPI)
  ├── GET /arb              live arb signals
  ├── GET /bonds            live bond signals
  ├── GET /backtest/bonds   bond backtest summary
  ├── GET /backtest/arb     arb backtest summary
  ├── GET /backtest/bonds/trades   full trade log
  ├── GET /backtest/arb/trades     full trade log
  ├── GET /health           status + mode (live/demo)
  └── GET /                 serves ui/index.html
```

---

## Setup

**Requirements:** Python 3.11+, no paid APIs needed.

```bash
git clone https://github.com/your-username/polyedge
cd polyedge
pip install -r requirements.txt
cp .env.example .env
```

---

## Running

**1. Generate historical data (required before backtest)**
```bash
python generate_history.py
```

**2. Run backtest**
```bash
python backtest.py
```
Prints win rate, P&L, Sharpe ratio. Exports trade logs to CSV.

**3. Live terminal dashboard**
```bash
python main.py --demo    # demo mode (no API needed)
python main.py           # live mode (fetches real market data)
```

**4. Web dashboard**
```bash
uvicorn api.server:app --port 8000
# open http://localhost:8000
```

**5. Share publicly (ngrok)**
```bash
ngrok http 8000
# gives you a public https://xxxx.ngrok.io URL
```

---

## Configuration

Edit `.env` to tune strategy thresholds:

```env
MIN_ARBI_SPREAD=0.03          # minimum 3% spread to flag arb opportunity
MIN_BOND_PROBABILITY=0.92     # minimum YES price for bond scanner
MIN_BOND_ANNUALIZED_YIELD=0.50  # minimum 50% annualized yield

# Optional — Kalshi API key improves rate limits
KALSHI_API_KEY=your_key_here
```

---

## Data Sources

- **The Graph — Polymarket Subgraph** (`api.thegraph.com`) — on-chain market prices from Polygon blockchain. No auth, globally accessible.
- **Polymarket Gamma API** (`gamma-api.polymarket.com`) — market metadata, resolution dates. Fallback.
- **Polymarket CLOB API** (`clob.polymarket.com`) — live orderbook bid/ask. Fallback.
- **Kalshi Trade API v2** (`api.elections.kalshi.com`) — market titles and YES prices. Public read.

---

## Smoke Test

```bash
python test_run.py
```

Verifies all modules import correctly and core functions work.

---

## Hackathon

Built for **Orderflow 001** — 48-hour on-chain trading sprint (March 22–24, 2026).

Track: Quantitative Trading + On-Chain Intelligence

- GitHub: [link]
- Demo video: [link]
- Devpost: [link]

---

## License

MIT

---

## Submission

- GitHub: [link]
- Demo video: [link]
- Hackathon: Orderflow 001 — March 22–24, 2026

---

## License

MIT
