def load_watchlist(path: str):
    syms = []
    with open(path, "r") as f:
        for line in f:
            s = line.strip().upper()
            if not s or s.startswith("#"):
                continue
            syms.append(s)
    return syms
