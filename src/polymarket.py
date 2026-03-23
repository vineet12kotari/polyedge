"""
Polymarket data client.
Primary: The Graph subgraph (on-chain, works globally including India)
Fallback: Gamma REST API (metadata)

The Graph endpoint is public, no auth, no geo-block.
"""

import requests
from typing import Optional

# ── The Graph — Polymarket subgraph on Polygon ────────────────────────────────
SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/polymarket/matic-markets-5"

# ── Gamma API — market metadata (titles, end dates, categories) ───────────────
GAMMA_BASE = "https://gamma-api.polymarket.com"

# ── CLOB API — live orderbook (may be geo-blocked) ───────────────────────────
CLOB_BASE = "https://clob.polymarket.com"

HEADERS = {"User-Agent": "PolyEdge/1.0"}
TIMEOUT = 12


# ── Subgraph helpers ──────────────────────────────────────────────────────────

def _subgraph_query(query: str, variables: dict = None) -> dict:
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    resp = requests.post(SUBGRAPH_URL, json=payload, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json().get("data", {})


def get_active_markets_subgraph(first: int = 200, skip: int = 0) -> list[dict]:
    """Fetch active markets from The Graph subgraph."""
    query = """
    query ActiveMarkets($first: Int!, $skip: Int!) {
      fixedProductMarketMakers(
        first: $first
        skip: $skip
        where: { outcomeTokenPrices_not: null }
        orderBy: collateralVolume
        orderDirection: desc
      ) {
        id
        question { id title }
        outcomes
        outcomeTokenPrices
        collateralVolume
        lastActiveDay
        resolutionTimestamp
        condition { id }
      }
    }
    """
    data = _subgraph_query(query, {"first": first, "skip": skip})
    raw = data.get("fixedProductMarketMakers", [])
    return [_normalize_subgraph_market(m) for m in raw]


def _normalize_subgraph_market(m: dict) -> dict:
    """Convert subgraph market to standard PolyEdge market dict."""
    prices = m.get("outcomeTokenPrices", [])
    outcomes = m.get("outcomes", ["YES", "NO"])

    yes_price = None
    for i, outcome in enumerate(outcomes):
        if outcome.upper() == "YES" and i < len(prices):
            try:
                yes_price = round(float(prices[i]), 4)
            except (ValueError, TypeError):
                pass
            break
    if yes_price is None and prices:
        try:
            yes_price = round(float(prices[0]), 4)
        except (ValueError, TypeError):
            pass

    question_obj = m.get("question") or {}
    title = question_obj.get("title", "") if isinstance(question_obj, dict) else ""

    resolution_ts = m.get("resolutionTimestamp")
    end_date = None
    if resolution_ts:
        try:
            from datetime import datetime, timezone
            end_date = datetime.fromtimestamp(int(resolution_ts), tz=timezone.utc).isoformat()
        except Exception:
            pass

    condition = m.get("condition") or {}
    condition_id = condition.get("id", "") if isinstance(condition, dict) else m.get("id", "")

    return {
        "id": m.get("id", ""),
        "question": title,
        "title": title,
        "conditionId": condition_id,
        "condition_id": condition_id,
        "yes_price": yes_price,
        "tokens": [
            {"outcome": "YES", "token_id": condition_id, "price": yes_price},
        ],
        "endDate": end_date,
        "end_date_iso": end_date,
        "collateralVolume": m.get("collateralVolume", "0"),
        "_source": "subgraph",
    }


# ── Gamma API helpers ─────────────────────────────────────────────────────────

def _get_gamma_markets(limit: int = 100, offset: int = 0) -> list[dict]:
    params = {"limit": limit, "offset": offset, "active": "true", "closed": "false"}
    resp = requests.get(f"{GAMMA_BASE}/markets", params=params, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _get_gamma_resolved(limit: int = 100, offset: int = 0) -> list[dict]:
    params = {"limit": limit, "offset": offset, "closed": "true", "active": "false"}
    resp = requests.get(f"{GAMMA_BASE}/markets", params=params, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


# ── Public API ────────────────────────────────────────────────────────────────

def get_all_active_markets(max_pages: int = 5) -> list[dict]:
    """
    Fetch active markets. Tries subgraph first (on-chain, global access),
    falls back to Gamma REST API.
    """
    # Try subgraph first
    try:
        markets = []
        for page in range(max_pages):
            batch = get_active_markets_subgraph(first=200, skip=page * 200)
            if not batch:
                break
            markets.extend(batch)
            if len(batch) < 200:
                break
        if markets:
            return markets
    except Exception:
        pass

    # Fallback: Gamma API
    markets = []
    for page in range(max_pages):
        try:
            batch = _get_gamma_markets(limit=100, offset=page * 100)
            if not batch:
                break
            markets.extend(batch)
            if len(batch) < 100:
                break
        except Exception:
            break
    return markets


def get_resolved_markets_gamma(max_pages: int = 20) -> list[dict]:
    """Fetch resolved markets from Gamma API for backtesting."""
    markets = []
    for page in range(max_pages):
        try:
            batch = _get_gamma_resolved(limit=100, offset=page * 100)
            if not batch:
                break
            markets.extend(batch)
            if len(batch) < 100:
                break
        except Exception as e:
            print(f"  Gamma page {page} error: {e}")
            break
    return markets


def get_market_price(condition_id: str) -> Optional[float]:
    """Get YES price — tries CLOB midpoint, falls back to subgraph."""
    # Try CLOB
    try:
        resp = requests.get(
            f"{CLOB_BASE}/midpoint",
            params={"token_id": condition_id},
            headers=HEADERS,
            timeout=5,
        )
        resp.raise_for_status()
        mid = resp.json().get("mid")
        if mid is not None:
            return float(mid)
    except Exception:
        pass

    # Fallback: subgraph single market
    try:
        query = """
        query Market($id: ID!) {
          fixedProductMarketMaker(id: $id) {
            outcomeTokenPrices
          }
        }
        """
        data = _subgraph_query(query, {"id": condition_id.lower()})
        fpmm = data.get("fixedProductMarketMaker")
        if fpmm:
            prices = fpmm.get("outcomeTokenPrices", [])
            if prices:
                return round(float(prices[0]), 4)
    except Exception:
        pass

    return None


def get_orderbook(token_id: str) -> Optional[dict]:
    try:
        resp = requests.get(
            f"{CLOB_BASE}/book",
            params={"token_id": token_id},
            headers=HEADERS,
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def get_best_bid_ask(token_id: str) -> tuple[Optional[float], Optional[float]]:
    """Return (best_bid, best_ask). Falls back to subgraph price if CLOB unavailable."""
    book = get_orderbook(token_id)
    if book:
        bids = book.get("bids", [])
        asks = book.get("asks", [])
        best_bid = float(bids[0]["price"]) if bids else None
        best_ask = float(asks[0]["price"]) if asks else None
        if best_bid or best_ask:
            return best_bid, best_ask

    # Fallback: use subgraph price as both bid and ask
    price = get_market_price(token_id)
    if price:
        return price, price
    return None, None
