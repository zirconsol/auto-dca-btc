import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Settings:
    db_url: str
    price_symbol: str
    price_base_url: str
    withdraw_network: str
    withdraw_address: str | None


def get_settings() -> Settings:
    load_dotenv()
    db_url = os.getenv("DCA_DB_URL") or "sqlite:///./dca.db"
    # Prioriza el env específico, luego TRADE_SYMBOL (para alinear con BTCARS), sino USDT.
    price_symbol = (os.getenv("DCA_PRICE_SYMBOL") or os.getenv("TRADE_SYMBOL") or "BTCUSDT").upper()
    price_base_url = os.getenv("DCA_PRICE_BASE_URL") or "https://api.binance.com"
    withdraw_network = (os.getenv("WITHDRAW_NETWORK") or "BSC").upper()
    withdraw_address = os.getenv("WITHDRAW_ADDRESS")

    return Settings(
        db_url=db_url,
        price_symbol=price_symbol,
        price_base_url=price_base_url.rstrip("/"),
        withdraw_network=withdraw_network,
        withdraw_address=withdraw_address,
    )
