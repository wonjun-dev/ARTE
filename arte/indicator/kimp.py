from arte.indicator.core.base_indicator import BaseIndicator


class Kimp(BaseIndicator):
    def __init__(self):
        self.data_name = ["kimchi_premium"]
        self.data_value = {name: None for name in self.data_name}

    def calc(self, upbit_ticker, binance_ticker, exchange_rate):
        kimp_dict = dict()
        for upbit_price, binance_price in zip(upbit_ticker.trade_price.items(), binance_ticker.trade_price.items()):
            if upbit_price[1] is not None and binance_price[1] is not None:
                kimp_dict[binance_price[0]] = (
                    (float(upbit_price[1]) / (float(binance_price[1]) * exchange_rate)) - 1
                ) * 100

        self.data_value[self.data_name[0]] = kimp_dict
        return kimp_dict
