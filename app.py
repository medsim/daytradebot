
import os
from fastapi import FastAPI
from dotenv import load_dotenv
from brokers.tradier_client import profile, balances
from utils.strategy import try_trade

load_dotenv(override=True)
app = FastAPI(title="daytradebot margin patch", version="1.0.0")

@app.get("/health")
def health(): return {"ok": True}

@app.get("/ping_tradier")
def ping(): 
    return {
        "profile": {"status_code": profile().status_code},
        "balances": {"status_code": balances().status_code}
    }

@app.api_route("/trade/test", methods=["GET","POST"])
def trade(symbol: str="F", last_price: float=12.0, signal: str="buy", min_notional: float=50.0):
    allow_live = os.getenv("ENABLE_LIVE_TRADES","false").lower()=="true"
    return {"allow_live": allow_live, "result": try_trade(symbol, signal, last_price, allow_live, min_notional)}
