from __future__ import annotations
import math
from typing import Dict
from .config import SETTINGS

def position_size(price: float, equity: float, stop_dist: float, cap: float) -> int:
    risk_dollars = equity * SETTINGS.risk_pct
    by_risk = math.floor(risk_dollars / max(0.01, stop_dist))
    by_cap = math.floor(cap / max(0.01, price))
    return max(0, min(by_risk, by_cap))

def cap_for_slots(open_positions_count: int) -> float:
    return SETTINGS.cap_boost if open_positions_count < SETTINGS.max_open else SETTINGS.cap_base
