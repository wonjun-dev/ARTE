import traceback
from apscheduler.schedulers.blocking import BlockingScheduler

from arte.data import SocketDataManager
from arte.data.user_data_manager import UserDataManager

from arte.system.account import Account
from arte.system import OrderHandler
from arte.system.order_recorder import OrderRecorder
from arte.system.strategy_manager import StrategyManager

from arte.indicator import IndicatorManager
from arte.indicator import Indicator
from arte.strategy import BollingerTouch


class BBTTTrader:
    def __init__(self, client, symbol, **kwargs):
        self.symbol = symbol
        self.client = client
        self.socket_data_manager = SocketDataManager(self.client)
        self.scheduler = BlockingScheduler()

        # init bot
        self.bot = None
        if "bot" in kwargs:
            self.bot = kwargs["bot"]
            self.bot.trader = self

        # Init Order Handler
        self.account = Account(client.request_client)
        self.oh = OrderHandler(client.request_client, self.account, symbol=self.symbol.upper())
        self.order_recorder = OrderRecorder()
        self.user_data_manager = UserDataManager(self.client, self.account, self.order_recorder)

        # Init strategy
        self.im = IndicatorManager(indicators=[Indicator.BOLLINGER])
        self.strategy = BollingerTouch(indicator_manager=self.im)
        self.strategy_manager = StrategyManager(self.oh, self.strategy, self.bot, max_order_count=3,)

    def mainloop(self):
        try:
            self.strategy_manager.run(candlestick=self.socket_data_manager.candlestick)
        except Exception:
            traceback.print_exc()

    def run(self, maxlen: int = 21, interval: str = "5m", watch_interval: float = 0.5):
        self.socket_data_manager.open_candlestick_socket(symbol=self.symbol.lower(), maxlen=maxlen, interval=interval)
        self.user_data_manager.open_user_data_socket()
        self.scheduler.add_job(self.mainloop, "interval", seconds=watch_interval, id="mainloop")
        if self.bot:
            self.scheduler.add_job(self.bot.bot_manager_setting)
        self.scheduler.start()
