import os
import datetime
import logging

from arte.indicator import IndicatorManager
from arte.indicator import Indicator


class ArbitrageDataChecker:
    """
    Upbit-Binance Pair Arbitrage 기초 전략
    """

    def __init__(self, trade_manager):
        self.im = IndicatorManager(indicators=[Indicator.PREMIUM])
        logging.basicConfig(filename=os.path.join("..", "btc_log.log"))
        self.mylogger = logging.getLogger("DataChecker")
        self.mylogger.setLevel(logging.INFO)

    def initialize(self, common_binance_symbols, except_list):
        pass

    def update(self, **kwargs):
        self.upbit_price = kwargs["upbit_price"]
        self.binance_spot_price = kwargs["binance_spot_price"]
        self.binance_future_price = kwargs["binance_future_price"]
        self.exchange_rate = kwargs["exchange_rate"]
        self.except_list = kwargs["except_list"]
        self.im.update_premium(self.upbit_price, self.binance_spot_price, self.exchange_rate)

    def run(self):
        dt = datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S")
        msg = f"[{dt}] Upbit: {int(self.upbit_price.price['KRW-BTC'])}, Binance: {self.binance_spot_price.price['BTCUSDT']}"
        print(msg)
        self.mylogger.info(msg)
