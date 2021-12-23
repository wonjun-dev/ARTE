import traceback
from apscheduler.schedulers.blocking import BlockingScheduler
from pandas import Timestamp

from arte.data import SocketDataManager
from arte.data import RequestDataManager
from arte.system.upbit.trade_manager import UpbitTradeManager

from strategy_loop import StrategyLoop


class TradeScheduler:
    def __init__(self, client_b, client_u, **kwargs):
        self.client_b = client_b
        self.client_u = client_u
        self.scheduler = BlockingScheduler()
        self.socket_data_manager = SocketDataManager(self.client_b)
        self.request_data_manager = RequestDataManager(self.client_b)

        self.symbols = ["NEAR"]

        self.tm = UpbitTradeManager(self.client_u, self.symbols, max_order_count=3)
        self.strategy = StrategyLoop(self.symbols, self.tm)

    def mainloop(self):
        try:
            self.strategy.update(
                upbit_price=self.socket_data_manager.upbit_trade, current_time=Timestamp.now(),
            )
            self.strategy.run()

        except Exception:
            traceback.print_exc()

    def start(self, watch_interval: float = 3.0):
        self.socket_data_manager.open_upbit_trade_socket(symbols=self.symbols)

        self.scheduler.add_job(self.mainloop, "interval", seconds=watch_interval)
        self.scheduler.start()


if __name__ == "__main__":
    import configparser
    from arte.system.client import Client, UpbitClient

    cfg = configparser.ConfigParser()
    cfg.read("/media/park/hard2000/arte_config/config.ini")
    config = cfg["REAL_JAEHAN"]

    mode = config["MODE"]
    api_key = config["API_KEY"]
    secret_key = config["SECRET_KEY"]
    use_bot = config.getboolean("USE_BOT")

    api_key_upbit = config["UPBIT_ACCESS_KEY"]
    secret_key_upbit = config["UPBIT_SECRET_KEY"]

    client_binance = Client(mode, api_key, secret_key)
    client_upbit = UpbitClient(api_key_upbit, secret_key_upbit)
    trader = TradeScheduler(client_binance, client_upbit)
    trader.start()
