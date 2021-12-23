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

ZERO = Decimal("0")


class UpbitAccount:
    def __init__(self, request_client, symbols):
        self.request_client = request_client
        self.symbols = symbols
        self._positions = {symbol: ZERO for symbol in self.symbols + ["KRW"]}
        self.update()

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
        result_dict = self._get_current_positions_by_api()
        union_keys = self._positions.keys() | result_dict.keys()
        for key in union_keys:
            if key in result_dict:
                self._positions[key] = result_dict[key]
            else:
                self._positions[key] = ZERO
        print(self._positions)

    def _sleep_update(self):
        time.sleep(0.05)
        self.update()

    def update_by_thread(self):
        threading.Thread(target=self._sleep_update).start()


if __name__ == "__main__":
    import time
    import configparser
    from upbit.client import Upbit

    cfg = configparser.ConfigParser()
    cfg.read("/media/park/hard2000/arte_config/config.ini")
    config = cfg["REAL_JAEHAN"]

    request_client = Upbit(config["UPBIT_ACCESS_KEY"], config["UPBIT_SECRET_KEY"])
    acc = UpbitAccount(request_client, ["NEAR", "QTUM"])
    print(acc)
    print(acc.symbols)
    print("start threaded update")
    acc.update_by_thread()
    for _ in range(20):
        time.sleep(1)
        print(acc, threading.active_count())

