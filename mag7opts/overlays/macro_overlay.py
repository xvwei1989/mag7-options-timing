from __future__ import annotations

from dataclasses import replace

from ..strategies.regime_rsi import Signal


TICKER_SENSITIVITY = {
    # heuristic multipliers for macro components
    # (rates/inflation) sensitivity tends to be higher for long-duration growth / high beta
    "NVDA": {"rates_inf": 1.6, "geo_energy": 1.2},
    "TSLA": {"rates_inf": 1.4, "geo_energy": 1.1},
    "AMZN": {"rates_inf": 1.3, "geo_energy": 1.0},
    "META": {"rates_inf": 1.2, "geo_energy": 1.0},
    "GOOGL": {"rates_inf": 1.1, "geo_energy": 1.0},
    "MSFT": {"rates_inf": 1.2, "geo_energy": 1.0},
    "AAPL": {"rates_inf": 1.1, "geo_energy": 1.0},
}


def apply_macro_overlay(sig: Signal, macro_total: int, macro_components: dict[str, int]) -> Signal:
    """Explainable macro overlay for daily signals.

    We treat macro as a *risk regime* modifier, not a prediction model.

    Rules (v1):
    - If macro is high risk-off (total>=18 OR geopolitics+energy>=12 OR credit>=10):
        - Skip CSP entries (BUY/CSP -> HOLD/NONE)
    - If rates+inflation elevated (rates+inflation>=10):
        - Also skip CSP entries (growth stocks sensitive to rates)
    - Otherwise: keep signal but annotate the regime.

    This keeps behavior transparent and tunable.
    """

    rationale = sig.rationale
    geo_energy = macro_components.get("geopolitics", 0) + macro_components.get("energy", 0)
    rates_inf = macro_components.get("rates", 0) + macro_components.get("inflation", 0)
    credit = macro_components.get("credit", 0)

    sens = TICKER_SENSITIVITY.get(sig.ticker, {"rates_inf": 1.0, "geo_energy": 1.0})
    geo_energy_adj = geo_energy * float(sens.get("geo_energy", 1.0))
    rates_inf_adj = rates_inf * float(sens.get("rates_inf", 1.0))

    level = "low"
    if macro_total >= 18 or geo_energy_adj >= 12 or credit >= 10:
        level = "high"
    elif macro_total >= 8 or geo_energy_adj >= 6 or rates_inf_adj >= 8:
        level = "moderate"

    # 1) Structure preference mapping
    # - geopolitics/energy elevated -> prefer premium collection (CC) over adding equity risk (CSP)
    # - rates/inflation elevated -> require deeper oversold to justify CSP
    prefer_cc = geo_energy_adj >= 10

    # 2) CSP gating (risk-off)
    skip_csp = False
    if level == "high":
        skip_csp = True
    if rates_inf_adj >= 10:
        skip_csp = True

    # If macro is moderate but rates are elevated, tighten oversold threshold for CSP
    csp_rsi_threshold = 35
    if rates_inf_adj >= 8:
        csp_rsi_threshold = 30

    # BUY/CSP tightening based on rates
    if sig.structure == "CSP" and sig.action == "BUY" and sig.rsi14 > csp_rsi_threshold:
        return replace(
            sig,
            action="HOLD",
            structure="NONE",
            expiration=None,
            strike=None,
            rationale=(
                rationale
                + f" | macro_overlay: total={macro_total} level={level} geo+energy={geo_energy} rates+infl={rates_inf} credit={credit}"
                + f" | mapping: rates_inf_adj={rates_inf_adj:.1f} -> require RSI<= {csp_rsi_threshold} for CSP"
            ),
        )

    if skip_csp and sig.structure == "CSP" and sig.action == "BUY":
        return replace(
            sig,
            action="HOLD",
            structure="NONE",
            expiration=None,
            strike=None,
            rationale=(
                rationale
                + f" | macro_overlay: total={macro_total} level={level} geo+energy={geo_energy} rates+infl={rates_inf} credit={credit}"
                + f" | mapping: geo_energy_adj={geo_energy_adj:.1f} rates_inf_adj={rates_inf_adj:.1f} -> skip CSP"
            ),
        )

    # Optional: when geopolitics/energy elevated and stock is somewhat strong, bias to CC
    if prefer_cc and sig.action == "HOLD" and sig.regime == "bull" and sig.rsi14 >= 60:
        return replace(
            sig,
            action="SELL",
            structure="CC",
            rationale=(
                rationale
                + f" | macro_overlay: total={macro_total} level={level} geo+energy={geo_energy} rates+infl={rates_inf} credit={credit}"
                + f" | mapping: geo_energy_adj={geo_energy_adj:.1f} -> bias to CC (RSI>=60)"
            ),
        )

    return replace(
        sig,
        rationale=(
            rationale
            + f" | macro_overlay: total={macro_total} level={level} geo+energy={geo_energy} rates+infl={rates_inf} credit={credit}"
            + f" | mapping: geo_energy_adj={geo_energy_adj:.1f} rates_inf_adj={rates_inf_adj:.1f}"
        ),
    )
