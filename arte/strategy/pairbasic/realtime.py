import traceback
from apscheduler.schedulers.blocking import BlockingScheduler
from pandas import Timestamp

from arte.data import SocketDataManager
from arte.data import RequestDataManager
from arte.data.common_symbol_collector import CommonSymbolCollector
from arte.system.binance.trade_manager import BinanceTradeManager
from arte.system.upbit.trade_manager import UpbitTradeManager
from arte.system.telegram_bot import SimonBot

from strategy_loop import StrategyLoop


class TradeScheduler:
    def __init__(self, client_binance, **kwargs):
        self.client_binance = client_binance
        self.scheduler = BlockingScheduler()
        self.socket_data_manager = SocketDataManager(self.client_binance)
        self.pair_symbols = ["ETC", "EOS"]

        # Init bot
        self.bot = None
        if "bot" in kwargs:
            self.bot = kwargs["bot"]
            self.bot.trader = self

        # Trade manager 
        self.tm_binance = BinanceTradeManager(client_binance, self.pair_symbols, max_order_count=1)
        self.strategy = StrategyLoop(trade_manager= self.tm_binance)
        

    def mainloop(self):
        try:
            _cur_time = Timestamp.now()

            #Update strategy
            self.strategy.update(
                future_prices=self.socket_data_manager.binance_future_trade,
                gamma=9.862,
                mu=8.373
            )
            self.strategy.run()

        except Exception:
            traceback.print_exc()

    def start(self, watch_interval: float = 3.0):
        self.socket_data_manager.open_binanace_future_trade_socket(symbols=self.pair_symbols)

        self.strategy.initialize(self.pair_symbols)

        self.scheduler.add_job(self.mainloop, "interval", seconds=watch_interval)
        if self.bot:
            self.bot.bot_manager_setting()
        self.scheduler.start()


if __name__ == "__main__":
    import configparser
    from arte.system.client import Client

    cfg = configparser.ConfigParser()
    cfg.read("/Users/wonjun/Desktop/arte/test/config.ini")
    config = cfg["REAL"]

    mode = config["MODE"]
    api_key = config["API_KEY"]
    secret_key = config["SECRET_KEY"]
    use_bot = config.getboolean("USE_BOT")

    telegram_bot = SimonBot()

    client_binance = Client(mode, api_key, secret_key)
    trader = TradeScheduler(client_binance, bot=telegram_bot)
    trader.start()
