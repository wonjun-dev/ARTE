from arte.indicator.core.base_indicator import BaseIndicator


class OHLC(BaseIndicator):
    def __init__(self):
        self.data_name = ["open", "high", "low", "close"]
        self.data_value = {name: None for name in self.data_name}

    def calc(self, data):
        super().calc(data)
        open = self.data_value["open"][-1]
        high = self.data_value["high"][-1]
        low = self.data_value["low"][-1]
        close = self.data_value["close"][-1]

        return open, high, low, close