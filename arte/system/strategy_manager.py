from enum import Enum
from functools import wraps
from decimal import Decimal, getcontext

getcontext().prec = 2

import numpy as np

from binance_f.model.constant import *
from arte.system.order_handler import OrderHandler
from arte.system.realized_pnl import RealizedPnl


def trunc(values, decs=3):
    return np.trunc(values * 10 ** decs) / (10 ** decs)


def _postprocess(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        order = method(self, *args, **kwargs)
        if order:
            self._postprocess_order(order)
        return order

    return _impl


class StrategyManager:
    """
    OrderHandler - StrategyManager - Strategy
    """

    def __init__(self, order_handler, strategy, bot, max_order_count):
        self.order_handler = order_handler
        self.account = self.order_handler.account
        self.strategy = strategy
        self.order_handler.manager = self
        self.strategy.manager = self
        self.bot = bot

        # state manage
        self.max_order_count = max_order_count
        self.order_count = 0
        self.positionSize = 0
        self.positionSide = PositionSide.INVALID

        # PNL manager
        self.pnl_manager = RealizedPnl("Bollinger")

    def run(self, data):
        self.strategy.run(data)

    def initialize_position_info(self):
        self.order_count = 0
        self.positionSide = PositionSide.INVALID

    @_postprocess
    def buy_long_market(self, usdt=None, ratio=None):
        if self.order_count < self.max_order_count:
            return self.order_handler.buy_market(
                order_side=OrderSide.BUY,
                position_side=PositionSide.LONG,
                price=self.strategy.current_price,
                usdt=usdt,
                ratio=ratio,
            )

    @_postprocess
    def buy_short_market(self, usdt=None, ratio=None):
        if self.order_count < self.max_order_count:
            return self.order_handler.buy_market(
                order_side=OrderSide.SELL,
                position_side=PositionSide.SHORT,
                price=self.strategy.current_price,
                usdt=usdt,
                ratio=ratio,
            )

    @_postprocess
    def buy_long_limit(self, price, usdt=None, ratio=None):
        if self.order_count < self.max_order_count:
            return self.order_handler.buy_limit(
                order_side=OrderSide.BUY, position_side=PositionSide.LONG, price=price, usdt=usdt, ratio=ratio
            )

    @_postprocess
    def buy_short_limit(self, price, usdt=None, ratio=None):
        if self.order_count < self.max_order_count:
            return self.order_handler.buy_limit(
                order_side=OrderSide.SELL, position_side=PositionSide.SHORT, price=price, usdt=usdt, ratio=ratio
            )

    @_postprocess
    def sell_long_market(self, ratio):
        return self.order_handler.sell_market(order_side=OrderSide.SELL, position_side=PositionSide.LONG, ratio=ratio)

    @_postprocess
    def sell_short_market(self, ratio):
        return self.order_handler.sell_market(order_side=OrderSide.BUY, position_side=PositionSide.SHORT, ratio=ratio)

    @_postprocess
    def sell_long_limit(self, price, ratio):
        return self.order_handler.sell_limit(
            order_side=OrderSide.SELL, position_side=PositionSide.LONG, price=price, ratio=ratio
        )

    @_postprocess
    def sell_short_limit(self, price, ratio):
        return self.order_handler.sell_limit(
            order_side=OrderSide.BUY, position_side=PositionSide.SHORT, price=price, ratio=ratio
        )

    def _postprocess_order(self, order):
        if self._is_buy_or_sell(order) == "BUY":
            self.order_count += 1
            self.positionSize = float(Decimal(self.positionSize + order.origQty))
            self.positionSide = order.positionSide

        elif self._is_buy_or_sell(order) == "SELL":
            self.positionSize = float(Decimal(self.positionSize - order.origQty))
            if self.positionSize == 0:
                self.initialize_position_info()
        self.pnl_manager.proceeding(order)

        message = f"Order {order.clientOrderId}: {order.side} {order.positionSide} {order.type} - {order.symbol} / Qty: {order.origQty}, Price: ${order.avgPrice}, \n Realized_PNL : ${self.pnl_manager.realized_pnl}"
        print(message)
        if self.bot:
            self.bot.sendMessage(message)

    @staticmethod
    def _is_buy_or_sell(order):
        if ((order.side == OrderSide.BUY) & (order.positionSide == PositionSide.LONG)) or (
            (order.side == OrderSide.SELL) & (order.positionSide == PositionSide.SHORT)
        ):
            return "BUY"
        elif ((order.side == OrderSide.SELL) & (order.positionSide == PositionSide.LONG)) or (
            (order.side == OrderSide.BUY) & (order.positionSide == PositionSide.SHORT)
        ):
            return "SELL"
        else:
            raise ValueError("Cannot check order is buy or sell")


if __name__ == "__main__":
    from arte.client import Client
    from arte.system import OrderHandler
    from arte.system import Account
    from arte.system.telegram_bot import SimonManager

    cl = Client(mode="TEST", req_only=True)
    account = Account(cl.request_client)
    order_handler = OrderHandler(cl.request_client, account, "ETHUSDT")
    strategy = None
    manager = StrategyManager(order_handler, strategy, SimonManager(), max_order_count=3, verbose_bot=False)
    manager.buy_short_market(usdt=100)
    print(manager.positionSide, manager.positionSize)
    manager.sell_short_market(ratio=0.5)
    print(manager.positionSide, manager.positionSize)
    manager.sell_short_market(ratio=1)
    print(manager.positionSide, manager.positionSize)
    manager.sell_short_market(ratio=1)
