from arte.system.order_handler import OrderHandler
from enum import Enum
from functools import wraps

from binance_f.model.constant import *


def _postprocess(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        order = method(self, *args, **kwargs)
        self._postprocess_order(order)

    return _impl


class StrategyManager:
    """
    OrderHandler - StrategyManager - Strategy
    """

    def __init__(self, order_handler, strategy, bot, max_order_count, verbose_bot=True):
        self.order_handler = order_handler
        self.account = self.order_handler.account
        self.strategy = strategy
        self.order_handler.manager = self
        # self.strategy.manager = self
        self.bot = bot
        self.verbose_bot = verbose_bot

        # state manage
        self.max_order_count = max_order_count
        self.order_count = 0
        self.positionSize = 0
        self.positionSide = PositionSide.INVALID

    def initialize_position_info(self):
        self.order_count = 0
        self.positionSide = PositionSide.INVALID

    @_postprocess
    def buy_long_market(self, usdt=None, ratio=None):
        if self.order_count < self.max_order_count:
            return self.order_handler.buy_market(
                position_side=PositionSide.LONG, price=self.order_handler._get_ticker_price(), usdt=usdt, ratio=ratio
            )

    @_postprocess
    def buy_short_market(self, usdt=None, ratio=None):
        if self.order_count < self.max_order_count:
            return self.order_handler.buy_market(
                position_side=PositionSide.SHORT, price=self.order_handler._get_ticker_price(), usdt=usdt, ratio=ratio
            )

    @_postprocess
    def buy_long_limit(self, price, usdt=None, ratio=None):
        if self.order_count < self.max_order_count:
            return self.order_handler.buy_limit(position_side=PositionSide.LONG, price=price, usdt=usdt, ratio=ratio)

    @_postprocess
    def buy_short_limit(self, price, usdt=None, ratio=None):
        if self.order_count < self.max_order_count:
            return self.order_handler.buy_limit(position_side=PositionSide.SHORT, price=price, usdt=usdt, ratio=ratio)

    @_postprocess
    def sell_long_market(self, ratio):
        return self.order_handler.sell_market(position_side=PositionSide.LONG, ratio=ratio)

    @_postprocess
    def sell_short_market(self, ratio):
        return self.order_handler.sell_market(position_side=PositionSide.SHORT, ratio=ratio)

    @_postprocess
    def sell_long_limit(self, price, ratio):
        return self.order_handler.sell_limit(position_side=PositionSide.LONG, price=price, ratio=ratio)

    @_postprocess
    def sell_short_limit(self, price, ratio):
        return self.order_handler.sell_limit(position_side=PositionSide.SHORT, price=price, ratio=ratio)

    def _postprocess_order(self, order):
        if order:
            if order.side == OrderSide.BUY:
                self.order_count += 1
                self.positionSize += order.origQty
                self.positionSide = order.positionSide

            elif order.side == OrderSide.SELL:
                self.positionSize -= order.origQty
                if self.positionSize == 0:
                    self.initialize_position_info()

            message = f"Order {order.clientOrderId}: {order.side} {order.positionSide} {order.type} - {order.symbol} / Qty: {order.origQty}, Price: ${order.avgPrice}"
            print(message)
            if self.verbose_bot:
                self.bot.sendMessage(message)


if __name__ == "__main__":
    from arte.client import Client
    from arte.system import OrderHandler
    from arte.system import Account
    from arte.system.telegram_bot import SimonManager

    cl = Client(mode="TEST", req_only=True)
    account = Account(cl.request_client)
    order_handler = OrderHandler(cl.request_client, account, "ETHUSDT")
    strategy = None
    manager = StrategyManager(order_handler, strategy, SimonManager(), 3)
    manager.buy_long_market(usdt=50)
    manager.sell_long_market(ratio=0.5)
    manager.sell_long_market(ratio=1)
    manager.sell_long_market(ratio=1)
