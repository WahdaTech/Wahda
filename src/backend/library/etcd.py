__all__ = ["ETCDClient", "etcd_api", "etcd_kv"]

import functools as ft
import json
import os

import grpc.aio

import proto.etcd.api.etcdserverpb.rpc_pb2 as etcd_api
import proto.etcd.api.etcdserverpb.rpc_pb2_grpc as etcd_api_grpc
import proto.etcd.api.mvccpb.kv_pb2 as etcd_kv
from core import awrap_, tp, unwrap_

P = tp.ParamSpec("P")
RT = tp.TypeVar("RT")


class MaxRetiresExceededException(tp.WDException):
    pass


class _ETCDClientImpl:
    JSON_CONFIG = json.dumps(
        {
            "methodConfig": [
                {
                    "name": [
                        {"service": "etcdserverpb.KV"},
                        {"service": "etcdserverpb.Lease"},
                    ],
                }
            ]
        }
    )
    KEY_SEP = ":"
    MAX_ATTEMPTS = 3

    def __init__(self) -> None:
        endpoints = os.environ["GRPC_ENDPOINTS_ETCD"].split(",")
        self._weights = [int(w) for w in os.environ["GRPC_WEIGHTS_ETCD"].split(",")]

        self._channels = [
            grpc.aio.insecure_channel(
                endpoint,
                options=[
                    ("grpc.service_config", _ETCDClientImpl.JSON_CONFIG),
                ],
            )
            for endpoint in endpoints
        ]
        self._stubs_kv = tp.cast(
            "list[etcd_api_grpc.KVAsyncStub]",
            [etcd_api_grpc.KVStub(ch) for ch in self._channels],
        )
        self._stubs_lease = tp.cast(
            "list[etcd_api_grpc.LeaseAsyncStub]",
            [etcd_api_grpc.LeaseStub(ch) for ch in self._channels],
        )
        self._endpoint_idx = 0
        self._endpoint_iter = iter(range(self._weights[self._endpoint_idx]))
        self._default_timeout = 1.0
        self._lease_keep_alive_timeout = 2.0
        self._with_retry = _ETCDClientImpl._with_retry_impl(self)

    @staticmethod
    def make_key(*parts: str) -> str:
        return _ETCDClientImpl.KEY_SEP.join(parts)

    @staticmethod
    def get_key_last_part(key: str) -> str:
        return key.rsplit(_ETCDClientImpl.KEY_SEP, maxsplit=1)[1]

    @staticmethod
    def make_prefix_range_request(
        orig_request: etcd_api.RangeRequest,
    ) -> etcd_api.RangeRequest:
        request = etcd_api.RangeRequest()
        request.CopyFrom(orig_request)
        request.range_end = request.key[:-1] + bytes([request.key[-1] + 1])

        return request

    @staticmethod
    def make_key_exists_compare_request(key: str) -> etcd_api.Compare:
        return etcd_api.Compare(
            result=etcd_api.Compare.CompareResult.NOT_EQUAL,
            target=etcd_api.Compare.CompareTarget.CREATE,
            key=key.encode(),
            create_revision=0,
        )

    @staticmethod
    def make_key_not_exists_compare_request(key: str) -> etcd_api.Compare:
        return etcd_api.Compare(
            result=etcd_api.Compare.CompareResult.EQUAL,
            target=etcd_api.Compare.CompareTarget.CREATE,
            key=key.encode(),
            create_revision=0,
        )

    @staticmethod
    def make_value_equals_compare_request(key: str, value: bytes) -> etcd_api.Compare:
        return etcd_api.Compare(
            result=etcd_api.Compare.CompareResult.EQUAL,
            target=etcd_api.Compare.CompareTarget.VALUE,
            key=key.encode(),
            value=value,
        )

    @staticmethod
    def make_value_not_equals_compare_request(
        key: str, value: bytes
    ) -> etcd_api.Compare:
        return etcd_api.Compare(
            result=etcd_api.Compare.CompareResult.NOT_EQUAL,
            target=etcd_api.Compare.CompareTarget.VALUE,
            key=key.encode(),
            value=value,
        )

    @staticmethod
    def _with_retry_impl(client: "_ETCDClientImpl"):
        def inner(func: tp.TAsyncFn[P, RT]) -> tp.TAsyncFn[P, RT]:
            @ft.wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
                exc = None

                for _ in range(_ETCDClientImpl.MAX_ATTEMPTS):
                    endpoint_idx = client._next_endpoint_idx()
                    kwargs["endpoint_idx"] = endpoint_idx

                    response, exc = await awrap_(
                        func,
                        # More granular re-raise is below.
                        suppress_classes=(BaseException,),
                    )(*args, **kwargs)

                    if exc is None:
                        return unwrap_(response)

                    if not isinstance(exc, grpc.RpcError) or (
                        exc.code()
                        not in (
                            grpc.StatusCode.UNAVAILABLE,
                            grpc.StatusCode.RESOURCE_EXHAUSTED,
                            grpc.StatusCode.DEADLINE_EXCEEDED,
                            grpc.StatusCode.DATA_LOSS,
                        )
                    ):
                        raise exc

                    client._switch_endpoint(endpoint_idx)
                raise MaxRetiresExceededException()

            return wrapper

        return inner

    def _switch_endpoint(self, cur_idx: int) -> None:
        if self._endpoint_idx == cur_idx:
            self._endpoint_idx = (self._endpoint_idx + 1) % len(self._channels)
            self._endpoint_iter = iter(range(self._weights[self._endpoint_idx]))

    def _next_endpoint_idx(self) -> int:
        if (_ := next(self._endpoint_iter, None)) is not None:
            return self._endpoint_idx

        self._switch_endpoint(self._endpoint_idx)

        return self._next_endpoint_idx()

    async def _kv_put(
        self,
        request: etcd_api.PutRequest,
        *,
        endpoint_idx: int = 0,
    ) -> etcd_api.PutResponse:
        return await self._stubs_kv[endpoint_idx].Put(
            request, timeout=self._default_timeout
        )

    async def kv_put(self, request: etcd_api.PutRequest) -> etcd_api.PutResponse:
        return await self._with_retry(self._kv_put)(request)

    async def _kv_range(
        self,
        request: etcd_api.RangeRequest,
        *,
        endpoint_idx: int = 0,
    ) -> etcd_api.RangeResponse:
        return await self._stubs_kv[endpoint_idx].Range(
            request, timeout=self._default_timeout
        )

    async def kv_range(self, request: etcd_api.RangeRequest) -> etcd_api.RangeResponse:
        return await self._with_retry(self._kv_range)(request)

    async def _kv_delete_range(
        self,
        request: etcd_api.DeleteRangeRequest,
        *,
        endpoint_idx: int = 0,
    ) -> etcd_api.DeleteRangeResponse:
        return await self._stubs_kv[endpoint_idx].DeleteRange(
            request, timeout=self._default_timeout
        )

    async def kv_delete_range(
        self, request: etcd_api.DeleteRangeRequest
    ) -> etcd_api.DeleteRangeResponse:
        return await self._with_retry(self._kv_delete_range)(request)

    async def _kv_txn(
        self,
        request: etcd_api.TxnRequest,
        *,
        endpoint_idx: int = 0,
    ) -> etcd_api.TxnResponse:
        return await self._stubs_kv[endpoint_idx].Txn(
            request, timeout=self._default_timeout
        )

    async def kv_txn(self, request: etcd_api.TxnRequest) -> etcd_api.TxnResponse:
        return await self._with_retry(self._kv_txn)(request)

    async def _lease_grant(
        self,
        request: etcd_api.LeaseGrantRequest,
        *,
        endpoint_idx: int = 0,
    ) -> etcd_api.LeaseGrantResponse:
        return await self._stubs_lease[endpoint_idx].LeaseGrant(
            request, timeout=self._default_timeout
        )

    async def lease_grant(
        self, request: etcd_api.LeaseGrantRequest
    ) -> etcd_api.LeaseGrantResponse:
        return await self._with_retry(self._lease_grant)(request)

    def _lease_keep_alive(
        self,
        requests_stream: (
            tp.AsyncIterator[etcd_api.LeaseKeepAliveRequest]
            | tp.Iterator[etcd_api.LeaseKeepAliveRequest]
        ),
        endpoint_idx: int,
    ) -> grpc.aio.StreamStreamCall[
        etcd_api.LeaseKeepAliveRequest, etcd_api.LeaseKeepAliveResponse
    ]:
        return self._stubs_lease[endpoint_idx].LeaseKeepAlive(
            requests_stream, timeout=self._lease_keep_alive_timeout
        )

    async def _lease_extend(
        self,
        lease_id: int,
        *,
        endpoint_idx: int = 0,
    ) -> etcd_api.LeaseKeepAliveResponse:
        stream = self._lease_keep_alive(
            requests_stream=iter((etcd_api.LeaseKeepAliveRequest(ID=lease_id),)),
            endpoint_idx=endpoint_idx,
        )

        async for response in stream:
            return response

        raise tp.WDException("Empty response stream")

    async def lease_extend(
        self,
        lease_id: int,
    ) -> etcd_api.LeaseKeepAliveResponse:
        return await self._with_retry(self._lease_extend)(lease_id)


class ETCDClient(_ETCDClientImpl):
    def __init__(self) -> None:
        if self._initialized:
            return

        super().__init__()
        self._initialized: bool = True

    def __new__(cls) -> "ETCDClient":
        if not hasattr(cls, "_instance"):
            cls._instance = super(ETCDClient, cls).__new__(cls)
            cls._initialized = False
        return cls._instance
