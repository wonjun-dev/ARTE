import time
import threading
from functools import wraps
from decimal import Decimal

from binance_f.model.constant import *
from arte.system.upbit.account import UpbitAccount
from arte.system.upbit.order_handler import UpbitOrderHandler
from arte.system.upbit.order_recorder import UpbitOrderRecorder


def _process_order(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        order = method(self, *args, **kwargs)
        if "error" in order["result"]:
            print(f"Error during order: {order}")
            return None
        else:
            self._postprocess_order_by_thread(order)
        return order

    return _impl


class UpbitTradeManager:
    def __init__(self, client, symbols, *args, **kwargs):
        self.client = client.request_client
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
        if self.symbols_state[symbol[4:]]["order_count"] < self.max_order_count:
            return self.order_handler.buy_market(symbol=symbol, krw=krw, ratio=ratio)

    @_process_order
    def sell_long_market(self, symbol, ratio):
        return self.order_handler.sell_market(symbol=symbol, ratio=ratio)

    def _postprocess_order_by_thread(self, order):
        threading.Thread(target=self._postprocess_order, args=(order,)).start()

    def _postprocess_order(self, order):
        time.sleep(0.25)  # minimum waiting time. need to adjust later (more longer?)
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
        order_inst = self.order_recorder.get_event(order_info)

        # Process result message
        message = f"Order {order_inst.clientOrderId}: {order_inst.side} {order_inst.type} - {order_inst.symbol} / Qty: {order_inst.origQty}, Price: KRW {order_inst.avgPrice}"
        print(message)
        if self.bot:
            self.bot.sendMessage(message)


if __name__ == "__main__":
    import time
    import configparser
    from arte.system.client import UpbitClient

    cfg = configparser.ConfigParser()
    cfg.read("/media/park/hard2000/arte_config/config.ini")
    config = cfg["REAL_JAEHAN"]
    access_key = config["UPBIT_ACCESS_KEY"]
    secret_key = config["UPBIT_SECRET_KEY"]

    cl = UpbitClient(access_key, secret_key)
    tm = UpbitTradeManager(client=cl, symbols=["XRP", "EOS"], max_order_count=3)
    order_result_buy = tm.buy_long_market("KRW-XRP", krw=5300)
    # print(order_result_buy)
    time.sleep(0.5)
    order_result_sell = tm.sell_long_market("KRW-XRP", ratio=1.0)
    # print(order_result_sell)
