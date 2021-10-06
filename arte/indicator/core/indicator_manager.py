from collections import deque

from arte.data.ticker_parser import TickerParser
from arte.data.trade_parser import TradeParser

from arte.data.candlestick_parser import CandlestickParser

from arte.indicator.bollinger import Bollinger
from arte.indicator.premium import Premium


class Indicator:
    PREMIUM = "Premium"
    BOLLINGER = "Bollinger"
    ATR = "ATR"


class IndicatorManager:
    def __init__(self, indicators: list, deque_maxlen: int = 100):
        self.indicators = indicators
        self.value_dict = {}
        for indicator in self.indicators:
            self.value_dict[indicator] = deque(maxlen=deque_maxlen)

    def __getitem__(self, key):
        return self.value_dict[key]

    def update_bollinger(self, candlestick):
        if isinstance(candlestick, CandlestickManager):
            result = Bollinger.calc(candlestick.close)
            if candlestick.candle_closed:
                self.value_dict[Indicator.BOLLINGER].append(result)
            else:
                try:
                    self.value_dict[Indicator.BOLLINGER].pop()
                except:
                    pass
                self.value_dict[Indicator.BOLLINGER].append(result)

    def update_premium(self, upbit_ticker, binance_ticker, exchange_rate):
        if isinstance(upbit_ticker, TradeManager) and isinstance(binance_ticker, TradeManager):
            self.value_dict[Indicator.PREMIUM].append(Premium.calc(upbit_ticker, binance_ticker, exchange_rate))
