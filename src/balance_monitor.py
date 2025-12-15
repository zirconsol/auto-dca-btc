import logging
import time
from typing import Callable

from src.binance_client import AssetBalance, BinanceClient


class BalanceMonitor:
    def __init__(
        self,
        client: BinanceClient,
        asset: str,
        poll_interval_seconds: float = 10,
        on_result: Callable[[AssetBalance], None] | None = None,
    ) -> None:
        self.client = client
        self.asset = asset
        self.poll_interval_seconds = poll_interval_seconds
        self.on_result = on_result

    def run_forever(self) -> None:
        logging.info(
            "Iniciando monitoreo de balance para %s cada %.1f segundos",
            self.asset,
            self.poll_interval_seconds,
        )
        while True:
            try:
                balance = self.client.get_asset_balance(self.asset)
                if self.on_result:
                    self.on_result(balance)
                else:
                    logging.info(
                        "Balance %s -> libre: %.8f | bloqueado: %.8f | total: %.8f",
                        balance.asset,
                        balance.free,
                        balance.locked,
                        balance.total,
                    )
            except KeyboardInterrupt:
                logging.info("Monitoreo detenido por el usuario.")
                break
            except Exception as exc:
                logging.error("Error en el ciclo de monitoreo: %s", exc)
            time.sleep(self.poll_interval_seconds)
