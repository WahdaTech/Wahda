import decimal

import pydantic

from core import tp

from .. import structures
from . import core_


@pydantic.dataclasses.dataclass(frozen=True)
class BinanceFuturesBalanceAsset:
    account_alias: str = pydantic.Field(alias="accountAlias")
    asset: str = pydantic.Field()
    balance: decimal.Decimal = pydantic.Field()
    cross_wallet_balance: decimal.Decimal = pydantic.Field(alias="crossWalletBalance")
    cross_unpnl: decimal.Decimal = pydantic.Field(alias="crossUnPnl")
    available_balance: decimal.Decimal = pydantic.Field(alias="availableBalance")
    max_withdraw_amount: decimal.Decimal = pydantic.Field(alias="maxWithdrawAmount")
    margin_available: bool = pydantic.Field(alias="marginAvailable")
    update_time: int = pydantic.Field(alias="updateTime")


BinanceFuturesBalance = list[BinanceFuturesBalanceAsset]


class BinanceClientFuturesBalance(core_.BinanceClientCore):
    def __init__(self) -> None:
        super().__init__()
        self.GET_FAPI_V3_BALANCE: tp.Final[core_.TAPIMethodKey] = (
            self._register_common_api_method("GET", "/fapi/v3/balance", weight=5)
        )

    async def _req_get_fapi_v3_balance(
        self, account: structures.BinanceAccount, use_trading_key: bool
    ) -> str:
        return await self._do_fapi_request(
            self.GET_FAPI_V3_BALANCE,
            core_.TRequestParams(
                account=account,
                force_use_trading_key=use_trading_key,
            ),
        )

    @staticmethod
    def _parse_futures_balance(json_str: str) -> BinanceFuturesBalance:
        return (
            pydantic.RootModel[BinanceFuturesBalance].model_validate_json(json_str).root
        )

    async def fetch_futures_balance(
        self,
        account: structures.BinanceAccount,
        use_trading_key: bool = False,
    ) -> BinanceFuturesBalance:
        return self._parse_futures_balance(
            await self._req_get_fapi_v3_balance(account, use_trading_key)
        )
