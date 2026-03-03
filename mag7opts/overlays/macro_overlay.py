from __future__ import annotations

from dataclasses import replace

from ..strategies.regime_rsi import Signal


def apply_macro_overlay(sig: Signal, macro_score: int) -> Signal:
    """Simple risk overlay.

    Heuristic:
    - If macro risk is high, be more conservative:
      - Avoid CSP entries (turn BUY->HOLD)
      - Prefer CC when overbought (SELL stays)
    - If macro risk is very low, allow slightly earlier CSP (not implemented yet)

    This is intentionally simple and explainable for v1.
    """

    rationale = sig.rationale

    if macro_score >= 18:
        # high risk-off environment
        if sig.structure == "CSP" and sig.action == "BUY":
            return replace(
                sig,
                action="HOLD",
                structure="NONE",
                expiration=None,
                strike=None,
                rationale=rationale + f" | macro_overlay: macro_score={macro_score} high -> skip CSP",
            )
        return replace(sig, rationale=rationale + f" | macro_overlay: macro_score={macro_score} high")

    if macro_score >= 8:
        # moderate risk
        return replace(sig, rationale=rationale + f" | macro_overlay: macro_score={macro_score} moderate")

    return replace(sig, rationale=rationale + f" | macro_overlay: macro_score={macro_score} low")
