import logging

from src.binance_client import BinanceClient


class AutoWithdrawer:
    """
    Envía retiros automáticos cuando se le indica un monto y la configuración lo permite.
    """

    def __init__(
        self,
        client: BinanceClient,
        coin: str,
        address: str | None,
        network: str = "BSC",
        min_amount: float = 0.0,
    ) -> None:
        self.client = client
        self.coin = coin.upper()
        self.address = address
        self.network = network.upper()
        self.min_amount = min_amount

    def withdraw(self, amount: float) -> None:
        if not self.address:
            logging.info("No se configuró WITHDRAW_ADDRESS; se omite el retiro automático.")
            return
        if amount <= 0:
            logging.info("Monto de retiro no válido (<=0), se omite: %.8f", amount)
            return
        if amount < self.min_amount:
            logging.info(
                "Monto %.8f inferior al mínimo configurado de retiro %.8f; no se envía.",
                amount,
                self.min_amount,
            )
            return

        logging.info(
            "Enviando retiro automático: coin=%s amount=%.8f network=%s address=%s",
            self.coin,
            amount,
            self.network,
            self.address,
        )
        resp = self.client.withdraw(
            coin=self.coin,
            address=self.address,
            amount=amount,
            network=self.network,
        )
        logging.info("Retiro enviado. Respuesta: %s", resp)
        return resp
