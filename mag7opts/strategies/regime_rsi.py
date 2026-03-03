from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from ..indicators.ta import rsi, sma


@dataclass(frozen=True)
class Signal:
    ticker: str
    asof: str
    spot: float
    regime: str  # bull/bear
    rsi14: float
    action: str  # BUY/SELL/HOLD
    structure: str  # CSP/CC/PutSpread/NONE
    rationale: str
    expiration: str | None = None
    strike: float | None = None


def generate_signal(ticker: str, hist: pd.DataFrame) -> Signal | None:
    if hist is None or hist.empty or len(hist) < 220:
        return None

    close = hist["close"]
    spot = float(close.iloc[-1])
    sma200 = float(sma(close, 200).iloc[-1])
    rsi14 = float(rsi(close, 14).iloc[-1])

    regime = "bull" if spot > sma200 else "bear"

    # simple timing rules
    action = "HOLD"
    structure = "NONE"
    rationale = f"regime={regime}, spot={spot:.2f}, sma200={sma200:.2f}, rsi14={rsi14:.1f}"

    if regime == "bull" and rsi14 <= 35:
        action = "BUY"
        structure = "CSP"
        rationale += " | oversold in bull -> sell cash-secured put"
    elif regime == "bull" and rsi14 >= 65:
        action = "SELL"
        structure = "CC"
        rationale += " | overbought in bull -> sell covered call"
    elif regime == "bear" and rsi14 <= 45:
        action = "HOLD"
        structure = "PutSpread"
        rationale += " | bear regime -> consider protective put spread (optional)"

    return Signal(
        ticker=ticker,
        asof=str(hist.index[-1].date()),
        spot=spot,
        regime=regime,
        rsi14=rsi14,
        action=action,
        structure=structure,
        rationale=rationale,
    )
