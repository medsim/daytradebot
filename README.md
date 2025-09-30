
# daytradebot — Margin Account Patch (Tradier)

Configured for Tradier margin account **6YB61940**.

## Features
- Form-encoded order posting (`x-www-form-urlencoded`)
- Margin-aware buying power checks (`stock_buying_power`)
- America/New_York market-hours gating
- `/trade/test` works via GET or POST

## Environment variables
```
TRADIER_BASE=https://api.tradier.com/v1
TRADIER_TOKEN=REPLACE_WITH_YOUR_TOKEN
TRADIER_ACCOUNT_ID=6YB61940
ENABLE_LIVE_TRADES=false
PORT=8000
```
