from core import tp

from .. import structures
from . import core_


class BinanceClientFuturesLeverage(core_.BinanceClientCore):
    def __init__(self) -> None:
        super().__init__()
        self.POST_FAPI_V1_LEVERAGE: tp.Final[core_.TAPIMethodKey] = (
            self._register_api_method(
                "POST",
                "/fapi/v1/leverage",
                trading=True,
                quota_usage_fn=self._simple_weight_fn(weight=1),
            )
        )

    async def _req_post_fapi_v1_leverage(
        self, account: structures.BinanceAccount, symbol: str, leverage: int
    ) -> str:
        return await self._do_fapi_request(
            self.POST_FAPI_V1_LEVERAGE,
            core_.TRequestParams(
                account=account,
                url_params=core_.TURLParams(
                    {"symbol": symbol, "leverage": str(leverage)}
                ),
            ),
        )

    async def futures_set_leverage(
        self, account: structures.BinanceAccount, symbol: str, leverage: int
    ) -> None:
        await self._req_post_fapi_v1_leverage(account, symbol, leverage)
