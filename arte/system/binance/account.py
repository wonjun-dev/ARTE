"""
BinanceAccount
"""
import time

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
        print(self)

    def __repr__(self):
        return f"BinanceAccount({str(self._positions)})"

    def _get_usdt_balance_restapi(self):
        result = self.request_client.get_balance_v2()
        return result[1].balance

    def _get_positions_restapi(self):
        positions = dict()
        for _psymbol in self._symbols:
            positions[_psymbol] = {
                PositionSide.LONG: 0,
                PositionSide.SHORT: 0,
                "positionSide": PositionSide.INVALID,
                "is_open": False,
            }
        results = self.request_client.get_position_v2()
        for pos in results:
            _psymbol = purify_binance_symbol(pos.symbol)
            if (_psymbol in self._symbols) and (pos.symbol[-4:] == "USDT"):
                if pos.positionAmt != 0:
                    positions[_psymbol][pos.positionSide] = pos.positionAmt
                    positions[_psymbol]["positionSide"] = pos.positionSide
                    positions[_psymbol]["is_open"] = True

                if positions[_psymbol][PositionSide.LONG] * positions[_psymbol][PositionSide.SHORT] != 0:
                    positions[_psymbol]["positionSide"] = PositionSide.BOTH

        return positions

    def _update_restapi(self):
        self._positions = self._get_positions_restapi()
        self._positions["USDT"] = self._get_usdt_balance_restapi()

    def update_deprecated(self, event):
        """
        User Data Stream based account update
        """
        self._positions["USDT"] = event.balances[0].crossWallet
        print(event.positions)
        for pos in event.positions:
            print(pos.positionSide)
            _psymbol = purify_binance_symbol(pos.symbol)
            if pos.positionSide in [PositionSide.LONG, PositionSide.SHORT]:
                self._positions[_psymbol][pos.positionSide] = pos.amount
                if pos.amount != 0:
                    self._positions[_psymbol]["positionSide"] = pos.positionSide
                    self._positions[_psymbol]["is_open"] = True

        if (self._positions[_psymbol][PositionSide.LONG] != 0) and (self._positions[_psymbol][PositionSide.SHORT] != 0):
            self._positions[_psymbol]["positionSide"] = PositionSide.BOTH
        elif (self._positions[_psymbol][PositionSide.LONG] == 0) and (
            self._positions[_psymbol][PositionSide.SHORT] == 0
        ):
            self._positions[_psymbol]["positionSide"] = PositionSide.INVALID
            self._positions[_psymbol]["is_open"] = False

    def update(self, event):
        """
        User Data Stream based account update
        !!! only works when event.positions arrive as [BOTH, LONG, SHORT] ordered sequence.
        !!! 0.004~6 sec slower than order return 
        """
        self._positions["USDT"] = event.balances[0].crossWallet
        long_pos = event.positions[1]
        short_pos = event.positions[2]
        _psymbol = purify_binance_symbol(long_pos.symbol)

        self._positions[_psymbol]["is_open"] = True
        if (long_pos.amount > 0) and (short_pos.amount == 0):
            self._positions[_psymbol]["positionSide"] = PositionSide.LONG
        elif (long_pos.amount == 0) and (short_pos.amount < 0):
            self._positions[_psymbol]["positionSide"] = PositionSide.SHORT
        elif (long_pos.amount != 0) and (short_pos.amount != 0):
            self._positions[_psymbol]["positionSide"] = PositionSide.BOTH
        elif (long_pos.amount == 0) and (short_pos.amount == 0):
            self._positions[_psymbol]["positionSide"] = PositionSide.INVALID
            self._positions[_psymbol]["is_open"] = False

        self._positions[_psymbol][PositionSide.LONG] = long_pos.amount
        self._positions[_psymbol][PositionSide.SHORT] = short_pos.amount

    def __getitem__(self, key):
        return self._positions[key]

    def get_account_total_value(self):
        pass

    def change_leverage(self, n_leverage):
        pass
