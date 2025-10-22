import pydantic

from core import tp

from .. import structures
from . import core_


@pydantic.dataclasses.dataclass(frozen=True)
class BinanceFuturesDownloadHistoryInfo:
    download_id: tp.Optional[str] = pydantic.Field(alias="downloadId")
    status: str = pydantic.Field()
    expiration_timestamp: int = pydantic.Field(alias="expirationTimestamp")
    url: str = pydantic.Field()
    s3_link: tp.Optional[str] = pydantic.Field(alias="s3Link")
    notified: bool = pydantic.Field()
    is_expired: tp.Optional[bool] = pydantic.Field(alias="isExpired")


class BinanceClientFuturesDownloadsHistory(core_.BinanceClientCore):
    async def _req_get_fapi_v1_download_asyn_id(
        self,
        api_method: tuple[str, str],
        account: structures.BinanceAccount,
        download_id: str,
    ) -> str:
        return await self._do_fapi_request(
            api_method,
            core_.TRequestParams(
                account=account,
                url_params=core_.TURLParams({"downloadId": download_id}),
            ),
        )

    @staticmethod
    def _parse_futures_download_history_info(
        json_str: str,
    ) -> BinanceFuturesDownloadHistoryInfo:
        return (
            pydantic.RootModel[BinanceFuturesDownloadHistoryInfo]
            .model_validate_json(json_str)
            .root
        )

    async def _fetch_futures_download_history(
        self,
        api_method: tuple[str, str],
        account: structures.BinanceAccount,
        download_id: str,
    ) -> BinanceFuturesDownloadHistoryInfo:
        return self._parse_futures_download_history_info(
            await self._req_get_fapi_v1_download_asyn_id(
                api_method, account, download_id
            )
        )
