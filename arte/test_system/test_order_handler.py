from decimal import Decimal, getcontext

getcontext().prec = 6

from functools import wraps

import numpy as np

from binance_f.model import Order
from binance_f.model.constant import *

from arte.test_system.test_account import TestAccount

MAKER_FEE_RATE = 0.0002
TAKER_FEE_RATE = 0.0004


def _print_status(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        order = method(self, *args, **kwargs)
        print(self.account)
        return order

    return _impl


class TestOrderHandler:
    def __init__(self, account):
        self.account = account
        self.short_tracker = dict()

    def _init_short_tracker(self):
        return {"avgPrice": Decimal(0), "quantity": Decimal(0)}

    def _select_fee_rate(self):
        return Decimal(TAKER_FEE_RATE)

    def _check_ratio_range(self, ratio):
        return True if 0 < ratio <= 1 else False

    @_print_status
    def open_long_market(self, symbol, price, ratio=None, usdt=None):
        fee_rate = self._select_fee_rate()
        price = Decimal(price)
        if ratio:
            if self._check_ratio_range(ratio):
                usdt_to_buy = Decimal(self.account["USDT"]) * Decimal(ratio)
            else:
                print("Warning: ratio should be in range (0,1]")
                return None
        elif usdt:
            usdt_to_buy = Decimal(usdt)
        fee = usdt_to_buy * fee_rate
        whole_cost = usdt_to_buy + fee
        quantity = usdt_to_buy / price
        if self.account["USDT"] > whole_cost:
            o = Order()
            o.symbol = symbol
            o.origQty = float(quantity)
            o.avgPrice = float(price)
            o.side = OrderSide.BUY
            o.positionSide = PositionSide.LONG
            o.type = OrderType.MARKET
            o.status = "FILLED"

            self.account.withdraw_usdt(whole_cost)
            self.account.deposit(symbol, PositionSide.LONG, quantity)
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
        if not (self.account[symbol][PositionSide.LONG] > 0):
            print("You cannot sell, no position to sell")
            return None
        quantity = Decimal(self.account[symbol][PositionSide.LONG]) * ratio
        usdt_by_sell = quantity * price
        fee = usdt_by_sell * fee_rate
        whole_earn = usdt_by_sell - fee
        o = Order()
        o.symbol = symbol
        o.origQty = float(quantity)
        o.avgPrice = float(price)
        o.side = OrderSide.SELL
        o.positionSide = PositionSide.LONG
        o.type = OrderType.MARKET
        o.status = "FILLED"

        self.account.deposit_usdt(whole_earn)
        self.account.withdraw(symbol, PositionSide.LONG, quantity)
        return o

    @_print_status
    def open_short_market(self, symbol, price, ratio=None, usdt=None):
        fee_rate = self._select_fee_rate()
        price = Decimal(price)
        if ratio:
            if self._check_ratio_range(ratio):
                usdt_to_buy = Decimal(self.account["USDT"]) * Decimal(ratio)
            else:
                print("ratio should be in range (0,1]")
                return None
        elif usdt:
            usdt_to_buy = Decimal(usdt)
        fee = usdt_to_buy * fee_rate
        whole_cost = usdt_to_buy + fee
        quantity = usdt_to_buy / price
        if self.account["USDT"] > whole_cost:
            o = Order()
            o.symbol = symbol
            o.origQty = float(quantity)
            o.avgPrice = float(price)
            o.side = OrderSide.SELL
            o.positionSide = PositionSide.SHORT
            o.type = OrderType.MARKET
            o.status = "FILLED"

            self.account.withdraw_usdt(whole_cost)
            self.account.deposit(symbol, PositionSide.SHORT, quantity)

            if symbol not in self.short_tracker.keys():
                self.short_tracker[symbol] = self._init_short_tracker()

            self.short_tracker[symbol]["avgPrice"] = (
                self.short_tracker[symbol]["avgPrice"] * self.short_tracker[symbol]["quantity"] + usdt_to_buy
            ) / (self.short_tracker[symbol]["quantity"] + quantity)
            self.short_tracker[symbol]["quantity"] += quantity
            return o
        else:
            return None

    @_print_status
    def close_short_market(self, symbol, price, ratio):
        fee_rate = self._select_fee_rate()
        if not self._check_ratio_range(ratio):
            print("Warning: ratio should be in range (0,1]")
            return None
        price = Decimal(price)
        ratio = Decimal(ratio)
        if not (self.account[symbol][PositionSide.SHORT] > 0):
            print("You cannot sell, no position to sell")
            return None
        quantity = self.account[symbol][PositionSide.SHORT] * ratio
        sell_price = self.short_tracker[symbol]["avgPrice"] * 2 - price
        usdt_by_sell = quantity * sell_price
        fee = usdt_by_sell * fee_rate
        whole_earn = usdt_by_sell - fee
        o = Order()
        o.symbol = symbol
        o.origQty = float(quantity)
        o.avgPrice = float(price)
        o.side = OrderSide.BUY
        o.positionSide = PositionSide.SHORT
        o.type = OrderType.MARKET
        o.status = "FILLED"

        self.account.deposit_usdt(whole_earn)
        self.account.withdraw(symbol, PositionSide.SHORT, quantity)

        # short_tracker 반영
        self.short_tracker[symbol]["quantity"] -= quantity
        return o


if __name__ == "__main__":
    acc = TestAccount(init_balance=1000)
    oh = TestOrderHandler(acc)
    oh.open_long_market(symbol="BTCUSDT", price=200, usdt=100)
    oh.close_long_market(symbol="BTCUSDT", price=300, ratio=1)
    oh.open_short_market(symbol="BTCUSDT", price=200, usdt=100)
    oh.close_short_market(symbol="BTCUSDT", price=100, ratio=1)
    # print(acc)
