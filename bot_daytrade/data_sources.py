from __future__ import annotations
import requests, pandas as pd, time
from typing import List, Dict, Any
from tenacity import retry, wait_fixed, stop_after_attempt
from .utils import log

EODHD_BASE = "https://eodhd.com/api"

@retry(wait=wait_fixed(1), stop=stop_after_attempt(3))
def eodhd_intraday(symbol: str, api_key: str, interval: str = "5m", session: requests.Session | None = None) -> pd.DataFrame:
    s = session or requests.Session()
    url = f"{EODHD_BASE}/intraday/{symbol}.US?api_token={api_key}&interval={interval}&order=d&fmt=json"
    r = s.get(url, timeout=10)
    r.raise_for_status()
    js = r.json()
    if not isinstance(js, list):
        raise RuntimeError(f"Bad intraday response for {symbol}: {js}")
    df = pd.DataFrame(js)
    # Expect columns: datetime, open, high, low, close, volume
    for col in ["open","high","low","close","volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def batch_intraday(symbols: List[str], api_key: str, interval: str = "5m") -> Dict[str, pd.DataFrame]:
    out: Dict[str, pd.DataFrame] = {}
    for sym in symbols:
        try:
            out[sym] = eodhd_intraday(sym, api_key, interval)
        except Exception as e:
            log.warning(f"Intraday fetch failed for {sym}: {e}")
    return out
