from core import tp

from . import core_


class BinanceClientFuturesAPIMethods(core_.BinanceClientCore):
    """Methods that supported in bypass proxy, but do not have full implementation"""

    def __init__(self) -> None:
        super().__init__()
        self.GET_API_V3_EXCHANGE_INFO: tp.Final[core_.TAPIMethodKey] = (
            self._register_common_api_method("GET", "/api/v3/exchangeInfo", weight=0)
        )
        self.GET_API_V3_GET_KLINES: tp.Final[core_.TAPIMethodKey] = (
            self._register_common_api_method("GET", "/api/v3/klines", weight=0)
        )
        self.GET_API_V3_GET_ACCOUNT: tp.Final[core_.TAPIMethodKey] = (
            self._register_common_api_method("GET", "/api/v3/account", weight=0)
        )

        self.GET_SAPI_V1_CAPITAL_DEPOSIT_ADDRESS: tp.Final[core_.TAPIMethodKey] = (
            self._register_common_api_method(
                "GET", "/sapi/v1/capital/deposit/address", weight=0
            )
        )
        self.GET_SAPI_V1_ACCOUNT_API_RESTRICTIONS: tp.Final[core_.TAPIMethodKey] = (
            self._register_common_api_method(
                "GET", "/sapi/v1/account/apiRestrictions", weight=0
            )
        )

        self.GET_FAPI_V1_USER_TRADES: tp.Final[core_.TAPIMethodKey] = (
            self._register_common_api_method("GET", "/fapi/v1/userTrades", weight=5)
        )
        self.GET_FAPI_V1_KLINES: tp.Final[core_.TAPIMethodKey] = (
            self._register_common_api_method("GET", "/fapi/v1/klines", weight=10)
        )
        self.GET_FAPI_V1_INCOME: tp.Final[core_.TAPIMethodKey] = (
            self._register_common_api_method("GET", "/fapi/v1/income", weight=30)
        )
        self.GET_FAPI_V2_POSITION_RISK: tp.Final[core_.TAPIMethodKey] = (
            self._register_common_api_method("GET", "/fapi/v2/positionRisk", weight=5)
        )
        self.GET_FAPI_V1_API_REFERRAL_IF_NEW_USER: tp.Final[core_.TAPIMethodKey] = (
            self._register_common_api_method(
                "GET", "/fapi/v1/apiReferral/ifNewUser", weight=100
            )
        )
