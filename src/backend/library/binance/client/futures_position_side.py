from core import tp

from .. import structures
from . import core_


class BinanceClientPositionSide(core_.BinanceClientCore):
    def __init__(self) -> None:
        super().__init__()
        self.POST_FAPI_V1_POSITION_SIDE_DUAL: tp.Final[core_.TAPIMethodKey] = (
            self._register_api_method(
                "POST",
                "/fapi/v1/positionSide/dual",
                trading=True,
                quota_usage_fn=self._simple_weight_fn(weight=1),
            )
        )

    async def _req_post_fapi_v1_positionside_dual(
        self,
        account: structures.BinanceAccount,
        dual_side_position: bool,
    ) -> str:
        return await self._do_fapi_request(
            self.POST_FAPI_V1_POSITION_SIDE_DUAL,
            core_.TRequestParams(
                account=account,
                url_params=core_.TURLParams(
                    {"dualSidePosition": str(dual_side_position).lower()}
                ),
            ),
        )

    async def futures_set_hedge_mode(self, account: structures.BinanceAccount) -> None:
        await self._req_post_fapi_v1_positionside_dual(account, True)
