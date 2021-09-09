from enum import Enum
from functools import wraps
from decimal import Decimal, getcontext

getcontext().prec = 2

import numpy as np

from binance_f.model.constant import *
from arte.system.order_handler import OrderHandler
from arte.system.realized_pnl import RealizedPnl


def _trunc(values, decs=3):
    return np.trunc(values * 10 ** decs) / (10 ** decs)


def _process_order(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        args = list(args)
        args[0] = args[0].upper()
        if args[0] not in self.symbols_state:
            self.symbols_state[args[0]] = self._init_state()
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
        self.max_order_count = max_order_count

        # state manage
        self.symbols_state = dict()

        # PNL manager
        self.pnl_manager = RealizedPnl("Bollinger")

    def _init_state(self):
        return dict(order_count=0, positionSize=0, positionSide=PositionSide.INVALID)

    def run(self, **kwargs):
        self.strategy.run(**kwargs)

    @_process_order
    def buy_long_market(self, symbol, price, usdt=None, ratio=None):
        if self.symbols_state[symbol]["order_count"] < self.max_order_count:
            return self.order_handler.buy_market(
                symbol=symbol,
                order_side=OrderSide.BUY,
                position_side=PositionSide.LONG,
                price=price,
                usdt=usdt,
                ratio=ratio,
            )

    @_process_order
    def buy_short_market(self, symbol, price, usdt=None, ratio=None):
        if self.symbols_state[symbol]["order_count"] < self.max_order_count:
            return self.order_handler.buy_market(
                symbol=symbol,
                order_side=OrderSide.SELL,
                position_side=PositionSide.SHORT,
                price=price,
                usdt=usdt,
                ratio=ratio,
            )

    @_process_order
    def buy_long_limit(self, symbol, price, usdt=None, ratio=None):
        if self.symbols_state[symbol]["order_count"] < self.max_order_count:
            return self.order_handler.buy_limit(
                symbol=symbol,
                order_side=OrderSide.BUY,
                position_side=PositionSide.LONG,
                price=price,
                usdt=usdt,
                ratio=ratio,
            )

    @_process_order
    def buy_short_limit(self, symbol, price, usdt=None, ratio=None):
        if self.symbols_state[symbol]["order_count"] < self.max_order_count:
            return self.order_handler.buy_limit(
                symbol=symbol,
                order_side=OrderSide.SELL,
                position_side=PositionSide.SHORT,
                price=price,
                usdt=usdt,
                ratio=ratio,
            )

    @_process_order
    def sell_long_market(self, symbol, ratio):
        return self.order_handler.sell_market(
            symbol=symbol, order_side=OrderSide.SELL, position_side=PositionSide.LONG, ratio=ratio
        )

    @_process_order
    def sell_short_market(self, symbol, ratio):
        return self.order_handler.sell_market(
            symbol=symbol, order_side=OrderSide.BUY, position_side=PositionSide.SHORT, ratio=ratio
        )

    @_process_order
    def sell_long_limit(self, symbol, price, ratio):
        return self.order_handler.sell_limit(
            symbol=symbol, order_side=OrderSide.SELL, position_side=PositionSide.LONG, price=price, ratio=ratio
        )

    @_process_order
    def sell_short_limit(self, symbol, price, ratio):
        return self.order_handler.sell_limit(
            symbol=symbol, order_side=OrderSide.BUY, position_side=PositionSide.SHORT, price=price, ratio=ratio
        )

    def _postprocess_order(self, order):
        symbol = order.symbol
        print(symbol)
        if self._is_buy_or_sell(order) == "BUY":
            self.symbols_state[symbol]["order_count"] += 1
            self.symbols_state[symbol]["positionSize"] = float(
                Decimal(self.symbols_state[symbol]["positionSize"] + order.origQty)
            )
            self.symbols_state[symbol]["positionSide"] = order.positionSide

        elif self._is_buy_or_sell(order) == "SELL":
            self.symbols_state[symbol]["positionSize"] = float(
                Decimal(self.symbols_state[symbol]["positionSize"] - order.origQty)
            )
            if self.symbols_state[symbol]["positionSize"] == 0:
                self.symbols_state[symbol] = self._init_state()

        # calculate PnL
        # self.pnl_manager.proceeding(order)

        # Process result message
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

    API_KEY = "0dcd28f57648b0a7d5ea2737487e3b3093d47935e67506b78291042d1dd2f9ea"
    SECRET_KEY = "b36dc15c333bd5950addaf92a0f9dc96d8ed59ea6835386c59a6e63e1ae26aa1"
    cl = Client(mode="TEST", api_key=API_KEY, secret_key=SECRET_KEY, req_only=True)
    account = Account(cl.request_client)
    order_handler = OrderHandler(cl.request_client, account)
    manager = StrategyManager(order_handler, strategy=None, bot=None, max_order_count=3)
    manager.buy_short_market("ethusdt", 3513, usdt=100)
    account._update_restapi()
    manager.sell_short_market("ethusdt", ratio=1)

