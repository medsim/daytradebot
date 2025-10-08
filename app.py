
import os
import time
import asyncio
import logging
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from dotenv import load_dotenv

from brokers.tradier_client import profile, balances, positions, quotes, place_equity_limit
from utils.strategy import try_trade, marketable_limit_for_sell, check_and_exit_positions
from utils.universe import symbols as load_symbols

# ------------------------------------------------------------
# Env & logging
# ------------------------------------------------------------
load_dotenv(override=False)  # host env takes precedence over .env
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("daytradebot")

# ------------------------------------------------------------
# App
# ------------------------------------------------------------
app = FastAPI(title="daytradebot (background trader + diagnostics)", version="1.4.0")

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def allow_live_trades() -> bool:
    """
    Live trading is gated ONLY by ENABLE_LIVE_TRADES=true
    """
    return os.getenv("ENABLE_LIVE_TRADES", "false").lower() == "true"


def is_market_open_et(now: datetime | None = None) -> bool:
    """
    Simple market-hours check: Mon-Fri 09:30–16:00 America/New_York.
    (Does not account for market holidays.)
    """
    tz = ZoneInfo("America/New_York")
    now = now.astimezone(tz) if now else datetime.now(tz)
    if now.weekday() >= 5:  # 5=Sat, 6=Sun
        return False
    start = dtime(9, 30)
    end = dtime(16, 0)
    return start <= now.time() <= end


def _effective_config() -> dict:
    try:
        syms = load_symbols()
        uni_len = len(syms)
    except Exception as e:
        syms = []
        uni_len = 0
        log.exception("Failed to load symbols: %s", e)
    return {
        "ENABLE_LIVE_TRADES": os.getenv("ENABLE_LIVE_TRADES"),
        "universe_size": uni_len,
        "notes": "ENABLE_LIVE_TRADES must be exactly 'true' (lowercase) to place live orders."
    }

# ------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------
@app.get("/health")
def health():
    return {"ok": True}

@app.get("/config")
def config():
    return _effective_config()

@app.get("/ping_tradier")
def ping_tradier():
    out = {}
    for name, fn in [("profile", profile), ("balances", balances)]:
        r = fn()
        out[name] = {"status_code": r.status_code, "text": (r.text or "")[:2000]}
    return out

@app.api_route("/trade/test", methods=["GET", "POST"])
def trade_test(symbol: str = "F", last_price: float = 12.0, signal: str = "buy",
               min_notional: float = 10.0, qty_cap: int = 5):
    allow_live = allow_live_trades()
    res = try_trade(symbol=symbol, signal=signal, last_price=last_price,
                    allow_live=allow_live, min_notional=min_notional, qty_cap=qty_cap)
    return {"allow_live": allow_live, "result": res}

@app.api_route("/trade/run", methods=["GET", "POST"])
def trade_run(cycles: int = 60, sleep_s: float = 5.0, up_thresh: float = 0.1,
              min_notional: float = 10.0, batch_size: int = 50,
              pause_between_batches_s: float = 0.4, qty_cap: int | None = 5,
              tp_pct: float = 1.0, sl_pct: float = 0.5,
              require_market_open: bool = False):
    """
    Run trade loop for a given number of cycles.
    - qty_cap defaulted to 5 (safer than None).
    - Optional market-hours gating via require_market_open=True.
    """
    allow_live = allow_live_trades()
    syms = load_symbols()
    logs = []

    # basic diagnostics each call
    logs.append({"diagnostics": {
        "allow_live": allow_live,
        "universe_size": len(syms),
        "params": {
            "cycles": cycles, "sleep_s": sleep_s, "up_thresh": up_thresh,
            "min_notional": min_notional, "batch_size": batch_size,
            "pause_between_batches_s": pause_between_batches_s, "qty_cap": qty_cap,
            "tp_pct": tp_pct, "sl_pct": sl_pct, "require_market_open": require_market_open
        }
    }})

    for _ in range(cycles):
        if require_market_open and not is_market_open_et():
            logs.append({"status": "skip_cycle", "reason": "market_closed"})
            time.sleep(sleep_s)
            continue

        for i in range(0, len(syms), batch_size):
            batch = syms[i:i+batch_size]
            try:
                qmap = quotes(batch, chunk_size=batch_size)
            except Exception as e:
                logs.append({"batch": batch, "error": str(e)})
                time.sleep(1.0)
                continue

            # exits first
            exit_res = check_and_exit_positions(qmap, tp_pct=tp_pct, sl_pct=sl_pct, allow_live=allow_live)
            logs.append({"exits": exit_res})

            # entries next
            for sym in batch:
                q = qmap.get(sym.upper())
                if not q:
                    logs.append({"sym": sym, "res": {"status": "skip", "reason": "no_quote"}})
                    continue

                chg = q.get("change_pct")
                last = q.get("last")
                if chg is None or last is None:
                    logs.append({"sym": sym, "res": {"status": "skip", "reason": "missing_fields", "q": q}})
                    continue

                # If change_pct units are fractional (e.g., 0.012=1.2%), up_thresh=0.1 is very high.
                # Tune up_thresh as needed. We just log an example here.
                sig = "buy" if chg >= up_thresh else "neutral"
                res = try_trade(sym, sig, last, allow_live=allow_live,
                                min_notional=min_notional, qty_cap=qty_cap)
                logs.append({"sym": sym, "sig": sig, "last": last, "chg%": chg, "res": res})

            time.sleep(pause_between_batches_s)
        time.sleep(sleep_s)

    tail = logs[-len(syms):] if len(logs) >= len(syms) else logs
    return {"allow_live": allow_live, "universe_size": len(syms), "last_cycle": tail, "total_events": len(logs)}

