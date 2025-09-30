
from datetime import datetime
from zoneinfo import ZoneInfo
import math
from brokers.tradier_client import market_is_open, balances, preview_equity, place_equity

DEFAULT_MIN_NOTIONAL = 10.0
MAX_RISK_PCT = 0.15
ASSUMED_EQUITY = 6000.0

def get_wallet():
    r = balances()
    if r.status_code != 200:
        return {"ok": False, "err": f"HTTP {r.status_code}", "raw": r.text}
    b = r.json().get("balances", {})
    acct_type = b.get("account_type", "margin")
    margin = b.get("margin", {}) or {}
    return {
        "ok": True,
        "account_type": acct_type,
        "stock_buying_power": float(margin.get("stock_buying_power", 0) or 0)
    }

def calc_qty(price, equity=ASSUMED_EQUITY):
    import math
    qty = max(0, math.floor((MAX_RISK_PCT * equity) / max(price, 0.01)))
    return max(qty, 1)  # ensure at least 1 share

def try_trade(symbol, signal, last_price, allow_live=False, min_notional=DEFAULT_MIN_NOTIONAL):
    now = datetime.now(ZoneInfo("America/New_York"))
    if not market_is_open(now):
        return {"status":"skip","reason":"market closed"}
    w = get_wallet()
    if not w["ok"]:
        return {"status":"error","detail":w}
    if w["stock_buying_power"] < min_notional:
        return {"status":"skip","reason":"low buying power","balances":w}
    qty = calc_qty(last_price)
    if qty < 1:
        return {"status":"skip","reason":"qty=0","balances":w}
    if signal != "buy":
        return {"status":"skip","reason":"neutral","balances":w}
    pv = preview_equity(symbol,"buy",qty)
    if pv.status_code != 200:
        return {"status":"skip","reason":"preview error","resp":pv.text}
    if not allow_live:
        return {"status":"ok","action":"preview-only","qty":qty,"symbol":symbol,"balances":w}
    resp = place_equity(symbol,"buy",qty)
    return {"status":"sent","qty":qty,"symbol":symbol,"resp_code":resp.status_code,"resp_body":resp.text}
