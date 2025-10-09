def midpoint(bid, ask):
    if bid and ask:
        return (bid + ask) / 2.0
    return max(bid, ask)

def tick_offset(px, ticks, tick_size=0.01):
    return px + ticks * tick_size
