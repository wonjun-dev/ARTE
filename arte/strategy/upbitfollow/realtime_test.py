import traceback
from apscheduler.schedulers.blocking import BlockingScheduler
from pandas import Timestamp

from arte.data import SocketDataManager
from arte.data import RequestDataManager
from arte.data.common_symbol_collector import CommonSymbolCollector
from arte.test_system import RTTUpbitTradeManager

from strategy_loop import StrategyLoop


class TradeScheduler:
    def __init__(self, client, **kwargs):
        self.client = client
        self.scheduler = BlockingScheduler()
        self.socket_data_manager = SocketDataManager(self.client)
        self.request_data_manager = RequestDataManager(self.client)
        # self.symbol_collector = CommonSymbolCollector()

        # Init bot
        self.bot = None
        if "bot" in kwargs:
            self.bot = kwargs["bot"]
            self.bot.trader = self

        self.backtest_id = None
        if "backtest_id" in kwargs:
            self.backtest_id = kwargs["backtest_id"]

        selected_assets = "BTC ETH BCH AAVE SOL LTC AXS ETC NEO DOT ATOM LINK QTUM OMG KAVA MANA EOS 1INCH ADA"
        self.common_symbols = selected_assets.split(" ")

        self.tm = RTTUpbitTradeManager(init_krw=400000, max_order_count=3, backtest_id=self.backtest_id)
        self.strategy = StrategyLoop(trade_manager=self.tm)

        # Init required data
        self.except_list = []  # self.request_data_manager.get_closed_symbols()
        self.exchange_rate = self.request_data_manager.get_usdt_to_kor()
        # self.common_symbols = self.symbol_collector.get_future_symbol()

    def mainloop(self):
        try:
            _cur_time = Timestamp.now()
            self.tm.update(
                test_current_time=_cur_time, orderbook=self.socket_data_manager.upbit_orderbook,
            )
            self.strategy.update(
                upbit_price=self.socket_data_manager.upbit_trade,
                binance_spot_price=self.socket_data_manager.binance_spot_trade,
                exchange_rate=self.exchange_rate,
                except_list=self.except_list,
                current_time=_cur_time,
            )
            self.strategy.print_state()
            self.strategy.run()

        except Exception:
            traceback.print_exc()

    def start(self, watch_interval: float = 1.0):
        self.socket_data_manager.open_upbit_orderbook_socket(symbols=self.common_symbols)
        self.socket_data_manager.open_upbit_trade_socket(symbols=self.common_symbols)
        self.socket_data_manager.open_binanace_spot_trade_socket(symbols=self.common_symbols)

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
    from arte.system.client import Client

    cfg = configparser.ConfigParser()
    cfg.read("test/config.ini")
    config = cfg["REAL"]

    mode = config["MODE"]
    api_key = config["API_KEY"]
    secret_key = config["SECRET_KEY"]
    use_bot = config.getboolean("USE_BOT")

    clients = Client(mode, api_key, secret_key)
    trader = TradeScheduler(clients, backtest_id="upbitfollow_20211128_rbt03")
    trader.start()