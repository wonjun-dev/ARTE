import talib
import numpy as np

from arte.indicator.core.base_indicator import BaseIndicator


class ATR(BaseIndicator):
    def __init__(self):
        self.data_name = ["high", "low", "close"]
        self.data_value = {name: None for name in self.data_name}

    def calc(self, data, timeperiod: int = 19):
        """
        Calucate ATR
        Args:
            data : candlestick data
            timeperiod
        Return:
            res: Most recent atr
        """
        super().calc(data)
        try:
            high = np.array(list(self.data_value["high"]))
            low = np.array(list(self.data_value["low"]))
            close = np.array(list(self.data_value["close"]))
            real = talib.ATR(high, low, close, timeperiod)
            res = real[-1]
            return res
        except BaseException:
            print("Errorlog")
