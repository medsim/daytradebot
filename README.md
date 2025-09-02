# DayTrade Bot (Tradier + EODHD)

Intraday equities-first trading bot that:
- Enters after **9:45 AM ET** and exits all by **3:55 PM ET**
- Max **5** concurrent positions, **≤20** round trips per day
- **$750** default cap per trade (can boost to **$1,000** if <5 setups active)
- Dynamic **ATR/Keltner** trailing, partials, and time stop
- **Inverse ETFs** on bearish market regime signals only (e.g., SQQQ, SPXU, SDS, TZA)

> This repo ships with a working skeleton wired for environment variables.
> You can run in Tradier Sandbox first, then switch to live by flipping `TRADIER_BASE_URL`.

---

## Quickstart

```bash
# 1) Create and activate a virtual environment (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate

# 2) Install requirements
pip install -r requirements.txt

# 3) Configure environment
cp .env.example .env
# Edit .env with your keys + prefs

# 4) Run
python -m bot_daytrade.main
```

The bot logs to stdout. You can containerize or deploy to Render/DigitalOcean later.

---

## Environment Variables

The bot reads everything from environment variables (load them via `.env` locally).

| Variable | Required | Example | Notes |
|---|---|---|---|
| `TRADIER_ACCESS_TOKEN` | yes (for trading) | `your_token` | Create a Sandbox token for paper trading. |
| `TRADIER_ACCOUNT_ID` | yes (for trading) | `1234567` | Your Tradier account ID. |
| `TRADIER_BASE_URL` | recommended | `https://sandbox.tradier.com` | Use `https://api.tradier.com` for live. |
| `EODHD_API_KEY` | yes (for data) | `your_eodhd_key` | For intraday & fundamentals. |
| `TIMEZONE` | optional | `America/New_York` | Bot assumes ET defaults. |
| `MAX_OPEN` | optional | `5` | Concurrent positions cap. |
| `MAX_TRADES` | optional | `20` | Per-session round-trip cap. |
| `CAP_BASE` | optional | `750` | Base per-trade dollar cap. |
| `CAP_BOOST` | optional | `1000` | Cap when <5 setups active. |
| `RISK_PCT` | optional | `0.004` | Fraction of equity risked per trade (0.4%). |
| `NO_ENTRY_BEFORE` | optional | `09:45` | Local TZ. |
| `FORCE_FLAT_AT` | optional | `15:55` | Local TZ. |
| `UNIVERSE_FILE` | optional | `sample_watchlist.csv` | Optional static universe override. |

> If you omit trading credentials, the bot runs in **simulation/dry-run** mode (no orders).

---

## Design Choices Mapped

- **Entry style:** Pullback-first to VWAP/EMA21 after impulse; breakout second (stricter).
- **Indicators:** VWAP + EMA(9/21) core; RSI(14) + ATR(14) confirmations; Keltner(20, 1.5×ATR).
- **Holding duration:** Intraday swings (20–90 min typical), never hold past 3:55 PM ET.
- **Universe:** Tier A = liquid S&P-like; Tier B = session gappers (RVOL ≥2). Inverse ETFs allowed on bearish regime only.
- **Execution:** Marketable-limit orders with slippage caps; final market fail-safe at 3:54:30 PM.

---

## Notes

- The included **`sample_watchlist.csv`** is small; wire your own universe or write a scanner.
- `bot_daytrade/data_sources.py` includes EODHD intraday client placeholders (batch-friendly).
- `bot_daytrade/brokers.py` places orders at Tradier; in dry-run mode, it only logs.
- Strategy/risk logic is in `strategy.py` and `risk.py`. Indicator math is in `indicators.py`.
- This is intentionally modular so you can unit-test the math and swap providers.
