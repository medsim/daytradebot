
import os, time, json, requests
from datetime import datetime
from zoneinfo import ZoneInfo

TRADIER_BASE = os.getenv("TRADIER_BASE", "https://api.tradier.com/v1")
TRADIER_TOKEN = os.getenv("TRADIER_TOKEN")
TRADIER_ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID", "6YB61940").upper()
TIMEOUT = 20

HDRS_JSON = {"Authorization": f"Bearer {TRADIER_TOKEN}", "Accept": "application/json"}
HDRS_FORM = {"Authorization": f"Bearer {TRADIER_TOKEN}", "Accept": "application/json",
             "Content-Type": "application/x-www-form-urlencoded"}

def _get(path, params=None):
    return requests.get(f"{TRADIER_BASE}{path}", headers=HDRS_JSON, params=params, timeout=TIMEOUT)

def _post(path, data):
    return requests.post(f"{TRADIER_BASE}{path}", headers=HDRS_FORM, data=data, timeout=TIMEOUT)

def market_is_open(now=None):
    now = now or datetime.now(ZoneInfo("America/New_York"))
    if now.weekday() > 4:
        return False
    open_t  = now.replace(hour=9, minute=30, second=0, microsecond=0)
    close_t = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return open_t <= now <= close_t

# Core endpoints
def profile():   return _get("/user/profile")
def balances():  return _get(f"/accounts/{TRADIER_ACCOUNT_ID}/balances")
def positions(): return _get(f"/accounts/{TRADIER_ACCOUNT_ID}/positions")
def orders():    return _get(f"/accounts/{TRADIER_ACCOUNT_ID}/orders")

# Quotes
def quote(symbol: str):
    r = _get("/markets/quotes", params={"symbols": symbol})
    r.raise_for_status()
    q = r.json()["quotes"]["quote"]
    last = float(q["last"])
    change_pct = float(q.get("change_percentage") or 0.0)
    bid = float(q.get("bid") or last)
    ask = float(q.get("ask") or last)
    return {"last": last, "change_pct": change_pct, "bid": bid, "ask": ask}

# Orders
def preview_equity_market(symbol, side, qty, duration="day"):
    data = {"class":"equity","symbol":symbol,"side":side,"quantity":str(qty),
            "type":"market","duration":duration,"preview":"true"}
    return _post(f"/accounts/{TRADIER_ACCOUNT_ID}/orders", data)

def place_equity_market(symbol, side, qty, duration="day", tag="daytradebot"):
    data = {"class":"equity","symbol":symbol,"side":side,"quantity":str(qty),
            "type":"market","duration":duration,"tag":tag}
    r = _post(f"/accounts/{TRADIER_ACCOUNT_ID}/orders", data); _log_order(r, data); return r

def place_equity_limit(symbol, side, qty, limit_price, duration="day", tag="daytradebot"):
    data = {"class":"equity","symbol":symbol,"side":side,"quantity":str(qty),
            "type":"limit","price":str(limit_price),"duration":duration,"tag":tag}
    r = _post(f"/accounts/{TRADIER_ACCOUNT_ID}/orders", data); _log_order(r, data); return r

def _log_order(r, data):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open("order_log.jsonl","a") as f:
            f.write(json.dumps({"ts":ts,"status":r.status_code,"req":data,"resp":r.text})+"\n")
    except Exception as e:
        print("[order_log] failed to write:", e)
