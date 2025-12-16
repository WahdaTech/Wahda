from . import (
    api_methods,
    futures_account_info,
    futures_balance,
    futures_incomes_download_history,
    futures_incomes_download_id,
    futures_leverage,
    futures_margin_type,
    futures_multi_assets_margin,
    futures_new_order,
    futures_open_orders,
    futures_position_side,
    futures_rate_limits_updater,
    futures_ticker_price,
    futures_trades_download_history,
    futures_trades_download_id,
)


# rate_limits_updater.BinanceClientFuturesRateLimits includes:
# - core
# - futures_exchange_info
# - futures_rate_limits_updater
# futures_account_info.BinanceClientFuturesAccountInfo includes:
# - futures_account_info
class BinanceClientImpl(
    api_methods.BinanceClientFuturesAPIMethods,
    futures_rate_limits_updater.BinanceClientFuturesRateLimitsUpdater,
    futures_account_info.BinanceClientFuturesAccountInfo,
    futures_balance.BinanceClientFuturesBalance,
    futures_ticker_price.BinanceClientFuturesTickerPrice,
    futures_new_order.BinanceClientFuturesNewOrder,
    futures_open_orders.BinanceClientFuturesOpenOrders,
    futures_position_side.BinanceClientPositionSide,
    futures_margin_type.BinanceClientFuturesMarginType,
    futures_multi_assets_margin.BinanceClientMultiAssetsMargin,
    futures_leverage.BinanceClientFuturesLeverage,
    futures_incomes_download_id.BinanceClientFuturesIncomesDownloadsId,
    futures_incomes_download_history.BinanceClientFuturesIncomesDownloadsHistory,
    futures_trades_download_history.BinanceClientFuturesTradesDownloadsHistory,
    futures_trades_download_id.BinanceClientFuturesTradesDownloadsId,
):
    pass


class BinanceClient(BinanceClientImpl):
    def __init__(self) -> None:
        if self._initialized:
            return

        super().__init__()
        self._initialized: bool = True

    def __new__(cls) -> "BinanceClient":
        if not hasattr(cls, "_instance"):
            cls._instance = super(BinanceClient, cls).__new__(cls)
            cls._initialized = False
        return cls._instance
