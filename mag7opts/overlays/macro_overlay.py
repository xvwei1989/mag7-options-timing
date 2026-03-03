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


def apply_macro_overlay(sig: Signal, macro_total: int, macro_components: dict[str, int]) -> tuple[Signal, dict]:
    """Explainable macro overlay for daily signals.

    Returns:
    - final Signal
    - overlay meta dict (explicit reasons for output)
    """

    geo_energy = macro_components.get("geopolitics", 0) + macro_components.get("energy", 0)
    rates_inf = macro_components.get("rates", 0) + macro_components.get("inflation", 0)
    credit = macro_components.get("credit", 0)

    sens = TICKER_SENSITIVITY.get(sig.ticker, {"rates_inf": 1.0, "geo_energy": 1.0})
    geo_energy_adj = geo_energy * float(sens.get("geo_energy", 1.0))
    rates_inf_adj = rates_inf * float(sens.get("rates_inf", 1.0))

    # Determine macro level
    level = "low"
    if macro_total >= 18 or geo_energy_adj >= 12 or credit >= 10:
        level = "high"
    elif macro_total >= 8 or geo_energy_adj >= 6 or rates_inf_adj >= 8:
        level = "moderate"

    prefer_cc = geo_energy_adj >= 10

    # CSP gating
    skip_csp = (level == "high") or (rates_inf_adj >= 10)

    # Tighten oversold threshold for CSP when rates are elevated
    csp_rsi_threshold = 35
    if rates_inf_adj >= 8:
        csp_rsi_threshold = 30

    reasons: list[str] = []

    # Rule: rates tighten CSP entry
    if sig.structure == "CSP" and sig.action == "BUY" and sig.rsi14 > csp_rsi_threshold:
        reasons.append(f"rates/inflation elevated -> CSP requires RSI<= {csp_rsi_threshold}")
        final = replace(sig, action="HOLD", structure="NONE", expiration=None, strike=None)
    # Rule: skip CSP in risk-off
    elif skip_csp and sig.structure == "CSP" and sig.action == "BUY":
        reasons.append("risk-off macro -> skip CSP entries")
        final = replace(sig, action="HOLD", structure="NONE", expiration=None, strike=None)
    # Rule: bias to CC in geo/energy risk
    elif prefer_cc and sig.action == "HOLD" and sig.regime == "bull" and sig.rsi14 >= 60:
        reasons.append("geo/energy risk elevated -> bias to covered call when RSI>=60")
        final = replace(sig, action="SELL", structure="CC")
    else:
        final = sig

    meta = {
        "macro_level": level,
        "macro_total": macro_total,
        "components": {
            "geopolitics": macro_components.get("geopolitics", 0),
            "energy": macro_components.get("energy", 0),
            "rates": macro_components.get("rates", 0),
            "inflation": macro_components.get("inflation", 0),
            "credit": macro_components.get("credit", 0),
        },
        "adjusted": {
            "geo_energy_adj": round(geo_energy_adj, 2),
            "rates_inf_adj": round(rates_inf_adj, 2),
        },
        "flags": {
            "prefer_cc": prefer_cc,
            "skip_csp": skip_csp,
            "csp_rsi_threshold": csp_rsi_threshold,
        },
        "reasons": reasons,
        "changed": (final.action != sig.action) or (final.structure != sig.structure),
        "before": {"action": sig.action, "structure": sig.structure},
        "after": {"action": final.action, "structure": final.structure},
    }

    # Append an explicit, readable overlay note to rationale as well
    overlay_note = f"macro={level} total={macro_total} geo+energy={geo_energy} rates+infl={rates_inf} credit={credit}"
    if reasons:
        overlay_note += " | reasons: " + "; ".join(reasons)

    final = replace(final, rationale=final.rationale + " | overlay: " + overlay_note)
    return final, meta
