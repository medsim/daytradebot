
import os, time
from fastapi import FastAPI
from dotenv import load_dotenv

from brokers.tradier_client import profile, balances
from utils.strategy import try_trade
from utils.signals import momentum_signal
from utils.universe import symbols

# Platform env should take precedence; don't override with .env by default.
load_dotenv(override=False)

app = FastAPI(title="daytradebot active patch", version="1.1.0")

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
def trade_test(symbol: str = "F", last_price: float = 12.0, signal: str = "buy", min_notional: float = 25.0):
    allow_live = os.getenv("ENABLE_LIVE_TRADES", "false").lower() == "true"
    res = try_trade(symbol=symbol, signal=signal, last_price=last_price, allow_live=allow_live, min_notional=min_notional)
    return {"allow_live": allow_live, "result": res}

@app.api_route("/trade/run", methods=["GET","POST"])
def trade_run(cycles: int = 60, sleep_s: float = 5.0, up_thresh: float = 0.3, min_notional: float = 25.0):
    allow_live = os.getenv("ENABLE_LIVE_TRADES", "false").lower() == "true"
    logs = []
    syms = symbols()
    for _ in range(cycles):
        for sym in syms:
            sig, q = momentum_signal(sym, up_thresh=up_thresh)
            res = try_trade(sym, sig, q["last"], allow_live=allow_live, min_notional=min_notional)
            logs.append({"sym": sym, "sig": sig, "last": q["last"], "res": res})
        time.sleep(sleep_s)
    tail = logs[-len(syms):] if len(logs) >= len(syms) else logs
    return {"allow_live": allow_live, "last_cycle": tail, "total_events": len(logs)}
