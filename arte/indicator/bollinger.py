"""
Calucate Bollinger band
Args:
    closes : 21 # of close value
    timeperiod
    up
    down
Return:
    data: (tuple) Most recent bollinger band
"""

import talib
import numpy as np


class Bollinger:
    @staticmethod
    def calc(closes, timeperiod: int = 21, up: float = 1.9, down: float = 1.9):
        upper, middle, low = talib.BBANDS(np.array(closes), timeperiod, up, down)
        return (upper[-1], middle[-1], low[-1])
