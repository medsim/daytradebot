
from brokers.tradier_client import profile, balances, positions, orders, preview_equity_market

def show(title, r):
    print("\n==", title, "==")
    try:
        print(r.status_code)
        print((r.text or "")[:4000])
    except Exception as e:
        print("error printing response:", e)

for title, fn in [
    ("Profile", profile),
    ("Balances", balances),
    ("Positions", positions),
    ("Orders (history)", orders),
]:
    show(title, fn())

print("\n== Preview F buy 1 (market) ==")
show("Preview", preview_equity_market("F", "buy", 1))
