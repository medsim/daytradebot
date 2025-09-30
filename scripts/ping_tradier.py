
from brokers.tradier_client import profile, balances, positions, orders, preview_equity

def show(name, r):
    print(f"\n== {name} ==")
    print(r.status_code, (r.text or "")[:2000])

show("Profile", profile())
show("Balances", balances())
show("Positions", positions())
show("Orders", orders())
show("Preview", preview_equity("F","buy",1))
