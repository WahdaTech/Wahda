# Aiesar (cyclone [ar.]) is a scheduler with predefined tasks generator (producer)
# that periodically executes all the tasks and stores their recent results.
# This is abstract class, you should redefine producer and consumer in a child class.

import asyncio
import dataclasses
import datetime

import arrow

from core import awrap_, telemetry, tp, unwrap_

LOG = telemetry.get_logger()


TKey: tp.TypeAlias = tp.Hashable
TRes = tp.TypeVar("TRes")  # parameter type for result
TPQItem: tp.TypeAlias = tuple[arrow.Arrow, TKey]


class AsyncioPriorityQueueUniq(asyncio.PriorityQueue[TPQItem]):
    def _init(self, maxsize: int) -> None:
        super()._init(maxsize)
        self._uniq_keys: tp.MutableSet[TKey] = set()

    def _put(self, item: TPQItem) -> None:
        super()._put(item)
        _, key = item
        self._uniq_keys.add(key)

    def put_nowait(self, item: TPQItem) -> None:
        """Dervied from the original asyncio.Queue method.
        Except it does no-op in case an item is already in the queue.
        """
        if self.full():
            raise asyncio.queues.QueueFull
        _, key = item
        if key not in self._uniq_keys:
            self._put(item)
            self._unfinished_tasks += 1  # type: ignore
            self._finished.clear()  # type: ignore
        self._wakeup_next(self._getters)  # type: ignore

    def _get(self) -> TPQItem:
        item = super()._get()
        _, key = item
        self._uniq_keys.remove(key)

        return item


@dataclasses.dataclass
class AiesarItem(tp.Generic[TRes]):
    key: TKey
    updated_at: arrow.Arrow = dataclasses.field(default_factory=arrow.utcnow)
    active: bool = True
    last_processed_at: tp.Optional[arrow.Arrow] = None
    result: tp.Optional[TRes] = None


class AiesarBase(tp.Generic[TRes]):
    def __init__(
        self,
        *,
        ttl: datetime.timedelta,
        pool_size: int = 10,
    ) -> None:
        self._ttl = ttl
        self._cleanup_ttl = datetime.timedelta(seconds=5)
        self._pool_size = pool_size
        self._max_delta_to_wait = 0.1
        self._queue = AsyncioPriorityQueueUniq()
        self._store: dict[TKey, AiesarItem[TRes]] = {}
        self._workers_handlers: list[asyncio.Task[None]] = []
        self._running = False

    @property
    def _get_interval(self) -> datetime.timedelta:
        return datetime.timedelta(seconds=1.0)

    def _hook_key_deleted(self, key: TKey) -> None:
        pass

    def _cleanup_item(self, key: TKey) -> None:
        del self._store[key]
        self._hook_key_deleted(key)

    def _cleanup_results(self) -> None:
        now = arrow.utcnow()
        for key, item in list(self._store.items()):
            if item.active:
                continue

            if item.last_processed_at is None:
                self._cleanup_item(key)
            elif item.last_processed_at + self._cleanup_ttl < now:
                self._cleanup_item(key)

    @property
    def results(self) -> tp.Mapping[TKey, TRes]:
        now = arrow.utcnow()
        return {
            key: item.result
            for key, item in self._store.items()
            if (item.result is not None) and (item.updated_at + self._ttl >= now)
        }

    def _task_is_active(self, key: TKey) -> bool:
        item = self._store.get(key)
        return (item is not None) and item.active

    def _process_item(self, key: TKey) -> tp.Optional[AiesarItem[TRes]]:
        if not self._task_is_active(key):
            return None

        item = self._store[key]
        item.last_processed_at = arrow.utcnow()

        return item

    async def _producer(self) -> tp.Iterable[TKey]:
        raise NotImplementedError()

    async def _consumer(self, key: TKey) -> TRes:
        raise NotImplementedError()

    def _handle_consumer_exception(self, key: TKey, exc: BaseException) -> None:
        self._process_item(key)

    def _update_result(
        self, item: AiesarItem[TRes], result_update: tp.Optional[TRes]
    ) -> None:
        item.result = result_update
        item.updated_at = unwrap_(item.last_processed_at)

    async def _process_task(self, key: TKey) -> tp.TExc:
        if not self._task_is_active(key):
            return None

        # awrap_ is required because an exception must be processed
        # by the separate handler below.
        result, exc = await awrap_(self._consumer)(key)
        if exc is not None:
            self._handle_consumer_exception(key, exc)
            raise exc
        elif (item := self._process_item(key)) is not None:
            self._update_result(item, result)

        return None

    async def _put_task(self, key: TKey) -> tp.TExc:
        if not self._task_is_active(key):
            return None

        run_at: arrow.Arrow = arrow.utcnow()
        if last_processed_at := self._store[key].last_processed_at:
            run_at = last_processed_at + self._get_interval

        await self._queue.put((run_at, key))

        return None

    async def _worker_loop_iteration(self, run_at: arrow.Arrow, key: TKey) -> None:
        delta = (run_at - arrow.utcnow()).total_seconds()
        if delta < self._max_delta_to_wait:
            await asyncio.sleep(delta)
            await awrap_(self._process_task)(key)
        else:
            await asyncio.sleep(self._max_delta_to_wait)

        if self._running:
            await self._put_task(key)

    async def _worker_loop(self) -> None:
        while True:
            if self._queue.empty():
                if not self._running:
                    break
                await asyncio.sleep(self._max_delta_to_wait)
                continue

            run_at, key = self._queue.get_nowait()

            # awrap_ required as we must call task_done() in any case.
            await awrap_(self._worker_loop_iteration)(run_at, key)
            self._queue.task_done()

    async def _worker(self, worker_id: int) -> None:
        while True:
            _, exc = await awrap_(self._worker_loop)()

            if exc is not None:
                if isinstance(exc, asyncio.CancelledError):
                    break
                continue

            # worker exited normally
            break

        LOG.info(
            "{scheduler_name} worker_{worker_id} stopped",
            scheduler_name=type(self).__name__,
            worker_id=worker_id,
        )

    async def sync_tasks(self) -> None:
        self._cleanup_results()

        keys = list(await self._producer())

        for item in self._store.values():
            item.active = False

        for key in keys:
            if key in self._store:
                self._store[key].active = True

        for key in keys:
            if key in self._store:
                continue

            self._store[key] = AiesarItem(key=key)
            # awrap_ is required here because the loop must not be broken amid.
            await awrap_(self._put_task)(key)

    async def _sync_tasks_worker(self) -> None:
        while self._running:
            # the show must go on
            await awrap_(self.sync_tasks)()
            await asyncio.sleep(5)

    async def run(self) -> None:
        self._running = True
        worker = asyncio.create_task(self._sync_tasks_worker())
        self._workers_handlers.append(worker)

        for worker_id in range(self._pool_size):
            worker = asyncio.create_task(self._worker(worker_id))
            self._workers_handlers.append(worker)

    def stop(self) -> None:
        self._running = False

    async def join(self) -> None:
        await self._queue.join()

        all_tasks = self._workers_handlers.copy()
        self._workers_handlers = []
        self._queue = AsyncioPriorityQueueUniq()

        await asyncio.gather(*all_tasks)
