from __future__ import annotations
import os, time
import pandas as pd
from typing import Dict, List
from .config import SETTINGS
from .utils import log, tznow, within_session
from .universe import get_universe
from .data_sources import batch_intraday
from .strategy import compute_indicators, regime_from_spy, signals_for_symbol, allow_asset
from .risk import position_size, cap_for_slots
from .brokers import TradierClient, dry_place

def fetch_equity() -> float:
    # For simplicity: user can replace with broker equity query.
    # Default to 20k if not provided.
    return float(os.getenv("START_EQUITY", "20000"))

def manage_trails(open_positions):
    # Placeholder: wire your stop/partial logic here or via broker OCOs.
    pass

def flat_all():
    # Placeholder for 15:55 ET forced exit; iterate broker open positions and close.
    pass

def main():
    log.info("Starting DayTrade Bot")
    now = tznow(SETTINGS.timezone)
    # Early wait loop until entry window opens; still manage existing positions if any.
    if not within_session(now, SETTINGS.no_entry_before, SETTINGS.force_flat_at):
        log.info("Waiting for entry window...")
    # Universe
    uni = get_universe(SETTINGS.universe_file)
    symbols = list(dict.fromkeys(uni["A"] + uni["B"] + uni["ETF"]))  # de-dup

    # Data pull
    api_key = SETTINGS.eodhd_api_key
    if not api_key:
        log.error("EODHD_API_KEY missing. Exiting.")
        return

    data_raw = batch_intraday(symbols, api_key, interval="5m")
    # Compute indicators
    data_ind = {}
    for sym, df in data_raw.items():
        if df.empty: 
            continue
        data_ind[sym] = compute_indicators(df)

    if "SPY" not in data_ind:
        log.error("SPY data missing; cannot compute regime.")
        return
    regime = regime_from_spy(data_ind["SPY"])
    log.info(f"Market regime: {regime}")

    # Scan signals
    signals = []
    for sym, df in data_ind.items():
        if sym == "SPY": 
            continue
        if not allow_asset(sym, regime): 
            continue
        signals += signals_for_symbol(sym, df)
    log.info(f"Signals found: {len(signals)}")

    # Load current state (in-memory for simplicity)
    trades_done = 0
    open_positions = []

    # Broker setup
    has_tradier = bool(SETTINGS.tradier_access_token and SETTINGS.tradier_account_id)
    broker = None
    if has_tradier:
        broker = TradierClient(SETTINGS.tradier_access_token, SETTINGS.tradier_account_id, SETTINGS.tradier_base_url)
        log.info("Tradier client initialized")
    else:
        log.warning("Tradier credentials missing: running in DRY-RUN mode (no orders).")

    equity = fetch_equity()
    for sig in signals:
        if trades_done >= SETTINGS.max_trades: 
            break
        if len(open_positions) >= SETTINGS.max_open:
            break
        cap = SETTINGS.cap_boost if len(open_positions) < SETTINGS.max_open else SETTINGS.cap_base
        qty = position_size(sig["price"], equity, sig["stop_dist"], cap)
        if qty <= 0: 
            continue

        if has_tradier:
            oid = broker.marketable_limit("buy", sig["symbol"], qty, sig["entry_limit"])
        else:
            oid = dry_place("buy", sig["symbol"], qty, sig["entry_limit"])

        open_positions.append({"symbol": sig["symbol"], "qty": qty, "entry": sig["price"], "oid": oid})
        trades_done += 1

    log.info(f"Entries placed: {trades_done}. Open positions: {len(open_positions)}")

    # Manage trailing/partials here (looping service in production)
    manage_trails(open_positions)

if __name__ == "__main__":
    main()
