
# daytradebot — Tradier-ready patch

This drop-in patch gives you a minimal, production-ready scaffold that **places real trades on Tradier** (when enabled), fixes the common blockers (form-encoded orders, correct ET market window, account/URL mismatches), and adds loud diagnostics so "no trades" is always explainable.

## What's included
- `brokers/tradier_client.py` — correct headers, form-encoded orders, ET market-hours guard, verbose order logging.
- `utils/strategy.py` — simple trade gate/sizing and an example `try_trade` call.
- `scripts/ping_tradier.py` — one-shot connectivity & permissions test (run during market hours).
- `app.py` — a small FastAPI app with `/health`, `/ping_tradier`, `/trade/test` endpoints.
- `requirements.txt`, `Dockerfile`, `render.yaml`, `.env.example`

> **Note**: This repo does not auto-trade by default. The `/trade/test` endpoint only places a tiny preview and an optional tiny live order if you set `ENABLE_LIVE_TRADES=true`. Use this safely with a funded account and understand cash-account T+1 settlement and PDT rules.

## Environment variables

Set these **consistently** (both live or both sandbox):

```bash
TRADIER_BASE=https://api.tradier.com/v1          # or https://sandbox.tradier.com/v1
TRADIER_TOKEN=...                                # token matching the BASE (live vs sandbox)
TRADIER_ACCOUNT_ID=...                           # from GET /v1/accounts
ENABLE_LIVE_TRADES=false                         # set true to allow /trade/test to send a tiny live order
PORT=8000                                        # render/heroku-compatible
```

You can copy `.env.example` to `.env` for local runs.

## Quick start (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# set envs (or echo into .env)
export $(grep -v '^#' .env | xargs) 2>/dev/null || true

uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000} --reload
```

Visit:
- `GET /health`
- `GET /ping_tradier`  → shows profile/accounts/balances + order preview
- `POST /trade/test`   → (optional) places a tiny market buy when ENABLE_LIVE_TRADES=true

## Render deploy

- Use the provided `Dockerfile`. In Render, **leave Start Command empty** so Render uses the image's `CMD`.
- Ensure env vars are set in the Render dashboard.


## Cash account realities

With a **cash** account (~$6,000), you're constrained by **settled cash (T+1)**. Immediately after a round-trip, `cash_available` may be 0, so the bot will skip additional trades. The code logs:
- `cash`, `cash_available`, `unsettled_funds`
- Skip reasons like `market closed`, `cash_available < MIN_NOTIONAL`, `qty=0`

## Logs

Every order attempt appends one line JSON to `order_log.jsonl` in the working directory (persist or mount a volume for durability).

## Safety switches

- `ENABLE_LIVE_TRADES=false` by default. Flip to `true` to allow `/trade/test` to place a **single**-share buy on a cheap symbol.
- The example endpoint uses a small notional and fails closed if `cash_available` is insufficient.
