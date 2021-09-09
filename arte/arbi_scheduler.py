import traceback
from apscheduler.schedulers.blocking import BlockingScheduler
from collections import deque

import binance
from binance.streams import BinanceSocketManager

from arte.data import SocketDataManager
from arte.data import RequestDataManager
from arte.data.common_symbol_collector import CommonSymbolCollector
from arte.system.strategy_manager import StrategyManager
from arte.system.account import Account
from arte.system import OrderHandler
from arte.system.telegram_bot import DominicManager

from arte.indicator import IndicatorManager
from arte.indicator import Indicator
from arte.indicator.premium import Premium

from arte.strategy import ArbitrageBasic

import time


class ArbiTrader:
    def __init__(self, client, **kwargs):

        self.client = client
        self.scheduler = BlockingScheduler()

        self.socket_data_manager = SocketDataManager(self.client)
        self.request_data_manager = RequestDataManager(self.client)
        self.symbol_collector = CommonSymbolCollector()

        # Init bot
        self.bot = None
        if "bot" in kwargs:
            self.bot = kwargs["bot"]
            self.bot.trader = self

        # Init Order Handler
        self.account = Account(client.request_client)
        self.oh = OrderHandler(client.request_client, self.account, symbol="BTCUSDT")  # need to fix!

        # Init strategy
        self.im = IndicatorManager(indicators=[Indicator.PREMIUM])
        self.strategy = ArbitrageBasic(indicator_manager=self.im)
        self.strategy_manager = StrategyManager(self.oh, self.strategy, self.bot, max_order_count=3)

        # Init required data
        self.except_list = self.request_data_manager.get_closed_symbols()
        self.exchange_rate = self.request_data_manager.get_usdt_to_kor()
        self.upbit_symbols, self.binance_symbols = self.symbol_collector.get_future_symbol()

    def mainloop(self):
        try:
            self.strategy_manager.run(
                upbit_ticker=self.socket_data_manager.upbit_trade,
                binance_ticker=self.socket_data_manager.binance_spot_trade,
                exchange_rate=self.exchange_rate,
                except_list=self.except_list,
            )

        except Exception:
            traceback.print_exc()

    def run(self, watch_interval: float = 0.5):
        self.socket_data_manager.open_upbit_trade_socket(symbols=self.upbit_symbols)
        self.socket_data_manager.open_binanace_spot_trade_socket(symbols=self.binance_symbols)

        self.scheduler.add_job(self.mainloop, "interval", seconds=watch_interval)
        self.scheduler.add_job(self.get_exchange_rate, "cron", minute="0")
        self.scheduler.add_job(self.update_closed_list, "cron", minute="0", second="1")
        if self.bot:
            self.bot.bot_manager_setting()
        self.scheduler.start()

    def get_exchange_rate(self):
        self.exchange_rate = self.request_data_manager.get_usdt_to_kor()

    def update_closed_list(self):
        self.except_list = self.request_data_manager.get_closed_symbols()
