from arte.indicator.core.base_indicator import BaseIndicator


class Kimp(BaseIndicator):
    def __init__(self):
        self.data_name = ["kimchi_premium"]
        self.data_value = {name: None for name in self.data_name}

    def calc(self, upbit_ticker, binance_ticker, exchange_rate):
        kimp_dict = dict()
        for a, b in zip(upbit_ticker.items(), binance_ticker.items()):
            kimp_dict[b[0]] = ((float(a[1]) / float(b[1]) * exchange_rate) - 1) * 100

        self.data_value[self.data_name[0]] = kimp_dict
        return kimp_dict
