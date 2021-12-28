import time
import threading
import configparser
from arte.system.client import UpbitClient, Client
from arte.system.upbit.trade_manager import UpbitTradeManager
from arte.data.socket_data_manager import SocketDataManager


cfg = configparser.ConfigParser()
cfg.read("/media/park/hard2000/arte_config/config.ini")
config = cfg["REAL_JAEHAN"]
API_KEY = config["API_KEY"]
SECRET_KEY = config["SECRET_KEY"]
UPBIT_API_KEY = config["UPBIT_ACCESS_KEY"]
UPBIT_SECRET_KEY = config["UPBIT_SECRET_KEY"]

symbols = ["ETH", "BTC"]
cl = Client(mode="REAL", api_key=API_KEY, secret_key=SECRET_KEY, req_only=False)
upbit_cl = UpbitClient(api_key=UPBIT_API_KEY, secret_key=UPBIT_SECRET_KEY)
tm = UpbitTradeManager(client=upbit_cl, symbols=symbols, max_order_count=3)

socket_data_manager = SocketDataManager(cl)
socket_data_manager.open_binanace_future_trade_socket(symbols=symbols)


# normal trade test / pass
# tm.buy_long_market("ETH", krw=5200)
# time.sleep(0.5)
# tm.sell_long_market("ETH", ratio=1)

# multi-asset trade test / pass
# tm.buy_long_market("ETH", krw=5200)
# tm.buy_long_market("BTC", krw=5200)
# time.sleep(0.5)
# tm.sell_long_market("ETH", ratio=1)
# tm.sell_long_market("BTC", ratio=1)

# error - buy over krw test / pass
# tm.buy_long_market("ETH", krw=40000)

# error - sell over ratio test / pass
# tm.buy_long_market("ETH", krw=5200)
# time.sleep(0.5)
# tm.sell_long_market("ETH", ratio=1)


for t in threading.enumerate():
    if t is threading.current_thread():
        continue
    t.join()
