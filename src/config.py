import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass
class AppConfig:
    api_key: str
    api_secret: str
    target_asset: str
    poll_interval_seconds: float
    trade_symbol: str
    min_quote_qty: float
    base_url: str
    withdraw_address: str | None
    withdraw_network: str
    withdraw_min_amount: float
    withdraw_coin: str
    withdraw_amount_override: float | None
    backend_api_base: str | None


def _read_env(key: str, fallback_key: Optional[str] = None) -> Optional[str]:
    value = os.getenv(key)
    if value:
        return value
    if fallback_key:
        return os.getenv(fallback_key)
    return None


def load_config() -> AppConfig:
    load_dotenv()

    api_key = _read_env("BINANCE_API_KEY", "BINANCE_API")
    api_secret = _read_env("BINANCE_API_SECRET", "BINANCE_SECRET")
    target_asset = (os.getenv("TARGET_ASSET") or "ARS").upper()
    trade_symbol = (os.getenv("TRADE_SYMBOL") or f"BTC{target_asset}").upper()
    poll_interval_raw = os.getenv("POLL_INTERVAL_SECONDS") or "10"
    min_quote_raw = os.getenv("MIN_QUOTE_QTY") or "0"
    base_url = os.getenv("BINANCE_BASE_URL") or "https://api.binance.com"
    withdraw_address = os.getenv("WITHDRAW_ADDRESS")
    withdraw_network = (os.getenv("WITHDRAW_NETWORK") or "BSC").upper()
    withdraw_min_amount_raw = os.getenv("WITHDRAW_MIN_AMOUNT") or "0"
    withdraw_coin = (os.getenv("WITHDRAW_COIN") or "BTC").upper()
    withdraw_amount_override_raw = os.getenv("WITHDRAW_AMOUNT")
    backend_api_base = os.getenv("BACKEND_API_BASE") or os.getenv("DCA_API_BASE")

    if not api_key or not api_secret:
        raise ValueError(
            "Faltan credenciales: define BINANCE_API_KEY/BINANCE_API y "
            "BINANCE_API_SECRET/BINANCE_SECRET en el archivo .env"
        )

    try:
        poll_interval = float(poll_interval_raw)
        if poll_interval <= 0:
            raise ValueError
    except ValueError as exc:
        raise ValueError("POLL_INTERVAL_SECONDS debe ser un número mayor a cero") from exc

    try:
        min_quote_qty = float(min_quote_raw)
        if min_quote_qty < 0:
            raise ValueError
    except ValueError as exc:
        raise ValueError("MIN_QUOTE_QTY debe ser un número mayor o igual a cero") from exc

    try:
        withdraw_min_amount = float(withdraw_min_amount_raw)
        if withdraw_min_amount < 0:
            raise ValueError
    except ValueError as exc:
        raise ValueError("WITHDRAW_MIN_AMOUNT debe ser un número mayor o igual a cero") from exc

    withdraw_amount_override = None
    if withdraw_amount_override_raw:
        try:
            withdraw_amount_override = float(withdraw_amount_override_raw)
            if withdraw_amount_override <= 0:
                raise ValueError
        except ValueError as exc:
            raise ValueError("WITHDRAW_AMOUNT debe ser un número mayor a cero") from exc

    return AppConfig(
        api_key=api_key,
        api_secret=api_secret,
        target_asset=target_asset,
        poll_interval_seconds=poll_interval,
        trade_symbol=trade_symbol,
        min_quote_qty=min_quote_qty,
        base_url=base_url.rstrip("/"),
        withdraw_address=withdraw_address,
        withdraw_network=withdraw_network,
        withdraw_min_amount=withdraw_min_amount,
        withdraw_coin=withdraw_coin,
        withdraw_amount_override=withdraw_amount_override,
        backend_api_base=backend_api_base.rstrip("/") if backend_api_base else None,
    )
