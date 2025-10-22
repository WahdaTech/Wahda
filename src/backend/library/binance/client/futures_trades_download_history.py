from core import tp

from .. import structures
from . import core_, futures_download_history_base


class BinanceClientFuturesTradesDownloadsHistory(
    futures_download_history_base.BinanceClientFuturesDownloadsHistory
):
    def __init__(self) -> None:
        super().__init__()
        self.GET_FAPI_V1_TRADE_ASYN_ID: tp.Final[core_.TAPIMethodKey] = (
            self._register_common_api_method("GET", "/fapi/v1/trade/asyn/id", weight=10)
        )

    async def fetch_futures_trades_download_history(
        self, account: structures.BinanceAccount, download_id: str
    ) -> futures_download_history_base.BinanceFuturesDownloadHistoryInfo:
        return await self._fetch_futures_download_history(
            self.GET_FAPI_V1_TRADE_ASYN_ID, account, download_id
        )
