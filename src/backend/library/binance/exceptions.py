from core import tp


class BinanceClientException(tp.WDException):
    pass


class BinanceClientRateLimiterException(BinanceClientException):
    pass


class BinanceClientServerException(BinanceClientException):
    pass
