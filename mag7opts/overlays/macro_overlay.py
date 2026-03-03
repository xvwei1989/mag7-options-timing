from __future__ import annotations

from dataclasses import replace

from ..strategies.regime_rsi import Signal


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

    level = "low"
    if macro_total >= 18 or geo_energy >= 12 or credit >= 10:
        level = "high"
    elif macro_total >= 8 or geo_energy >= 6 or rates_inf >= 8:
        level = "moderate"

    # CSP gating
    skip_csp = False
    if level == "high":
        skip_csp = True
    if rates_inf >= 10:
        skip_csp = True

    if skip_csp and sig.structure == "CSP" and sig.action == "BUY":
        return replace(
            sig,
            action="HOLD",
            structure="NONE",
            expiration=None,
            strike=None,
            rationale=(
                rationale
                + f" | macro_overlay: total={macro_total} level={level} geo+energy={geo_energy} rates+infl={rates_inf} credit={credit} -> skip CSP"
            ),
        )

    return replace(
        sig,
        rationale=(
            rationale
            + f" | macro_overlay: total={macro_total} level={level} geo+energy={geo_energy} rates+infl={rates_inf} credit={credit}"
        ),
    )
