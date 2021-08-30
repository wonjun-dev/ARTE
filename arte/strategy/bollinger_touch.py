import numpy as np

from arte.strategy.core.base_strategy import BaseStrategy
from arte.strategy.core.base_strategy import check_touch


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
        self.past_price = None
        self.signals = {"TouchDirection": None, "Volatility": None, "StartFrom": None}


    def _make_signals(self, indicators: dict):


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

    # 전략 특화 함수들
    def __check_candle_update(self, price_deque):
        if self.past_price is None:
            self.past_price = np.array(list(price_deque))[:5]
        else:
            cur_price = np.array(list(price_deque)[:5])
            diff = self.past_price - cur_price

            if not np.all((diff == 0)):
                self.enter_cur_candle = False
                self.past_price = cur_price
    
    def __touch_direction(self, current_price, band_line):
        pass

    def __volatility(self, ):
        pass

    def __start_from(self):
        pass

