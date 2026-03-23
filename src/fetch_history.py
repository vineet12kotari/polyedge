"""
Fetches resolved Polymarket markets and saves to data/resolved_markets.json.
Uses Gamma API for resolved market data + price snapshots.

Run: python fetch_history.py
  or: python -m src.fetch_history
"""

import json
import os
import time
import requests
from datetime import datetime, timezone

GAMMA_BASE = "https://gamma-api.polymarket.com"
OUT_PATH   = os.path.join(os.path.dirname(__file__), "..", "data", "resolved_markets.json")
HEADERS    = {"User-Agent": "PolyEdge/1.0"}
TIMEOUT    = 15


def fetch_resolved_page(limit: int = 100, offset: int = 0) -> list[dict]:
    params = {
        "limit": limit,
        "offset": offset,
        "closed": "true",
        "active": "false",
    }
    resp = requests.get(f"{GAMMA_BASE}/markets", params=params, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _extract_yes_price(m: dict) -> float | None:
    """Pull YES price from various field locations Gamma API uses."""
    # tokens array
    for t in m.get("tokens", []):
        if t.get("outcome", "").upper() == "YES":
            p = t.get("price") or t.get("lastTradePrice")
            if p is not None:
                try:
                    return round(float(p), 4)
                except (ValueError, TypeError):
                    pass
    # top-level fields
    for field in ("lastTradePrice", "last_trade_price", "bestAsk", "midpoint"):
        v = m.get(field)
        if v is not None:
            try:
                return round(float(v), 4)
            except (ValueError, TypeError):
                pass
    return None


def _extract_outcome(m: dict) -> str | None:
    """Determine YES/NO resolution outcome."""
    # winner field
    winner = m.get("winner") or m.get("winnerOutcome") or m.get("resolvedOutcome")
    if winner is not None:
        s = str(winner).strip().upper()
        if s in ("YES", "1", "TRUE", "WIN"):
            return "YES"
        if s in ("NO", "0", "FALSE", "LOSS"):
            return "NO"

    # tokens: resolved token has price=1.0
    for t in m.get("tokens", []):
        p = t.get("price")
        if p is not None:
            try:
                if float(p) >= 0.99:
                    outcome = t.get("outcome", "").upper()
                    if outcome in ("YES", "NO"):
                        return outcome
            except (ValueError, TypeError):
                pass

    return None


def _days_between(start_iso: str | None, end_iso: str | None) -> float | None:
    """Calculate days between two ISO timestamps."""
    if not start_iso or not end_iso:
        return None
    try:
        def parse(s):
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        delta = (parse(end_iso) - parse(start_iso)).total_seconds() / 86400
        return round(max(delta, 0.1), 2)
    except Exception:
        return None


def normalize(m: dict) -> dict:
    """Extract all fields needed by backtester from a Gamma market dict."""
    yes_price = _extract_yes_price(m)
    outcome   = _extract_outcome(m)

    created   = m.get("createdAt") or m.get("created_at")
    end_date  = m.get("endDateIso") or m.get("end_date_iso") or m.get("endDate")
    days      = _days_between(created, end_date)

    # end_date as unix timestamp for backtester compatibility
    end_ts = None
    if end_date:
        try:
            end_ts = datetime.fromisoformat(
                end_date.replace("Z", "+00:00")
            ).timestamp()
        except Exception:
            pass

    created_ts = None
    if created:
        try:
            created_ts = datetime.fromisoformat(
                created.replace("Z", "+00:00")
            ).timestamp()
        except Exception:
            pass

    return {
        "question":            m.get("question") or m.get("title", ""),
        "condition_id":        m.get("conditionId") or m.get("condition_id", ""),
        "last_trade_price":    yes_price,
        "yes_price_snapshot":  yes_price,
        # arb backtest needs both — we only have poly here, kalshi left None
        "poly_price_snapshot": yes_price,
        "kalshi_price_snapshot": None,
        "outcome":             outcome,
        "resolved_yes":        outcome == "YES",
        "end_date":            end_date,
        "end_date_timestamp":  end_ts,
        "snapshot_timestamp":  created_ts,
        "days_to_resolution":  days,
    }


def main():
    os.makedirs(os.path.dirname(os.path.abspath(OUT_PATH)), exist_ok=True)
    all_markets = []
    print("Fetching resolved markets from Polymarket Gamma API...")
    print("(This may take 30-60 seconds for 2000 markets)\n")

    for page in range(20):  # up to 2000 markets
        offset = page * 100
        try:
            batch = fetch_resolved_page(limit=100, offset=offset)
        except Exception as e:
            print(f"  Error on page {page}: {e}")
            break

        if not batch:
            break

        normalized = [normalize(m) for m in batch]
        # Only keep markets where we have a price and outcome
        valid = [m for m in normalized if m["yes_price_snapshot"] is not None and m["outcome"] is not None]
        all_markets.extend(valid)

        total_fetched = (page + 1) * 100
        print(f"  Page {page+1}: {len(batch)} fetched, {len(valid)} usable (total usable: {len(all_markets)})")

        if len(batch) < 100:
            break
        time.sleep(0.25)

    with open(OUT_PATH, "w") as f:
        json.dump(all_markets, f, indent=2)

    print(f"\n✓ Saved {len(all_markets)} usable resolved markets to data/resolved_markets.json")
    print("  Run: python backtest.py")


if __name__ == "__main__":
    main()
