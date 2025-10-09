def midpoint(bid: float, ask: float) -> float:
    if bid and ask:
        return (bid + ask) / 2.0
    return max(bid, ask)

def tick_offset(px: float, ticks: int, tick_size: float = 0.01) -> float:
    return px + ticks * tick_size
