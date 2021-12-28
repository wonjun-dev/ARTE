"""
BinanceAccount
"""
from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *

from arte.system.utils import purify_binance_symbol


class BinanceAccount:
    def __init__(self, request_client, symbols):
        self.request_client = request_client
        self._symbols = symbols
        self._positions = dict()
        self._update_restapi()

    def __repr__(self):
        return str(self._positions)

    def _get_usdt_balance_restapi(self):
        result = self.request_client.get_balance_v2()
        return result[1].balance

    def _get_positions_restapi(self, symbols: list):
        positions = {}
        results = self.request_client.get_position_v2()
        for pos in results:
            _psymbol = purify_binance_symbol(pos.symbol)
            if _psymbol in symbols:
                if _psymbol not in positions:
                    positions[_psymbol] = {PositionSide.LONG: 0, PositionSide.SHORT: 0}
                if pos.positionSide == PositionSide.LONG:
                    positions[_psymbol][pos.positionSide] = pos.positionAmt
                elif pos.positionSide == PositionSide.SHORT:
                    positions[_psymbol][pos.positionSide] = pos.positionAmt
        return positions

    def _update_restapi(self):
        self._positions["USDT"] = self._get_usdt_balance_restapi()
        self._positions = self._get_positions_restapi(self._symbols)

    def update(self, event):
        """
        User Data Stream based account update
        """
        self._positions["USDT"] = event.balances[0].crossWallet
        for pos in event.positions:
            _psymbol = purify_binance_symbol(pos.symbol)
            if pos.positionSide == PositionSide.LONG:
                self._positions[_psymbol][pos.positionSide] = pos.amount
            elif pos.positionSide == PositionSide.SHORT:
                self._positions[_psymbol][pos.positionSide] = pos.amount

    def __getitem__(self, key):
        return self._positions[key]

    def get_account_total_value(self):
        pass

    def change_leverage(self, n_leverage):
        pass


if __name__ == "__main__":
    KEY = None
    SECRET = None
    # BASE_URL = "https://fapi.binance.com"  # production base url
    BASE_URL = "https://testnet.binancefuture.com"  # testnet base url
    request_client = RequestClient(api_key=KEY, secret_key=SECRET, url=BASE_URL)
    acc = BinanceAccount(request_client, symbols=["ETH"])
    print(acc["ETH"][PositionSide.LONG].positionAmt)
    print(acc["ETH"][PositionSide.SHORT].positionAmt)
    print(acc["USDT"])
