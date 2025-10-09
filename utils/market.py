from datetime import datetime
from zoneinfo import ZoneInfo

def nyc_now():
    return datetime.now(ZoneInfo("America/New_York"))

def market_is_open(now=None):
    now = now or nyc_now()
    if now.weekday() > 4:
        return False
    open_t = now.replace(hour=9, minute=30, second=0, microsecond=0)
    close_t = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return open_t <= now <= close_t
