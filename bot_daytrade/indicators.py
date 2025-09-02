from __future__ import annotations
import numpy as np
import pandas as pd

def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / (loss.replace(0, np.nan))
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = (high - low).abs()
    tr = np.maximum(tr, (high - prev_close).abs())
    tr = np.maximum(tr, (low - prev_close).abs())
    return tr.rolling(period).mean()

def vwap(df: pd.DataFrame) -> pd.Series:
    pv = df["close"] * df["volume"]
    cum_pv = pv.cumsum()
    cum_v = df["volume"].cumsum().replace(0, np.nan)
    return (cum_pv / cum_v).fillna(method="ffill")

def keltner_channels(df: pd.DataFrame, ema_period: int = 20, atr_mult: float = 1.5):
    mid = ema(df["close"], ema_period)
    rng = atr(df, 14)
    upper = mid + atr_mult * rng
    lower = mid - atr_mult * rng
    return mid, upper, lower
