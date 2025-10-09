
import os, requests
TRADIER_BASE = os.getenv("TRADIER_BASE", "https://api.tradier.com/v1")
TRADIER_TOKEN = os.getenv("TRADIER_TOKEN")
ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID")
TIMEOUT = float(os.getenv("TRADIER_TIMEOUT", "10"))

HDRS_JSON = {"Authorization": f"Bearer {TRADIER_TOKEN}", "Accept": "application/json"}
HDRS_FORM = {"Authorization": f"Bearer {TRADIER_TOKEN}", "Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}

class TradierBroker:
    def __init__(self, preview_only=False):
        self.preview_only = preview_only

    def fetch_quote(self, symbol: str):
        r = requests.get(f"{TRADIER_BASE}/markets/quotes", headers=HDRS_JSON, params={"symbols": symbol}, timeout=TIMEOUT)
        r.raise_for_status()
        q = (r.json().get("quotes", {}) or {}).get("quote", {})
        if isinstance(q, list):
            q = q[0] if q else {}
        return {"symbol": q.get("symbol"), "bid": float(q.get("bid", 0) or 0), "ask": float(q.get("ask", 0) or 0), "last": float(q.get("last", 0) or 0), "volume": int(q.get("volume", 0) or 0)}

    def submit_order(self, order: dict):
        if self.preview_only:
            return {"ok": True, "status": "preview-only", **order}
        payload = {
            "class": "equity",
            "symbol": order["symbol"],
            "side": order["side"],
            "quantity": str(order["qty"]),
            "type": "limit",
            "duration": "day",
            "time_in_force": order.get("time_in_force", "ioc"),
            "price": f"{order['limit_price']:.2f}",
            "tag": order.get("tag", "fastbreak")
        }
        r = requests.post(f"{TRADIER_BASE}/accounts/{ACCOUNT_ID}/orders", headers=HDRS_FORM, data=payload, timeout=TIMEOUT)
        try:
            return r.json()
        except Exception:
            return {"status_code": r.status_code, "text": r.text}
