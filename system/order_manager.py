"""
OrderManager의 역할
1. 함수 하나로 사용하는 쉬운 오더 (파라미터를 최소화 시키는 방식 - 코딩 실수를 막기 위해)
2. 신청된 오더들을 기록 (오더 리스트)
3. 신청된 오더가 체결된 경우를 체크 (메인루프 안에서 정기적으로 확인 및 갱신)
4. 체결된 오더의 기록

나머지는 다 이미 api화가 되어있는듯?
- 오더 취소
- 포지션 / 밸런스 계산 및 시각화
- 레버리지 / 마진 변화
"""
import math
import time
from functools import wraps

from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *

from account import Account


def get_timestamp():
    return int(time.time())  # * 1000)


def _postprocess_order(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        results = method(self, *args, **kwargs)
        if results:
            order_name = results[0]
            order = results[1]
            message = f"Order {order.clientOrderId}: {order_name} {order.type} - {order.symbol} / Qty: {order.origQty}, Price: ${order.avgPrice}"
            self.bot.sendMessage(message)
            print(message)
            self.account.update()
            self.order_list.append(order)
            self.order_count += 1
        return results

    return _impl


class OrderManager:
    """
    "특정" 에셋을 위한 오더 매니저
    인스턴스를 만들때 symbol로 넣는 에셋 하나만을 거래합니다.
    다수의 에셋을 거래하고 싶다면 여러개의 오더매니저가 필요합니다.
    """

    def __init__(self, request_client, account, bot, symbol: str):
        self.request_client = request_client
        self.account = account
        self.bot = bot
        self.order_list = []
        self.order_count = 0
        self.symbol = symbol

    def update(self):
        """
        주 목적 - 리미트 주문이 filled 되는지를 검사하여 로컬에 반영
        """
        for o in self.order_list:
            if o.type == "LIMIT":
                if o.status == "NEW":
                    result = self.request_client.get_order(
                        self.symbol, origClientOrderId=o.clientOrderId
                    )
                    if o.status != result.status:
                        print(
                            f"""Status Changed - Order {result.clientOrderId}: {o.status} -> {result.status} /
                            {result.side} {result.type} - {result.symbol} / Qty: {result.origQty}, Price: ${result.price}"""
                        )
                        o.status = (
                            result.status
                        )  # NEEDFIX: it should update whole instance
                        self.account.update()

    def long_limit(self, price: float, quantity: float):
        result = self.request_client.post_order(
            symbol=self.symbol,
            side=OrderSide.BUY,
            ordertype=OrderType.LIMIT,
            price=float(price),
            quantity=quantity,
            timeInForce=TimeInForce.GTC,
            newClientOrderId=self._generate_order_id(),
        )
        return result

    def long_market(self, quantity: float):
        result = self.request_client.post_order(
            symbol=self.symbol,
            side=OrderSide.BUY,
            ordertype=OrderType.MARKET,
            quantity=quantity,
            newClientOrderId=self._generate_order_id(),
            newOrderRespType=OrderRespType.RESULT,
        )
        return result

    def short_limit(self, price: float, quantity: float):
        result = self.request_client.post_order(
            symbol=self.symbol,
            side=OrderSide.SELL,
            ordertype=OrderType.LIMIT,
            price=price,
            quantity=quantity,
            timeInForce=TimeInForce.GTC,
            newClientOrderId=self._generate_order_id(),
        )
        return result

    def short_market(self, quantity: float):
        result = self.request_client.post_order(
            symbol=self.symbol,
            side=OrderSide.SELL,
            ordertype=OrderType.MARKET,
            quantity=quantity,
            newClientOrderId=self._generate_order_id(),
            newOrderRespType=OrderRespType.RESULT,
        )
        return result

    @_postprocess_order
    def buy_long_limit(self, price, quantity=None, ratio=None):
        """
        curpos - long: add more long position
        curpos - none: add long position
        curpos - short: not working

        Args:
            price: order price
            quantity: order quantity
            ratio: ratio of usdt, need to be in [0, 1)
        """
        if bool(quantity) ^ bool(ratio):
            if ratio:
                quantity = self._usdt_ratio_to_quantity(ratio, price)
            if self.account.positions[self.symbol].positionAmt >= 0:
                return ("BUY_LONG", self.long_limit(price, quantity))
            else:
                print(
                    "Cannot execute buy_long, you have already opened short position."
                )
                return None
        else:
            raise ValueError("You have to pass either quantity or ratio.")

    @_postprocess_order
    def sell_long_limit(self, price, quantity=None, ratio=None):
        """
        curpos - long: decrease long position
        curpos - none: not working
        curpos - short: not working

        Args:
            price: order price
            quantity: order quantity
            ratio: ratio of asset, need to be in [0, 1]
        """
        if bool(quantity) ^ bool(ratio):
            if ratio:
                quantity = self._symbol_ratio_to_quantity(ratio)
            if self.account.positions[self.symbol].positionAmt > 0:
                return ("SELL_LONG", self.short_limit(price, quantity))
            else:
                print("Cannot execute sell_long, you dont have any long position.")
                return None
        else:
            raise ValueError("You have to pass either quantity or ratio.")

    @_postprocess_order
    def buy_short_limit(self, price, quantity=None, ratio=None):
        """
        curpos - long: not working
        curpos - none: add short position
        curpos - short: add more short position

        Args:
            price: order price
            quantity: order quantity
            ratio: ratio of usdt, need to be in [0, 1)
        """
        if bool(quantity) ^ bool(ratio):
            if ratio:
                quantity = self._usdt_ratio_to_quantity(ratio, price)
            if self.account.positions[self.symbol].positionAmt <= 0:
                return ("BUY_SHORT", self.short_limit(price, quantity))
            else:
                print(
                    "Cannot execute buy_short, you have already opened long position."
                )
                return None
        else:
            raise ValueError("You have to pass either quantity or ratio.")

    @_postprocess_order
    def sell_short_limit(self, price, quantity=None, ratio=None):
        """
        curpos - long: not working
        curpos - none: not working
        curpos - short: decrease short position

        Args:
            price: order price
            quantity: order quantity
            ratio: ratio of asset, need to be in [0, 1]
        """
        if bool(quantity) ^ bool(ratio):
            if ratio:
                quantity = self._symbol_ratio_to_quantity(ratio)
            if self.account.positions[self.symbol].positionAmt < 0:
                return ("SELL_SHORT", self.long_limit(price, quantity))
            else:
                print("Cannot execute sell_short, you dont have any short position.")
                return None
        else:
            raise ValueError("You have to pass either quantity or ratio.")

    @_postprocess_order
    def buy_long_market(self, quantity=None, ratio=None):
        """
        curpos - long: add more long position
        curpos - none: add long position
        curpos - short: not working

        Args:
            quantity: order quantity
            ratio: ratio of usdt, need to be in [0, 1)
        """
        if bool(quantity) ^ bool(ratio):
            if ratio:
                quantity = self._usdt_ratio_to_quantity(ratio, self.get_ticker_price())
            if self.account.positions[self.symbol].positionAmt >= 0:
                return ("BUY_LONG", self.long_market(quantity))
            else:
                print(
                    "Cannot execute buy_long, you have already opened short position."
                )
                return None
        else:
            raise ValueError("You have to pass either quantity or ratio.")

    @_postprocess_order
    def sell_long_market(self, quantity=None, ratio=None):
        """
        curpos - long: decrease long position
        curpos - none: not working
        curpos - short: not working

        Args:
            quantity: order quantity
            ratio: ratio of asset, need to be in [0, 1]
        """
        if bool(quantity) ^ bool(ratio):
            if ratio:
                quantity = self._symbol_ratio_to_quantity(ratio)
            if self.account.positions[self.symbol].positionAmt > 0:
                return ("SELL_LONG", self.short_market(quantity))
            else:
                print("Cannot execute sell_long, you dont have any long position.")
                return None
        else:
            raise ValueError("You have to pass either quantity or ratio.")

    @_postprocess_order
    def buy_short_market(self, quantity=None, ratio=None):
        """
        curpos - long: not working
        curpos - none: add short position
        curpos - short: add more short position

        Args:
            quantity: order quantity
            ratio: ratio of usdt, need to be in [0, 1)
        """
        if bool(quantity) ^ bool(ratio):
            if ratio:
                quantity = self._usdt_ratio_to_quantity(ratio, self.get_ticker_price())
            if self.account.positions[self.symbol].positionAmt <= 0:
                return ("BUY_SHORT", self.short_market(quantity))
            else:
                print(
                    "Cannot execute buy_short, you have already opened long position."
                )
                return None
        else:
            raise ValueError("You have to pass either quantity or ratio.")

    @_postprocess_order
    def sell_short_market(self, quantity=None, ratio=None):
        """
        curpos - long: not working
        curpos - none: not working
        curpos - short: decrease short position

        Args:
            quantity: order quantity
            ratio: ratio of asset, need to be in [0, 1]
        """
        if bool(quantity) ^ bool(ratio):
            if ratio:
                quantity = self._symbol_ratio_to_quantity(ratio)
            if self.account.positions[self.symbol].positionAmt < 0:
                return ("SELL_SHORT", self.long_market(quantity))
            else:
                print("Cannot execute sell_short, you dont have any short position.")
                return None
        else:
            raise ValueError("You have to pass either quantity or ratio.")

    def get_ticker_price(self):
        result = self.request_client.get_symbol_price_ticker(symbol=self.symbol)
        return result[0].price

    def _usdt_ratio_to_quantity(self, ratio, price, unit_float=3):
        return math.floor(
            ((self.account.usdt_balance * ratio) / price) * (10 ** unit_float)
        ) / (
            10 ** unit_float
        )  # cut 3 decimal under floating point

    def _symbol_ratio_to_quantity(self, ratio, unit_float=3):
        symbol_quantity = abs(self.account.positions[self.symbol].positionAmt)
        return math.floor((symbol_quantity * ratio) * (10 ** unit_float)) / (
            10 ** unit_float
        )

    def _generate_order_id(self):
        _id = self.symbol + str(get_timestamp()) + f"num{self.order_count:05}"
        return _id


if __name__ == "__main__":
    import sys

    sys.path.append("..")
    from arte.client import Client
    from telegram_bot import SimonManager

    cl = Client(mode="TEST")
    account = Account(cl.request_client)
    bot = SimonManager()
    btc_om = OrderManager(cl.request_client, account, bot, "ETHUSDT")

    res = btc_om.buy_long_market(ratio=0.01)
    print(res)
