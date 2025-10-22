import pytest

from library import binance
from library.binance.client.core_ import (
    BinanceClientCore,
    TAPIKind,
    TAPIMethod,
    THeaders,
    TRequestParams,
    TRequestQuotaUsage,
    TURLParams,
)


class BinanceClientCoreTest(BinanceClientCore):
    def build_url_test(self, api_method: TAPIMethod) -> str:
        return self._build_url(api_method)

    @staticmethod
    def _get_cur_timestamp() -> int:
        return 1703028215865

    async def sign_request_test(
        self, req_params: binance.TRequestParams, trading: bool
    ) -> None:
        await super()._sign_request(req_params, trading)


@pytest.mark.asyncio
async def test_fapi_endpoint() -> None:
    client = BinanceClientCoreTest()
    await client.run()
    await client.stop()

    def quota_usage_fn(_: TRequestParams):
        return TRequestQuotaUsage()

    assert (
        client.build_url_test(
            TAPIMethod(
                TAPIKind.API,
                "GET",
                "/api/v3/exchangeInfo",
                trading=False,
                quota_usage_fn=quota_usage_fn,
                ignore_used_limits=False,
            )
        )
        == "https://api.binance.com/api/v3/exchangeInfo"
    )

    assert (
        client.build_url_test(
            TAPIMethod(
                TAPIKind.FAPI,
                "GET",
                "/fapi/v1/exchangeInfo",
                trading=False,
                quota_usage_fn=quota_usage_fn,
                ignore_used_limits=False,
            )
        )
        == "https://fapi.binance.com/fapi/v1/exchangeInfo"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["trading", "key", "sign"],
    [
        (
            False,
            "abc",
            "c555dd33624e2004f182c137b3d24787157460a51321eeefdd22c432b8be7e66",
        ),
        (
            True,
            "foo",
            "fbbc4b4bf61ea4a9c06e83a4288d9125449dbc522aeef48471cd9183c72d6d19",
        ),
    ],
)
async def test_sign_request(trading: bool, key: str, sign: str) -> None:
    client = BinanceClientCoreTest()
    account = binance.BinanceAccount("xyz", "abc", "123", "foo", "bar")
    await client.run()
    await client.stop()

    headers = THeaders({"Header": "Value"})
    params = TURLParams({"foo": "bar"})
    data = {"bimbim": "bambam"}
    await client.sign_request_test(
        binance.TRequestParams(
            account=account,
            headers=headers,
            url_params=params,
            body_data=data,
        ),
        trading,
    )

    assert headers["Header"] == "Value"
    assert headers["X-MBX-APIKEY"] == key
    assert params["signature"] == sign
