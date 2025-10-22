import arrow
import pydantic

from core import tp

from .. import structures
from . import core_


@pydantic.dataclasses.dataclass(frozen=True)
class BinanceFuturesDownloadInfo:
    avg_cost_last_month: tp.Optional[int] = pydantic.Field(
        alias="avgCostTimestampOfLast30d"
    )
    download_id: tp.Optional[str] = pydantic.Field(alias="downloadId")


class BinanceClientFuturesDownloadsId(core_.BinanceClientCore):
    async def _req_get_fapi_download_v1_asyn(
        self,
        api_method: tuple[str, str],
        account: structures.BinanceAccount,
        start_time_ms: int,
        end_time_ms: int,
    ) -> str:
        return await self._do_fapi_request(
            api_method,
            core_.TRequestParams(
                account=account,
                url_params=core_.TURLParams(
                    {"startTime": str(start_time_ms), "endTime": str(end_time_ms)}
                ),
            ),
        )

    @staticmethod
    def _parse_futures_download_info(
        json_str: str,
    ) -> BinanceFuturesDownloadInfo:
        return (
            pydantic.RootModel[BinanceFuturesDownloadInfo]
            .model_validate_json(json_str)
            .root
        )

    async def _fetch_futures_download_id(
        self,
        api_method: tuple[str, str],
        account: structures.BinanceAccount,
        start_time: arrow.Arrow,
        end_time: arrow.Arrow,
    ) -> BinanceFuturesDownloadInfo:
        start_time_ms = int(start_time.timestamp() * 1000)
        end_time_ms = int(end_time.timestamp() * 1000)

        return self._parse_futures_download_info(
            await self._req_get_fapi_download_v1_asyn(
                api_method, account, start_time_ms, end_time_ms
            )
        )
