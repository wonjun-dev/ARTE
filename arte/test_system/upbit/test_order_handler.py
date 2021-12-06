"""
Upbit
"""

import sys
from decimal import Decimal, getcontext

getcontext().prec = 6

from functools import wraps

import numpy as np

from binance_f.model import Order
from binance_f.model.constant import *

MAKER_FEE_RATE = 0.0005
TAKER_FEE_RATE = 0.0005


def _print_status(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        order = method(self, *args, **kwargs)
        # print(self.account)
        return order

    return _impl


class OrderHandler:
    def __init__(self, account):
        self.account = account

    def _select_fee_rate(self):
        return Decimal(TAKER_FEE_RATE)

    def _check_ratio_range(self, ratio):
        return True if 0 < ratio <= 1 else False

    @_print_status
    def open_long_market(self, symbol, price, ratio=None, krw=None):
        fee_rate = self._select_fee_rate()
        price = Decimal(price)
        if ratio:
            if self._check_ratio_range(ratio):
                krw_to_buy = Decimal(self.account["KRW"]) * Decimal(ratio)
            else:
                print("Warning: ratio should be in range (0,1]")
                return None
        elif krw:
            krw_to_buy = Decimal(krw)
        fee = krw_to_buy * fee_rate
        whole_cost = krw_to_buy + fee
        quantity = krw_to_buy / price
        if self.account["KRW"] > whole_cost:
            o = Order()
            o.symbol = symbol
            o.origQty = float(quantity)
            o.avgPrice = float(price)
            o.side = OrderSide.BUY
            o.positionSide = PositionSide.LONG
            o.type = OrderType.MARKET
            o.status = "FILLED"
            o.fee = float(fee)

            self.account.withdraw("KRW", whole_cost)
            self.account.deposit(symbol, quantity)
            return o
        else:
            return None

    @_print_status
    def close_long_market(self, symbol, price, ratio):
        fee_rate = self._select_fee_rate()
        if not self._check_ratio_range(ratio):
            print("Warning: ratio should be in range (0,1]")
            return None
        price = Decimal(price)
        ratio = Decimal(ratio)
        if not self.account.has_asset(symbol, sys.float_info.epsilon):
            print(f"{symbol} has never been traded or no position to sell, you cannot sell.")
            return None
        quantity = Decimal(self.account[symbol]) * ratio
        krw_by_sell = quantity * price
        fee = krw_by_sell * fee_rate
        whole_earn = krw_by_sell - fee
        o = Order()
        o.symbol = symbol
        o.origQty = float(quantity)
        o.avgPrice = float(price)
        o.side = OrderSide.SELL
        o.positionSide = PositionSide.LONG
        o.type = OrderType.MARKET
        o.status = "FILLED"
        o.fee = float(fee)

        self.account.deposit("KRW", whole_earn)
        self.account.withdraw(symbol, quantity)
        return o


if __name__ == "__main__":
    from test_account import Account

    acc = Account(init_balance=100000)
    oh = OrderHandler(acc)
    oh.open_long_market(symbol="KRW-BTC", price=50000000, krw=50000)
    oh.close_long_market(symbol="KRW-BTC", price=51000000, ratio=1)
