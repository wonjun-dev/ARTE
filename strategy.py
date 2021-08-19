from abc import ABC, abstractmethod
from collections import deque
from enum import Enum

import numpy as np

from signal_hub import SignalHub


class OrderState(Enum):
    EMPTY = 0  # only buy
    GROWING = 1  # buy and sell
    FULL = 2  # only sell


class Position(Enum):
    NO = 0
    LONG = 1
    SHORT = 2


class BaseStrategy(ABC):
    def __init__(
        self,
        indicators,
        account,
        order_manager,
        max_pos,
        buy_ratio,
        sell_ratio,
    ):
        super().__init__()
        self.signal_hub = SignalHub(indicators)
        self.account = account
        self.om = order_manager
        self.MAX_POS = max_pos
        self.BUY_RATIO = buy_ratio
        self.SELL_RATIO = sell_ratio
        self.num_pos = 0
        self.order_state = OrderState.EMPTY
        self.pos_state = Position.NO

    def run(self, price: deque):
        self._update_state()
        self.signal_hub.update(price)
        signal = self.signal_hub.get_signal(
            self.signal_hub.used_indicator[0]
        )  # TODO: get multiple indicator signals
        recent_signal = list(signal)[-1]

        print(
            f"Signal: {recent_signal}, Current Position: {self.pos_state.name}, Order State: {self.order_state.name}, # Postions: {self.num_pos}/{self.MAX_POS},"
        )
        if self.order_state.name == "EMPTY":
            self._empty_order_loop(recent_signal, price)
        elif self.order_state.name == "GROWING":
            self._growing_order_loop(recent_signal, price)
        else:
            self._full_order_loop(recent_signal, price)

    def _update_state(self):
        assert self.num_pos >= 0, "# of position cannot be negative."

        if self.num_pos == 0:
            self.order_state = OrderState.EMPTY
        else:
            if self.num_pos != self.MAX_POS:
                self.order_state = OrderState.GROWING
            else:
                self.order_state = OrderState.FULL

    @abstractmethod
    def _empty_order_loop(self, signal, price):
        pass

    @abstractmethod
    def _growing_order_loop(self, signal, price):
        pass

    @abstractmethod
    def _full_order_loop(self, signal, price):
        pass


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
        super().__init__(
            indicators, account, order_manager, max_pos, buy_ratio, sell_ratio
        )

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

    # def run(self, price: deque):
    #     """
    #     Run trade algorithms
    #     Args:
    #         price: (deque)
    #     """
