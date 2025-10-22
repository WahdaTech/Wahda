import functools as ft

from . import sentry, telemetry, tp

LOG = telemetry.get_logger()


def __handle_exception(
    exc: BaseException,
    suppress_classes: tp.Optional[tuple[type[BaseException]]] = None,
    discard_classes: tp.Optional[tuple[type[BaseException]]] = None,
) -> None:
    discarded: tuple[type[BaseException], ...] = ()
    if discard_classes is not None:
        discarded = discarded + discard_classes

    for cls in discarded:
        if isinstance(exc, cls):
            return

    suppressed: tuple[type[BaseException], ...] = ()
    if suppress_classes is not None:
        suppressed = suppressed + suppress_classes

    for cls in suppressed:
        if isinstance(exc, cls):
            LOG.opt(exception=exc).warning("suppressed exception")
            return

    LOG.exception(exc)
    sentry.capture_exception(exc)


def wrap_(
    fn: tp.TFn[tp.P, tp.RT],
    *,
    suppress_classes: tp.Optional[tuple[type[BaseException]]] = None,
    discard_classes: tp.Optional[tuple[type[BaseException]]] = None,
) -> tp.TFn[tp.P, tp.TValExc[tp.RT]]:
    @ft.wraps(fn)
    def wrapped(*args: tp.P.args, **kwargs: tp.P.kwargs) -> tp.TValExc[tp.RT]:
        try:
            return fn(*args, **kwargs), None
        except BaseException as exc:
            __handle_exception(exc, suppress_classes, discard_classes)
            return None, exc

    return wrapped


def awrap_(
    fn: tp.TAsyncFn[tp.P, tp.RT],
    *,
    suppress_classes: tp.Optional[tuple[type[BaseException]]] = None,
    discard_classes: tp.Optional[tuple[type[BaseException]]] = None,
) -> tp.TAsyncFn[tp.P, tp.TValExc[tp.RT]]:
    @ft.wraps(fn)
    async def wrapped(*args: tp.P.args, **kwargs: tp.P.kwargs) -> tp.TValExc[tp.RT]:
        try:
            return await fn(*args, **kwargs), None
        except BaseException as exc:
            __handle_exception(exc, suppress_classes, discard_classes)
            return None, exc

    return wrapped


def unwrap_(val: tp.Optional[tp.T]) -> tp.T:
    if val is None:
        raise tp.WDException("Unwrap exception")

    return val
