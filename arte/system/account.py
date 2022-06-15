"""
Account

핵심기능
1. 현재 usdt 잔액
2. 현재 보유 포지션 및 정보(롱, 숏, 보유 시작 시간, amount)

부가기능
1. 현재가 입력시 내 총자산 크기(구매가격 필요)
"""
from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *


class Account:
    def __init__(self, request_client):
        self.request_client = request_client
        self._positions = self._get_positions(["ETHUSDT"])
        self._positions["USDT"] = self._get_usdt_balance()

    def _get_usdt_balance(self):
        result = self.request_client.get_balance_v2()
        return result[1].balance

    def _get_positions(self, symbols: list):
        positions = {}
        results = self.request_client.get_position_v2()
        for pos in results:
            if pos.symbol in symbols:
                if pos.symbol not in positions:
                    positions[pos.symbol] = dict()
                if pos.positionSide == PositionSide.LONG:
                    positions[pos.symbol][pos.positionSide] = pos
                elif pos.positionSide == PositionSide.SHORT:
                    positions[pos.symbol][pos.positionSide] = pos
        return positions

    def update(self):
        self._positions["USDT"] = self._get_usdt_balance()
        self._positions = self._get_positions(["ETHUSDT"])

    def __getitem__(self, key):
        return self._positions[key]

    def get_account_total_value(self):
        pass

    def change_leverage(self, n_leverage):
        pass


if __name__ == "__main__":
    KEY = ""
    SECRET = ""
    # BASE_URL = "https://fapi.binance.com"  # production base url
    BASE_URL = "https://testnet.binancefuture.com"  # testnet base url
    request_client = RequestClient(api_key=KEY, secret_key=SECRET, url=BASE_URL)
    acc = Account(request_client)
    print(acc["ETHUSDT"][PositionSide.LONG].positionAmt)
    print(acc["ETHUSDT"][PositionSide.SHORT].positionAmt)
    print(acc["USDT"])
