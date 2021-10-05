import traceback
from apscheduler.schedulers.blocking import BlockingScheduler

from arte.data import SocketDataManager
from arte.data import RequestDataManager
from arte.data.common_symbol_collector import CommonSymbolCollector

from arte.system.trade_manager import TradeManager
from arte.test_system.test_trade_manager import TestTradeManager

from arte.strategy import ArbitrageBasic
from arte.strategy.arbi_data_check import ArbitrageDataChecker


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

        self.tm = TestTradeManager(init_usdt=1000, max_order_count=3)
        self.strategy = ArbitrageDataChecker(trade_manager=self.tm)

        # Init required data
        self.except_list = self.request_data_manager.get_closed_symbols()
        self.exchange_rate = self.request_data_manager.get_usdt_to_kor()
        self.upbit_symbols, self.binance_symbols = self.symbol_collector.get_future_symbol()

    def mainloop(self):
        try:
            self.strategy.update(
                upbit_price=self.socket_data_manager.upbit_trade,
                binance_spot_price=self.socket_data_manager.binance_spot_trade,
                binance_future_price=self.socket_data_manager.binance_future_trade,
                exchange_rate=self.exchange_rate,
                except_list=self.except_list,
            )
            self.strategy.run()

        except Exception:
            traceback.print_exc()

    def start(self, watch_interval: float = 1.0):
        self.socket_data_manager.open_upbit_trade_socket(symbols=self.upbit_symbols)
        self.socket_data_manager.open_binanace_spot_trade_socket(symbols=self.binance_symbols)
        self.socket_data_manager.open_binanace_future_trade_socket(symbols=self.binance_symbols)

        self.strategy.initialize(self.binance_symbols, self.except_list)

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
