#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

# Allow running as a script without installing the package
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mag7opts.data_sources.yahoo import YahooDataSource, resolve_universe
from mag7opts.macro.rss import DEFAULT_FEEDS, fetch_rss, macro_risk_score
from mag7opts.overlays.macro_overlay import apply_macro_overlay
from mag7opts.strategies.regime_rsi import generate_signal


def run(universe: str = "mag7", period: str = "2y") -> dict:
    ds = YahooDataSource()
    tickers = resolve_universe(universe)

    # macro
    all_items = []
    for _, url in DEFAULT_FEEDS.items():
        try:
            all_items.extend(fetch_rss(url))
        except Exception:
            continue
    score, top = macro_risk_score(all_items)

    signals = []
    for t in tickers:
        hist = ds.history(t, period=period)
        sig = generate_signal(t, hist)
        if not sig:
            continue
        sig2 = apply_macro_overlay(sig, score)
        signals.append(sig2)

    out = {
        "asof": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "universe": universe,
        "macro_score": score,
        "macro_top": [{"title": h.title, "link": h.link, "published": h.published} for h in top],
        "signals": [s.__dict__ for s in signals],
    }
    return out


if __name__ == "__main__":
    payload = run()
    Path("outputs").mkdir(exist_ok=True)
    fname = Path("outputs") / f"premarket_{datetime.now().strftime('%Y%m%d')}.json"
    fname.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(fname))
