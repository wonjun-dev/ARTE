import time
from functools import wraps
from decimal import Decimal

from binance_f.model.constant import *
from .account import UpbitAccount
from .order_handler import UpbitOrderHandler
from .order_recorder import UpbitOrderRecorder


def _process_order(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        order = method(self, *args, **kwargs)
        if "error" in order:
            print(f"Error during order: {order}")
        else:
            self._postprocess_order(order)
        return order

    return _impl


class UpbitTradeManager:
    def __init__(self, client, symbols, *args, **kwargs):
        self.client = client.upbit_request_client
        self.account = UpbitAccount(self.client)
        self.order_handler = UpbitOrderHandler(self.client, self.account)
        self.order_handler.manager = self
        self.order_recorder = UpbitOrderRecorder()
        self.symbols = symbols

        # Trader have to be assigned
        self.environment = None

        self.bot = None
        if "bot" in kwargs:
            self.bot = kwargs["bot"]
        if "max_order_count" in kwargs:
            self.max_order_count = kwargs["max_order_count"]

        # state manage
        self.symbols_state = dict()
        for _psymbol in self.symbols:
            self.symbols_state[_psymbol] = self._init_symbol_state()

    def __getitem__(self, key):
        return self.symbols_state[key]

    def _init_symbol_state(self):
        return dict(order_count=0, position_size=0)

    @_process_order
    def buy_long_market(self, symbol, krw=None, ratio=None):
        if self.symbols_state[symbol]["order_count"] < self.max_order_count:
            return self.order_handler.buy_market(symbol=symbol, krw=krw, ratio=ratio)

    @_process_order
    def sell_long_market(self, symbol, ratio):
        return self.order_handler.sell_market(symbol=symbol, ratio=ratio)

    def _postprocess_order_by_thread(self, order):
        threading.Thread(target=self._postprocess_order, args=(order)).start()

    def _postprocess_order(self, order):
        time.sleep(0.05)
        order_result = order["result"]
        pure_symbol = order_result["market"][4:]
        # update account
        self.account.update()

        # update self.symbols_state
        for _symbol in self.account.symbols():
            self.symbols_state[_symbol]["position_size"] = self.account[_symbol]

        if order_result["side"] == UpbitOrderSide.BUY:
            self.symbols_state[pure_symbol]["order_count"] += 1

        elif order_result["side"] == UpbitOrderSide.SELL:
            if self.symbols_state[pure_symbol]["position_size"] <= 0.00000001:
                self.symbols_state[pure_symbol]["order_count"] = 0

        # update order_record
        resp = self.client.Order.Order_info(uuid=order_result["uuid"])
        order_info = resp["result"]

        # Process result message
        # message = f"Order {order.clientOrderId}: {order.side} {order.type} - {order.symbol} / Qty: {order.origQty}, Price: ${order.avgPrice}"
        # print(message)
        # if self.bot:
        #     self.bot.sendMessage(message)


if __name__ == "__main__":
    import threading
    import time
    from arte.system.client import Client

    API_KEY = None
    SECRET_KEY = None
    cl = Client(mode="TEST", api_key=API_KEY, secret_key=SECRET_KEY, req_only=False)
    tm = UpbitTradeManager(client=cl, max_order_count=3)
    tm.buy_short_market("ethusdt", 2783, usdt=100)
    time.sleep(0.05)
    tm.sell_short_market("ethusdt", ratio=1)

    for t in threading.enumerate():
        if t is threading.current_thread():
            continue
        t.join()
