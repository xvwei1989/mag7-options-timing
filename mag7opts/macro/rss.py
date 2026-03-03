from __future__ import annotations

import re
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
from email.utils import parsedate_to_datetime

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


def _age_hours(pub: str | None) -> float | None:
    if not pub:
        return None
    try:
        dt = parsedate_to_datetime(pub)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - dt.astimezone(timezone.utc)).total_seconds() / 3600.0
    except Exception:
        return None


def freshness_weight(pub: str | None, half_life_hours: float = 48.0, floor: float = 0.25) -> float:
    """Exponential decay by age. 48h half-life by default.

    Returns a multiplier in [floor, 1].
    """
    age = _age_hours(pub)
    if age is None:
        return 1.0
    # w = 0.5^(age/half_life)
    w = math.pow(0.5, age / half_life_hours)
    return max(floor, min(1.0, w))


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

    Adds a *freshness weight* so newer headlines matter more.
    """

    hs = list(headlines)[:max_items]
    total_f = 0.0
    comps_f = {k: 0.0 for k in CATEGORIES.keys()}
    scored: list[tuple[float, MacroHeadline]] = []

    for h in hs:
        w = freshness_weight(h.published)
        per = score_by_category(h.title)
        s = float(sum(per.values()))
        sw = s * w
        total_f += sw
        for k, v in per.items():
            comps_f[k] += float(v) * w
        scored.append((sw, h))

    # present as ints for stability
    total = int(round(total_f))
    comps = {k: int(round(v)) for k, v in comps_f.items()}

    top = [h for s, h in sorted(scored, key=lambda p: -p[0]) if s > 0][:8]
    return total, comps, top
