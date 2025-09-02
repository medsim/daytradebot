import os
from dataclasses import dataclass

@dataclass
class Settings:
    timezone: str = os.getenv("TIMEZONE", "America/New_York")
    max_open: int = int(os.getenv("MAX_OPEN", "5"))
    max_trades: int = int(os.getenv("MAX_TRADES", "20"))
    cap_base: float = float(os.getenv("CAP_BASE", "750"))
    cap_boost: float = float(os.getenv("CAP_BOOST", "1000"))
    risk_pct: float = float(os.getenv("RISK_PCT", "0.004"))
    no_entry_before: str = os.getenv("NO_ENTRY_BEFORE", "09:45")
    force_flat_at: str = os.getenv("FORCE_FLAT_AT", "15:55")
    universe_file: str = os.getenv("UNIVERSE_FILE", "")
    eodhd_api_key: str = os.getenv("EODHD_API_KEY", "")
    tradier_access_token: str = os.getenv("TRADIER_ACCESS_TOKEN", "")
    tradier_account_id: str = os.getenv("TRADIER_ACCOUNT_ID", "")
    tradier_base_url: str = os.getenv("TRADIER_BASE_URL", "https://sandbox.tradier.com")

SETTINGS = Settings()
