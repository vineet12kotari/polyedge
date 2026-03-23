"""
PolyEdge — main entry point.
Runs the live scanner loop with Rich terminal dashboard.

Usage:
  py main.py          # live mode (requires API access)
  py main.py --demo   # demo mode with realistic mock data
"""

import sys
import time
import traceback
from dotenv import load_dotenv

load_dotenv()

DEMO_MODE = "--demo" in sys.argv

from src.dashboard import render, console

SCAN_INTERVAL = 60  # seconds between scans


def scan_live() -> tuple[list, list, list]:
    from src.polymarket import get_all_active_markets
    from src.kalshi import get_all_active_markets as get_kalshi_markets
    from src.matcher import find_matches
    from src.arbitrage import find_arb_signals
    from src.bond_scanner import find_bond_signals

    errors = []
    arb_signals = []
    bond_signals = []

    try:
        console.print("[dim]Fetching Polymarket markets...[/dim]")
        poly_markets = get_all_active_markets(max_pages=5)
        console.print(f"[dim]  Got {len(poly_markets)} Polymarket markets[/dim]")
    except Exception as e:
        errors.append(f"Polymarket fetch failed: {e}")
        poly_markets = []

    try:
        console.print("[dim]Fetching Kalshi markets...[/dim]")
        kalshi_markets = get_kalshi_markets(max_pages=5)
        console.print(f"[dim]  Got {len(kalshi_markets)} Kalshi markets[/dim]")
    except Exception as e:
        errors.append(f"Kalshi fetch failed: {e}")
        kalshi_markets = []

    if poly_markets and kalshi_markets:
        try:
            matches = find_matches(poly_markets, kalshi_markets, threshold=72.0)
            arb_signals = find_arb_signals(matches)
        except Exception as e:
            errors.append(f"Arb engine error: {e}")
            traceback.print_exc()

    if poly_markets:
        try:
            bond_signals = find_bond_signals(poly_markets)
        except Exception as e:
            errors.append(f"Bond scanner error: {e}")
            traceback.print_exc()

    return arb_signals, bond_signals, errors


def scan_demo() -> tuple[list, list, list]:
    from src.mock_data import get_mock_arb_signals, get_mock_bond_signals
    return get_mock_arb_signals(), get_mock_bond_signals(), []


def main():
    mode_label = "[yellow]DEMO MODE[/yellow]" if DEMO_MODE else "[green]LIVE MODE[/green]"
    console.print(f"[bold cyan]PolyEdge starting — {mode_label}[/bold cyan]")
    scan_count = 0

    while True:
        scan_count += 1
        if DEMO_MODE:
            arb_signals, bond_signals, errors = scan_demo()
        else:
            arb_signals, bond_signals, errors = scan_live()

        render(arb_signals, bond_signals, scan_count=scan_count, errors=errors)

        try:
            time.sleep(SCAN_INTERVAL)
        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down. Goodbye.[/yellow]")
            break


if __name__ == "__main__":
    main()
