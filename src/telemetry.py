import logging
from datetime import datetime
from typing import Optional

import requests


class TradeReporter:
    def __init__(self, base_url: Optional[str]) -> None:
        self.base_url = base_url.rstrip("/") if base_url else None

    def is_enabled(self) -> bool:
        return bool(self.base_url)

    def report_trade(
        self,
        *,
        buy_timestamp: datetime,
        fiat_spent: float,
        btc_bought: float,
        price_fiat_per_btc: float,
        wallet: str,
        transfer_timestamp: Optional[datetime] = None,
    ) -> None:
        if not self.base_url:
            return

        payload = {
            "buy_timestamp": buy_timestamp.isoformat(),
            "fiat_spent": fiat_spent,
            "btc_bought": btc_bought,
            "price_fiat_per_btc": price_fiat_per_btc,
            "wallet": wallet,
            "transfer_timestamp": transfer_timestamp.isoformat() if transfer_timestamp else None,
        }
        try:
            resp = requests.post(f"{self.base_url}/trades", json=payload, timeout=5)
            resp.raise_for_status()
            logging.info("Trade registrado en backend: %s", resp.json())
        except Exception as exc:  # noqa: BLE001
            logging.error("No se pudo registrar el trade en backend: %s", exc)
