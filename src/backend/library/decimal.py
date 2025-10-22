import decimal

from core import tp

ZERO = decimal.Decimal(0)
ONE = decimal.Decimal(1)


def quantize(value: decimal.Decimal, step: decimal.Decimal, rounding: str):
    """
    Quantize a value to the nearest multiple of step.
    """
    if rounding in (decimal.ROUND_HALF_EVEN, decimal.ROUND_05UP):
        raise tp.WDException(f"{rounding} is not supported")

    if step.is_zero():
        return value

    return step * (value / step).to_integral_value(rounding=rounding)
