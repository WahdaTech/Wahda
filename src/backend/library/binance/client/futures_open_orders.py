import decimal

import msgspec

from core import tp

from .. import structures
from . import core_


class BinanceFuturesOpenOrder(msgspec.Struct, frozen=True):
    avg_price: decimal.Decimal = msgspec.field(name="avgPrice")
    client_order_id: str = msgspec.field(name="clientOrderId")
    cum_quote: decimal.Decimal = msgspec.field(name="cumQuote")
    executed_qty: decimal.Decimal = msgspec.field(name="executedQty")
    order_id: int = msgspec.field(name="orderId")
    orig_qty: decimal.Decimal = msgspec.field(name="origQty")
    orig_type: str = msgspec.field(name="origType")
    price: decimal.Decimal
    reduce_only: bool = msgspec.field(name="reduceOnly")
    side: str
    position_side: str = msgspec.field(name="positionSide")
    status: str
    close_position: bool = msgspec.field(name="closePosition")
    symbol: str
    time: int
    time_in_force: str = msgspec.field(name="timeInForce")
    type: str
    update_time: int = msgspec.field(name="updateTime")
    working_type: str = msgspec.field(name="workingType")
    price_protect: bool = msgspec.field(name="priceProtect")
    price_match: str = msgspec.field(name="priceMatch")
    self_trade_prevention_mode: str = msgspec.field(name="selfTradePreventionMode")
    good_till_date: int = msgspec.field(name="goodTillDate")
    stop_price: tp.Optional[decimal.Decimal] = msgspec.field(
        name="stopPrice", default=None
    )
    activate_price: tp.Optional[decimal.Decimal] = msgspec.field(
        name="activatePrice", default=None
    )
    price_rate: tp.Optional[decimal.Decimal] = msgspec.field(
        name="priceRate", default=None
    )


BinanceFuturesOpenOrders = list[BinanceFuturesOpenOrder]


class BinanceClientFuturesOpenOrders(core_.BinanceClientCore):
    open_orders_decoder = msgspec.json.Decoder(
        strict=False, type=BinanceFuturesOpenOrders
    )

    def __init__(self) -> None:
        super().__init__()
        self.GET_FAPI_V1_OPEN_ORDERS: tp.Final[core_.TAPIMethodKey] = (
            self._register_api_method(
                "GET",
                "/fapi/v1/openOrders",
                trading=False,
                quota_usage_fn=self._simple_weight_fn(weight=40),
            )
        )

    async def _req_get_fapi_v1_open_orders(
        self,
        account: structures.BinanceAccount,
    ) -> str:
        return await self._do_fapi_request(
            self.GET_FAPI_V1_OPEN_ORDERS,
            core_.TRequestParams(account=account),
        )

    @staticmethod
    def _parse_open_orders(json_str: str) -> BinanceFuturesOpenOrders:
        return BinanceClientFuturesOpenOrders.open_orders_decoder.decode(json_str)

    async def futures_get_open_orders(
        self, account: structures.BinanceAccount
    ) -> BinanceFuturesOpenOrders:
        return self._parse_open_orders(await self._req_get_fapi_v1_open_orders(account))
