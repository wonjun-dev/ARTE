from abc import ABCMeta, abstractmethod
from collections import deque
from enum import Enum

from arte.strategy.impl.signal_hub import SignalHub


class OrderState(Enum):
    EMPTY = 0  # only buy
    GROWING = 1  # buy and sell
    FULL = 2  # only sell


class Position(Enum):
    NO = 0
    LONG = 1
    SHORT = 2


class BaseStrategy(metaclass=ABCMeta):
    def __init__(
        self, indicators, account, order_manager, max_pos, buy_ratio, sell_ratio,
    ):
        self.signal_hub = SignalHub(indicators)
        self.account = account
        self.om = order_manager
        self.MAX_POS = max_pos
        self.BUY_RATIO = buy_ratio
        self.SELL_RATIO = sell_ratio
        self.num_pos = 0
        self.order_state = OrderState.EMPTY
        self.pos_state = Position.NO
        self.current_price = None

    def run(self, price: deque):
        self._update_state()
        self._update_price(price[-1])
        self.signal_hub.update(price)
        signal = self.signal_hub.get_signal(self.signal_hub.used_indicator[0])  # TODO: get multiple indicator signals
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

    def _update_price(self, price):
        self.current_price = price

    @abstractmethod
    def _empty_order_loop(self, signal, price):
        pass

    @abstractmethod
    def _growing_order_loop(self, signal, price):
        pass

    @abstractmethod
    def _full_order_loop(self, signal, price):
        pass
