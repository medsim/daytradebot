import os
from brokers.tradier_fastpatch import TradierBroker
from bot_daytrade.engine_fast import FastEngine
from bot_daytrade.strategy_fastbreak import FastBreakStrategy

WATCHLIST = os.getenv("WATCHLIST", "sample_watchlist.csv")

def main():
    broker = TradierBroker(preview_only=os.getenv("ALLOW_LIVE", "false").lower() != "true")
    strategy = FastBreakStrategy()
    engine = FastEngine(broker, strategy)
    engine.run(WATCHLIST)

if __name__ == "__main__":
    main()
