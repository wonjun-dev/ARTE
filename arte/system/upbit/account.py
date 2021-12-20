"""
Account

핵심기능
1. 현재 KRW 잔액
2. 현재 보유 포지션 및 정보(holding start time, amount, etc)

부가기능
1. 현재가 입력시 내 총자산 크기(구매가격 필요)
"""
import time
import threading
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor

from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *


class UpbitAccount:
    def __init__(self, request_client):
        self.request_client = request_client
        self._positions = self._get_current_positions_by_api()

    def __getitem__(self, key):
        return self._positions[key]

    def __repr__(self):
        return str(self._positions)

    def _json_parse(self, response):
        result_dict = {}
        for position in response:
            result_dict[position["currency"]] = Decimal(position["balance"])
        return result_dict

    def _get_current_positions_by_api(self):
        response = self.request_client.Account.Account_info()
        return self._json_parse(response["result"])

    def update(self):
        self._positions = self._get_current_positions_by_api()
        print(self._positions)

    def _sleep_update(self):
        time.sleep(0.05)
        self.update()
        # time.sleep(3)
        # self._positions['KRW'] += 10000

    def update_by_thread(self):
        threading.Thread(target=self._sleep_update).start()

    def symbols(self):
        return self._positions.keys()


if __name__ == "__main__":
    import time
    import configparser
    from upbit.client import Upbit

    cfg = configparser.ConfigParser()
    cfg.read("/media/park/hard2000/arte_config/config.ini")
    config = cfg["REAL_JAEHAN"]

    request_client = Upbit(config["UPBIT_ACCESS_KEY"], config["UPBIT_SECRET_KEY"])
    acc = UpbitAccount(request_client)
    print(acc["EOS"])
    print(acc)
    print("start threaded update")
    acc.update_by_thread()
    for _ in range(50):
        time.sleep(0.1)
        print(acc, threading.active_count())

