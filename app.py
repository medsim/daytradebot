
import os
from fastapi import FastAPI
from dotenv import load_dotenv

from brokers.tradier_client import profile, accounts, balances
from utils.strategy import try_trade

load_dotenv(override=True)

app = FastAPI(title="daytradebot patch", version="1.0.0")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/ping_tradier")
def ping_tradier():
    out = {}
    for name, fn in [("profile", profile), ("accounts", accounts), ("balances", balances)]:
        r = fn()
        out[name] = {"status_code": r.status_code, "text": (r.text or "")[:2000]}
    return out

@app.post("/trade/test")
def trade_test(symbol: str = "AAPL", last_price: float = 30.0, signal: str = "buy"):
    allow_live = os.getenv("ENABLE_LIVE_TRADES", "false").lower() == "true"
    res = try_trade(symbol=symbol, signal=signal, last_price=last_price, allow_live=allow_live)
    return {"allow_live": allow_live, "result": res}
