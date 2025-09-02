from __future__ import annotations
import requests, time
from typing import Optional, Dict, Any
from .utils import log

class TradierClient:
    def __init__(self, token: str, account_id: str, base_url: str):
        self.token = token
        self.account_id = account_id
        self.base = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        })
        self.live = "sandbox" not in self.base

    def _post(self, path: str, data: Dict[str, Any]):
        url = f"{self.base}{path}"
        r = self.session.post(url, data=data, timeout=10)
        if r.status_code >= 400:
            log.error(f"Tradier error {r.status_code} {r.text}")
        r.raise_for_status()
        return r.json()

    def marketable_limit(self, side: str, symbol: str, qty: int, limit_px: float) -> Optional[str]:
        if qty <= 0:
            return None
        data = {
            "class": "equity",
            "symbol": symbol,
            "duration": "day",
            "side": side,
            "quantity": qty,
            "type": "limit",
            "price": f"{limit_px:.2f}",
            "account_id": self.account_id,
        }
        js = self._post("/v1/accounts/{}/orders".format(self.account_id), data=data)
        order_id = str(js.get("order", {}).get("id", ""))
        log.info(f"Placed {side} {qty} {symbol} @ {limit_px:.2f} (id={order_id})")
        return order_id

def dry_place(side: str, symbol: str, qty: int, limit_px: float) -> str:
    log.info(f"[DRY] {side} {qty} {symbol} @ {limit_px:.2f}")
    return "DRY-ORDER"
