import enum


class Side(enum.Enum):
    BUY = 1
    SELL = 2

    @property
    def reversed(self):
        if self == Side.BUY:
            return Side.SELL
        return Side.BUY


class PositionSide(enum.Enum):
    BOTH = 0
    LONG = 1
    SHORT = 2


class OrderType(enum.Enum):
    MARKET = 1
