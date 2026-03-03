from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

import pandas as pd
import yfinance as yf


MAG7 = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA"]


@dataclass(frozen=True)
class UnderlyingBar:
    dt: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float


class YahooDataSource:
    """Thin wrapper around yfinance.

    Notes:
    - yfinance data quality varies; treat as best-effort.
    - For production, plug in a paid market data provider.
    """

    def history(self, ticker: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval, auto_adjust=False)
        # normalize columns
        if df.empty:
            return df
        df = df.rename(columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        })
        df.index.name = "dt"
        return df[["open", "high", "low", "close", "volume"]]

    def option_expirations(self, ticker: str) -> list[str]:
        t = yf.Ticker(ticker)
        return list(t.options)

    def option_chain(self, ticker: str, expiration: str):
        t = yf.Ticker(ticker)
        chain = t.option_chain(expiration)
        calls = chain.calls.copy()
        puts = chain.puts.copy()
        calls["type"] = "call"
        puts["type"] = "put"
        return pd.concat([calls, puts], ignore_index=True)

    def last_close(self, ticker: str) -> float | None:
        df = self.history(ticker, period="5d", interval="1d")
        if df.empty:
            return None
        return float(df["close"].iloc[-1])


def resolve_universe(name: str) -> list[str]:
    name = name.lower().strip()
    if name in ("mag7", "magnificent7", "magnificent-7"):
        return MAG7
    # comma-separated
    return [x.strip().upper() for x in name.split(",") if x.strip()]
