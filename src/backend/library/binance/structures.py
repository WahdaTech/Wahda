import datetime
import hmac
import sys

import arrow

from core import telemetry

LOG = telemetry.get_logger()


class BinanceLimit:
    WEIGHT_1M_LABEL: str = "weight_1m"
    ORDERS_1M_LABEL: str = "orders_1m"
    ORDERS_10S_LABEL: str = "orders_10s"

    def __init__(
        self,
        *,
        reserved: int,
        label: str,
        interval: datetime.timedelta,
        lim_store: dict[str, int],
    ) -> None:
        self._allocated: int = 0
        self._reserved: int = reserved
        self.label: str = label
        self._interval: datetime.timedelta = interval
        self._interval_begin = arrow.utcnow()
        self._lim_store: dict[str, int] = lim_store
        self._used: int = sys.maxsize

    @property
    def used(self) -> int:
        if arrow.utcnow() > self._interval_begin + self._interval:
            self.used = 0

        if self._used == sys.maxsize:
            return 0

        return self._used

    @used.setter
    def used(self, new_value: int) -> None:
        if new_value < self._used:
            self._interval_begin = arrow.utcnow()

        self._used = new_value

    @property
    def remaining(self) -> int:
        return (
            self._lim_store[self.label] - self.used - self._reserved - self._allocated
        )

    def allocate(self, amount: int) -> bool:
        if amount <= 0:
            return True

        if self.remaining < amount:
            LOG.warning(
                "Cannot make a request due to rate limit ({label}), "
                "requires: {amount}, available: {available}",
                label=self.label,
                amount=amount,
                available=self.remaining + amount,
            )
            return False

        self._allocated += amount
        return True

    def free(self, amount: int) -> bool:
        if amount <= 0:
            return True

        if self._allocated < amount:
            self.allocated = 0
            LOG.warning("Freeing more resources than was taken")
            return False

        self._allocated -= amount
        return True


class BinanceAccount:
    def __init__(
        self,
        account_id: str,
        api_key: str = "",
        api_secret: str = "",
        trading_api_key: str = "",
        trading_api_secret: str = "",
        ip_whitelisted: bool = False,
    ):
        self.account_id = account_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.trading_api_key = trading_api_key
        self.trading_api_secret = trading_api_secret
        self.ip_whitelisted = ip_whitelisted

    def __hash__(self) -> int:
        return hash(self.account_id)

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, BinanceAccount):
            return False

        return self.account_id == __value.account_id

    def __repr__(self) -> str:
        return self.account_id

    def get_signature(
        self,
        msg: str,
        trading: bool = False,
    ) -> str:
        api_secret = self.trading_api_secret if trading else self.api_secret

        return hmac.new(api_secret.encode(), msg.encode(), "sha256").hexdigest()
