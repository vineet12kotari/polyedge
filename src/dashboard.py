"""
Rich terminal dashboard — live arbitrage + bond signals.
"""

from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich import box

console = Console()


def _arb_table(signals: list[dict]) -> Table:
    t = Table(
        title="⚡ Cross-Platform Arbitrage Signals",
        box=box.ROUNDED,
        border_style="cyan",
        show_lines=True,
    )
    t.add_column("Market", style="white", max_width=48, no_wrap=False)
    t.add_column("Poly", justify="right", style="green")
    t.add_column("Kalshi", justify="right", style="yellow")
    t.add_column("Spread", justify="right", style="bold magenta")
    t.add_column("Direction", style="cyan")
    t.add_column("Match%", justify="right", style="dim")

    if not signals:
        t.add_row("[dim]No signals above threshold[/dim]", "", "", "", "", "")
        return t

    for s in signals[:15]:
        direction_label = (
            "BUY Kalshi → SELL Poly" if s["direction"] == "BUY_KALSHI_SELL_POLY"
            else "BUY Poly → SELL Kalshi"
        )
        t.add_row(
            s["poly_question"][:48],
            f"{s['poly_price']:.3f}",
            f"{s['kalshi_price']:.3f}",
            f"[bold]{s['spread_pct']:.2f}%[/bold]",
            direction_label,
            f"{s['match_score']:.0f}",
        )
    return t


def _bond_table(signals: list[dict]) -> Table:
    t = Table(
        title="💰 High-Probability Bond Signals",
        box=box.ROUNDED,
        border_style="green",
        show_lines=True,
    )
    t.add_column("Market", style="white", max_width=48, no_wrap=False)
    t.add_column("YES Price", justify="right", style="green")
    t.add_column("Days Left", justify="right", style="yellow")
    t.add_column("Gross Return", justify="right", style="cyan")
    t.add_column("Ann. Yield", justify="right", style="bold magenta")

    if not signals:
        t.add_row("[dim]No signals above threshold[/dim]", "", "", "", "")
        return t

    for s in signals[:15]:
        t.add_row(
            s["question"][:48],
            f"{s['yes_price']:.3f}",
            f"{s['days_to_resolution']:.1f}d",
            f"{s['gross_return_pct']:.2f}%",
            f"[bold]{s['annualized_yield_pct']:.0f}%[/bold]",
        )
    return t


def render(
    arb_signals: list[dict],
    bond_signals: list[dict],
    scan_count: int = 0,
    errors: list[str] = None,
) -> None:
    """Clear screen and render full dashboard."""
    console.clear()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = Text(f"PolyEdge  |  Scan #{scan_count}  |  {now}", style="bold white")
    console.print(Panel(header, border_style="bright_blue"))

    console.print(_arb_table(arb_signals))
    console.print()
    console.print(_bond_table(bond_signals))

    if errors:
        console.print()
        for e in errors:
            console.print(f"[red][warn] {e}[/red]")

    console.print(
        f"\n[dim]Arb signals: {len(arb_signals)}  |  "
        f"Bond signals: {len(bond_signals)}  |  "
        f"Refreshes every 60s  |  Ctrl+C to exit[/dim]"
    )


def print_backtest_report(result: dict) -> None:
    """Pretty-print a backtest result dict."""
    if "error" in result:
        console.print(f"[red]{result['error']}[/red]")
        return

    strategy = result.get("strategy", "Strategy")
    console.print(Panel(f"[bold]{strategy} — Backtest Report[/bold]", border_style="cyan"))

    t = Table(box=box.SIMPLE)
    t.add_column("Metric", style="dim")
    t.add_column("Value", style="bold white")

    skip = {"strategy", "trades"}
    for k, v in result.items():
        if k in skip:
            continue
        label = k.replace("_", " ").title()
        t.add_row(label, str(v))

    console.print(t)

    trades = result.get("trades", [])
    if trades:
        console.print(f"\n[dim]Showing first 10 of {len(trades)} trades:[/dim]")
        tt = Table(box=box.SIMPLE, show_lines=False)
        keys = [k for k in trades[0].keys() if k != "question"]
        tt.add_column("Market", max_width=40)
        for k in keys:
            tt.add_column(k.replace("_", " ").title(), justify="right")
        for trade in trades[:10]:
            row = [trade.get("question", "N/A")[:40]]
            for k in keys:
                row.append(str(trade.get(k, "")))
            tt.add_row(*row)
        console.print(tt)
