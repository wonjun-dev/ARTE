from abc import ABCMeta, abstractmethod
from enum import Enum


class TouchDirection(Enum):
    NO = 0
    UP = 1
    DOWN = 2


class BaseStrategy(metaclass=ABCMeta):
    def __init__(
        self,
        indicator_manager,
        buy_ratio: float = 0.1,
        sell_ratio: float = 1.0,
    ):
        self.im = indicator_manager
        self.data = None
        self.BUY_RATIO = buy_ratio
        self.SELL_RATIO = sell_ratio
        self.current_pirce = None
        self.manager = None

    def run(self, data):
        self.data = data
        self.current_price = data.close[-1]
        indicators = self.im.update(data)
        signals = self._make_signals(indicators)
        self._order(signals)

    @abstractmethod
    def _make_signals(self, indicators: dict):
        # indicators를 활용하여 signals를 만드는 함수들 호출
        pass

    @abstractmethod
    def _order(self, signals: dict):
        # signals를 활용하여 주문을 넣는 전략 구현.
        pass


def check_touch():
    pass