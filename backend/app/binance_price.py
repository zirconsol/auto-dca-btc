import logging
from typing import Optional

import requests


def fetch_price(symbol: str, base_url: str = "https://api.binance.com") -> Optional[float]:
    url = f"{base_url.rstrip('/')}/api/v3/ticker/price"
    try:
        resp = requests.get(url, params={"symbol": symbol}, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("price", 0))
    except Exception as exc:  # noqa: BLE001
        logging.error("No se pudo obtener precio para %s en %s: %s", symbol, base_url, exc)
        return None
