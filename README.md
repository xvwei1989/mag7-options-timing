# MAG7 Options Timing Framework

A lightweight **research framework** for systematic option selection + timing strategies for the **Magnificent 7** equities:

- AAPL, MSFT, AMZN, GOOGL, META, NVDA, TSLA

## Disclaimer
This repository is for **research/education only**. It is **not** investment advice. Options trading involves substantial risk.

---

## Goals

1. Provide a clean data/analytics layer for:
   - underlying price history
   - option chains (calls/puts)
   - derived metrics (IV proxy, moneyness, DTE, breakevens)
2. Implement repeatable strategies that output **buy/sell signals**.
3. Offer a simple CLI to:
   - generate today’s signals
   - export signals to CSV/JSON

---

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Example: generate signals for all MAG7
python -m mag7opts signals --universe mag7 --asof today
```

---

## Strategy (v0)

We start with a practical, “timing + structure” approach:

### Regime filter (timing)
- **Bull regime**: price > SMA(200)
- **Bear regime**: price <= SMA(200)

### Entry signals
- **Cash-secured put (CSP)** in bull regime when RSI(14) is oversold (<= 35)
- **Covered call (CC)** in bull regime when RSI(14) is overbought (>= 65)
- **Bear regime hedge**: optional put debit spread when price < SMA(200) and RSI is weak

### Option selection rules (defaults)
- Target **DTE**: 21–45 days
- CSP delta proxy via moneyness: strike ~ 0.90–0.95 * spot
- CC strike: ~ 1.05–1.10 * spot

Outputs:
- `signal`: BUY / SELL / HOLD
- `structure`: CSP / CC / PutSpread
- recommended strikes + expiration

---

## Repo Layout

```
mag7opts/
  data_sources/
  indicators/
  options/
  strategies/
  cli.py
```

---

## Data Sources

v0 uses **yfinance** (convenient but not perfect). The framework is designed so you can later swap in Polygon/Tradier/IEX.

---

## License
MIT
