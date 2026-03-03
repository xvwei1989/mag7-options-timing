from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from .data_sources.yahoo import YahooDataSource, resolve_universe
from .options.selectors import pick_cc, pick_csp
from .strategies.regime_rsi import generate_signal

app = typer.Typer(add_completion=False, help="MAG7 options timing research CLI")
console = Console()


@app.callback()
def _root():
    """Quant options timing utilities."""


@app.command("signals")
def signals_cmd(
    universe: str = typer.Option("mag7", help="Universe: mag7 or comma-separated tickers"),
    period: str = typer.Option("2y", help="History lookback period (yfinance)")
):
    """Generate today-style timing signals for the selected universe."""
    ds = YahooDataSource()
    tickers = resolve_universe(universe)

    rows = []
    for t in tickers:
        hist = ds.history(t, period=period)
        sig = generate_signal(t, hist)
        if not sig:
            continue

        # Option pick (best-effort)
        try:
            spot = sig.spot
            expirations = ds.option_expirations(t)
            # choose an expiration roughly 21-45 days out
            exp_pick = None
            for exp in expirations:
                # exp format: YYYY-MM-DD
                dte = (pd.to_datetime(exp).date() - date.today()).days
                if 21 <= dte <= 45:
                    exp_pick = exp
                    break
            if exp_pick is None and expirations:
                exp_pick = expirations[0]

            if exp_pick and sig.structure in ("CSP", "CC"):
                chain = ds.option_chain(t, exp_pick)
                chain["expiration"] = exp_pick
                opt = pick_csp(chain, spot) if sig.structure == "CSP" else pick_cc(chain, spot)
                if opt:
                    sig = sig.__class__(
                        **{**sig.__dict__, "expiration": exp_pick, "strike": opt.strike}
                    )
        except Exception:
            pass

        rows.append(sig)

    table = Table(title="MAG7 Options Timing Signals")
    table.add_column("Ticker")
    table.add_column("AsOf")
    table.add_column("Spot", justify="right")
    table.add_column("Regime")
    table.add_column("RSI14", justify="right")
    table.add_column("Action")
    table.add_column("Structure")
    table.add_column("Exp")
    table.add_column("Strike", justify="right")
    for s in rows:
        exp = s.expiration or "—"
        strike = f"{s.strike:.2f}" if s.strike is not None else "—"
        table.add_row(s.ticker, s.asof, f"{s.spot:.2f}", s.regime, f"{s.rsi14:.1f}", s.action, s.structure, exp, strike)

    console.print(table)


def main():
    app()


if __name__ == "__main__":
    main()
