import decimal
import random
import string

from core import tp

from .. import enums, structures
from . import core_

_BROKER_ID = "PecK6W5K"
_ORDER_ID_PREFIX = f"x-{_BROKER_ID}"
_ORDER_ID_MAX_LEN = 35
_SUFFIX_MAX_LEN = _ORDER_ID_MAX_LEN - len(_ORDER_ID_PREFIX)
_GENERATOR_SYMBOLS = string.ascii_letters + string.digits


class BinanceClientFuturesNewOrder(core_.BinanceClientCore):
    def __init__(self) -> None:
        super().__init__()
        self.POST_FAPI_V1_ORDER: tp.Final[core_.TAPIMethodKey] = (
            self._register_api_method(
                "POST",
                "/fapi/v1/order",
                trading=True,
                quota_usage_fn=self._simple_weight_fn(orders=1),
            )
        )

    @staticmethod
    def _get_new_client_order_id() -> str:
        uniq_suffix = "".join(
            random.sample(
                population=_GENERATOR_SYMBOLS,
                k=_SUFFIX_MAX_LEN,
                counts=[3] * len(_GENERATOR_SYMBOLS),
            ),
        )
        return _ORDER_ID_PREFIX + uniq_suffix

    async def _req_post_fapi_v1_market_order(
        self,
        account: structures.BinanceAccount,
        symbol: str,
        side: str,
        quantity: decimal.Decimal,
        position_side: tp.Optional[enums.PositionSide],
        reduce_only: bool,
        new_client_order_id: tp.Optional[str],
    ) -> str:
        url_params = core_.TURLParams(
            {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quantity": str(quantity),
                "newClientOrderId": (
                    self._get_new_client_order_id()
                    if new_client_order_id is None
                    else new_client_order_id
                ),
            }
        )
        if position_side is not None:
            url_params["positionSide"] = position_side.name
        elif reduce_only:
            url_params["reduceOnly"] = "true"

        return await self._do_fapi_request(
            self.POST_FAPI_V1_ORDER,
            core_.TRequestParams(
                account=account,
                url_params=url_params,
            ),
        )

    async def futures_new_market_order(
        self,
        account: structures.BinanceAccount,
        *,
        symbol: str,
        side: enums.Side,
        quantity: decimal.Decimal,
        position_side: tp.Optional[enums.PositionSide] = None,
        reduce_only: bool = False,
        new_client_order_id: tp.Optional[str] = None,
    ) -> None:
        await self._req_post_fapi_v1_market_order(
            account,
            symbol,
            side.name,
            quantity,
            position_side,
            reduce_only,
            new_client_order_id,
        )
