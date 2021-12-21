import configparser
import threading
import time

from arte.system.client import Client
from arte.data.user_data_manager import UserDataManager
from arte.system.binance.account import BinanceAccount
from arte.system.binance.order_recorder import BinanceOrderRecorder

cfg = configparser.ConfigParser()
cfg.read("/media/park/hard2000/arte_config/config.ini")
config = cfg["REAL"]

mode = config["MODE"]
api_key = config["API_KEY"]
secret_key = config["SECRET_KEY"]
use_bot = config.getboolean("USE_BOT")

cl = Client(mode, api_key, secret_key)
acc = BinanceAccount(cl.request_client)
orc = BinanceOrderRecorder()

udm = UserDataManager(cl, acc, orc)
udm.open_user_data_socket()

st = time.time()
# time.sleep(2)
# sdm.unsubscribe_all()


# mp = cl.request_client.get_all_mark_price()
# print(mp)
def loop_time_check(st):
    while True:
        time.sleep(30)
        print(time.time() - st)


time_thread = threading.Thread(target=loop_time_check, args=(st,))
time_thread.start()

for t in threading.enumerate():
    if t is threading.current_thread():
        continue
    t.join()
