import collections
import dataclasses
import datetime
import enum
import os

import aiohttp
import arrow
import multidict
import prometheus_client

import library.util.http_client
from core import awrap_, telemetry, tp, unwrap_, wrap_

from .. import exceptions, structures

LOG = telemetry.get_logger()

TBinanceCore = tp.TypeVar("TBinanceCore", bound="BinanceClientCore")
TRequesLimit = collections.defaultdict[str, structures.BinanceLimit]
TAPIMethodKey = tuple[str, str]
THeaders = multidict.CIMultiDict
TURLParams = multidict.MultiDict


class TAPIKind(enum.Enum):
    API = 1
    FAPI = 2


@dataclasses.dataclass()
class TRequestParams:
    account: tp.Optional[structures.BinanceAccount] = None
    headers: THeaders[str] = dataclasses.field(default_factory=THeaders)
    url_params: TURLParams[str] = dataclasses.field(default_factory=TURLParams)
    body_data: tp.Optional[tp.TDict] = None
    force_use_trading_key: bool = False


@dataclasses.dataclass(frozen=True)
class TRequestQuotaUsage:
    fapi_weight: int = 0
    fapi_orders: int = 0


TAPIMethodQuotaUsageFn = tp.TFn[[TRequestParams], TRequestQuotaUsage]


@dataclasses.dataclass(frozen=True)
class TAPIMethod:
    api_kind: TAPIKind
    http_method: str
    path: str
    trading: bool
    quota_usage_fn: TAPIMethodQuotaUsageFn
    ignore_used_limits: bool


