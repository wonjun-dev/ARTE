import sys
import traceback
import threading
from functools import wraps
from decimal import Decimal, getcontext

getcontext().prec = 4  # x.xxx (count as 4)

from binance_f.model.constant import *
from .account import BinanceAccount
from .order_handler import BinanceOrderHandler
from arte.system.binance.order_recorder import BinanceOrderRecorder
from arte.data.user_data_manager import UserDataManager
from arte.system.utils import purify_binance_symbol


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


def _process_order(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        try:
            order = method(self, *args, **kwargs)
        except:
            traceback.print_exc()
        else:
            self._postprocess_order(order)

    return _impl


class BinanceTradeManager:
    def __init__(self, client, symbols, max_order_count, bot=None):
        self.symbols = symbols
        self.max_order_count = max_order_count
        self.account = BinanceAccount(client.request_client, self.symbols)
        self.order_handler = BinanceOrderHandler(client.request_client, self.account)
        self.order_handler.manager = self
        self.order_recorder = BinanceOrderRecorder()
        self.user_data_manager = UserDataManager(client, self.account, self.order_recorder)

        # TradeScheduler have to be assigned
        self.environment = None

        # bot
        self.bot = bot if bot else None

        # state(per symbol) init
        self.symbols_state = dict()
        for _psymbol in self.symbols:
            self.symbols_state[_psymbol] = self._init_symbol_state()

        # start user data stream
        self.user_data_manager.open_user_data_socket()

    def _init_symbol_state(self):
        return dict(order_count=0, positionSize=0, positionSide=PositionSide.INVALID, is_open=False)

    @threaded
    @_process_order
    def buy_long_market(self, symbol, usdt=None, ratio=None):
        if self.symbols_state[symbol]["order_count"] < self.max_order_count:
            return self.order_handler.buy_market(
                symbol=symbol,
                order_side=OrderSide.BUY,
                position_side=PositionSide.LONG,
                price=self.environment.socket_data_manager.binance_future_trade.price[symbol],
                usdt=usdt,
                ratio=ratio,
            )
        else:
            raise ValueError("Exceeded condition: order_count or position_side")

    @threaded
    @_process_order
    def buy_short_market(self, symbol, usdt=None, ratio=None):
        if self.symbols_state[symbol]["order_count"] < self.max_order_count:
            return self.order_handler.buy_market(
                symbol=symbol,
                order_side=OrderSide.SELL,
                position_side=PositionSide.SHORT,
                price=self.environment.socket_data_manager.binance_future_trade.price[symbol],
                usdt=usdt,
                ratio=ratio,
            )
        else:
            raise ValueError("Exceeded condition: order_count or position_side")

    @threaded
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
        else:
            raise ValueError("Exceeded condition: order_count or position_side")

    @threaded
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
        else:
            raise ValueError("Exceeded condition: order_count or position_side")

    @threaded
    @_process_order
    def sell_long_market(self, symbol, ratio):
        return self.order_handler.sell_market(
            symbol=symbol, order_side=OrderSide.SELL, position_side=PositionSide.LONG, ratio=ratio
        )

    @threaded
    @_process_order
    def sell_short_market(self, symbol, ratio):
        return self.order_handler.sell_market(
            symbol=symbol, order_side=OrderSide.BUY, position_side=PositionSide.SHORT, ratio=ratio
        )

    @threaded
    @_process_order
    def sell_long_limit(self, symbol, price, ratio):
        return self.order_handler.sell_limit(
            symbol=symbol, order_side=OrderSide.SELL, position_side=PositionSide.LONG, price=price, ratio=ratio
        )

    @threaded
    @_process_order
    def sell_short_limit(self, symbol, price, ratio):
        return self.order_handler.sell_limit(
            symbol=symbol, order_side=OrderSide.BUY, position_side=PositionSide.SHORT, price=price, ratio=ratio
        )

    def _postprocess_order(self, order):
        symbol = purify_binance_symbol(order.symbol)
        _orderside = self._is_buy_or_sell(order)
        if _orderside == "BUY":
            self.symbols_state[symbol]["order_count"] += 1
            self.symbols_state[symbol]["positionSize"] = float(
                Decimal(self.symbols_state[symbol]["positionSize"] + order.origQty)
            )
            self.symbols_state[symbol]["positionSide"] = order.positionSide
            self.symbols_state[symbol]["is_open"] = True

        elif _orderside == "SELL":
            self.symbols_state[symbol]["positionSize"] = float(
                Decimal(self.symbols_state[symbol]["positionSize"] - order.origQty)
            )
            if self.symbols_state[symbol]["positionSize"] <= sys.float_info.epsilon:
                self.symbols_state[symbol] = self._init_symbol_state()

        # Process result message
        message = f"Order {order.clientOrderId}: {_orderside} {order.positionSide} {order.type} - {order.symbol} / Qty: {order.origQty}, Price: ${order.avgPrice}"
        print(message)
        print(self.symbols_state)
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
    import configparser
    from arte.system.client import Client

    cfg = configparser.ConfigParser()
    cfg.read("/media/park/hard2000/arte_config/config.ini")
    config = cfg["TEST"]
    # access_key = config["UPBIT_ACCESS_KEY"]
    # secret_key = config["UPBIT_SECRET_KEY"]

    API_KEY = config["API_KEY"]
    SECRET_KEY = config["SECRET_KEY"]
    cl = Client(mode="TEST", api_key=API_KEY, secret_key=SECRET_KEY, req_only=False)
    tm = BinanceTradeManager(client=cl, max_order_count=3)
    tm.buy_short_market("ETH", 2783, usdt=100)
    time.sleep(0.05)
    tm.sell_short_market("ETH", ratio=1)

    for t in threading.enumerate():
        if t is threading.current_thread():
            continue
        t.join()
