import asyncio
import decimal

import pydantic

from core import awrap_, tp

from . import core_


@pydantic.dataclasses.dataclass(frozen=True)
class BinanceFuturesTickerPriceSymbol:
    symbol: str = pydantic.Field(alias="symbol")
    price: decimal.Decimal = pydantic.Field(alias="price")


BinanceFuturesTickerPrice = list[BinanceFuturesTickerPriceSymbol]


class BinanceClientFuturesTickerPrice(core_.BinanceClientCore):
    def __init__(self) -> None:
        super().__init__()
        self.GET_FAPI_V2_TICKER_PRICE: tp.Final[core_.TAPIMethodKey] = (
            self._register_api_method(
                "GET",
                "/fapi/v2/ticker/price",
                trading=False,
                quota_usage_fn=self._simple_weight_fn(weight=1),
                ignore_used_limits=True,
            )
        )
        self._ticker_price: dict[str, BinanceFuturesTickerPriceSymbol] = {}
        self._ticker_price_updates_enabled: bool = False
        self._ticker_price_updates_task: tp.Optional[asyncio.Task[None]] = None
        self._ticker_price_update_interval = 1

    async def _req_get_fapi_v2_ticker_price(self) -> str:
        return await self._do_fapi_request(self.GET_FAPI_V2_TICKER_PRICE)

    @staticmethod
    def _parse_futures_ticker_price(json_str: str) -> BinanceFuturesTickerPrice:
        return (
            pydantic.RootModel[BinanceFuturesTickerPrice]
            .model_validate_json(json_str)
            .root
        )

    async def _update_futures_ticker_price(self) -> None:
        json_str = await self._req_get_fapi_v2_ticker_price()

        self._ticker_price = {
            symbol.symbol: symbol
            for symbol in self._parse_futures_ticker_price(json_str)
        }

    async def _update_futures_ticker_price_task(self) -> None:
        while self._ticker_price_updates_enabled:
            await awrap_(self._update_futures_ticker_price)()
            await asyncio.sleep(self._ticker_price_update_interval)

    def run_futures_ticker_price_updates(self) -> None:
        if self._ticker_price_updates_enabled:
            raise tp.WDException("Ticker price updates are already running")

        if self._ticker_price_updates_task is not None:
            if not self._ticker_price_updates_task.done():
                raise tp.WDException("Ticker price updates are still stopping")

        self._ticker_price_updates_enabled = True
        self._ticker_price_updates_task = asyncio.create_task(
            self._update_futures_ticker_price_task()
        )

    def stop_futures_ticker_price_updates(self) -> None:
        self._ticker_price_updates_enabled = False

    async def fetch_futures_ticker_price(self) -> BinanceFuturesTickerPrice:
        return self._parse_futures_ticker_price(
            await self._req_get_fapi_v2_ticker_price()
        )

    def futures_ticker_price(self) -> dict[str, BinanceFuturesTickerPriceSymbol]:
        return self._ticker_price
