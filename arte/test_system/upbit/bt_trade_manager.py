"""
Upbit
"""
import sys
from functools import wraps
from decimal import Decimal, getcontext

getcontext().prec = 6

from binance_f.model.constant import *
from .test_account import Account
from .test_order_handler import OrderHandler
from arte.test_system.bt_order_recorder import BackTestOrderRecorder


def _process_order(method):
    @wraps(method)
    def _impl(self, **kwargs):
        # print(kwargs)
        kwargs["symbol"] = kwargs["symbol"].upper()
        if kwargs["symbol"] not in self.symbols_state:
            self.symbols_state[kwargs["symbol"]] = self._init_symbol_state()
        order = method(self, **kwargs)
        if order:
            self._postprocess_order(order)
        return order

    return _impl


class BackTestUpbitTradeManager:
    def __init__(self, init_krw=100000, *args, **kwargs):
        self.account = Account(init_balance=init_krw)
        self.order_handler = OrderHandler(self.account)
        self.order_recorder = BackTestOrderRecorder()

        self.test_current_time = None
        self.trade_prices = None

        self.bot = None
        if "bot" in kwargs:
            self.bot = kwargs["bot"]
        if "max_order_count" in kwargs:
            self.max_order_count = kwargs["max_order_count"]

        # state manage
        self.symbols_state = dict()

    def _init_symbol_state(self):
        return dict(order_count=0, positionSize=0, positionSide=PositionSide.INVALID)

    def calc_market_order_price(self, last_price, last_askbid, buy_or_sell):
        if last_price < 10:
            tick_size = 0.01
        elif last_price < 100:
            tick_size = 0.1
        elif last_price < 1000:
            tick_size = 1
        elif last_price < 10000:
            tick_size = 5
        elif last_price < 100000:
            tick_size = 10
        elif last_price < 500000:
            tick_size = 50
        elif last_price < 1000000:
            tick_size = 100
        elif last_price < 2000000:
            tick_size = 500
        else:
            tick_size = 1000

        if buy_or_sell == "BUY":
            if last_askbid == "ASK":
                trade_price = last_price
            elif last_askbid == "BID":
                trade_price = last_price + tick_size
        elif buy_or_sell == "SELL":
            if last_askbid == "ASK":
                trade_price = last_price - tick_size
            elif last_askbid == "BID":
                trade_price = last_price

        return trade_price

    @_process_order
    def buy_long_market(self, symbol, krw=None, ratio=None):
        if self.symbols_state[symbol]["order_count"] < self.max_order_count:
            market_trade_price = self.calc_market_order_price(
                last_price=self.trade_prices[symbol[4:]], last_askbid=self.last_askbid[symbol[4:]], buy_or_sell="BUY"
            )
            return self.order_handler.open_long_market(symbol=symbol, price=market_trade_price, krw=krw, ratio=ratio)

    @_process_order
    def sell_long_market(self, symbol, ratio):
        market_trade_price = self.calc_market_order_price(
            last_price=self.trade_prices[symbol[4:]], last_askbid=self.last_askbid[symbol[4:]], buy_or_sell="SELL"
        )
        return self.order_handler.close_long_market(symbol=symbol, price=market_trade_price, ratio=ratio)

    def _postprocess_order(self, order):
        symbol = order.symbol
        if order.side == OrderSide.BUY:
            self.symbols_state[symbol]["order_count"] += 1
            self.symbols_state[symbol]["positionSize"] = float(
                Decimal(self.symbols_state[symbol]["positionSize"] + order.origQty)
            )
            self.symbols_state[symbol]["positionSide"] = order.positionSide

        elif order.side == OrderSide.SELL:
            self.symbols_state[symbol]["positionSize"] = float(
                Decimal(self.symbols_state[symbol]["positionSize"] - order.origQty)
            )
            if self.symbols_state[symbol]["positionSize"] < sys.float_info.epsilon:
                self.symbols_state[symbol] = self._init_symbol_state()

        self._process_order_record(order)

    def _process_order_record(self, order):
        self.order_recorder.test_order_to_order_dict(order, self.test_current_time)

    def update(self, test_current_time, trade_prices, last_askbid):
        self.test_current_time = test_current_time
        self.trade_prices = trade_prices
        self.last_askbid = last_askbid

    def end_bt(self):
        return self.order_recorder.return_records()


if __name__ == "__main__":
    tm = TestUpbitTradeManager(init_krw=100000, max_order_count=3)
    symbol = "KRW-ETH"
    # tm.update(0, trade_prices={symbol[4:]:2783000.0}, last_askbid='BID')
    # tm.buy_long_market(symbol=symbol, krw=50000)
    # tm.update(0, trade_prices={symbol[4:]:2700000.0})
    # tm.sell_long_market(symbol=symbol, ratio=1)
    # print(tm.calc_market_order_price(1500, 'BID', 'BUY'))
