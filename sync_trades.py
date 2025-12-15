"""
Sincroniza compras de BTC desde Binance hacia el backend (Supabase vía FastAPI).

Usa:
- Credenciales Binance y trade symbol desde .env
- BACKEND_API_BASE para enviar POST /trades
"""
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Set

import requests

# Asegura imports de src/*
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.binance_client import BinanceClient  # noqa: E402
from src.config import load_config  # noqa: E402
from src.telemetry import TradeReporter  # noqa: E402


def fetch_existing_trades(api_base: str) -> Set[str]:
    try:
        resp = requests.get(f"{api_base}/trades", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return {t.get("buy_timestamp") for t in data if t.get("buy_timestamp")}
    except Exception as exc:  # noqa: BLE001
        logging.error("No se pudieron obtener trades existentes: %s", exc)
        return set()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    config = load_config()

    if not config.backend_api_base:
        logging.error("Define BACKEND_API_BASE para sincronizar trades.")
        sys.exit(1)

    client = BinanceClient(
        api_key=config.api_key,
        api_secret=config.api_secret,
        base_url=config.base_url,
    )
    reporter = TradeReporter(base_url=config.backend_api_base)

    logging.info("Obteniendo trades de Binance para %s ...", config.trade_symbol)
    trades = client.get_my_trades(config.trade_symbol)
    if not trades:
        logging.info("No se encontraron trades en Binance para %s", config.trade_symbol)
        return

    existing = fetch_existing_trades(config.backend_api_base)
    created = 0
    skipped = 0

    for t in sorted(trades, key=lambda x: x.get("time", 0)):
        buy_dt = datetime.fromtimestamp(int(t.get("time", 0)) / 1000, tz=timezone.utc)
        buy_iso = buy_dt.isoformat()
        qty = float(t.get("qty", 0))
        quote_qty = float(t.get("quoteQty", 0))
        price = float(t.get("price", 0))

        if buy_iso in existing:
            skipped += 1
            continue

        reporter.report_trade(
            buy_timestamp=buy_dt,
            fiat_spent=quote_qty,
            btc_bought=qty,
            price_fiat_per_btc=price if price > 0 else (quote_qty / qty if qty else 0),
            wallet=config.withdraw_address or "",
            transfer_timestamp=None,
        )
        created += 1

    logging.info("Sincronización completada. Nuevos: %s | Omitidos (ya estaban): %s", created, skipped)


if __name__ == "__main__":
    main()
