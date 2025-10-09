from datetime import datetime

# zoneinfo fallback for older Python
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:  # pragma: no cover
    try:
        from backports.zoneinfo import ZoneInfo  # backport
    except Exception:
        ZoneInfo = None

def nyc_now():
    if ZoneInfo is None:
        # naive fallback; UTC naive time
        return datetime.utcnow()
    return datetime.now(ZoneInfo("America/New_York"))

def market_is_open(now=None):
    now = now or nyc_now()
    # naive fallback: assume already in ET if ZoneInfo missing
    if ZoneInfo is None:
        hour = now.hour
        minute = now.minute
        weekday = now.weekday()
        if weekday > 4:
            return False
        return (hour > 9 or (hour == 9 and minute >= 30)) and (hour < 16 or (hour == 16 and minute == 0))
    if now.weekday() > 4:
        return False
    open_t = now.replace(hour=9, minute=30, second=0, microsecond=0)
    close_t = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return open_t <= now <= close_t
