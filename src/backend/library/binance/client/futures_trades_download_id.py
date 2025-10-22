import arrow

from core import tp

from .. import structures
from . import core_, futures_download_id_base


class BinanceClientFuturesTradesDownloadsId(
    futures_download_id_base.BinanceClientFuturesDownloadsId
):
    def __init__(self) -> None:
        super().__init__()
        self.GET_FAPI_V1_TRADE_ASYN: tp.Final[core_.TAPIMethodKey] = (
            self._register_common_api_method("GET", "/fapi/v1/trade/asyn", weight=1000)
        )

    async def fetch_futures_trades_download_id(
        self,
        account: structures.BinanceAccount,
        start_time: arrow.Arrow,
        end_time: arrow.Arrow,
    ) -> futures_download_id_base.BinanceFuturesDownloadInfo:
        return await self._fetch_futures_download_id(
            self.GET_FAPI_V1_TRADE_ASYN, account, start_time, end_time
        )
