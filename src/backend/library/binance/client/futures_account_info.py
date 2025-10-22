import decimal

import arrow
import msgspec

from core import tp

from .. import structures
from . import core_


class BinanceFuturesAccountInfoAsset(msgspec.Struct, frozen=True):
    asset: str
    wallet_balance: decimal.Decimal = msgspec.field(name="walletBalance")
    unrealized_profit: decimal.Decimal = msgspec.field(name="unrealizedProfit")
    margin_balance: decimal.Decimal = msgspec.field(name="marginBalance")
    maint_margin: decimal.Decimal = msgspec.field(name="maintMargin")
    initial_margin: decimal.Decimal = msgspec.field(name="initialMargin")
    position_initial_margin: decimal.Decimal = msgspec.field(
        name="positionInitialMargin"
    )
    open_order_initial_margin: decimal.Decimal = msgspec.field(
        name="openOrderInitialMargin"
    )
    cross_wallet_balance: decimal.Decimal = msgspec.field(name="crossWalletBalance")
    cross_unpnl: decimal.Decimal = msgspec.field(name="crossUnPnl")
    available_balance: decimal.Decimal = msgspec.field(name="availableBalance")
    max_withdraw_amount: decimal.Decimal = msgspec.field(name="maxWithdrawAmount")
    margin_available: bool = msgspec.field(name="marginAvailable")
    update_time: int = msgspec.field(name="updateTime")


class BinanceFuturesAccountInfoPosition(msgspec.Struct, frozen=True):
    symbol: str
    initial_margin: decimal.Decimal = msgspec.field(name="initialMargin")
    maint_margin: decimal.Decimal = msgspec.field(name="maintMargin")
    unrealized_profit: decimal.Decimal = msgspec.field(name="unrealizedProfit")
    position_initial_margin: decimal.Decimal = msgspec.field(
        name="positionInitialMargin"
    )
    open_order_initial_margin: decimal.Decimal = msgspec.field(
        name="openOrderInitialMargin"
    )
    leverage: int
    isolated: bool
    entry_price: decimal.Decimal = msgspec.field(name="entryPrice")
    max_notional: decimal.Decimal = msgspec.field(name="maxNotional")
    position_side: str = msgspec.field(name="positionSide")
    position_amt: decimal.Decimal = msgspec.field(name="positionAmt")
    update_time: int = msgspec.field(name="updateTime")


class BinanceFuturesAccountInfo(msgspec.Struct, frozen=True):
    fee_tier: int = msgspec.field(name="feeTier")
    can_trade: bool = msgspec.field(name="canTrade")
    multi_assets_margin: bool = msgspec.field(name="multiAssetsMargin")
    total_initial_margin: decimal.Decimal = msgspec.field(name="totalInitialMargin")
    total_maint_margin: decimal.Decimal = msgspec.field(name="totalMaintMargin")
    total_wallet_balance: decimal.Decimal = msgspec.field(name="totalWalletBalance")
    total_unrealized_profit: decimal.Decimal = msgspec.field(
        name="totalUnrealizedProfit"
    )
    total_margin_balance: decimal.Decimal = msgspec.field(name="totalMarginBalance")
    total_position_initial_margin: decimal.Decimal = msgspec.field(
        name="totalPositionInitialMargin"
    )
    total_open_order_initial_margin: decimal.Decimal = msgspec.field(
        name="totalOpenOrderInitialMargin"
    )
    total_cross_wallet_balance: decimal.Decimal = msgspec.field(
        name="totalCrossWalletBalance"
    )
    total_cross_unpnl: decimal.Decimal = msgspec.field(name="totalCrossUnPnl")
    available_balance: decimal.Decimal = msgspec.field(name="availableBalance")
    max_withdraw_amount: decimal.Decimal = msgspec.field(name="maxWithdrawAmount")
    assets: list[BinanceFuturesAccountInfoAsset]
    positions: list[BinanceFuturesAccountInfoPosition]
    created_at: str = msgspec.field(default_factory=lambda: arrow.utcnow().isoformat())


class BinanceClientFuturesAccountInfo(core_.BinanceClientCore):
    decoder = msgspec.json.Decoder(strict=False, type=BinanceFuturesAccountInfo)

    def __init__(self) -> None:
        super().__init__()
        self.GET_FAPI_V2_ACCOUNT_INFO: tp.Final[core_.TAPIMethodKey] = (
            self._register_common_api_method("GET", "/fapi/v2/account", weight=5)
        )

    async def _req_get_fapi_v2_account(self, account: structures.BinanceAccount) -> str:
        return await self._do_fapi_request(
            self.GET_FAPI_V2_ACCOUNT_INFO,
            core_.TRequestParams(account=account),
        )

    @staticmethod
    def _parse_futures_account_info(json_str: str) -> BinanceFuturesAccountInfo:
        return BinanceClientFuturesAccountInfo.decoder.decode(json_str)

    async def fetch_futures_account_info(
        self, account: structures.BinanceAccount
    ) -> BinanceFuturesAccountInfo:
        return self._parse_futures_account_info(
            await self._req_get_fapi_v2_account(account)
        )
