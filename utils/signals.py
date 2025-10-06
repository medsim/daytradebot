
import os, requests
TRADIER_BASE = os.getenv("TRADIER_BASE", "https://api.tradier.com/v1")
TRADIER_TOKEN = os.getenv("TRADIER_TOKEN")
HDRS = {"Authorization": f"Bearer {TRADIER_TOKEN}", "Accept": "application/json"}
def quote(symbol: str):
    r = requests.get(f"{TRADIER_BASE}/markets/quotes", headers=HDRS, params={"symbols": symbol}, timeout=10)
    r.raise_for_status()
    q = r.json()["quotes"]["quote"]
    last = float(q["last"]); change_pct = float(q.get("change_percentage") or 0.0)
    bid = float(q.get("bid") or last); ask = float(q.get("ask") or last)
    return {"last": last, "change_pct": change_pct, "bid": bid, "ask": ask}
def momentum_signal(symbol: str, up_thresh=0.1):
    q = quote(symbol)
    if q["change_pct"] >= up_thresh: return "buy", q
    return "neutral", q
