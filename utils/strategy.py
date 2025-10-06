
from datetime import datetime
from zoneinfo import ZoneInfo
import math

from brokers.tradier_client import market_is_open, balances, preview_equity_market, place_equity_limit, quote as q_fast, positions

# --- Moderate-Aggressive Tunings ---
DEFAULT_MIN_NOTIONAL = 10.0      # keep tiny trades allowed
MAX_RISK_PCT         = 0.25      # 25% of equity per trade (more assertive sizing)
ASSUMED_EQUITY       = 6000.0    # used when balances not available
MAX_GROSS_EXPOSURE   = 0.85      # allow larger concurrent exposure

def get_wallet():
    r = balances()
    if r.status_code != 200:
        return {"ok": False, "err": f"HTTP {r.status_code}", "raw": r.text}
    b = r.json().get("balances", {})
    margin = b.get("margin", {}) or {}
    return {
        "ok": True,
        "account_type": b.get("account_type", "margin"),
        "stock_buying_power": float(margin.get("stock_buying_power", 0) or 0),
        "total_cash": float(b.get("total_cash", 0) or 0),
    }

def calc_qty(price, equity=ASSUMED_EQUITY, qty_cap=None):
    qty = max(0, math.floor((MAX_RISK_PCT * equity) / max(price, 0.01)))
    qty = max(qty, 1)  # 1-share floor
    if qty_cap is not None:
        qty = min(qty, int(qty_cap))
    return qty

def exposure_ok(price, qty, equity=ASSUMED_EQUITY):
    return (price * qty) <= (MAX_GROSS_EXPOSURE * equity)

def marketable_limit_for_buy(symbol, last_price):
    q = q_fast(symbol)
    return max(q["ask"], last_price) + 0.01

def marketable_limit_for_sell(symbol, last_price):
    q = q_fast(symbol)
    return max(0.01, min(q["bid"], last_price) - 0.01)

def try_trade(symbol: str, signal: str, last_price: float, allow_live: bool=False, min_notional: float = DEFAULT_MIN_NOTIONAL, qty_cap=None):
    now = datetime.now(ZoneInfo("America/New_York"))
    if not market_is_open(now):
        return {"status":"skip", "reason":"market closed"}
    w = get_wallet()
    if not w.get("ok"):
        return {"status":"error", "reason":"balances error", "detail":w}
    if w["stock_buying_power"] < min_notional:
        return {"status":"skip", "reason":f"buying_power {w['stock_buying_power']:.2f} < {min_notional}", "balances":w}
    qty = calc_qty(last_price, qty_cap=qty_cap)
    if not exposure_ok(last_price, qty):
        return {"status":"skip", "reason":"gross exposure cap", "balances":w}
    if signal != "buy":
        return {"status":"skip", "reason":"neutral", "balances":w}
    pv = preview_equity_market(symbol, "buy", qty)
    if pv.status_code != 200:
        return {"status":"skip", "reason":f"preview error {pv.status_code}", "resp":pv.text, "balances":w}
    limit = marketable_limit_for_buy(symbol, last_price)
    if not allow_live:
        return {"status":"ok", "action":"preview-only", "qty":qty, "symbol":symbol, "limit":limit, "balances":w}
    resp = place_equity_limit(symbol, "buy", qty, limit_price=limit)
    return {"status":"sent", "side":"buy", "qty":qty, "symbol":symbol, "limit":limit, "resp_code":resp.status_code, "resp_body":resp.text, "balances":w}

# ---- Auto exits (unchanged) ----
def _positions_map():
    r = positions()
    if r.status_code != 200:
        return {"ok": False, "err": f"HTTP {r.status_code}", "raw": r.text}
    try:
        data = r.json().get("positions", {}).get("position", [])
        if isinstance(data, dict): data = [data]
        out = {}
        for p in data or []:
            sym = p["symbol"].upper()
            qty = int(p.get("quantity") or 0)
            entry = None
            for k in ("cost_basis","costbasis","average_price","avg_price","price","lastprice"):
                if k in p and p[k] is not None:
                    try:
                        entry = float(p[k]); break
                    except: pass
            if entry is None: entry = 0.0
            out[sym] = {"qty": qty, "entry": entry}
        return {"ok": True, "positions": out}
    except Exception as e:
        return {"ok": False, "err": f"parse error: {e}", "raw": r.text}

def check_and_exit_positions(qmap, tp_pct=1.0, sl_pct=0.5, allow_live=False):
    pos = _positions_map()
    if not pos.get("ok"):
        return {"status":"error", "detail": pos}
    results = []
    for sym, meta in pos["positions"].items():
        qty = meta["qty"]
        if qty <= 0: continue
        entry = meta["entry"]
        q = qmap.get(sym) or q_fast(sym)
        last = q["last"]
        pnl_pct = ((last - entry) / entry * 100.0) if entry > 0 else 0.0
        reason = None
        if entry > 0 and pnl_pct >= float(tp_pct):
            reason = f"take-profit {pnl_pct:.2f}% >= {tp_pct}%"
        elif entry > 0 and pnl_pct <= -float(sl_pct):
            reason = f"stop-loss {pnl_pct:.2f}% <= -{sl_pct}%"
        if reason:
            limit = marketable_limit_for_sell(sym, last)
            if allow_live:
                resp = place_equity_limit(sym, "sell", qty, limit_price=limit)
                results.append({"symbol": sym, "qty": qty, "limit": limit, "action": "sent-sell", "reason": reason, "resp_code": resp.status_code, "resp_body": (resp.text or "")[:2000]})
            else:
                results.append({"symbol": sym, "qty": qty, "limit": limit, "action": "preview-sell", "reason": reason})
        else:
            results.append({"symbol": sym, "qty": qty, "action": "hold", "pnl_pct": round(pnl_pct,2)})
    return {"status":"ok", "exits": results}
