from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import requests


@dataclass(frozen=True)
class MacroHeadline:
    title: str
    link: str | None
    published: str | None


DEFAULT_FEEDS = {
    # relatively accessible RSS endpoints
    "bbc_business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "bbc_world": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "bbc_us_canada": "https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",
}


def fetch_rss(url: str, timeout: int = 12) -> list[MacroHeadline]:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    text = r.text
    root = ET.fromstring(text)

    items: list[MacroHeadline] = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip() or None
        pub = (item.findtext("pubDate") or "").strip() or None
        if title:
            items.append(MacroHeadline(title=title, link=link, published=pub))
    return items


CATEGORIES: dict[str, dict[str, int]] = {
    # Geopolitical / energy
    "geopolitics": {
        "war": 4,
        "strike": 3,
        "missile": 4,
        "attack": 3,
        "iran": 3,
        "israel": 3,
        "gulf": 2,
        "sanction": 2,
        "drone": 3,
        "hostage": 2,
    },
    "energy": {
        "oil": 3,
        "gas": 2,
        "brent": 2,
        "wti": 2,
        "opec": 2,
    },
    # Rates / inflation
    "rates": {
        "fed": 3,
        "rates": 3,
        "yield": 2,
        "bond": 2,
        "treasury": 2,
        "hike": 2,
        "cut": 2,
    },
    "inflation": {
        "inflation": 4,
        "cpi": 3,
        "ppi": 2,
        "prices": 1,
    },
    # Growth / credit stress
    "credit": {
        "default": 4,
        "bank": 2,
        "crisis": 4,
        "downgrade": 2,
        "layoffs": 2,
        "recession": 5,
    },
}


def score_by_category(title: str) -> dict[str, int]:
    t = title.lower()
    out: dict[str, int] = {}
    for cat, kws in CATEGORIES.items():
        s = 0
        for k, w in kws.items():
            if k in t:
                s += w
        out[cat] = s
    return out


def macro_risk_score(
    headlines: Iterable[MacroHeadline],
    max_items: int = 30,
) -> tuple[int, dict[str, int], list[MacroHeadline]]:
    """Return: (total_score, component_scores, top_headlines)

    - total_score: sum across categories
    - component_scores: per-category sum
    - top_headlines: most risk-relevant headlines (any category)
    """

    hs = list(headlines)[:max_items]
    total = 0
    comps = {k: 0 for k in CATEGORIES.keys()}
    scored: list[tuple[int, MacroHeadline]] = []

    for h in hs:
        per = score_by_category(h.title)
        s = sum(per.values())
        total += s
        for k, v in per.items():
            comps[k] += v
        scored.append((s, h))

    top = [h for s, h in sorted(scored, key=lambda p: -p[0]) if s > 0][:8]
    return total, comps, top
