import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlencode

import requests
from requests import HTTPError


@dataclass
class AssetBalance:
    asset: str
    free: float
    locked: float

    @property
    def total(self) -> float:
        return self.free + self.locked


class BinanceClient:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://api.binance.com",
        recv_window: int = 5000,
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret.encode()
        self.base_url = base_url.rstrip("/")
        self.recv_window = recv_window
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    def _sign(self, query_string: str) -> str:
        return hmac.new(self.api_secret, query_string.encode(), hashlib.sha256).hexdigest()

    def _public_request(self, method: str, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self.base_url}{path}"
        response = self.session.request(method, url, params=params or {}, timeout=10)
        try:
            response.raise_for_status()
        except HTTPError as exc:
            raise HTTPError(
                f"{exc} | body={response.text}",
                response=response,
                request=exc.request,
            ) from None
        return response.json()

    def _signed_request(self, method: str, path: str, params: Optional[dict] = None) -> dict:
        params = params.copy() if params else {}
        params["timestamp"] = int(time.time() * 1000)
        params.setdefault("recvWindow", self.recv_window)

        query_string = urlencode(params, doseq=True)
        signature = self._sign(query_string)
        url = f"{self.base_url}{path}?{query_string}&signature={signature}"

        response = self.session.request(method, url, timeout=10)
        try:
            response.raise_for_status()
        except HTTPError as exc:
            # Adjunta cuerpo de error para depurar (p.ej. api-key inválida, timestamp, permisos).
            raise HTTPError(
                f"{exc} | body={response.text}",
                response=response,
                request=exc.request,
            ) from None
        return response.json()

    def get_asset_balance(self, asset: str) -> AssetBalance:
        payload = self._signed_request("GET", "/api/v3/account")
        balances = payload.get("balances", [])
        match = next((b for b in balances if b.get("asset") == asset), None)

        if not match:
            return AssetBalance(asset=asset, free=0.0, locked=0.0)

        def _to_float(value: Optional[str]) -> float:
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        return AssetBalance(
            asset=asset,
            free=_to_float(match.get("free")),
            locked=_to_float(match.get("locked")),
        )

    def get_symbol_info(self, symbol: str) -> dict:
        payload = self._public_request("GET", "/api/v3/exchangeInfo", params={"symbol": symbol})
        symbols = payload.get("symbols", [])
        if not symbols:
            raise ValueError(f"Símbolo no encontrado en exchangeInfo: {symbol}")
        return symbols[0]

    def get_symbol_min_notional(self, symbol: str) -> float:
        """
        Devuelve el mínimo de notional permitido para órdenes de mercado de un símbolo.
        """
        info = self.get_symbol_info(symbol)
        filters = info.get("filters", [])
        min_notional = 0.0

        for f in filters:
            if f.get("filterType") in ("MIN_NOTIONAL", "NOTIONAL"):
                try:
                    min_notional = max(min_notional, float(f.get("minNotional", 0)))
                except (TypeError, ValueError):
                    pass
        return min_notional

    def withdraw(
        self,
        coin: str,
        address: str,
        amount: float,
        network: Optional[str] = None,
        address_tag: Optional[str] = None,
    ) -> dict:
        """
        Envía un retiro usando /sapi/v1/capital/withdraw/apply.
        Requiere que la API key tenga permiso de retiros y que el network/coin sean válidos.
        """
        params: dict[str, str | float] = {
            "coin": coin.upper(),
            "address": address,
            "amount": amount,
        }
        if network:
            params["network"] = network.upper()
        if address_tag:
            params["addressTag"] = address_tag

        return self._signed_request("POST", "/sapi/v1/capital/withdraw/apply", params)

    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: Optional[float] = None,
        quote_order_qty: Optional[float] = None,
        new_order_resp_type: str = "FULL",
    ) -> dict:
        """
        Envía una orden de mercado. Para comprar usando el total de un activo de cotización,
        usar quote_order_qty.
        """
        if quantity is None and quote_order_qty is None:
            raise ValueError("Debes especificar 'quantity' o 'quote_order_qty'")

        params: dict[str, str | float] = {"symbol": symbol, "side": side.upper(), "type": "MARKET"}
        if quantity is not None:
            params["quantity"] = quantity
        if quote_order_qty is not None:
            params["quoteOrderQty"] = quote_order_qty
        params["newOrderRespType"] = new_order_resp_type

        return self._signed_request("POST", "/api/v3/order", params)

    def get_my_trades(self, symbol: str, start_time: Optional[int] = None, end_time: Optional[int] = None) -> list[dict]:
        params: dict[str, str | int] = {"symbol": symbol}
        if start_time:
            params["startTime"] = int(start_time)
        if end_time:
            params["endTime"] = int(end_time)
        return self._signed_request("GET", "/api/v3/myTrades", params)
