import numpy as np

from arte.strategy.impl.base_strategy import BaseStrategy
from arte.strategy.impl.base_strategy import Position


class BollingerTouch(BaseStrategy):
    def __init__(
        self,
        indicators: list,
        account,
        order_manager,
        max_pos: int = 3,
        buy_ratio: float = 0.1,
        sell_ratio: float = 1.0,
    ):
        super().__init__(indicators, account, order_manager, max_pos, buy_ratio, sell_ratio)

        # 전략 특화 초기화
        self.enter_cur_candle = False
        self.past_price = None

    def __check_candle_update(self, price):
        if self.past_price is None:
            self.past_price = np.array(list(price))[:5]
        else:
            cur_price = np.array(list(price)[:5])
            diff = self.past_price - cur_price

            if not np.all((diff == 0)):
                self.enter_cur_candle = False
                self.past_price = cur_price

    def _empty_order_loop(self, signal, price):
        self.__check_candle_update(price)
        if not self.enter_cur_candle:
            try:
                direction, volt, past = signal[0], signal[1], signal[2]
            except:
                print("Start trading! No enough data to generate signal.")
                return
            if direction.name == "UP":
                if volt + past == 3:
                    if self.om.buy_short_market(ratio=self.BUY_RATIO):
                        self.num_pos += 1
                        self.enter_cur_candle = True
                        self.pos_state = Position.SHORT
            elif direction.name == "DOWN":
                if past - volt == 0:
                    if self.om.buy_long_market(ratio=self.BUY_RATIO):
                        self.num_pos += 1
                        self.enter_cur_candle = True
                        self.pos_state = Position.LONG
            else:  # No
                pass
        else:  # 현재 분봉에서 이미 포지션을 산 경우
            pass

    def _growing_order_loop(self, signal, price):
        self.__check_candle_update(price)
        if not self.enter_cur_candle:
            direction, volt, past = signal[0], signal[1], signal[2]
            if direction.name == "UP":
                if volt + past == 3:
                    if self.pos_state.name == "LONG":
                        if self.om.sell_long_market(ratio=self.SELL_RATIO):
                            self.num_pos = 0
                            self.pos_state = Position.NO
                    elif self.pos_state.name == "SHORT":
                        if self.om.buy_short_market(ratio=self.BUY_RATIO):
                            self.num_pos += 1
                            self.enter_cur_candle = True
            elif direction.name == "DOWN":
                if past - volt == 0:
                    if self.pos_state.name == "SHORT":
                        if self.om.sell_short_market(ratio=self.SELL_RATIO):
                            self.num_pos = 0
                            self.pos_state = Position.NO
                    elif self.pos_state.name == "LONG":
                        if self.om.buy_long_market(ratio=self.BUY_RATIO):
                            self.num_pos += 1
                            self.enter_cur_candle = True
            else:
                pass
        else:
            pass

    def _full_order_loop(self, signal, price):
        self.__check_candle_update(price)
        if not self.enter_cur_candle:
            direction, volt, past = signal[0], signal[1], signal[2]
            if direction.name == "UP":
                if volt + past == 3:
                    if self.pos_state.name == "LONG":  # 익절
                        if self.om.sell_long_market(ratio=self.SELL_RATIO):
                            self.num_pos = 0
                            self.pos_state = Position.NO
                    elif self.pos_state.name == "SHORT":  # 손절
                        pass
                        # if self.om.sell_short_market(ratio=self.SELL_RATIO):
                        #     self.num_pos = 0
                        #     self.pos_state = Position.NO
            elif direction.name == "DOWN":
                if past - volt == 0:
                    if self.pos_state.name == "SHORT":  # 익절
                        if self.om.sell_short_market(ratio=self.SELL_RATIO):
                            self.num_pos = 0
                            self.pos_state = Position.NO
                    elif self.pos_state.name == "LONG":  # 손절
                        pass
                        # if self.om.sell_long_market(ratio=self.SELL_RATIO):
                        #     self.num_pos = 0
                        #     self.pos_state = Position.NO
            else:
                pass
        else:
            pass