@app.get("/positions")
def get_positions():
    r = positions()
    return {"status_code": r.status_code, "body": (r.text or "")[:8000]}

@app.post("/flatten")
def flatten_all():
    allow_live = allow_live_trades()
    if not allow_live:
        return {"allow_live": allow_live, "status":"skip", "reason":"set ENABLE_LIVE_TRADES=true to flatten"}
    pos = positions()
    if pos.status_code != 200:
        return {"allow_live": allow_live, "status":"error", "detail": pos.text}
    try:
        data = pos.json().get("positions", {}).get("position", [])
        if isinstance(data, dict): data = [data]
    except Exception as e:
        return {"allow_live": allow_live, "status":"error", "detail": f"parse error: {e}", "raw": pos.text}
    results = []
    for p in data:
        sym = p["symbol"]; qty = int(p.get("quantity") or 0)
        if qty <= 0: continue
        last_price = float(p.get("lastprice") or 0) or 1.0
        limit = marketable_limit_for_sell(sym, last_price)
        resp = place_equity_limit(sym, "sell", qty, limit_price=limit)
        results.append({"symbol": sym, "qty": qty, "limit": limit, "resp_code": resp.status_code, "resp_body": (resp.text or "")[:2000]})
    return {"allow_live": allow_live, "status": "sent", "results": results}

@app.post("/manage/exits")
def manage_exits(tp_pct: float = 1.0, sl_pct: float = 0.5):
    allow_live = allow_live_trades()
    from brokers.tradier_client import quotes as batch_quotes
    pos = positions()
    if pos.status_code != 200:
        return {"allow_live": allow_live, "status": "error", "detail": pos.text}
    try:
        data = pos.json().get("positions", {}).get("position", [])
        if isinstance(data, dict): data = [data]
        syms = [p["symbol"].upper() for p in data or [] if int(p.get("quantity") or 0) > 0]
    except Exception as e:
        return {"allow_live": allow_live, "status":"error", "detail": f"parse error: {e}", "raw": pos.text}
    if not syms:
        return {"allow_live": allow_live, "status":"ok", "exits": [], "note":"no open positions"}
    qmap = batch_quotes(syms, chunk_size=max(1, min(50, len(syms))))
    exit_res = check_and_exit_positions(qmap, tp_pct=tp_pct, sl_pct=sl_pct, allow_live=allow_live)
    return {"allow_live": allow_live, "status":"ok", "exits": exit_res}

# ------------------------------------------------------------
# Background trader
# ------------------------------------------------------------
async def _background_trader():
    """
    Lightweight continuous trader that calls trade_run(cycles=1) on a loop.
    By default it requires market open. Set MARKET_HOURS_ONLY=false to bypass.
    """
    market_hours_only = os.getenv("MARKET_HOURS_ONLY", "true").lower() == "true"
    delay_s = float(os.getenv("BACKGROUND_LOOP_DELAY_S", "5.0"))

    log.info("Background trader starting (market_hours_only=%s, delay_s=%s)", market_hours_only, delay_s)
    while True:
        try:
            if market_hours_only and not is_market_open_et():
                await asyncio.sleep(delay_s)
                continue
            # Run one quick cycle with conservative defaults; tune as desired
            await asyncio.to_thread(trade_run, cycles=1, sleep_s=0.0, require_market_open=False)
        except Exception as e:
            log.exception("Background trade loop error: %s", e)
        await asyncio.sleep(delay_s)


@app.on_event("startup")
async def startup_event():
    cfg = _effective_config()
    log.info("Startup config: %s", cfg)
    # Start background trader task
    asyncio.create_task(_background_trader())
