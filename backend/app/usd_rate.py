import logging
from functools import lru_cache
from typing import Optional

import requests


@lru_cache(maxsize=1)
def get_usd_rate() -> Optional[float]:
    """
    Devuelve la cotización del dólar (blue) en ARS usando la API pública de Bluelytics.
    Usa value_sell como referencia. Cachea la llamada para evitar repetirla en el mismo proceso.
    """
    url = "https://api.bluelytics.com.ar/v2/latest"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        blue = data.get("blue") or {}
        rate = float(blue.get("value_sell") or 0)
        if rate <= 0:
            return None
        return rate
    except Exception as exc:  # noqa: BLE001
        logging.error("No se pudo obtener cotización USD (Bluelytics): %s", exc)
        return None

