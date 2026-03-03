from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class OptionPick:
    expiration: str
    option_type: str  # call/put
    strike: float
    last_price: float | None
    bid: float | None
    ask: float | None
    implied_vol: float | None
    in_the_money: bool | None


def _pick_nearest_strike(df: pd.DataFrame, target: float) -> pd.Series | None:
    if df.empty:
        return None
    idx = (df["strike"] - target).abs().idxmin()
    return df.loc[idx]


def pick_csp(chain: pd.DataFrame, spot: float, moneyness: float = 0.93) -> OptionPick | None:
    puts = chain[chain["type"] == "put"].copy()
    row = _pick_nearest_strike(puts, spot * moneyness)
    if row is None:
        return None
    return OptionPick(
        expiration=str(row.get("expiration", "")),
        option_type="put",
        strike=float(row["strike"]),
        last_price=_maybe(row.get("lastPrice")),
        bid=_maybe(row.get("bid")),
        ask=_maybe(row.get("ask")),
        implied_vol=_maybe(row.get("impliedVolatility")),
        in_the_money=_maybe_bool(row.get("inTheMoney")),
    )


def pick_cc(chain: pd.DataFrame, spot: float, moneyness: float = 1.07) -> OptionPick | None:
    calls = chain[chain["type"] == "call"].copy()
    row = _pick_nearest_strike(calls, spot * moneyness)
    if row is None:
        return None
    return OptionPick(
        expiration=str(row.get("expiration", "")),
        option_type="call",
        strike=float(row["strike"]),
        last_price=_maybe(row.get("lastPrice")),
        bid=_maybe(row.get("bid")),
        ask=_maybe(row.get("ask")),
        implied_vol=_maybe(row.get("impliedVolatility")),
        in_the_money=_maybe_bool(row.get("inTheMoney")),
    )


def _maybe(x):
    try:
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return None
        return float(x)
    except Exception:
        return None


def _maybe_bool(x):
    if x is None:
        return None
    return bool(x)
