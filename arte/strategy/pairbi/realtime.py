import traceback
from apscheduler.schedulers.blocking import BlockingScheduler
from pandas import Timestamp

from arte.data import SocketDataManager
from arte.data import RequestDataManager
from arte.data.common_symbol_collector import CommonSymbolCollector
from arte.system.binance.trade_manager import BinanceTradeManager
from arte.system.upbit.trade_manager import UpbitTradeManager

from strategy_loop import StrategyLoop


class TradeScheduler:
    def __init__(self, client_binance, client_upbit, **kwargs):
        self.client_binance = client_binance
        self.client_upbit = client_upbit
        self.scheduler = BlockingScheduler()
        self.socket_data_manager = SocketDataManager(self.client_binance)
        self.request_data_manager = RequestDataManager(self.client_binance)
        # self.symbol_collector = CommonSymbolCollector()

        # selected_assets = "BTC ETH BCH AAVE SOL LTC AXS ETC NEO DOT ATOM LINK QTUM OMG KAVA MANA EOS 1INCH ADA"
        self.common_symbols = ["QTUM"]
        # Init bot
        self.bot = None
        if "bot" in kwargs:
            self.bot = kwargs["bot"]
            self.bot.trader = self

        # Trade manager 
        self.tm_upbit = UpbitTradeManager(client_upbit, self.common_symbols, max_order_count=3)
        self.tm_binance = BinanceTradeManager(client_binance, self.common_symbols, max_order_count=3)
        self.strategy = StrategyLoop(trade_manager_upbit=self.tm_upbit, trade_manager_binance= self.tm_binance)

        # Init required data
        self.except_list = []  # self.request_data_manager.get_closed_symbols()
        self.exchange_rate = self.request_data_manager.get_usdt_to_kor()
        # self.common_symbols = self.symbol_collector.get_future_symbol()

    def mainloop(self):
        try:
            _cur_time = Timestamp.now()

            # Update strategy
            self.strategy.update(
                upbit_price=self.socket_data_manager.upbit_trade,
                binance_spot_price=self.socket_data_manager.binance_future_trade,
                exchange_rate=self.exchange_rate,
                except_list=self.except_list,
                current_time=_cur_time,
            )

            self.strategy.print_state()
            self.strategy.run()

        except Exception:
            traceback.print_exc()

    def start(self, watch_interval: float = 3.0):
        self.socket_data_manager.open_upbit_trade_socket(symbols=self.common_symbols)
        self.socket_data_manager.open_binanace_future_trade_socket(symbols=self.common_symbols)

        self.strategy.initialize(self.common_symbols, self.except_list)

        self.scheduler.add_job(self.mainloop, "interval", seconds=watch_interval)
        self.scheduler.add_job(self.get_exchange_rate, "cron", minute="0")
        # self.scheduler.add_job(self.update_closed_list, "cron", minute="0", second="1")
        if self.bot:
            self.bot.bot_manager_setting()
        self.scheduler.start()

    def get_exchange_rate(self):
        self.exchange_rate = self.request_data_manager.get_usdt_to_kor()

    def update_closed_list(self):
        self.except_list = self.request_data_manager.get_closed_symbols()


if __name__ == "__main__":
    import configparser
    from arte.system.client import Client, UpbitClient

    cfg = configparser.ConfigParser()
    cfg.read("/Users/gyuyoung/Documents/arte/arte/strategy/pairbi/config.ini")
    config = cfg["REAL"]

    mode = config["MODE"]
    api_key = config["API_KEY"]
    secret_key = config["SECRET_KEY"]
    use_bot = config.getboolean("USE_BOT")

    api_key_upbit = config["API_KEY_UPBIT"]
    secret_key_upbit = config["SECRET_KEY_UPBIT"]

    client_binance = Client(mode, api_key, secret_key)
    client_upbit = UpbitClient(api_key_upbit, secret_key_upbit)
    trader = TradeScheduler(client_binance, client_upbit)
    trader.start()
