from dataclasses import dataclass
from typing import Dict, List, Tuple
from utils.pricing import midpoint, tick_offset

@dataclass
class Order:
    symbol: str
    side: str
    qty: int
    type: str
    time_in_force: str
    limit_price: float
    tag: str

class FastBreakStrategy:
    max_spread_bps = 25
    min_momo_bps = 8
    default_qty = 5
    max_notional = 2500
    tick_improve = 2

    def __init__(self):
        self.last_px = {}

    def _ok_liquidity(self, q: dict) -> bool:
        if not q or q.get("bid")==0 or q.get("ask")==0:
            return False
        spr = q["ask"] - q["bid"]
        mp = midpoint(q["bid"], q["ask"])
        return (spr / mp * 1e4) <= self.max_spread_bps

    def _momo_ok(self, sym: str, q: dict) -> Tuple[bool, float]:
        mp = midpoint(q["bid"], q["ask"])
        prev = self.last_px.get(sym, mp)
        chg = (mp - prev) / prev * 1e4
        self.last_px[sym] = mp
        return (chg >= self.min_momo_bps), chg

    def _sized_qty(self, q: dict) -> int:
        mp = midpoint(q["bid"], q["ask"])
        qty = max(1, min(self.default_qty, int(self.max_notional / max(1.0, mp))))
        return qty

    def generate(self, quotes: Dict[str, dict]) -> Tuple[List[Order], List[Order]]:
        buys, sells = [], []

        for sym, q in quotes.items():
            if not self._ok_liquidity(q):
                continue

            up, chg = self._momo_ok(sym, q)
            mp = midpoint(q["bid"], q["ask"])
            qty = self._sized_qty(q)

            if up:
                limit_px = tick_offset(mp, +self.tick_improve)
                buys.append(Order(sym, "buy", qty, "limit", "ioc", round(limit_px, 2), f"momo_up_{int(chg)}"))
            else:
                limit_px = tick_offset(mp, -self.tick_improve)
                sells.append(Order(sym, "sell", qty, "limit", "ioc", round(limit_px, 2), f"momo_down_{int(chg)}"))

        return buys, sells
