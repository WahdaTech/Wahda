from core import tp

from .. import structures
from . import core_


class BinanceClientMultiAssetsMargin(core_.BinanceClientCore):
    def __init__(self) -> None:
        super().__init__()
        self.POST_FAPI_V1_MULTI_ASSETS_MARGIN: tp.Final[core_.TAPIMethodKey] = (
            self._register_api_method(
                "POST",
                "/fapi/v1/multiAssetsMargin",
                trading=True,
                quota_usage_fn=self._simple_weight_fn(weight=1),
            )
        )

    async def _req_post_fapi_v1_multi_assets_margin(
        self,
        account: structures.BinanceAccount,
        multi_assets_margin: bool,
    ) -> str:
        return await self._do_fapi_request(
            self.POST_FAPI_V1_MULTI_ASSETS_MARGIN,
            core_.TRequestParams(
                account=account,
                url_params=core_.TURLParams(
                    {"multiAssetsMargin": str(multi_assets_margin).lower()}
                ),
            ),
        )

    async def futures_enable_multi_assets_mode(
        self, account: structures.BinanceAccount
    ) -> None:
        await self._req_post_fapi_v1_multi_assets_margin(account, True)
