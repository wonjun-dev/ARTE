import traceback
from apscheduler.schedulers.blocking import BlockingScheduler
from collections import deque

from arte.data.data_manager import DataManager
from arte.data.get_common_symbols import GetCommonSymbol
from arte.system.strategy_manager import StrategyManager
from arte.system.account import Account
from arte.system import OrderHandler
from arte.system.telegram_bot import DominicManager

# from arte.indicator.core.indicator_manager import IndicatorManager
from arte.indicator.kimp import Kimp

import time


class ArbiTrader:
    def __init__(self, client):

        self.client = client
        self.data_manager = DataManager(self.client)
        self.symbol_manager = GetCommonSymbol()
        self.scheduler = BlockingScheduler()

        self.threshold = 2.5
        self.update_closed_list()
        self.higher_coins = []

        # init bot manager
        self.bot_manager = DominicManager()
        self.bot_manager.trader = self

        # Init Order Handler
        # self.account = Account(client.request_client)
        # self.oh = OrderHandler(client.request_client, self.account, symbol=self.symbol.upper())

        # Init strategy
        self.indicator = Kimp()

        self.set_exchange_rate()
        # self.im = IndicatorManager(indicator_instance=INDICATORS)
        # self.strategy = BollingerTouch(indicator_manager=self.im)
        # self.strategy_manager = StrategyManager(
        #    self.oh, self.strategy, self.bot_manager, max_order_count=3, verbose_bot=False
        # )

    def mainloop(self):
        """주기적으로 실행되는 함수"""
        try:

            kimp_dict = self.indicator.calc(
                self.data_manager.upbit_ticker, self.data_manager.binance_ticker, self.exchange_rate
            )
            self.update_higher_coins(kimp_dict)

        except Exception:
            traceback.print_exc()

    def update_higher_coins(self, kimp_dict):
        for keys in kimp_dict:
            if kimp_dict[keys] > self.threshold:
                if keys[:-4] not in self.except_list:
                    if keys not in self.higher_coins:
                        self.higher_coins.append(keys)
                        message1 = "[***" + keys[:-4] + "***] :\n 현재 김프 " + str(kimp_dict[keys]) + "%\n"
                        message2 = (
                            "현재 Upbit 가격 :" + str(self.data_manager.upbit_ticker.trade_price["KRW-" + keys[:-4]]) + "\n"
                        )
                        message3 = (
                            "현재 Binance 가격 :"
                            + str(self.data_manager.binance_ticker.trade_price[keys] * self.exchange_rate)
                            + "\n"
                            + "현재 환율 : "
                            + str(self.exchange_rate)
                        )
                        self.bot_manager.sendMessage(message1 + message2 + message3)
                        print(self.higher_coins)
            else:
                if keys in self.higher_coins:
                    self.higher_coins.remove(keys)
                    print(self.higher_coins)

    def run(self, watch_interval: float = 0.2):
        """
        mainloop를 watch_interval마다 실행시켜주는 함수
        """
        self.upbit_symbols, self.binance_symbols = self.symbol_manager.get_future_symbol()

        self.data_manager.open_upbit_ticker_socket(symbols=self.upbit_symbols)
        self.data_manager.open_binance_ticker_socket(symbols=self.binance_symbols)

        self.runner = self.scheduler.add_job(self.mainloop, "interval", seconds=watch_interval)
        self.updating_exchange = self.scheduler.add_job(self.set_exchange_rate, "cron", minute="0")
        self.updating_closed_list = self.scheduler.add_job(self.update_closed_list, "cron", minute="0", second="1")
        self.bot_manager.bot_manager_setting()
        self.scheduler.start()
        # self.data_manager.open_candlestick_socket(symbol=self.symbol.lower(), maxlen=maxlen, interval=interval)
        # self.scheduler.start()

    def set_exchange_rate(self):
        self.exchange_rate = self.data_manager.get_usdt_to_kor()

    def update_closed_list(self):
        self.except_list = self.data_manager.get_closed_symbols()
