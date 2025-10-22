from core import tp

from .. import structures
from . import core_


class BinanceClientFuturesMarginType(core_.BinanceClientCore):
    def __init__(self) -> None:
        super().__init__()
        self.POST_FAPI_V1_MARGIN_TYPE: tp.Final[core_.TAPIMethodKey] = (
            self._register_api_method(
                "POST",
                "/fapi/v1/marginType",
                trading=True,
                quota_usage_fn=self._simple_weight_fn(weight=1),
            )
        )

    async def _req_post_fapi_v1_margintype(
        self, account: structures.BinanceAccount, symbol: str, margin_type: str
    ) -> str:
        return await self._do_fapi_request(
            self.POST_FAPI_V1_MARGIN_TYPE,
            core_.TRequestParams(
                account=account,
                url_params=core_.TURLParams(
                    {"symbol": symbol, "marginType": margin_type}
                ),
            ),
        )

    async def futures_set_crossed_margin(
        self, account: structures.BinanceAccount, symbol: str
    ) -> None:
        await self._req_post_fapi_v1_margintype(account, symbol, "CROSSED")
