
import os, time, json, requests
from datetime import datetime
from zoneinfo import ZoneInfo

TRADIER_BASE = os.getenv("TRADIER_BASE", "https://api.tradier.com/v1")  # or https://sandbox.tradier.com/v1
TRADIER_TOKEN = os.getenv("TRADIER_TOKEN")
TRADIER_ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID")
TIMEOUT = 20

if not TRADIER_TOKEN:
    print("[warn] TRADIER_TOKEN is not set")
if not TRADIER_ACCOUNT_ID:
    print("[warn] TRADIER_ACCOUNT_ID is not set")

HDRS_JSON = {"Authorization": f"Bearer {TRADIER_TOKEN}", "Accept": "application/json"}
HDRS_FORM = {"Authorization": f"Bearer {TRADIER_TOKEN}", "Accept": "application/json",
             "Content-Type": "application/x-www-form-urlencoded"}

def _get(path, params=None):
    return requests.get(f"{TRADIER_BASE}{path}", headers=HDRS_JSON, params=params, timeout=TIMEOUT)

def _post(path, data):
    # Tradier requires x-www-form-urlencoded for orders
    return requests.post(f"{TRADIER_BASE}{path}", headers=HDRS_FORM, data=data, timeout=TIMEOUT)

def market_is_open(now=None):
    now = now or datetime.now(ZoneInfo("America/New_York"))
    if now.weekday() > 4:  # Sat/Sun
        return False
    open_t  = now.replace(hour=9, minute=30, second=0, microsecond=0)
    close_t = now.replace(hour=16, minute=0,  second=0, microsecond=0)
    return open_t <= now <= close_t

def profile():   return _get("/user/profile")
def accounts():  return _get("/accounts")
def balances():  return _get(f"/accounts/{TRADIER_ACCOUNT_ID}/balances")
def positions(): return _get(f"/accounts/{TRADIER_ACCOUNT_ID}/positions")
def orders():    return _get(f"/accounts/{TRADIER_ACCOUNT_ID}/orders")

def preview_equity(symbol, side, qty, order_type="market", duration="day", price=None, stop=None):
    data = {"class":"equity","symbol":symbol,"side":side,"quantity":str(qty),
            "type":order_type,"duration":duration,"preview":"true"}
    if order_type == "limit" and price is not None: data["price"]=str(price)
    if order_type == "stop"  and stop  is not None: data["stop"]=str(stop)
    return _post(f"/accounts/{TRADIER_ACCOUNT_ID}/orders", data)

def place_equity(symbol, side, qty, order_type="market", duration="day",
                 price=None, stop=None, tag="daytradebot"):
    data = {"class":"equity","symbol":symbol,"side":side,"quantity":str(qty),
            "type":order_type,"duration":duration,"tag":tag}
    if order_type == "limit" and price is not None: data["price"]=str(price)
    if order_type == "stop"  and stop  is not None: data["stop"]=str(stop)

    r = _post(f"/accounts/{TRADIER_ACCOUNT_ID}/orders", data)
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open("order_log.jsonl","a") as f:
            f.write(json.dumps({"ts":ts,"req":data,"status":r.status_code,"resp":r.text})+"\n")
    except Exception as e:
        print("[order_log] failed to write:", e)
    return r
