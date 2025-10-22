import asyncio
import decimal

import pydantic

from core import awrap_, tp, unwrap_

from . import core_


@pydantic.dataclasses.dataclass(frozen=True)
class BinanceFuturesExchangeInfoRateLimit:
    rate_limit_type: str = pydantic.Field(validation_alias="rateLimitType")
    interval: str = pydantic.Field()
    interval_num: int = pydantic.Field(validation_alias="intervalNum")
    limit: int = pydantic.Field()


@pydantic.dataclasses.dataclass(frozen=True)
class BinanceFuturesExchangeInfoAsset:
    asset: str = pydantic.Field()
    margin_available: bool = pydantic.Field(validation_alias="marginAvailable")
    auto_asset_exchange: str = pydantic.Field(validation_alias="autoAssetExchange")


@pydantic.dataclasses.dataclass(frozen=True)
class BinanceFuturesExchangeInfoSymbolFilter:
    filter_type: str = pydantic.Field(validation_alias="filterType")
    # LOT_SIZE or MARKET_LOT_SIZE
    min_qty: tp.Optional[decimal.Decimal] = pydantic.Field(
        None,
        validation_alias="minQty",
    )
    max_qty: tp.Optional[decimal.Decimal] = pydantic.Field(
        None,
        validation_alias="maxQty",
    )
    step_size: tp.Optional[decimal.Decimal] = pydantic.Field(
        None,
        validation_alias="stepSize",
    )
    # MIN_NOTIONAL
    notional: tp.Optional[decimal.Decimal] = None


@pydantic.dataclasses.dataclass(frozen=True)
class BinanceFuturesExchangeInfoSymbol:
    symbol: str = pydantic.Field()
    pair: str = pydantic.Field()
    contract_type: str = pydantic.Field(validation_alias="contractType")
    status: str = pydantic.Field()
    base_asset: str = pydantic.Field(validation_alias="baseAsset")
    quote_asset: str = pydantic.Field(validation_alias="quoteAsset")
    margin_asset: str = pydantic.Field(validation_alias="marginAsset")
    filters: list[BinanceFuturesExchangeInfoSymbolFilter] = pydantic.Field()


@pydantic.dataclasses.dataclass(frozen=True)
class BinanceFuturesExchangeInfo:
    server_time: int = pydantic.Field(validation_alias="serverTime")
    rate_limits: list[BinanceFuturesExchangeInfoRateLimit] = pydantic.Field(
        validation_alias="rateLimits"
    )
    assets: list[BinanceFuturesExchangeInfoAsset] = pydantic.Field()
    symbols: list[BinanceFuturesExchangeInfoSymbol] = pydantic.Field()


class BinanceClientFuturesExchangeInfo(core_.BinanceClientCore):
    def __init__(self) -> None:
        super().__init__()
        self.GET_FAPI_V1_EXCHANGE_INFO: tp.Final[core_.TAPIMethodKey] = (
            self._register_common_api_method(
                "GET",
                "/fapi/v1/exchangeInfo",
                weight=0,  # It's not 0, but we need it to init
            )
        )
        self._exchange_info_data: tp.Optional[BinanceFuturesExchangeInfo] = None
        self._symbols_info: dict[str, BinanceFuturesExchangeInfoSymbol] = {}
        self._exchange_info_updates_enabled: bool = False
        self._exchange_info_updates_task: tp.Optional[asyncio.Task[None]] = None
        self._exchange_info_update_interval = 5

    async def _req_get_fapi_v1_exchange_info(self) -> str:
        return await self._do_fapi_request(self.GET_FAPI_V1_EXCHANGE_INFO)

    @staticmethod
    def _parse_futures_exchange_info(json_str: str) -> BinanceFuturesExchangeInfo:
        return (
            pydantic.RootModel[BinanceFuturesExchangeInfo]
            .model_validate_json(json_str)
            .root
        )

    async def _update_futures_exchange_info(self) -> None:
        json_str, exc = await awrap_(self._req_get_fapi_v1_exchange_info)()
        self._exchange_info_data = None

        if exc is not None:
            raise exc

        self._exchange_info_data = self._parse_futures_exchange_info(unwrap_(json_str))

    def _update_symbols_info(self) -> None:
        if self._exchange_info_data is None:
            return

        self._symbols_info = {
            symbol.symbol: symbol for symbol in self._exchange_info_data.symbols
        }

    async def _update_futures_exchange_info_task_inner(self) -> None:
        await self._update_futures_exchange_info()
        self._update_symbols_info()
        await asyncio.sleep(self._exchange_info_update_interval)

    async def _update_futures_exchange_info_task(self) -> None:
        while self._exchange_info_updates_enabled:
            await awrap_(self._update_futures_exchange_info_task_inner)()

    def _run_futures_exchange_info_updates(self) -> None:
        if self._exchange_info_updates_enabled:
            raise tp.WDException("Exchange info updates are already running")

        if self._exchange_info_updates_task is not None:
            if not self._exchange_info_updates_task.done():
                raise tp.WDException("Exchange info updates are still stopping")

        self._exchange_info_updates_enabled = True
        self._exchange_info_updates_task = asyncio.create_task(
            self._update_futures_exchange_info_task()
        )

    def _stop_futures_exchange_info_updates(self) -> None:
        self._exchange_info_updates_enabled = False

    async def run(self) -> None:
        await super().run()

        # Totally useless but typechecker cannot get that exc is bound otherwise.
        exc = None
        attempt = 1

        while attempt <= 3:
            _, exc = await awrap_(self._update_futures_exchange_info)()
            # Assuming that on production we run every process under infinite restart:
            # if we face IP ban during init we must not stop the process,
            # otherwise initial request on each restart shall increase detention time,
            # which is +2 minutes for each request under the imposed ban.
            # This eventually would lead us to permaban. Hence there is a conditional
            # increase of attempt: *only* if exception was not related to the limiter.
            # In other cases, it is apparently safe to restart an instance.
            if not isinstance(exc, core_.exceptions.BinanceClientRateLimiterException):
                attempt += 1
            if exc is not None:
                await asyncio.sleep(1)
                continue
            break
        else:
            # elif is not supported here >_<
            if exc is not None:
                raise exc

        self._run_futures_exchange_info_updates()

    async def stop(self) -> None:
        self._stop_futures_exchange_info_updates()

        await super().stop()

    def futures_exchange_info(self) -> tp.Optional[BinanceFuturesExchangeInfo]:
        return self._exchange_info_data

    def symbols_info(self) -> dict[str, BinanceFuturesExchangeInfoSymbol]:
        return self._symbols_info

    def exchange_info_ok(self) -> bool:
        return self._exchange_info_data is not None
