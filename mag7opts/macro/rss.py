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


KEYWORDS = {
    # risk-off / macro shock
    "war": 3,
    "strike": 2,
    "missile": 3,
    "attack": 2,
    "sanction": 2,
    "oil": 2,
    "inflation": 3,
    "cpi": 2,
    "ppi": 2,
    "fed": 2,
    "rates": 2,
    "recession": 4,
    "default": 3,
    "bank": 2,
    "crisis": 4,
    "shutdown": 2,
    "tariff": 2,
    "layoffs": 2,
    "downgrade": 2,
    "geopolitical": 2,
}


def score_headline(title: str) -> int:
    t = title.lower()
    s = 0
    for k, w in KEYWORDS.items():
        if k in t:
            s += w
    return s


def macro_risk_score(headlines: Iterable[MacroHeadline], max_items: int = 30) -> tuple[int, list[MacroHeadline]]:
    hs = list(headlines)[:max_items]
    scored = [(score_headline(h.title), h) for h in hs]
    total = sum(x for x, _ in scored)
    top = [h for x, h in sorted(scored, key=lambda p: -p[0]) if x > 0][:8]
    return total, top
