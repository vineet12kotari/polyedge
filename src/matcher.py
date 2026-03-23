"""
Cross-platform market matcher.
Fuzzy-matches Polymarket questions against Kalshi market titles
to find the same event priced on both platforms.
"""

from rapidfuzz import fuzz
from typing import Optional
import re


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def match_score(poly_question: str, kalshi_title: str) -> float:
    """Return 0-100 similarity score between two market titles."""
    a = _normalize(poly_question)
    b = _normalize(kalshi_title)
    # Weighted combo: token_set handles word-order differences
    token_set = fuzz.token_set_ratio(a, b)
    partial   = fuzz.partial_ratio(a, b)
    return 0.7 * token_set + 0.3 * partial


def find_matches(
    poly_markets: list[dict],
    kalshi_markets: list[dict],
    threshold: float = 72.0,
) -> list[dict]:
    """
    For each Polymarket market, find the best Kalshi match above threshold.
    Returns list of match dicts with both market objects + score.
    """
    matches = []

    for pm in poly_markets:
        poly_q = pm.get("question", "") or pm.get("title", "")
        if not poly_q:
            continue

        best_score = 0.0
        best_km: Optional[dict] = None

        for km in kalshi_markets:
            kalshi_title = km.get("title", "") or km.get("subtitle", "")
            if not kalshi_title:
                continue
            score = match_score(poly_q, kalshi_title)
            if score > best_score:
                best_score = score
                best_km = km

        if best_km and best_score >= threshold:
            matches.append({
                "poly_market": pm,
                "kalshi_market": best_km,
                "match_score": round(best_score, 1),
            })

    return sorted(matches, key=lambda x: x["match_score"], reverse=True)
