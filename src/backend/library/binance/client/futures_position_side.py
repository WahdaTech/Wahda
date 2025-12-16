import msgspec

from core import tp

from .. import structures
from . import core_


class BinanceDualSidePosition(msgspec.Struct, frozen=True):
    dual_side_position: bool = msgspec.field(name="dualSidePosition")


class BinanceClientPositionSide(core_.BinanceClientCore):
    dual_side_position_decoder = msgspec.json.Decoder(
        strict=False, type=BinanceDualSidePosition
    )

    def __init__(self) -> None:
        super().__init__()
        self.GET_FAPI_V1_POSITION_SIDE_DUAL: tp.Final[core_.TAPIMethodKey] = (
            self._register_api_method(
                "GET",
                "/fapi/v1/positionSide/dual",
                trading=False,
                quota_usage_fn=self._simple_weight_fn(weight=30),
            )
        )
        self.POST_FAPI_V1_POSITION_SIDE_DUAL: tp.Final[core_.TAPIMethodKey] = (
            self._register_api_method(
                "POST",
                "/fapi/v1/positionSide/dual",
                trading=True,
                quota_usage_fn=self._simple_weight_fn(weight=1),
            )
        )

    async def _req_get_fapi_v1_positionside_dual(
        self,
        account: structures.BinanceAccount,
    ) -> str:
        return await self._do_fapi_request(
            self.GET_FAPI_V1_POSITION_SIDE_DUAL,
            core_.TRequestParams(account=account),
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

    @staticmethod
    def _parse_dual_side_position(json_str: str) -> BinanceDualSidePosition:
        return BinanceClientPositionSide.dual_side_position_decoder.decode(json_str)

    async def futures_get_hedge_mode(
        self, account: structures.BinanceAccount
    ) -> BinanceDualSidePosition:
        return self._parse_dual_side_position(
            await self._req_get_fapi_v1_positionside_dual(account)
        )

    async def futures_set_hedge_mode(self, account: structures.BinanceAccount) -> None:
        await self._req_post_fapi_v1_positionside_dual(account, True)
