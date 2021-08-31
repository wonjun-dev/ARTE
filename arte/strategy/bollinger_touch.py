import numpy as np

from arte.strategy.core.base_strategy import BaseStrategy
from arte.strategy.core.base_strategy import check_cross


class BollingerTouch(BaseStrategy):
    def __init__(
        self,
        indicator_manager,
        buy_ratio: float = 0.1,
        sell_ratio: float = 1.0,
    ):
        super().__init__(indicator_manager, buy_ratio, sell_ratio)

        # 전략 특화 초기화
        self.enter_cur_candle = False
        self.price_queue = None
        self.signals = {"TouchDirection": None, "Volatility": None, "StartFrom": None}

    def _make_signals(self, indicators: dict):
        print(indicators)
        bu = [v[0] for v in list(indicators["Bollinger"])]
        bm = [v[0] for v in list(indicators["Bollinger"])]
        bl = [v[0] for v in list(indicators["Bollinger"])]

        self.signals["TouchDirection"] = self.__touch_direction(self.data.close, bu)

        # self.price_queue = self.data.close
        # self.__check_candle_update(self.price_queue)
        # make signal
        # signal1 = func1(indicator['Bollinger up'], self.current_price)
        # signal2 = func1(indicator['Bollinger down'], self.current_price)
        # self.signals.append(signal1)
        # self.signals.append(signal2)
        pass

    def _order(self, signals: dict):
        pass

        # if self.signal[0] > cond1:
        #     order1
        # else:
        #     order2

    def __touch_direction(self, current_price, line):
        return check_cross(current_price, line, window=1)

    def __volatility(self):
        pass

    def __start_from(self):
        pass
