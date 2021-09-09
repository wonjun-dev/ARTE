from collections import deque

from arte.data.ticker_manager import TickerManager
from arte.data.trade_manager import TradeManager

from arte.data.candlestick_manager import CandlestickManager

from arte.indicator.bollinger import Bollinger
from arte.indicator.premium import Premium


class Indicator:
    PREMIUM = "Premium"
    BOLLINGER = "Bollinger"
    ATR = "ATR"


class IndicatorManager:
    def __init__(self, indicators: list, deque_maxlen: int = 50):
        """
        Manage various indicators
        Args:
            indicator_instance: (list) list of indicator instance
            deque_maxlen: (int) maxlen of deque
        """

        self.indicators = indicators
        self.value_dict = {}

        for indicator in self.indicators:
            self.value_dict[indicator] = deque(maxlen=deque_maxlen)

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

    def __getitem__(self, key):
        return self.value_dict[key]
