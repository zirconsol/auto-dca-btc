import logging
import sys
from pathlib import Path

# Asegura que el proyecto esté en sys.path al ejecutar el archivo directamente.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.binance_client import AssetBalance, BinanceClient
from src.config import load_config


class BTCBalanceChecker:
    """Consulta el balance de BTC de la cuenta (libre, bloqueado, total)."""

    def __init__(self, client: BinanceClient) -> None:
        self.client = client

    def get_balance(self) -> AssetBalance:
        return self.client.get_asset_balance("BTC")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    config = load_config()
    client = BinanceClient(
        api_key=config.api_key,
        api_secret=config.api_secret,
        base_url=config.base_url,
    )
    checker = BTCBalanceChecker(client)
    balance = checker.get_balance()
    logging.info(
        "Balance BTC -> libre: %.8f | bloqueado: %.8f | total: %.8f",
        balance.free,
        balance.locked,
        balance.total,
    )


if __name__ == "__main__":
    main()
