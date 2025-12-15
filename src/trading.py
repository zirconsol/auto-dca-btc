import logging
from datetime import datetime, timezone

from src.binance_client import AssetBalance, BinanceClient
from src.telemetry import TradeReporter


class AutoSwapper:
    """
    Detecta saldo libre en un activo de cotización y lo usa para comprar
    el par configurado mediante orden de mercado.
    """

    def __init__(
        self,
        client: BinanceClient,
        quote_asset: str,
        symbol: str,
        min_quote_qty: float = 0.0,
        withdrawer=None,
        withdraw_coin: str = "BTC",
        reporter: TradeReporter | None = None,
        wallet: str | None = None,
    ) -> None:
        self.client = client
        self.quote_asset = quote_asset
        self.symbol = symbol
        self.min_quote_qty = min_quote_qty
        self.symbol_min_notional = self._load_min_notional()
        self.withdrawer = withdrawer
        self.withdraw_coin = withdraw_coin.upper()
        self.reporter = reporter
        self.wallet = wallet or ""

    def _load_min_notional(self) -> float:
        try:
            min_notional = self.client.get_symbol_min_notional(self.symbol)
            if min_notional > 0:
                logging.info(
                    "MinNotional para %s según exchangeInfo: %.8f",
                    self.symbol,
                    min_notional,
                )
            return min_notional
        except Exception as exc:  # noqa: BLE001
            logging.warning("No se pudo leer MinNotional para %s: %s", self.symbol, exc)
            return 0.0

    def handle_balance(self, balance: AssetBalance) -> None:
        if balance.asset != self.quote_asset:
            return

        available = balance.free
        if available <= 0:
            return

        effective_min = max(self.min_quote_qty, self.symbol_min_notional)
        if available < effective_min:
            logging.info(
                "Saldo %s (%.8f) menor al mínimo requerido %.8f; no se envía orden.",
                balance.asset,
                available,
                effective_min,
            )
            return

        logging.info(
            "Detectados %.8f %s libres. Enviando orden de compra en %s con todo el saldo...",
            available,
            balance.asset,
            self.symbol,
        )

        order = self.client.place_market_order(symbol=self.symbol, side="BUY", quote_order_qty=available)
        logging.info(
            "Orden ejecutada: id=%s status=%s cummulativeQuoteQty=%s executedQty=%s",
            order.get("orderId"),
            order.get("status"),
            order.get("cummulativeQuoteQty"),
            order.get("executedQty"),
        )

        executed_qty = self._to_float(order.get("executedQty"))
        fiat_spent = self._to_float(order.get("cummulativeQuoteQty"))
        buy_ts = self._order_timestamp(order)
        transfer_ts = None
        price = self._avg_price(order, fiat_spent, executed_qty)

        if self.withdrawer and executed_qty > 0:
            try:
                resp = self.withdrawer.withdraw(amount=executed_qty)
                if resp is not None:
                    transfer_ts = datetime.now(timezone.utc)
            except Exception as exc:  # noqa: BLE001
                logging.error("Error al enviar retiro automático: %s", exc)

        if self.reporter and executed_qty > 0:
            try:
                self.reporter.report_trade(
                    buy_timestamp=buy_ts,
                    fiat_spent=fiat_spent,
                    btc_bought=executed_qty,
                    price_fiat_per_btc=price,
                    wallet=self.wallet,
                    transfer_timestamp=transfer_ts,
                )
            except Exception as exc:  # noqa: BLE001
                logging.error("No se pudo reportar el trade al backend: %s", exc)

    @staticmethod
    def _to_float(value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _order_timestamp(order: dict) -> datetime:
        ts_ms = order.get("transactTime") or order.get("updateTime")
        if ts_ms:
            try:
                return datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc)
            except (TypeError, ValueError):
                pass
        return datetime.now(timezone.utc)

    def _avg_price(self, order: dict, fiat_spent: float, executed_qty: float) -> float:
        fills = order.get("fills") or []
        total_qty = 0.0
        total_quote = 0.0
        for f in fills:
            qty = self._to_float(f.get("qty"))
            price = self._to_float(f.get("price"))
            total_qty += qty
            total_quote += qty * price

        if total_qty > 0 and total_quote > 0:
            return total_quote / total_qty

        if executed_qty > 0 and fiat_spent > 0:
            return fiat_spent / executed_qty

        return 0.0
