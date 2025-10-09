
def load_watchlist(path: str):
    syms = []
    try:
        with open(path, "r") as f:
            for line in f:
                s = line.strip().upper()
                if not s or s.startswith("#"):
                    continue
                syms.append(s)
    except FileNotFoundError:
        syms = ["AAPL","MSFT","NVDA","AMD","META","TSLA","IONQ","PLTR","SOFI","INTC"]
    return syms
