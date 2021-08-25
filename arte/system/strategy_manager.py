from arte.system.order_handler import OrderHandler
from enum import Enum
from functools import wraps

from binance_f.model.constant import *


def _postprocess_buy(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        order = method(self, *args, **kwargs)
        if order:
            self.order_count += 1
            self.positionSide = order.positionSide
        return order

    return _impl


def _postprocess_sell(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        order = method(self, *args, **kwargs)
        if order:
            self.initialize_position_info()
        return order

    return _impl


class StrategyManager:
    """
    OrderHandler - StrategyManager - Strategy
    """

    def __init__(self, order_handler, strategy, max_order_count):
        self.order_handler = order_handler
        self.strategy = strategy
        self.order_handler.manager = self
        # self.strategy.manager = self

        # state manage
        self.max_order_count = max_order_count
        self.order_count = 0
        self.positionSide = PositionSide.INVALID

    def initialize_position_info(self):
        self.order_count = 0
        self.positionSide = PositionSide.INVALID

    @_postprocess_buy
    def buy_long_market(self, usdt=None, ratio=None):
        if self.order_count < self.max_order_count:
            return self.order_handler.buy_market(
                position_side=PositionSide.LONG, price=self.order_handler._get_ticker_price(), usdt=usdt, ratio=ratio
            )

    @_postprocess_buy
    def buy_short_market(self, usdt=None, ratio=None):
        if self.order_count < self.max_order_count:
            return self.order_handler.buy_market(
                position_side=PositionSide.SHORT, price=self.order_handler._get_ticker_price(), usdt=usdt, ratio=ratio
            )

    @_postprocess_buy
    def buy_long_limit(self, price, usdt=None, ratio=None):
        if self.order_count < self.max_order_count:
            return self.order_handler.buy_limit(position_side=PositionSide.LONG, price=price, usdt=usdt, ratio=ratio)

    @_postprocess_buy
    def buy_short_limit(self, price, usdt=None, ratio=None):
        if self.order_count < self.max_order_count:
            return self.order_handler.buy_limit(position_side=PositionSide.SHORT, price=price, usdt=usdt, ratio=ratio)

    @_postprocess_sell
    def sell_long_market(self, ratio):
        return self.order_handler.sell_market(position_side=PositionSide.LONG, ratio=ratio)

    @_postprocess_sell
    def sell_short_market(self, ratio):
        return self.order_handler.sell_market(position_side=PositionSide.SHORT, ratio=ratio)

    @_postprocess_sell
    def sell_long_limit(self, price, ratio):
        return self.order_handler.sell_limit(position_side=PositionSide.LONG, price=price, ratio=ratio)

    @_postprocess_sell
    def sell_short_limit(self, price, ratio):
        return self.order_handler.sell_limit(position_side=PositionSide.SHORT, price=price, ratio=ratio)


if __name__ == "__main__":
    from arte.client import Client
    from arte.system import OrderHandler
    from arte.system import Account
    from arte.system.telegram_bot import SimonManager

    cl = Client(mode="TEST", req_only=True)
    account = Account(cl.request_client)
    bot = SimonManager()
    eth_oh = OrderHandler(cl.request_client, account, bot, "ETHUSDT")
    sm = StrategyManager(eth_oh, None, 3)
    sm.buy_long_market(usdt=50)
    # sm.buy_short_market(usdt=50)
    sm.sell_long_market(ratio=0.5)
