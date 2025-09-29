
from datetime import datetime
from zoneinfo import ZoneInfo
import math

from brokers.tradier_client import market_is_open, balances, preview_equity, place_equity

MIN_NOTIONAL   = 200.0     # skip tiny orders that round to qty=0
MAX_RISK_PCT   = 0.33      # per-trade cap for ~$6k cash ≈ $2k
ASSUMED_EQUITY = 6000.0

def get_cash_triplet():
    r = balances()
    if r.status_code != 200:
        return {"ok": False, "err": f"HTTP {r.status_code}", "raw": r.text}
    try:
        b = r.json().get("balances", {})
        cash = float(b.get("cash", 0) or 0)
        cash_avail = float(b.get("cash_available", 0) or 0)
        unsettled = float(b.get("unsettled_funds", 0) or 0)
        return {"ok": True, "cash": cash, "cash_available": cash_avail, "unsettled_funds": unsettled}
    except Exception as e:
        return {"ok": False, "err": f"parse error: {e}", "raw": r.text}

def calc_qty(price, equity=ASSUMED_EQUITY):
    return max(0, math.floor((MAX_RISK_PCT*equity)/max(price,0.01)))

def try_trade(symbol: str, signal: str, last_price: float, allow_live: bool=False):
    now = datetime.now(ZoneInfo("America/New_York"))
    if not market_is_open(now):
        return {"status":"skip", "reason":"market closed"}

    cash = get_cash_triplet()
    if not cash.get("ok", False):
        return {"status":"error", "reason":"balances error", "detail":cash}

    cash_avail = cash["cash_available"]
    if cash_avail < MIN_NOTIONAL:
        return {"status":"skip", "reason":f"cash_available {cash_avail:.2f} < {MIN_NOTIONAL} (cash acct, T+1)", "balances":cash}

    qty = calc_qty(last_price)
    if qty < 1:
        return {"status":"skip", "reason":f"qty=0 (price={last_price:.2f}, equity={ASSUMED_EQUITY:.0f})", "balances":cash}

    if signal != "buy":
        return {"status":"skip", "reason":"neutral/no-sell-path", "balances":cash}

    pv = preview_equity(symbol, "buy", qty)
    if pv.status_code != 200:
        return {"status":"skip", "reason":f"preview error {pv.status_code}", "resp":pv.text}

    if not allow_live:
        return {"status":"ok", "action":"preview-only", "qty":qty, "symbol":symbol, "price":last_price}

    resp = place_equity(symbol, "buy", qty, order_type="market")
    return {"status":"sent", "qty":qty, "symbol":symbol, "resp_code":resp.status_code, "resp_body":resp.text}
