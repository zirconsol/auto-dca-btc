"""
Envío manual de BTC por red BNB (BSC).

Configura las variables en .env antes de ejecutar:
- WITHDRAW_COIN (por defecto BTC)
- WITHDRAW_AMOUNT (por defecto 0.000001)
- WITHDRAW_ADDRESS (requerido)
- WITHDRAW_NETWORK (por defecto BSC)
"""
import logging
import os
import sys
from pathlib import Path

# Asegura que el proyecto esté en sys.path al ejecutar el archivo directamente.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.binance_client import BinanceClient  # noqa: E402
from src.config import load_config  # noqa: E402


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    config = load_config()
    client = BinanceClient(
        api_key=config.api_key,
        api_secret=config.api_secret,
        base_url=config.base_url,
    )

    coin = os.getenv("WITHDRAW_COIN", "BTC").upper()
    network = os.getenv("WITHDRAW_NETWORK", "BSC").upper()
    address = os.getenv("WITHDRAW_ADDRESS")
    amount_raw = os.getenv("WITHDRAW_AMOUNT", "0.000001")

    if not address:
        raise ValueError("WITHDRAW_ADDRESS es obligatorio para enviar el retiro.")

    try:
        amount = float(amount_raw)
        if amount <= 0:
            raise ValueError
    except ValueError as exc:
        raise ValueError("WITHDRAW_AMOUNT debe ser un número mayor a cero.") from exc

    logging.info(
        "Enviando retiro: coin=%s amount=%.8f network=%s address=%s",
        coin,
        amount,
        network,
        address,
    )
    resp = client.withdraw(coin=coin, address=address, amount=amount, network=network)
    logging.info("Retiro enviado. Respuesta: %s", resp)


if __name__ == "__main__":
    main()
