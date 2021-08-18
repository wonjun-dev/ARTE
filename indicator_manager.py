from collections import deque
from enum import Enum

import talib


class TouchDirection(Enum):
    NO = 0
    UP = 1
    DOWN = 2


class Bollinger:
    def __init__(self):
        pass

    def calc(self, close, timeperiod: int = 21, up: float = 2, dn: float = 2):
        """
        Calucate Bollinger band
        Args:
            close
            timeperiod
            up
            dn
        Return:
            data: (tuple) Most recent bollinger band
        """
        upper, middle, low = talib.BBANDS(close, timeperiod, up, dn)
        data = upper[-1], middle[-1], low[-1]
        return data

    def check_touch(self, value_queue: deque, price_queue: deque, window: int = 2):
        """
        Checking touch state of current price with bollinger band
        Args:
            value_queue : bollinger band value (up, middle, down)
            price_queue : current price
            window : size of window
        Return:
            touch_state : (tuple) vector of (state of touch, size of breakthrough, start position)
        """
        if len(value_queue) < window or len(price_queue) < window:
            return

        else:
            boll_values = list(value_queue)[-window:]
            prices = list(price_queue)[-window:]
            loc_idxs = list()

            for pair in list(zip(boll_values, prices)):
                boll_value, price = pair[0], pair[1]
                tmp = list(boll_value)
                tmp.append(price)
                tmp.sort()
                idx = tmp.index(price)
                loc_idxs.append(idx)

            past, current = loc_idxs[0], loc_idxs[-1]

            if current == past:
                # No touch
                touch_state = TouchDirection.NO, None, None
                return touch_state
            elif current > past:
                # upward breakthrough
                volt = current - past
                touch_state = TouchDirection.UP, volt, past
                return touch_state
            elif current < past:
                # downward breakthrough
                volt = past - current
                touch_state = TouchDirection.DOWN, volt, past
                return touch_state
