import time
import traceback
import threading
from functools import wraps
from decimal import Decimal

from binance_f.model.constant import *
from arte.system.upbit.account import UpbitAccount
from arte.system.upbit.order_handler import UpbitOrderHandler
from arte.system.upbit.order_recorder import UpbitOrderRecorder
from arte.system.utils import threaded, print_important


def _process_order(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        message = None
        if "message" in kwargs:
            message = kwargs["message"]
        try:
            order = method(self, *args, **kwargs)
        except:
            traceback.print_exc()
        # if "error" in order["result"]:
        #     print(f"Error during order: {order}")
        #     return None
        else:
            self._postprocess_order(order, message)

    return _impl


class UpbitTradeManager:
    def __init__(self, client, symbols, max_buy_order_count: float, budget_per_symbol: dict, bot=None):
        self.req_client = client.request_client
        self.symbols = symbols
        self.max_buy_order_count = max_buy_order_count
        self.budget_per_symbol = budget_per_symbol
        self.bot = bot if bot else None

        self.account = UpbitAccount(self.req_client, self.symbols)
        self.order_handler = UpbitOrderHandler(self.req_client, self.account)
        self.order_recorder = UpbitOrderRecorder()

        # state manage
        self._initialize_symbol_state()

        print_important("Upbit Trade Manager Initialized, Trading start!", line_length=100)

    def _initialize_symbol_state(self):
        self.symbols_state = dict()
        for _psymbol in self.symbols:
            self.symbols_state[_psymbol] = dict(buy_order_count=0, left_budget=self.budget_per_symbol[_psymbol])

    @threaded
    @_process_order
    def buy_long_market(self, symbol, krw=None, ratio=None, **kwargs):
        if self._check_trade_condition(symbol):
            return self.order_handler.buy_market(symbol=symbol, krw=krw, ratio=ratio)
        else:
            raise ValueError("Exceeded condition: order_count or position_side")

    @threaded
    @_process_order
    def sell_long_market(self, symbol, ratio, **kwargs):
        return self.order_handler.sell_market(symbol=symbol, ratio=ratio)

    def _check_trade_condition(self, symbol):
        return (self.symbols_state[symbol]["buy_order_count"] < self.max_buy_order_count) and (
            self.symbols_state[symbol]["left_budget"] > 0  # left_budget is not perfect. last order could over budget.
        )

    def _postprocess_order(self, order, message=None):
        time.sleep(0.3)  # minimum waiting time. need to adjust later (more longer?)
        order_result = order["result"]
        psymbol = order_result["market"][4:]
        # update account
        self.account.update_changed_recursive()

        # update order_record
        resp = self.req_client.Order.Order_info(uuid=order_result["uuid"])
        order_info = resp["result"]
        order_info["message"] = message
        order_inst = self.order_recorder.get_event(order_info)

        # update self.symbols_state
        if order_result["side"] == UpbitOrderSide.BUY:
            self.symbols_state[psymbol]["buy_order_count"] += 1
            self.symbols_state[psymbol]["left_budget"] -= order_inst.avgPrice * order_inst.origQty

        elif order_result["side"] == UpbitOrderSide.SELL:
            if self.account[psymbol][PositionSide.LONG] <= 0.00000001:
                self.symbols_state[psymbol] = dict(buy_order_count=0, position_size=self.budget_per_symbol[psymbol])

        # Process result message
        message = f"Order {order_inst.clientOrderId}: {order_inst.side} {order_inst.type} - {order_inst.symbol} / Qty: {order_inst.origQty}, Price: KRW {order_inst.avgPrice}"
        print(message)
        print(self.account)
        print(self.symbols_state)
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
