import aiohttp

from core import tp


class HttpClient:
    def __init__(
        self,
        local_addr: tp.Optional[tuple[str, int]] = None,
        total_timeout: float = 60.0,
        connect_timeout: float = 5.0,
    ) -> None:
        self._local_addr = local_addr
        self._session: tp.Optional[aiohttp.ClientSession] = None
        self._running: bool = False
        self._total_timeout = total_timeout
        self._connect_timeout = connect_timeout

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise tp.WDException("session is not initialized")

        return self._session

    async def run(self) -> None:
        if self._running:
            raise tp.WDException("HttpClient is already running.")

        conn = aiohttp.TCPConnector(local_addr=self._local_addr)
        timeout = aiohttp.ClientTimeout(
            total=self._total_timeout, connect=self._connect_timeout
        )
        self._session = aiohttp.ClientSession(
            connector=conn,
            timeout=timeout,
            raise_for_status=True,
        )
        self._running = True

    async def stop(self) -> None:
        if self._session is not None:
            await self._session.close()
        self._running = False
