
# daytradebot — Active Trading Patch (Tradier, Margin 6YB61940)

This patch increases trade activity safely:
- Lower entry threshold (`min_notional` $25)
- Conservative sizing (`MAX_RISK_PCT=0.15`) with **1‑share floor**
- **Momentum** signal (intraday % change)
- **Marketable‑limit** orders (ask + $0.01) for better fills
- **Universe scanner** endpoint (`/trade/run`) to loop over 15 liquid tickers
- **Gross exposure** cap (40% of equity)
- Margin‑aware gating using `stock_buying_power`

> Live orders are allowed only if `ENABLE_LIVE_TRADES=true` at runtime.

## Env (defaults for your margin account)

```
TRADIER_BASE=https://api.tradier.com/v1
TRADIER_TOKEN=REPLACE_WITH_LIVE_TOKEN
TRADIER_ACCOUNT_ID=6YB61940
ENABLE_LIVE_TRADES=false
PORT=8000
```

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
```

## Useful endpoints
- `GET /health`
- `GET /ping_tradier`
- `GET or POST /trade/test?symbol=F&last_price=12&signal=buy&min_notional=25`
- `GET or POST /trade/run?cycles=60&sleep_s=5&up_thresh=0.3&min_notional=25`

Use `/docs` for an interactive UI.
