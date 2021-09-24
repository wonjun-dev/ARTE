from functools import wraps
from decimal import Decimal, getcontext

getcontext().prec = 4  # x.xxx (count as 4)

from binance_f.model.constant import *
from arte.system.account import Account
from arte.system.order_handler import OrderHandler
from arte.system.order_recorder import OrderRecorder
from arte.data.user_data_manager import UserDataManager


def _process_order(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        args = list(args)
        args[0] = args[0].upper()
        if args[0] not in self.symbols_state:
            self.symbols_state[args[0]] = self._init_symbol_state()
        order = method(self, *args, **kwargs)
        if order:
            self._postprocess_order(order)
        return order

    return _impl


class TradeManager:
    def __init__(self, client, *args, **kwargs):
        self.account = Account(client.request_client)
        self.order_handler = OrderHandler(client.request_client, self.account)
        self.order_handler.manager = self
        self.order_recorder = OrderRecorder()
        self.user_data_manager = UserDataManager(client, self.account, self.order_recorder)

        self.bot = None
        if "bot" in kwargs:
            self.bot = kwargs["bot"]
        if "max_order_count" in kwargs:
            self.max_order_count = kwargs["max_order_count"]

        # state manage
        self.symbols_state = dict()

        # start user data stream
        self.user_data_manager.open_user_data_socket()

    def _init_symbol_state(self):
        return dict(order_count=0, positionSize=0, positionSide=PositionSide.INVALID)

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
                self.symbols_state[symbol] = self._init_symbol_state()

        # Process result message
        message = f"Order {order.clientOrderId}: {order.side} {order.positionSide} {order.type} - {order.symbol} / Qty: {order.origQty}, Price: ${order.avgPrice}"
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
    import threading
    import time
    from arte.client import Client

    API_KEY = "0dcd28f57648b0a7d5ea2737487e3b3093d47935e67506b78291042d1dd2f9ea"
    SECRET_KEY = "b36dc15c333bd5950addaf92a0f9dc96d8ed59ea6835386c59a6e63e1ae26aa1"
    cl = Client(mode="TEST", api_key=API_KEY, secret_key=SECRET_KEY, req_only=False)
    tm = TradeManager(client=cl, max_order_count=3)
    tm.buy_short_market("ethusdt", 2783, usdt=100)
    time.sleep(0.05)
    tm.sell_short_market("ethusdt", ratio=1)

    for t in threading.enumerate():
        if t is threading.current_thread():
            continue
        t.join()
