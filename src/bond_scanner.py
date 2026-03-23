"""
High-Probability Bond Scanner.
Finds Polymarket markets priced >92% YES and ranks by annualized yield.
Near-certain outcomes are systematically underpriced relative to time-adjusted yield.
"""

import os
from datetime import datetime, timezone
from typing import Optional
from src.polymarket import get_best_bid_ask, get_market_price


MIN_PROB   = float(os.getenv("MIN_BOND_PROBABILITY", "0.92"))
MIN_YIELD  = float(os.getenv("MIN_BOND_ANNUALIZED_YIELD", "0.50"))


def _yes_price(pm: dict) -> Optional[float]:
    """Get best YES ask price (what you pay to buy YES)."""
    tokens = pm.get("tokens", [])
    for token in tokens:
        if token.get("outcome", "").upper() == "YES":
            token_id = token.get("token_id")
            if token_id:
                _, ask = get_best_bid_ask(token_id)
                if ask:
                    return round(ask, 4)
    cid = pm.get("conditionId") or pm.get("condition_id")
    if cid:
        p = get_market_price(cid)
        if p:
            return round(p, 4)
    return None


def _days_to_resolution(pm: dict) -> Optional[float]:
    """Calculate days until market end date."""
    end_date = pm.get("endDate") or pm.get("end_date_iso") or pm.get("end_date")
    if not end_date:
        return None
    try:
        if isinstance(end_date, (int, float)):
            end_dt = datetime.fromtimestamp(end_date, tz=timezone.utc)
        else:
            end_date = end_date.replace("Z", "+00:00")
            end_dt = datetime.fromisoformat(end_date)
        now = datetime.now(tz=timezone.utc)
        delta = (end_dt - now).total_seconds() / 86400
        return max(delta, 0.1)  # floor at 0.1 days to avoid div/0
    except Exception:
        return None


def annualized_yield(price: float, days: float) -> float:
    """
    Return on buying at `price` and collecting 1.0 at resolution,
    annualized over `days`.
    Formula: (1/price - 1) * (365 / days)
    """
    return (1.0 / price - 1.0) * (365.0 / days)


def find_bond_signals(
    markets: list[dict],
    min_prob: float = MIN_PROB,
    min_yield: float = MIN_YIELD,
) -> list[dict]:
    """
    Scan markets for high-probability bond opportunities.

    Returns list of signal dicts sorted by annualized_yield descending.
    """
    signals = []

    for pm in markets:
        price = _yes_price(pm)
        if price is None or price < min_prob or price >= 1.0:
            continue

        days = _days_to_resolution(pm)
        if days is None or days <= 0:
            continue

        ann_yield = annualized_yield(price, days)
        if ann_yield < min_yield:
            continue

        gross_return = round((1.0 / price - 1.0) * 100, 2)

        signals.append({
            "question": pm.get("question", pm.get("title", "N/A")),
            "yes_price": price,
            "days_to_resolution": round(days, 1),
            "gross_return_pct": gross_return,
            "annualized_yield_pct": round(ann_yield * 100, 1),
            "market": pm,
        })

    return sorted(signals, key=lambda x: x["annualized_yield_pct"], reverse=True)
