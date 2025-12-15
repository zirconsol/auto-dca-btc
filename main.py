import logging

from src.balance_monitor import BalanceMonitor
from src.binance_client import AssetBalance, BinanceClient
from src.config import load_config
from src.telemetry import TradeReporter
from src.trading import AutoSwapper
from src.withdrawer import AutoWithdrawer


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    config = load_config()
    client = BinanceClient(
        api_key=config.api_key,
        api_secret=config.api_secret,
        base_url=config.base_url,
    )
    withdrawer = AutoWithdrawer(
        client=client,
        coin=config.withdraw_coin,
        address=config.withdraw_address,
        network=config.withdraw_network,
        min_amount=config.withdraw_min_amount,
    )
    reporter = TradeReporter(base_url=config.backend_api_base)

    swapper = AutoSwapper(
        client=client,
        quote_asset=config.target_asset,
        symbol=config.trade_symbol,
        min_quote_qty=config.min_quote_qty,
        withdrawer=withdrawer,
        withdraw_coin=config.withdraw_coin,
        reporter=reporter,
        wallet=config.withdraw_address or "",
    )

    def handle_balance(balance: AssetBalance) -> None:
        logging.info(
            "Balance %s -> libre: %.8f | bloqueado: %.8f | total: %.8f",
            balance.asset,
            balance.free,
            balance.locked,
            balance.total,
        )
        swapper.handle_balance(balance)

    monitor = BalanceMonitor(
        client=client,
        asset=config.target_asset,
        poll_interval_seconds=config.poll_interval_seconds,
        on_result=handle_balance,
    )
    monitor.run_forever()


if __name__ == "__main__":
    main()
