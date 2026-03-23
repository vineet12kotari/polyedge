"""
PolyEdge — backtest entry point.
Run: python backtest.py
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()

from src.backtester import run_bond_backtest, run_arb_backtest
from src.dashboard import print_backtest_report, console


def main():
    # Check data exists
    data_path = os.path.join(os.path.dirname(__file__), "data", "resolved_markets.json")
    if not os.path.exists(data_path):
        console.print("[yellow]No historical data found. Attempting to fetch from API...[/yellow]")
        try:
            from src.fetch_history import main as fetch
            fetch()
        except Exception as e:
            console.print(f"[yellow]API fetch failed ({e}). Generating synthetic dataset...[/yellow]")
            from src.generate_history import main as generate
            generate()
    if not os.path.exists(data_path):
        from src.generate_history import main as generate
        generate()

    console.print("\n[bold cyan]Running Bond Harvester backtest...[/bold cyan]")
    bond_result = run_bond_backtest(
        min_prob=float(os.getenv("MIN_BOND_PROBABILITY", "0.92")),
        min_yield=float(os.getenv("MIN_BOND_ANNUALIZED_YIELD", "0.50")),
        stake_per_trade=100.0,
    )
    print_backtest_report(bond_result)

    console.print("\n[bold cyan]Running Cross-Platform Arb backtest...[/bold cyan]")
    arb_result = run_arb_backtest(
        min_spread=float(os.getenv("MIN_ARBI_SPREAD", "0.03")),
        stake_per_trade=100.0,
    )
    print_backtest_report(arb_result)

    # Export to CSV
    import csv
    for result, name in [(bond_result, "bond"), (arb_result, "arb")]:
        trades = result.get("trades", [])
        if not trades:
            continue
        csv_path = f"backtest_{name}_results.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=trades[0].keys())
            writer.writeheader()
            writer.writerows(trades)
        console.print(f"[green]Exported {len(trades)} trades to {csv_path}[/green]")


if __name__ == "__main__":
    main()
