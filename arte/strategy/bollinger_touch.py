from collections import deque

import numpy as np

from arte.strategy.core.base_strategy import BaseStrategy
from arte.strategy.core.base_strategy import CrossDirection


class BollingerTouch(BaseStrategy):
    def __init__(
        self,
        indicator_manager,
        buy_ratio: float = 0.1,
        sell_ratio: float = 1.0,
    ):
        super().__init__(indicator_manager, buy_ratio, sell_ratio)

        # 전략 특화 초기화
        self.past_touch = None
        self.patience = 2
        self.price_idxs = deque(maxlen=2)
        self.signals = {"TouchDirection": None, "PastLoc": None, "CurLoc": None, "PastTouch": self.past_touch}
        self.enter_cur_candle = False
    
    def run(self, data):
        super().run(data)
        print(f"{self.signals}")

    def _make_signals(self, indicators: dict):
        pidx = self.__find_current_price_location(self.current_price, indicators["Bollinger"][-1])

        if self.data.candle_closed:
            self.price_idxs.append(pidx)
            self.enter_cur_candle = False

            if self.past_touch is not None:
                    self.patience -= 1
                    if self.patience == 0:
                        self.__reset_past_touch()
        else:
            try:
                self.price_idxs.pop()
            except:
                pass
            self.price_idxs.append(pidx)

        if len(self.price_idxs) > 1:
            past_idx = self.price_idxs[0]
            cur_idx = self.price_idxs[-1]

            if cur_idx == past_idx:
                direction = CrossDirection.NO
                self.signals['TouchDirection'] = direction.name
                self.signals['CurLoc'] = cur_idx
                self.signals['PastLoc'] = past_idx

            elif cur_idx > past_idx:
                # upward break
                direction = CrossDirection.UP
                if self.past_touch is None:
                    self.past_touch = self.current_price, direction

                self.signals['TouchDirection'] = direction.name
                self.signals['CurLoc'] = cur_idx
                self.signals['PastLoc'] = past_idx
                self.signals['PastTouch'] = self.past_touch
                
            elif cur_idx < past_idx:
                # downward break
                direction = CrossDirection.DOWN
                if self.past_touch is None:
                    self.past_touch = self.current_price, direction

                self.signals['TouchDirection'] = direction.name
                self.signals['CurLoc'] = cur_idx
                self.signals['PastLoc'] = past_idx
                self.signals['PastTouch'] = self.past_touch
            
        return self.signals
        


    def _order(self, signals: dict):
        if signals["PastTouch"] is not None:
            if signals["PastTouch"][-1].name == "UP" and signals["TouchDirection"].name == "DOWN" and signals["PastLoc"] == 3:
                self.manager.sell_long_market(ratio=self.SELL_RATIO)
                if not self.enter_cur_candle:
                    if self.manager.buy_short_market(ratio=self.BUY_RATIO):
                        self.enter_cur_candle = True
                self.__reset_past_touch()

            elif signals["PastTouch"][-1].name == "DOWN" and signals["TouchDirection"].name == "UP" and signals["PastLoc"] == 0:
                self.manager.sell_short_market(ratio=self.SELL_RATIO)
                if not self.enter_cur_candle:
                    if self.manager.buy_long_market(ratio=self.BUY_RATIO):
                        self.enter_cur_candle = True
                self.__reset_past_touch()
        
        if signals["PastLoc"] == 1 and signals["CurLoc"] == 2:
            self.manager.sell_long_market(ratio=self.SELL_RATIO * 0.5)
        
        if signals["PastLoc"] == 2 and signals["CurLoc"] == 1:
            self.manager.sell_short_market(ratio=self.SELL_RATIO * 0.5)

    



    def __find_current_price_location(self, current_price: float, bband: tuple):
        """
        Find location of current price in the bband.
        Args:
            current_price
        Return:
            where: (int) location of current price in the bband. 0: lower, 1: low~midddle, 2: middle~up, 3: upper
        """
        tmp = list(bband)
        tmp.append(current_price)
        tmp.sort()
        where = tmp.index(current_price)
        
        return where


    def __reset_past_touch(self):
        self.past_touch = None
