import asyncio
import datetime

import pytest

from core import tp
from library.util.schedule import aiesar

N_TASKS = 50


class AiesarTest(aiesar.AiesarBase[int]):
    def __init__(
        self,
        *,
        ttl: datetime.timedelta,
        pool_size: int = 10,
    ) -> None:
        super().__init__(ttl=ttl, pool_size=pool_size)
        self.ranges = [iter(range(0, 100)) for _ in range(N_TASKS)]

    async def _producer(self) -> tp.Iterable[str]:
        return map(str, range(N_TASKS))

    async def _consumer(self, key: aiesar.TKey) -> int:
        if isinstance(key, str):
            id_ = int(key)
            return next(self.ranges[id_], 0)

        raise tp.WDException(f"Key type {type(key)} is not supported")


@pytest.mark.asyncio
async def test_basic() -> None:
    aiesar = AiesarTest(ttl=datetime.timedelta(seconds=10))

    await aiesar.run()
    await asyncio.sleep(2.5)
    aiesar.stop()
    await aiesar.join()
    assert list(aiesar.results.values()) == ([2] * N_TASKS)
