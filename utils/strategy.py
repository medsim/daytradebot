
from datetime import datetime
from zoneinfo import ZoneInfo
import math

from brokers.tradier_client import market_is_open, balances, preview_equity_market, place_equity_limit, quote as q_fast

# Tunables
DEFAULT_MIN_NOTIONAL = 10.0      # lowered threshold to allow more trades
MAX_RISK_PCT         = 0.15      # 15% of equity per trade (demo)
ASSUMED_EQUITY       = 6000.0    # for qty sizing
MAX_GROSS_EXPOSURE   = 0.40      # 40% cap on total new notional (naive)

def get_wallet():
    r = balances()
    if r.status_code != 200:
        return {"ok": False, "err": f"HTTP {r.status_code}", "raw": r.text}
    b = r.json().get("balances", {})
    acct_type = b.get("account_type", "margin")
    margin = b.get("margin", {}) or {}
    stock_bp = float(margin.get("stock_buying_power", 0) or 0)
    total_cash = float(b.get("total_cash", 0) or 0)
    return {"ok": True, "account_type": acct_type, "stock_buying_power": stock_bp, "total_cash": total_cash}

def calc_qty(price, equity=ASSUMED_EQUITY):
    qty = max(0, math.floor((MAX_RISK_PCT * equity) / max(price, 0.01)))
    return max(qty, 1)  # 1-share floor

def exposure_ok(price, qty, equity=ASSUMED_EQUITY):
    new_notional = price * qty
    return new_notional <= (MAX_GROSS_EXPOSURE * equity)

def try_trade(symbol: str, signal: str, last_price: float, allow_live: bool=False, min_notional: float = DEFAULT_MIN_NOTIONAL):
    now = datetime.now(ZoneInfo("America/New_York"))
    if not market_is_open(now):
        return {"status":"skip", "reason":"market closed"}

    w = get_wallet()
    if not w.get("ok"):
        return {"status":"error", "reason":"balances error", "detail":w}

    if w["stock_buying_power"] < min_notional:
        return {"status":"skip", "reason":f"buying_power {w['stock_buying_power']:.2f} < {min_notional}", "balances":w}

    qty = calc_qty(last_price)
    if not exposure_ok(last_price, qty):
        return {"status":"skip", "reason":"gross exposure cap", "balances":w}

    if signal != "buy":
        return {"status":"skip", "reason":"neutral", "balances":w}

    pv = preview_equity_market(symbol, "buy", qty)
    if pv.status_code != 200:
        return {"status":"skip", "reason":f"preview error {pv.status_code}", "resp":pv.text, "balances":w}

    # marketable-limit: cross the ask by 1 cent to get filled quickly but with price control
    q = q_fast(symbol)
    limit = max(q["ask"], last_price) + 0.01

    if not allow_live:
        return {"status":"ok", "action":"preview-only", "qty":qty, "symbol":symbol, "limit":limit, "balances":w}

    resp = place_equity_limit(symbol, "buy", qty, limit_price=limit)
    return {"status":"sent", "qty":qty, "symbol":symbol, "limit":limit, "resp_code":resp.status_code, "resp_body":resp.text, "balances":w}
