"""
Mock data for demo mode — used when live APIs are unreachable.
Run: py main.py --demo
"""

from datetime import datetime, timezone, timedelta


def get_mock_arb_signals() -> list[dict]:
    return [
        {
            "direction": "BUY_KALSHI_SELL_POLY",
            "poly_price": 0.671,
            "kalshi_price": 0.598,
            "spread": 0.073,
            "spread_pct": 7.30,
            "poly_question": "Will the Fed cut rates in May 2026?",
            "kalshi_title": "Fed rate cut May 2026",
            "match_score": 88.4,
        },
        {
            "direction": "BUY_KALSHI_SELL_POLY",
            "poly_price": 0.542,
            "kalshi_price": 0.487,
            "spread": 0.055,
            "spread_pct": 5.50,
            "poly_question": "Will Bitcoin exceed $100k before April 2026?",
            "kalshi_title": "Bitcoin above $100,000 by April 2026",
            "match_score": 82.1,
        },
        {
            "direction": "BUY_POLY_SELL_KALSHI",
            "poly_price": 0.312,
            "kalshi_price": 0.358,
            "spread": 0.046,
            "spread_pct": 4.60,
            "poly_question": "Will the US enter recession in 2026?",
            "kalshi_title": "US recession declared in 2026",
            "match_score": 79.3,
        },
        {
            "direction": "BUY_KALSHI_SELL_POLY",
            "poly_price": 0.789,
            "kalshi_price": 0.751,
            "spread": 0.038,
            "spread_pct": 3.80,
            "poly_question": "Will Ethereum ETF see net inflows in Q1 2026?",
            "kalshi_title": "Ethereum ETF net positive Q1 2026",
            "match_score": 76.8,
        },
        {
            "direction": "BUY_KALSHI_SELL_POLY",
            "poly_price": 0.445,
            "kalshi_price": 0.411,
            "spread": 0.034,
            "spread_pct": 3.40,
            "poly_question": "Will the S&P 500 close above 5500 in March 2026?",
            "kalshi_title": "S&P 500 above 5500 end of March 2026",
            "match_score": 74.2,
        },
    ]


def get_mock_bond_signals() -> list[dict]:
    now = datetime.now(tz=timezone.utc)
    return [
        {
            "question": "Will the US avoid a government shutdown before March 25, 2026?",
            "yes_price": 0.941,
            "days_to_resolution": 1.4,
            "gross_return_pct": 6.27,
            "annualized_yield_pct": 1634,
        },
        {
            "question": "Will Jerome Powell remain Fed Chair through March 2026?",
            "yes_price": 0.963,
            "days_to_resolution": 2.1,
            "gross_return_pct": 3.84,
            "annualized_yield_pct": 668,
        },
        {
            "question": "Will Polymarket resolve the NATO summit market by March 28?",
            "yes_price": 0.952,
            "days_to_resolution": 4.5,
            "gross_return_pct": 5.04,
            "annualized_yield_pct": 409,
        },
        {
            "question": "Will the ECB hold rates at March 2026 meeting?",
            "yes_price": 0.934,
            "days_to_resolution": 7.2,
            "gross_return_pct": 7.07,
            "annualized_yield_pct": 358,
        },
        {
            "question": "Will Apple market cap stay above $3T through end of March?",
            "yes_price": 0.921,
            "days_to_resolution": 8.0,
            "gross_return_pct": 8.58,
            "annualized_yield_pct": 392,
        },
        {
            "question": "Will Solana stay above $100 through March 24, 2026?",
            "yes_price": 0.944,
            "days_to_resolution": 1.8,
            "gross_return_pct": 5.93,
            "annualized_yield_pct": 1202,
        },
    ]


def get_mock_bond_backtest() -> dict:
    return {
        "strategy": "Bond Harvester",
        "total_trades": 210,
        "wins": 199,
        "losses": 11,
        "win_rate_pct": 94.8,
        "total_pnl_usd": 1058.21,
        "avg_pnl_per_trade": 5.04,
        "sharpe_ratio": 26.63,
        "max_drawdown_pct": 3.25,
        "avg_annualized_yield_pct": 818.0,
    }


def get_mock_arb_backtest() -> dict:
    return {
        "strategy": "Cross-Platform Arbitrage",
        "total_trades": 864,
        "win_rate_pct": 100.0,
        "total_pnl_usd": 3823.20,
        "avg_pnl_per_trade": 4.42,
        "avg_spread_pct": 5.42,
        "sharpe_ratio": 47.63,
        "max_drawdown_pct": 0.0,
    }
