__all__ = [
    "RT",
    "Any",
    "AsyncIterator",
    "BinaryIO",
    "Callable",
    "Coroutine",
    "Final",
    "Generator",
    "Generic",
    "Hashable",
    "Iterable",
    "Iterator",
    "Mapping",
    "MutableSet",
    "Optional",
    "P",
    "ParamSpec",
    "Sequence",
    "T",
    "TAsyncFn",
    "TDict",
    "TExc",
    "TFn",
    "TValExc",
    "TypeAlias",
    "TypeVar",
    "WDException",
    "cast",
]


from collections.abc import (
    AsyncIterator,
    Callable,
    Coroutine,
    Generator,
    Hashable,
    Iterable,
    Iterator,
    Mapping,
    MutableSet,
    Sequence,
)
from typing import (
    Any,
    BinaryIO,
    Final,
    Generic,
    Optional,
    ParamSpec,
    TypeAlias,
    TypeVar,
    cast,
)


class WDException(BaseException):
    pass


T = TypeVar("T")
P = ParamSpec("P")
RT = TypeVar("RT")
TExc: TypeAlias = BaseException | None
TFn: TypeAlias = Callable[P, RT]
TAsyncFn: TypeAlias = Callable[P, Coroutine[Any, Any, RT]]
TValExc: TypeAlias = tuple[T | None, TExc]
TDict: TypeAlias = dict[str, Any]
