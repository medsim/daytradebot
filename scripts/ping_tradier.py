
from brokers.tradier_client import profile, accounts, balances, positions, orders, preview_equity

def show(title, r):
    print("\n==", title, "==")
    try:
        print(r.status_code)
        print((r.text or "")[:4000])
    except Exception as e:
        print("error printing response:", e)

for title, fn in [
    ("Profile", profile),
    ("Accounts", accounts),
    ("Balances", balances),
    ("Positions", positions),
    ("Orders (history)", orders),
]:
    show(title, fn())

print("\n== Preview SPY buy 1 ==")
show("Preview", preview_equity("SPY", "buy", 1))
