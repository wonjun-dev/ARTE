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
        self.usdt_balance = self.get_usdt_balance()
        self.positions = self.get_positions(["BTCUSDT"])

    def get_usdt_balance(self):
        result = self.request_client.get_balance_v2()
        return result[1].balance

    def get_positions(self, symbols: list):
        """
        this could lead high usage of weight
        - get positions of 129 assets at everytime function called

        Args:
            symbols: list of symbols

        Returns:
            positions: dictionary of positions
        """
        positions = {}
        result = self.request_client.get_position_v2()
        for pos in result:
            if pos.symbol in symbols:
                positions[pos.symbol] = pos
        return positions

    def update(self):
        self.usdt_balance = self.get_usdt_balance()
        self.positions = self.get_positions(["BTCUSDT"])

    def get_account_total_value(self):
        pass

    def change_leverage(self, n_leverage):
        pass


if __name__ == "__main__":
    KEY = "0dcd28f57648b0a7d5ea2737487e3b3093d47935e67506b78291042d1dd2f9ea"
    SECRET = "b36dc15c333bd5950addaf92a0f9dc96d8ed59ea6835386c59a6e63e1ae26aa1"
    # BASE_URL = "https://fapi.binance.com"  # production base url
    BASE_URL = "https://testnet.binancefuture.com"  # testnet base url
    request_client = RequestClient(api_key=KEY, secret_key=SECRET, url=BASE_URL)
    my_account = Account(request_client)
