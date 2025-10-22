import decimal

import library.decimal
from core import tp, wrap_


def test_quantize() -> None:
    def _test_one(val: str, step: str, rounding: str, expected: str):
        assert library.decimal.quantize(
            decimal.Decimal(val), decimal.Decimal(step), rounding
        ) == decimal.Decimal(expected)

    _test_one("123.456", "0.0001", decimal.ROUND_DOWN, "123.456")
    _test_one("123.456", "0.001", decimal.ROUND_DOWN, "123.456")
    _test_one("123.456", "0.01", decimal.ROUND_DOWN, "123.45")
    _test_one("123.456", "0.1", decimal.ROUND_DOWN, "123.4")
    _test_one("123.456", "1", decimal.ROUND_DOWN, "123")
    _test_one("123.456", "10", decimal.ROUND_DOWN, "120")
    _test_one("123.456", "100", decimal.ROUND_DOWN, "100")
    _test_one("123.456", "1000", decimal.ROUND_DOWN, "0")

    _test_one("123.456", "1.0", decimal.ROUND_DOWN, "123")
    _test_one("123.456", "125", decimal.ROUND_UP, "125")
    _test_one("7", "2", decimal.ROUND_HALF_DOWN, "6")
    _test_one("7", "2", decimal.ROUND_HALF_UP, "8")
    _test_one("7.8", "5.0", decimal.ROUND_DOWN, "5.0")

    _test_one("-123.45", "0.1", decimal.ROUND_DOWN, "-123.4")
    _test_one("-123.45", "0.1", decimal.ROUND_HALF_UP, "-123.5")
    _test_one("-123.45", "0.1", decimal.ROUND_CEILING, "-123.4")
    _test_one("-123.45", "0.1", decimal.ROUND_FLOOR, "-123.5")
    _test_one("-123.45", "0.1", decimal.ROUND_UP, "-123.5")
    _test_one("-123.45", "0.1", decimal.ROUND_HALF_DOWN, "-123.4")

    _test_one("123.456789", "0", decimal.ROUND_DOWN, "123.456789")

    _, exc = wrap_(_test_one)("-123.45", "0.1", decimal.ROUND_HALF_EVEN, "0")
    assert isinstance(exc, tp.WDException)

    _, exc = wrap_(_test_one)("-123.45", "0.1", decimal.ROUND_05UP, "0")
    assert isinstance(exc, tp.WDException)
