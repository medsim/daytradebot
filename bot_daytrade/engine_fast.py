
import os, time, random
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.logging import get_logger
from utils.market import market_is_open
from utils.watchlist import load_watchlist
from bot_daytrade.strategy_fastbreak import FastBreakStrategy
from brokers.tradier_fastpatch import TradierBroker

POLL_SECONDS = float(os.getenv("POLL_SECONDS", "2.0"))
MAX_WORKERS  = int(os.getenv("MAX_WORKERS", "16"))
UNIVERSE_MAX = int(os.getenv("UNIVERSE_MAX", "100"))
SHUFFLE      = os.getenv("SHUFFLE_UNIVERSE", "true").lower() == "true"

log = get_logger("engine_fast")

class FastEngine:
    def __init__(self, broker: TradierBroker, strategy: FastBreakStrategy):
        self.broker = broker
        self.strategy = strategy
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self, watchlist_path: str):
        symbols = load_watchlist(watchlist_path)[:UNIVERSE_MAX]
        if SHUFFLE:
            random.shuffle(symbols)
        log.info(f"Universe size: {len(symbols)} (UNIVERSE_MAX={UNIVERSE_MAX})")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            while not self._stop:
                if not market_is_open():
                    time.sleep(10)
                    continue

                futs = {pool.submit(self.broker.fetch_quote, s): s for s in symbols}
                quotes = {}
                for fut in as_completed(futs):
                    sym = futs[fut]
                    try:
                        q = fut.result()
                        if q: quotes[sym] = q
                    except Exception as e:
                        log.warning(f"Quote error {sym}: {e}")

                entries, exits = self.strategy.generate(quotes)

                order_futs = []
                for o in entries + exits:
                    order_futs.append(pool.submit(self.broker.submit_order, o.__dict__))

                for fut in as_completed(order_futs):
                    try:
                        res = fut.result()
                        log.info(f"Order response: {res}")
                    except Exception as e:
                        log.error(f"Order error: {e}")

                time.sleep(POLL_SECONDS)
