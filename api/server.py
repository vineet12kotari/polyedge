"""
PolyEdge FastAPI server.
Exposes live signals and backtest results as JSON endpoints.
Run: uvicorn api.server:app --reload --port 8000
"""

import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.polymarket import get_all_active_markets
from src.kalshi import get_all_active_markets as get_kalshi_markets
from src.matcher import find_matches
from src.arbitrage import find_arb_signals
from src.bond_scanner import find_bond_signals
from src.backtester import run_bond_backtest, run_arb_backtest

app = FastAPI(title="PolyEdge API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Cache ──────────────────────────────────────────────────────────────────────
_cache: dict = {"arb": [], "bonds": [], "last_scan": None}
_bt_cache: dict = {}  # backtest results cached at startup


def _run_scan():
    try:
        poly   = get_all_active_markets(max_pages=5)
        kalshi = get_kalshi_markets(max_pages=5)
        matches = find_matches(poly, kalshi)
        _cache["arb"]   = find_arb_signals(matches)
        _cache["bonds"] = find_bond_signals(poly)
        from datetime import datetime
        _cache["last_scan"] = datetime.utcnow().isoformat()
        _cache["mode"] = "live"
    except Exception as e:
        # Fall back to mock data so the UI always shows something
        from src.mock_data import get_mock_arb_signals, get_mock_bond_signals
        _cache["arb"]   = get_mock_arb_signals()
        _cache["bonds"] = get_mock_bond_signals()
        from datetime import datetime
        _cache["last_scan"] = datetime.utcnow().isoformat()
        _cache["mode"] = "demo"
        _cache["error"] = str(e)


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "last_scan": _cache.get("last_scan"), "mode": _cache.get("mode", "initializing")}


@app.get("/arb")
def arb_signals(background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_scan)
    signals = _cache["arb"]
    # Strip heavy nested market dicts for clean JSON response
    return [
        {k: v for k, v in s.items() if k not in ("poly_market", "kalshi_market")}
        for s in signals
    ]


@app.get("/bonds")
def bond_signals(background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_scan)
    signals = _cache["bonds"]
    return [
        {k: v for k, v in s.items() if k != "market"}
        for s in signals
    ]


@app.get("/scan")
def trigger_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_scan)
    return {"message": "Scan triggered", "last_scan": _cache.get("last_scan")}


@app.get("/backtest/bonds")
def backtest_bonds():
    if "bond" not in _bt_cache:
        result = run_bond_backtest()
        _bt_cache["bond"] = result if "error" not in result else None
    result = _bt_cache.get("bond")
    if not result:
        from src.mock_data import get_mock_bond_backtest
        return get_mock_bond_backtest()
    return {k: v for k, v in result.items() if k != "trades"}


@app.get("/backtest/arb")
def backtest_arb():
    if "arb" not in _bt_cache:
        result = run_arb_backtest()
        _bt_cache["arb"] = result if "error" not in result else None
    result = _bt_cache.get("arb")
    if not result:
        from src.mock_data import get_mock_arb_backtest
        return get_mock_arb_backtest()
    return {k: v for k, v in result.items() if k != "trades"}


@app.get("/backtest/bonds/trades")
def backtest_bonds_trades():
    if "bond" not in _bt_cache:
        _bt_cache["bond"] = run_bond_backtest()
    return _bt_cache.get("bond", {}).get("trades", [])


@app.get("/backtest/arb/trades")
def backtest_arb_trades():
    if "arb" not in _bt_cache:
        _bt_cache["arb"] = run_arb_backtest()
    return _bt_cache.get("arb", {}).get("trades", [])


# ── Serve UI ───────────────────────────────────────────────────────────────────
import pathlib
_UI_DIR = pathlib.Path(__file__).parent.parent / "ui"

if _UI_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(_UI_DIR), html=True), name="ui")

    @app.get("/")
    def root():
        return FileResponse(str(_UI_DIR / "index.html"))
