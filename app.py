
import os, time
from fastapi import FastAPI
from dotenv import load_dotenv

from brokers.tradier_client import profile, balances, positions, quotes, place_equity_limit
from utils.strategy import try_trade, marketable_limit_for_sell, check_and_exit_positions
from utils.universe import symbols as load_symbols

load_dotenv(override=False)

app = FastAPI(title="daytradebot auto-exit patch", version="1.3.0")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/ping_tradier")
def ping_tradier():
    out = {}
    for name, fn in [("profile", profile), ("balances", balances)]:
        r = fn()
        out[name] = {"status_code": r.status_code, "text": (r.text or "")[:2000]}
    return out

@app.api_route("/trade/test", methods=["GET","POST"])
def trade_test(symbol: str = "F", last_price: float = 12.0, signal: str = "buy",
               min_notional: float = 10.0, qty_cap: int = 5):
    allow_live = os.getenv("ENABLE_LIVE_TRADES", "false").lower() == "true"
    res = try_trade(symbol=symbol, signal=signal, last_price=last_price,
                    allow_live=allow_live, min_notional=min_notional, qty_cap=qty_cap)
    return {"allow_live": allow_live, "result": res}

@app.api_route("/trade/run", methods=["GET","POST"])
def trade_run(cycles: int = 60, sleep_s: float = 5.0, up_thresh: float = 0.1,
              min_notional: float = 10.0, batch_size: int = 50,
              pause_between_batches_s: float = 0.4, qty_cap: int | None = None,
              tp_pct: float = 1.0, sl_pct: float = 0.5):
    allow_live = os.getenv("ENABLE_LIVE_TRADES", "false").lower() == "true"
    syms = load_symbols()
    logs = []

    for _ in range(cycles):
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
                    logs.append({"sym": sym, "res": {"status":"skip","reason":"no_quote"}}); continue
                sig = "buy" if q["change_pct"] >= up_thresh else "neutral"
                res = try_trade(sym, sig, q["last"], allow_live=allow_live,
                                min_notional=min_notional, qty_cap=qty_cap)
                logs.append({"sym": sym, "sig": sig, "last": q["last"], "chg%": q["change_pct"], "res": res})

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
    allow_live = os.getenv("ENABLE_LIVE_TRADES", "false").lower() == "true"
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
    from utils.strategy import marketable_limit_for_sell
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
    allow_live = os.getenv("ENABLE_LIVE_TRADES", "false").lower() == "true"
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
