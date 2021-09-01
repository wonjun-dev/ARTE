import talib
import numpy as np

from arte.indicator.core.base_indicator import BaseIndicator


class Bollinger(BaseIndicator):
    def __init__(self):
        self.data_name = ["close"]
        self.data_value = {name: None for name in self.data_name}

    def calc(self, data, timeperiod: int = 21, up: float = 1.9, dn: float = 1.9):
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
        super().calc(data)
        close = np.array(list(self.data_value["close"]))
        upper, middle, low = talib.BBANDS(close, timeperiod, up, dn)
        res = upper[-1], middle[-1], low[-1]
        return res
