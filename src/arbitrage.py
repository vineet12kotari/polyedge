"""
Arbitrage signal generator.
Takes matched Polymarket/Kalshi market pairs, fetches live prices,
and calculates exploitable spreads.
"""

import os
from typing import Optional
from src.polymarket import get_best_bid_ask, get_market_price
from src.kalshi import get_market


MIN_SPREAD = float(os.getenv("MIN_ARBI_SPREAD", "0.03"))


def _kalshi_yes_price(km: dict) -> Optional[float]:
    """Extract YES ask price from a Kalshi market dict."""
    # yes_ask is the price to BUY yes on Kalshi
    yes_ask = km.get("yes_ask")
    if yes_ask is not None:
        return round(yes_ask / 100, 4)  # Kalshi uses cents (0-100)
    yes_price = km.get("last_price")
    if yes_price is not None:
        return round(yes_price / 100, 4)
    return None


def _poly_yes_price(pm: dict) -> Optional[float]:
    """Get live YES mid price for a Polymarket market."""
    # Try tokens list first
    tokens = pm.get("tokens", [])
    for token in tokens:
        if token.get("outcome", "").upper() == "YES":
            token_id = token.get("token_id")
            if token_id:
                bid, ask = get_best_bid_ask(token_id)
                if bid and ask:
                    return round((bid + ask) / 2, 4)
    # Fallback: use conditionId as token_id
    cid = pm.get("conditionId") or pm.get("condition_id")
    if cid:
        price = get_market_price(cid)
        if price:
            return round(price, 4)
    return None


def _refresh_kalshi_price(km: dict) -> Optional[float]:
    """Re-fetch latest Kalshi market price."""
    ticker = km.get("ticker")
    if not ticker:
        return _kalshi_yes_price(km)
    fresh = get_market(ticker)
    if fresh:
        return _kalshi_yes_price(fresh)
    return _kalshi_yes_price(km)


def find_arb_signals(matches: list[dict], min_spread: float = MIN_SPREAD) -> list[dict]:
    """
    For each matched pair, fetch live prices and compute arb spread.
    Returns signals where abs(spread) >= min_spread.

    Signal dict:
      direction: "BUY_KALSHI_SELL_POLY" or "BUY_POLY_SELL_KALSHI"
      poly_price: float
      kalshi_price: float
      spread: float  (positive = profit per $1)
      poly_market: dict
      kalshi_market: dict
      match_score: float
    """
    signals = []

    for match in matches:
        pm = match["poly_market"]
        km = match["kalshi_market"]
        score = match["match_score"]

        poly_price = _poly_yes_price(pm)
        kalshi_price = _refresh_kalshi_price(km)

        if poly_price is None or kalshi_price is None:
            continue

        spread = poly_price - kalshi_price

        if abs(spread) < min_spread:
            continue

        direction = (
            "BUY_KALSHI_SELL_POLY" if spread > 0 else "BUY_POLY_SELL_KALSHI"
        )

        signals.append({
            "direction": direction,
            "poly_price": poly_price,
            "kalshi_price": kalshi_price,
            "spread": round(abs(spread), 4),
            "spread_pct": round(abs(spread) * 100, 2),
            "poly_question": pm.get("question", pm.get("title", "N/A")),
            "kalshi_title": km.get("title", km.get("subtitle", "N/A")),
            "poly_market": pm,
            "kalshi_market": km,
            "match_score": score,
        })

    return sorted(signals, key=lambda x: x["spread"], reverse=True)
