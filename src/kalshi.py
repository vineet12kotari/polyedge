"""
Kalshi API client — public market data endpoints.
Auth is optional for read-only market data.
"""

import os
import requests
from typing import Optional

KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"
HEADERS = {"User-Agent": "PolyEdge/1.0", "Accept": "application/json"}


def _auth_headers() -> dict:
    key = os.getenv("KALSHI_API_KEY", "")
    if key:
        return {**HEADERS, "Authorization": f"Bearer {key}"}
    return HEADERS


def get_events(limit: int = 100, cursor: str = "") -> dict:
    """Fetch active events from Kalshi."""
    params = {"limit": limit, "status": "open"}
    if cursor:
        params["cursor"] = cursor
    resp = requests.get(
        f"{KALSHI_BASE}/events",
        params=params,
        headers=_auth_headers(),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def get_all_active_events(max_pages: int = 10) -> list[dict]:
    """Paginate through all open Kalshi events."""
    events = []
    cursor = ""
    for _ in range(max_pages):
        data = get_events(limit=100, cursor=cursor)
        batch = data.get("events", [])
        events.extend(batch)
        cursor = data.get("cursor", "")
        if not cursor or len(batch) < 100:
            break
    return events


def get_markets_for_event(event_ticker: str) -> list[dict]:
    """Get all markets (YES/NO contracts) for a Kalshi event."""
    try:
        resp = requests.get(
            f"{KALSHI_BASE}/events/{event_ticker}",
            headers=_auth_headers(),
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("event", {}).get("markets", [])
    except Exception:
        return []


def get_market(ticker: str) -> Optional[dict]:
    """Get a single Kalshi market by ticker."""
    try:
        resp = requests.get(
            f"{KALSHI_BASE}/markets/{ticker}",
            headers=_auth_headers(),
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json().get("market")
    except Exception:
        return None


def get_all_active_markets(max_pages: int = 10) -> list[dict]:
    """Fetch all open Kalshi markets directly."""
    markets = []
    cursor = ""
    for _ in range(max_pages):
        params = {"limit": 100, "status": "open"}
        if cursor:
            params["cursor"] = cursor
        try:
            resp = requests.get(
                f"{KALSHI_BASE}/markets",
                params=params,
                headers=_auth_headers(),
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            batch = data.get("markets", [])
            markets.extend(batch)
            cursor = data.get("cursor", "")
            if not cursor or len(batch) < 100:
                break
        except Exception:
            break
    return markets
