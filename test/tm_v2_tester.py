import threading
import time
import configparser
from arte.system.client import Client
from arte.system.binance.trade_manager_v2 import BinanceTradeManager

from arte.data.socket_data_manager import SocketDataManager


class Environment:
    def __init__(self, client, symbols):
        self.client = client
        self.symbols = symbols
        self.socket_data_manager = SocketDataManager(self.client)
        self.socket_data_manager.open_binanace_future_trade_socket(symbols=self.symbols)


cfg = configparser.ConfigParser()
cfg.read("/media/park/hard2000/arte_config/config.ini")
config = cfg["TEST"]
API_KEY = config["API_KEY"]
SECRET_KEY = config["SECRET_KEY"]

symbols = ["ETH", "BTC"]
cl = Client(mode="TEST", api_key=API_KEY, secret_key=SECRET_KEY, req_only=False)
tm = BinanceTradeManager(client=cl, symbols=symbols, max_order_count=3)
tm.environment = Environment(cl, symbols)

# tm test
# for i in range(4):
#     tm.sell_long_market("ETH", ratio=1)
#     time.sleep(2)
#     tm.buy_short_market("ETH", usdt=100)

# time to take order test
# for i in range(5):
#     st = time.time()
#     tm.buy_short_market("ETH", usdt=100)
#     print(time.time() - st)
#     time.sleep(2)

# order methods test
# tm.buy_long_market("ETH", usdt=100)
# time.sleep(0.2)
# tm.sell_long_market("ETH", ratio=1)

# time.sleep(1)

# tm.buy_short_market("ETH", usdt=100)
# time.sleep(0.2)
# tm.sell_short_market("ETH", ratio=0.5)

# order - account update time interval test
# order - symbol_state update time interval test
# order - account update interval result: ~ 0.2 sec
# order - symbol_state update interval result: ~ 0.16 sec
# print(time.time())
# tm.buy_long_market("ETH", usdt=100)

# symbols_state is_open test
# tm.buy_long_market("ETH", usdt=100)
# time.sleep(0.2)
# tm.sell_long_market("ETH", ratio=1)

# multi-asset trade test
tm.buy_long_market("ETH", usdt=100)
tm.buy_short_market("BTC", usdt=200)
time.sleep(0.2)
tm.sell_long_market("ETH", ratio=1)
tm.sell_short_market("BTC", ratio=1)

for t in threading.enumerate():
    if t is threading.current_thread():
        continue
    t.join()
