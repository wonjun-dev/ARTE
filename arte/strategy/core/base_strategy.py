from abc import ABCMeta, abstractmethod
from enum import Enum


class CrossDirection(Enum):
    NO = 0
    UP = 1
    DOWN = 2


class BaseStrategy(metaclass=ABCMeta):
    """
    BaseStrategy - IndicatorManager - Indicator
    """

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
        self.current_price = None
        self.manager = None

    def run(self, data):
        self.data = data
        self.current_price = data.close[-1]
        indicators = self.im.update(data)
        signals = self._make_signals(indicators)
        self._order(signals)

    @abstractmethod
    def _make_signals(self, indicators: dict):
        """
        indicators를 활용하여 signals를 만드는 함수들 호출
        Args:
            indicators: (dict of deques) indicator deque 가 담긴 dictionary.
        """
        pass

    @abstractmethod
    def _order(self, signals: dict):
        # signals를 활용하여 주문을 넣는 전략 구현.
        pass


def check_cross(values_1, values_2, window: int = 2):
    """
    value_1이 value_2를 window 길이 동안 위 혹은 아래로 뚫었는지 확인
    Args:
        value_1, value_2: (deque or list)
        window: (int)
    Return:
        pass
    """
    res = CrossDirection.NO

    try:
        values_1 = list(values_1)[-(window + 1) :]
        values_2 = list(values_2)[-(window + 1) :]

        start_value_1, start_value_2 = values_1[0], values_2[0]
        check_values_1, check_values_2 = values_1[1:], values_2[1:]

        if start_value_1 > start_value_2:
            # 아래로 뚫었는지 확인
            if max(check_values_1) < min(check_values_2):
                res = CrossDirection.DOWN
                return res

        elif start_value_1 < start_value_2:
            # 위로 뚫었는지 확인
            if min(check_values_1) > max(check_values_2):
                res = CrossDirection.UP
                return res

    except:
        print(f"Not enough data.")
