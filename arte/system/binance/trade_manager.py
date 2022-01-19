import sys
import time
import traceback
from functools import wraps

from binance_f.model.constant import *
from .account import BinanceAccount
from .order_handler import BinanceOrderHandler
from arte.system.binance.order_recorder import BinanceOrderRecorder
from arte.data.user_data_manager import UserDataManager
from arte.system.utils import purify_binance_symbol, threaded, print_important


def _process_order(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        try:
            order = method(self, *args, **kwargs)
        except:
            traceback.print_exc()
            return False
        else:
            self._postprocess_order(order)
            return True

    return _impl


def _check_buy_condition(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        if self._check_trade_condition(args[0]):
            order = method(self, *args, **kwargs)
            return order
        else:
            raise ValueError("Exceeded condition: buy_order_count or budget")

    return _impl


class BinanceTradeManager:
    def __init__(self, client, symbols, max_buy_order_count: float, budget_per_symbol: dict, bot=None):
        self.symbols = symbols
        self.max_buy_order_count = max_buy_order_count
        self.budget_per_symbol = budget_per_symbol
        if not isinstance(self.budget_per_symbol, dict):
            raise ValueError("Argument error: 'budget_per_symbol' should be dictionary")
        self.bot = bot if bot else None

        self.account = BinanceAccount(client.request_client, self.symbols)
        self.order_handler = BinanceOrderHandler(client.request_client, self.account)
        self.order_recorder = BinanceOrderRecorder()
        self.user_data_manager = UserDataManager(client, self.account, self.order_recorder)

        # TradeScheduler have to be assigned
        self.environment = None

        # state(per symbol) init
        self._initialize_symbol_state()
        self._position_diff_tracker = {key: 0 for key in self.symbols}

        # start user data stream
        self.user_data_manager.open_user_data_socket()

        print_important("Binance Trade Manager Initialized, Trading start!", line_length=100)

    # @threaded
    @_process_order
    @_check_buy_condition
    def buy_long_market(self, symbol, usdt=None, ratio=None):
        return self.order_handler.buy_market(
            symbol=symbol,
            order_side=OrderSide.BUY,
            position_side=PositionSide.LONG,
            price=self.environment.socket_data_manager.binance_future_trade.price[symbol],
            usdt=usdt,
            ratio=ratio,
        )

    # @threaded
    @_process_order
    @_check_buy_condition
    def buy_short_market(self, symbol, usdt=None, ratio=None):
        return self.order_handler.buy_market(
            symbol=symbol,
            order_side=OrderSide.SELL,
            position_side=PositionSide.SHORT,
            price=self.environment.socket_data_manager.binance_future_trade.price[symbol],
            usdt=usdt,
            ratio=ratio,
        )

    # @threaded
    @_process_order
    @_check_buy_condition
    def buy_long_limit(self, symbol, price, usdt=None, ratio=None):
        return self.order_handler.buy_limit(
            symbol=symbol,
            order_side=OrderSide.BUY,
            position_side=PositionSide.LONG,
            price=price,
            usdt=usdt,
            ratio=ratio,
        )

    # @threaded
    @_process_order
    @_check_buy_condition
    def buy_short_limit(self, symbol, price, usdt=None, ratio=None):
        return self.order_handler.buy_limit(
            symbol=symbol,
            order_side=OrderSide.SELL,
            position_side=PositionSide.SHORT,
            price=price,
            usdt=usdt,
            ratio=ratio,
        )

    # @threaded
    @_process_order
    def sell_long_market(self, symbol, ratio):
        return self.order_handler.sell_market(
            symbol=symbol, order_side=OrderSide.SELL, position_side=PositionSide.LONG, ratio=ratio
        )

    # @threaded
    @_process_order
    def sell_short_market(self, symbol, ratio):
        return self.order_handler.sell_market(
            symbol=symbol, order_side=OrderSide.BUY, position_side=PositionSide.SHORT, ratio=ratio
        )

    # @threaded
    @_process_order
    def sell_long_limit(self, symbol, price, ratio):
        return self.order_handler.sell_limit(
            symbol=symbol, order_side=OrderSide.SELL, position_side=PositionSide.LONG, price=price, ratio=ratio
        )

    # @threaded
    @_process_order
    def sell_short_limit(self, symbol, price, ratio):
        return self.order_handler.sell_limit(
            symbol=symbol, order_side=OrderSide.BUY, position_side=PositionSide.SHORT, price=price, ratio=ratio
        )

    def _check_trade_condition(self, symbol):
        return (self.symbols_state[symbol]["buy_order_count"] < self.max_buy_order_count) and (
            self.symbols_state[symbol]["left_budget"] > 0  # left_budget is not perfect. last order could over budget.
        )

    def _initialize_symbol_state(self):
        self.symbols_state = dict()
        for _psymbol in self.symbols:
            self.symbols_state[_psymbol] = dict(buy_order_count=0, left_budget=self.budget_per_symbol[_psymbol])

    def _postprocess_order(self, order):
        symbol = purify_binance_symbol(order.symbol)
        _orderside = self._is_buy_or_sell(order)
        if _orderside == "BUY":
            self.symbols_state[symbol]["buy_order_count"] += 1
            self.symbols_state[symbol]["left_budget"] -= order.origQty * order.avgPrice
            self._position_diff_tracker[symbol] += order.origQty
        elif _orderside == "SELL":
            self.symbols_state[symbol]["left_budget"] += order.origQty * order.avgPrice
            self._position_diff_tracker[symbol] -= order.origQty
            if abs(self._position_diff_tracker[symbol]) <= sys.float_info.epsilon:
                self.symbols_state[symbol] = dict(buy_order_count=0, left_budget=self.budget_per_symbol[symbol])

        # Process result message
        message = f"Order {order.clientOrderId}: {_orderside} {order.positionSide} {order.type} - {order.symbol} / Qty: {order.origQty}, Price: ${order.avgPrice}"
        print(message)
        print(self.symbols_state)
        if self.bot:
            self.bot.sendMessage(message)

    @staticmethod
    def _is_buy_or_sell(order):
        if ((order.side == OrderSide.BUY) and (order.positionSide == PositionSide.LONG)) or (
            (order.side == OrderSide.SELL) and (order.positionSide == PositionSide.SHORT)
        ):
            return "BUY"
        elif ((order.side == OrderSide.SELL) and (order.positionSide == PositionSide.LONG)) or (
            (order.side == OrderSide.BUY) and (order.positionSide == PositionSide.SHORT)
        ):
            return "SELL"
        else:
            raise ValueError("Cannot check order is buy or sell")
