
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except Exception:
    try:
        from backports.zoneinfo import ZoneInfo
    except Exception:
        ZoneInfo = None

def nyc_now():
    if ZoneInfo is None:
        return datetime.utcnow()
    return datetime.now(ZoneInfo("America/New_York"))

def market_is_open(now=None):
    now = now or nyc_now()
    if ZoneInfo is None:
        weekday = now.weekday()
        hour = now.hour
        minute = now.minute
        if weekday > 4:
            return False
        return (hour > 9 or (hour == 9 and minute >= 30)) and (hour < 16 or (hour == 16 and minute == 0))
    if now.weekday() > 4:
        return False
    open_t = now.replace(hour=9, minute=30, second=0, microsecond=0)
    close_t = now.replace(hour=16, minute=0, microsecond=0)
    return open_t <= now <= close_t