class BinanceClientCore:
    def __init__(self) -> None:
        self._src_ip = os.environ.get("SOURCE_IP")
        local_addr = (self._src_ip, 0) if self._src_ip else None
        self._public_client = library.util.http_client.HttpClient(
            local_addr=local_addr, total_timeout=5.0
        )
        self._private_client = library.util.http_client.HttpClient(total_timeout=5.0)
        self._reqv_window = os.environ.get("BINANCE_CLIENT_REQV_WINDOW", "5000")
        self._lim_store: dict[str, int] = {}
        self._throttled_until = {
            TAPIKind.API: arrow.utcnow(),
            TAPIKind.FAPI: arrow.utcnow(),
        }
        self._fapi_weight_1m: TRequesLimit = collections.defaultdict(
            lambda: structures.BinanceLimit(
                reserved=50,
                label=structures.BinanceLimit.WEIGHT_1M_LABEL,
                interval=datetime.timedelta(minutes=1),
                lim_store=self._lim_store,
            ),
        )
        self._fapi_orders_1m: TRequesLimit = collections.defaultdict(
            lambda: structures.BinanceLimit(
                reserved=25,
                label=structures.BinanceLimit.ORDERS_1M_LABEL,
                interval=datetime.timedelta(minutes=1),
                lim_store=self._lim_store,
            ),
        )
        self._fapi_orders_10s: TRequesLimit = collections.defaultdict(
            lambda: structures.BinanceLimit(
                reserved=5,
                label=structures.BinanceLimit.ORDERS_10S_LABEL,
                interval=datetime.timedelta(seconds=10),
                lim_store=self._lim_store,
            ),
        )
        self._proxy: tp.Optional[str] = os.environ.get("BINANCE_CLIENT_PROXY")
        self._api_endpoint: str = os.environ.get(
            "BINANCE_CLIENT_API_ENDPOINT", "https://api.binance.com"
        )
        self._fapi_endpoint: str = os.environ.get(
            "BINANCE_CLIENT_FAPI_ENDPOINT", "https://fapi.binance.com"
        )
        self._fapi_trading_endpoint: tp.Optional[str] = os.environ.get(
            "BINANCE_CLIENT_FAPI_TRADING_ENDPOINT"
        )
        self._whitelist_endpoint: str | None = os.environ.get(
            "BINANCE_CLIENT_IP_WHITELISTED_ENDPOINT"
        )
        self._metric_used_weight: tp.Optional[prometheus_client.Gauge] = None
        self._api_methods: dict[TAPIMethodKey, TAPIMethod] = {}

    @staticmethod
    def _simple_weight_fn(weight: int = 0, orders: int = 0) -> TAPIMethodQuotaUsageFn:
        def wrapped(_: TRequestParams):
            return TRequestQuotaUsage(weight, orders)

        return wrapped

    def _register_api_method(
        self,
        http_method: str,
        path: str,
        *,
        trading: bool,
        quota_usage_fn: TAPIMethodQuotaUsageFn,
        ignore_used_limits: bool = False,
    ) -> TAPIMethodKey:
        if path.startswith("/api/") or path.startswith("/sapi/"):
            api_kind = TAPIKind.API
        elif path.startswith("/fapi/"):
            api_kind = TAPIKind.FAPI
        else:
            raise ValueError("Attempt to register unsupported API method")

        key = (http_method, path)
        self._api_methods[key] = TAPIMethod(
            api_kind,
            http_method,
            path,
            trading,
            quota_usage_fn,
            ignore_used_limits,
        )

        return key

    def get_api_method(self, http_method: str, path: str) -> TAPIMethod:
        if api_method := self._api_methods.get((http_method, path)):
            return api_method

        raise exceptions.BinanceClientException(f"Unknown method: {http_method} {path}")

    def _register_common_api_method(
        self, http_method: str, path: str, weight: int
    ) -> TAPIMethodKey:
        return self._register_api_method(
            http_method,
            path,
            trading=False,
            quota_usage_fn=self._simple_weight_fn(weight=weight),
        )

    async def run(self) -> None:
        self._metric_used_weight = prometheus_client.Gauge(
            "binance_client_used_weight",
            "Used requests weight for Binance",
            ["interval", "src_iface"],
        )

        await self._public_client.run()
        await self._private_client.run()

    async def stop(self) -> None:
        if self._metric_used_weight is not None:
            prometheus_client.REGISTRY.unregister(self._metric_used_weight)

        await self._public_client.stop()
        await self._private_client.stop()

    @staticmethod
    def _request_params_to_payload(params: tp.Mapping[str, tp.Any]) -> str:
        return "&".join(f"{k}={v}" for k, v in params.items())

    @staticmethod
    def _get_cur_timestamp() -> int:
        timestamp = arrow.utcnow().timestamp()
        return int(timestamp * 1000)

    async def _sign_request(self, req_params: TRequestParams, trading: bool) -> None:
        account = unwrap_(req_params.account)
        req_params.headers["X-MBX-APIKEY"] = (
            account.trading_api_key if trading else account.api_key
        )
        req_params.url_params.update(
            {
                "recvWindow": str(self._reqv_window),
                "timestamp": str(self._get_cur_timestamp()),
            }
        )
        payload = self._request_params_to_payload(req_params.url_params)
        if req_params.body_data is not None:
            payload += self._request_params_to_payload(req_params.body_data)

        if trading and account.trading_api_secret.startswith("enc_proto_"):
            req_params.headers["X-ACCOUNT-ID"] = account.account_id
            req_params.headers["X-ENCRYPTED-SECRET"] = account.trading_api_secret
        else:
            req_params.url_params["signature"] = account.get_signature(payload, trading)

    def _update_used_limits(
        self,
        headers: tp.Mapping[str, str],
        src_iface: str,
        account: tp.Optional[structures.BinanceAccount],
    ) -> None:
        if used_weight_1m := headers.get("x-mbx-used-weight-1m"):
            used_weight = int(used_weight_1m)
            self._fapi_weight_1m[src_iface].used = used_weight
            unwrap_(self._metric_used_weight).labels(
                interval="1m", src_iface=src_iface
            ).set(used_weight)

        if account is not None:
            if order_count_1m := headers.get("x-mbx-order-count-1m"):
                self._fapi_orders_1m[account.account_id].used = int(order_count_1m)
            if order_count_10s := headers.get("x-mbx-order-count-10s"):
                self._fapi_orders_10s[account.account_id].used = int(order_count_10s)

    def _handle_retry_after(
        self, api_method: TAPIMethod, status: int, headers: tp.Mapping[str, str]
    ):
        # If we got 418 (banned), then set default throttle 120 sec
        # in the case Retry-After is not present in the response.
        if status == 418:
            default_throttle = arrow.utcnow() + datetime.timedelta(seconds=120)
            self._throttled_until[api_method.api_kind] = max(
                self._throttled_until[api_method.api_kind], default_throttle
            )

        # 429 responses for methods limited by account/UID
        # will not contain Retry-After, according to the docs.
        # I hope that we can trust this, as otherwise such query for account with
        # exhausted quota hypothetically able to throttle the whole proxy.
        if retry_after := headers.get("retry-after"):
            self._throttled_until[api_method.api_kind] = (
                arrow.utcnow() + datetime.timedelta(seconds=int(retry_after) + 10)
            )

    async def _handle_request_response(
        self,
        api_method: TAPIMethod,
        resp: aiohttp.client.ClientResponse,
        src_iface: str,
        account: tp.Optional[structures.BinanceAccount],
    ) -> None:
        if api_method.api_kind == TAPIKind.FAPI and not api_method.ignore_used_limits:
            wrap_(self._update_used_limits)(resp.headers, src_iface, account)

        if account is None:
            LOG.debug(
                (
                    "request to {path} done from ({src_iface}):"
                    "\n- weight (1m): {weight_1m_used}"
                ),
                path=resp.url.path,
                src_iface=src_iface,
                weight_1m_used=self._fapi_weight_1m[src_iface].used,
            )
        else:
            orders_1m = self._fapi_orders_1m[account.account_id].used
            orders_10s = self._fapi_orders_10s[account.account_id].used
            LOG.debug(
                (
                    "request to {path} done from ({src_iface}):"
                    "\n- weight (1m): {weight_1m_used}, "
                    "orders (1m): {orders_1m_used}, "
                    "orders (10s): {orders_10s_used}"
                ),
                path=resp.url.path,
                src_iface=src_iface,
                weight_1m_used=self._fapi_weight_1m[src_iface].used,
                orders_1m_used=orders_1m,
                orders_10s_used=orders_10s,
            )

    def _build_fapi_trading_endpoint_url(self, path: str) -> str:
        return f"{self._fapi_trading_endpoint}{path}"

    def _build_url(self, api_method: TAPIMethod, ip_whitelisted=False) -> str:
        if ip_whitelisted and self._whitelist_endpoint:
            return f"{self._whitelist_endpoint}{api_method.path}"

        match api_method.api_kind:
            case TAPIKind.API:
                return f"{self._api_endpoint}{api_method.path}"
            case TAPIKind.FAPI:
                return f"{self._fapi_endpoint}{api_method.path}"

    # Source interface, either eth ip or proxy
    def _get_src_iface(self) -> str:
        if self._proxy is not None:
            return self._proxy
        if self._src_ip is not None:
            return self._src_ip
        return "0.0.0.0"

    def _allocate_limits(
        self,
        quota_usage: TRequestQuotaUsage,
        req_params: TRequestParams,
        src_iface: str,
    ) -> bool:
        if not self._fapi_weight_1m[src_iface].allocate(quota_usage.fapi_weight):
            return False

        if (req_params.account is None) or (quota_usage.fapi_orders == 0):
            return True
        account_id = req_params.account.account_id

        if not self._fapi_orders_10s[account_id].allocate(quota_usage.fapi_orders):
            self._fapi_weight_1m[src_iface].free(quota_usage.fapi_weight)
            return False

        if not self._fapi_orders_1m[account_id].allocate(quota_usage.fapi_orders):
            self._fapi_weight_1m[src_iface].free(quota_usage.fapi_weight)
            self._fapi_orders_10s[account_id].free(quota_usage.fapi_orders)
            return False

        return True

    def _free_limits(
        self,
        quota_usage: TRequestQuotaUsage,
        req_params: TRequestParams,
        src_iface: str,
    ) -> None:
        self._fapi_weight_1m[src_iface].free(quota_usage.fapi_weight)

        if (req_params.account is None) or (quota_usage.fapi_orders == 0):
            return
        account_id = req_params.account.account_id

        self._fapi_orders_10s[account_id].free(quota_usage.fapi_orders)
        self._fapi_orders_1m[account_id].free(quota_usage.fapi_orders)

    async def _do_request_inner(
        self,
        client: library.util.http_client.HttpClient,
        api_method: TAPIMethod,
        url: str,
        req_params: TRequestParams,
        trading: bool,
        proxy: tp.Optional[str],
        src_iface: str,
    ) -> aiohttp.ClientResponse:
        if arrow.utcnow() < self._throttled_until[api_method.api_kind]:
            raise exceptions.BinanceClientRateLimiterException("Request was trottled")

        if req_params.account is not None:
            await self._sign_request(req_params, trading)

        req_headers = req_params.headers.copy()
        req_headers["Accept-Encoding"] = "gzip"

        async with client.session.request(
            api_method.http_method,
            url,
            headers=req_params.headers,
            params=req_params.url_params,
            data=req_params.body_data,
            raise_for_status=False,
            proxy=proxy,
        ) as resp:
            await self._handle_request_response(
                api_method, resp, src_iface, req_params.account
            )
            await resp.read()

            return resp

    async def do_request_raw(
        self,
        api_method: TAPIMethod,
        req_params: tp.Optional[TRequestParams] = None,
    ) -> aiohttp.ClientResponse:
        _params = req_params if req_params is not None else TRequestParams()
        trading = _params.force_use_trading_key or api_method.trading

        if trading and self._fapi_trading_endpoint is not None:
            client = self._private_client
            url = self._build_fapi_trading_endpoint_url(api_method.path)
            proxy = None
            src_iface = self._fapi_trading_endpoint
        else:
            client = self._public_client
            url = self._build_url(
                api_method,
                _params.account.ip_whitelisted
                if _params.account is not None
                else False,
            )
            proxy = self._proxy
            src_iface = self._get_src_iface()

        quota_usage = api_method.quota_usage_fn(_params)
        if not self._allocate_limits(quota_usage, _params, src_iface):
            raise exceptions.BinanceClientRateLimiterException(
                "Cannot allocate requested amount"
            )

        resp_, exc = await awrap_(self._do_request_inner)(
            client, api_method, url, _params, trading, proxy, src_iface
        )

        wrap_(self._free_limits)(quota_usage, _params, src_iface)

        if exc is not None:
            raise exc

        resp = unwrap_(resp_)

        if resp.status in (418, 429):
            wrap_(self._handle_retry_after)(api_method, resp.status, resp.headers)

        return resp

    async def do_request(
        self, method: str, path: str, req_params: tp.Optional[TRequestParams] = None
    ) -> aiohttp.ClientResponse:
        api_method = self.get_api_method(method, path)
        resp = await self.do_request_raw(api_method, req_params)

        if resp.status == 200:
            return resp

        resp_text = await resp.text()
        status_code_msg = f"Status code: {resp.status}, response text: {resp_text}"

        if resp.status >= 500:
            raise exceptions.BinanceClientServerException(status_code_msg)

        if resp.status in (418, 429):
            raise exceptions.BinanceClientRateLimiterException(status_code_msg)

        raise exceptions.BinanceClientException(status_code_msg)

    async def _do_fapi_request(
        self,
        api_method: tuple[str, str],
        req_params: tp.Optional[TRequestParams] = None,
    ) -> str:
        method, path = api_method
        _params = req_params if req_params is not None else TRequestParams()

        resp = await self.do_request(method, path, req_params=_params)

        return await resp.text()
