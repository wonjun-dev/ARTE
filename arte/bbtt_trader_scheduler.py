import traceback
from apscheduler.schedulers.blocking import BlockingScheduler

from arte.data import SocketDataManager
from arte.system.trade_manager import TradeManager

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

        self.tm = TradeManager(self.client)

        # Init strategy
        self.im = IndicatorManager(indicators=[Indicator.BOLLINGER])
        self.strategy = BollingerTouch(indicator_manager=self.im)

    def mainloop(self):
        try:
            self.strategy.run(candlestick=self.socket_data_manager.candlestick)
        except Exception:
            traceback.print_exc()

    def run(self, maxlen: int = 21, interval: str = "5m", watch_interval: float = 0.5):
        self.socket_data_manager.open_candlestick_socket(symbol=self.symbol.lower(), maxlen=maxlen, interval=interval)
        self.scheduler.add_job(self.mainloop, "interval", seconds=watch_interval, id="mainloop")
        if self.bot:
            self.scheduler.add_job(self.bot.bot_manager_setting)
        self.scheduler.start()
