from core import tp, wrap_

from .. import exceptions, structures
from .futures_exchange_info import (
    BinanceClientFuturesExchangeInfo,
    BinanceFuturesExchangeInfoRateLimit,
)


class BinanceClientFuturesRateLimitsUpdater(BinanceClientFuturesExchangeInfo):
    def _parse_rate_limit(
        self, rate_limit: BinanceFuturesExchangeInfoRateLimit
    ) -> None:
        limit: int
        match rate_limit:
            case BinanceFuturesExchangeInfoRateLimit(
                rate_limit_type="REQUEST_WEIGHT",
                interval="MINUTE",
                interval_num=1,
                limit=limit,
            ):
                self._lim_store[structures.BinanceLimit.WEIGHT_1M_LABEL] = limit
            case BinanceFuturesExchangeInfoRateLimit(
                rate_limit_type="ORDERS",
                interval="MINUTE",
                interval_num=1,
                limit=limit,
            ):
                self._lim_store[structures.BinanceLimit.ORDERS_1M_LABEL] = limit
            case BinanceFuturesExchangeInfoRateLimit(
                rate_limit_type="ORDERS",
                interval="SECOND",
                interval_num=10,
                limit=limit,
            ):
                self._lim_store[structures.BinanceLimit.ORDERS_10S_LABEL] = limit
            case _:
                msg = f"Unknown rate limit: {rate_limit}"
                raise exceptions.BinanceClientException(msg)

    def _reconfigure_rate_limits(self) -> tp.TExc:
        self._lim_store.update(
            {
                structures.BinanceLimit.WEIGHT_1M_LABEL: 0,
                structures.BinanceLimit.ORDERS_1M_LABEL: 0,
                structures.BinanceLimit.ORDERS_10S_LABEL: 0,
            }
        )

        if self._exchange_info_data is None:
            return exceptions.BinanceClientException("No exchage info data")

        exc: tp.TExc = None
        for rate_limit in self._exchange_info_data.rate_limits:
            _, exc_ = wrap_(self._parse_rate_limit)(rate_limit)
            if exc_ is not None:
                exc = exc_

        return exc

    async def _update_futures_exchange_info(self) -> None:
        await super()._update_futures_exchange_info()
        self._reconfigure_rate_limits()
