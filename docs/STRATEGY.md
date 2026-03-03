# Strategies & Signals

## Philosophy
This project focuses on **timing** (when to deploy option structures) plus **structure selection** (what option trade to express the view), with simple, explainable rules.

> Not investment advice.

---

## Universe
MAG7: AAPL, MSFT, AMZN, GOOGL, META, NVDA, TSLA

---

## Strategy v0: Regime + RSI (CSP/CC)

### Inputs
- Daily close prices
- Indicators:
  - SMA(200)
  - RSI(14)

### Regime filter
- **Bull** if `spot > SMA200`
- **Bear** otherwise

### Signals
| Regime | Condition | Action | Structure |
|--------|-----------|--------|-----------|
| Bull | RSI14 <= 35 | BUY | CSP (sell cash-secured put) |
| Bull | RSI14 >= 65 | SELL | CC (sell covered call) |
| Bear | otherwise | HOLD | NONE (optional hedge in later versions) |

### Option selection (best-effort)
- Expiration: choose first expiration with **DTE 21–45** (fallback to nearest)
- CSP strike: nearest strike to `0.93 * spot`
- CC strike: nearest strike to `1.07 * spot`

### Output fields
- `action`: BUY / SELL / HOLD
- `structure`: CSP / CC / NONE
- `expiration`: option expiration date (if applicable)
- `strike`: suggested strike (if applicable)

---

## Planned next steps
- Replace moneyness heuristic with **delta-based** targeting (requires better data)
- Add volatility regime (IV percentile / IV rank)
- Add execution / fill assumptions (bid-ask, slippage)
- Add backtesting engine for options PnL (with early assignment modeling)
- Integrate professional data providers (Polygon/Tradier)
