import configparser
import threading
import time

from arte import Client
from arte.data import SocketDataManager
from arte.data.common_symbol_collector import CommonSymbolCollector

cfg = configparser.ConfigParser()
cfg.read("test/config.ini")
config = cfg["REAL"]

mode = config["MODE"]
api_key = config["API_KEY"]
secret_key = config["SECRET_KEY"]
use_bot = config.getboolean("USE_BOT")

cl = Client(mode, api_key, secret_key)
sdm = SocketDataManager(cl)
# symbol_collector = CommonSymbolCollector()
# symbols = symbol_collector.get_future_symbol()
# print(symbols)
sdm.open_upbit_orderbook_socket(["ETH"])
# time.sleep(2)
# sdm.unsubscribe_all()


# mp = cl.request_client.get_all_mark_price()
# print(mp)


for t in threading.enumerate():
    if t is threading.current_thread():
        continue
    t.join()
