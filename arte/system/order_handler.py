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
from binance_f.model.diffdepthevent import Order
import math
import time
from functools import wraps
import secrets

from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *


def get_timestamp():
    return int(time.time())  # * 1000)


class OrderHandler:
    """
    실제 헷지 모드 세팅에서만 작동하며, 가상의 원웨이 모드를 구성합니다. 
    """

    def __init__(self, request_client, account):
        self.request_client = request_client
        self.account = account
        self.manager = None

    def _limit(self, symbol: str, order_side: OrderSide, position_side: PositionSide, price: float, quantity: float):
        result = self.request_client.post_order(
            symbol=symbol,
            side=order_side,
            positionSide=position_side,
            ordertype=OrderType.LIMIT,
            price=float(price),
            quantity=quantity,
            timeInForce=TimeInForce.GTC,
            newClientOrderId=self._generate_order_id(symbol),
            newOrderRespType=OrderRespType.RESULT,
        )
        return result

    def _market(self, symbol: str, order_side: OrderSide, position_side: PositionSide, quantity: float):
        result = self.request_client.post_order(
            symbol=symbol,
            side=order_side,
            positionSide=position_side,
            ordertype=OrderType.MARKET,
            quantity=quantity,
            newClientOrderId=self._generate_order_id(symbol),
            newOrderRespType=OrderRespType.RESULT,
        )
        print("market order done")
        return result

    def _stop_market(
        self, symbol: str, order_side: OrderSide, position_side: PositionSide, stop_price: float, quantity: float
    ):
        result = self.request_client.post_order(
            symbol=symbol,
            side=order_side,
            positionSide=position_side,
            ordertype=OrderType.STOP_MARKET,
            stopPrice=stop_price,
            quantity=quantity,
            newClientOrderId=self._generate_order_id(symbol),
            newOrderRespType=OrderRespType.RESULT,
        )
        return result

    def buy_limit(self, symbol: str, order_side: OrderSide, position_side: PositionSide, price, usdt=None, ratio=None):
        if bool(usdt) ^ bool(ratio):
            if ratio:
                usdt = self.account["USDT"] * ratio
            if self.manager.symbols_state[symbol]["positionSide"] in [PositionSide.INVALID, position_side]:
                return self._limit(symbol, order_side, position_side, price, self._usdt_to_quantity(usdt, price))
            else:
                print(
                    f"Cannot execute buy_{position_side}, you have already opened {self.manager.positionSide} position."
                )
                return None
        else:
            raise ValueError("You have to pass either quantity or ratio.")

    def buy_market(self, symbol: str, order_side: OrderSide, position_side: PositionSide, price, usdt=None, ratio=None):
        if bool(usdt) ^ bool(ratio):
            if ratio:
                usdt = self.account["USDT"] * ratio
            if self.manager.symbols_state[symbol]["positionSide"] in [PositionSide.INVALID, position_side]:
                return self._market(symbol, order_side, position_side, self._usdt_to_quantity(usdt, price))
            else:
                print(
                    f"Cannot execute buy_{position_side}, you have already opened {self.manager.positionSide} position."
                )
                return None
        else:
            raise ValueError("You have to pass either quantity or ratio.")

    def sell_limit(self, symbol: str, order_side: OrderSide, position_side: PositionSide, price, ratio):
        if self.manager.symbols_state[symbol]["positionSide"] == position_side:
            return self._limit(
                symbol, order_side, position_side, price, self._asset_ratio_to_quantity(symbol, position_side, ratio)
            )
        else:
            print(f"Cannot execute sell_{position_side}, you dont have any {position_side} position.")
            return None

    def sell_market(self, symbol: str, order_side: OrderSide, position_side: PositionSide, ratio):
        if self.manager.symbols_state[symbol]["positionSide"] == position_side:
            return self._market(
                symbol, order_side, position_side, self._asset_ratio_to_quantity(symbol, position_side, ratio)
            )
        else:
            print(f"Cannot execute sell_{position_side}, you dont have any {position_side} position.")
            return None

    def _get_ticker_price(self, symbol: str):
        # temporary function
        result = self.request_client.get_symbol_price_ticker(symbol=symbol)
        return result[0].price

    def _usdt_to_quantity(self, usdt, price, unit_float=3):
        return math.floor((usdt / price) * (10 ** unit_float)) / (10 ** unit_float)

    def _asset_ratio_to_quantity(self, symbol: str, position_side: PositionSide, ratio, unit_float=3):
        asset_quantity = abs(self.account[symbol][position_side])
        return math.floor((asset_quantity * ratio) * (10 ** unit_float)) / (10 ** unit_float)

    def _generate_order_id(self, symbol: str):
        _id = symbol + str(get_timestamp()) + f"-{secrets.token_hex(4)}"
        return _id


if __name__ == "__main__":
    from arte.client import Client
    from arte.system.account import Account
    import threading

    cl = Client(
        mode="TEST",
        api_key="0dcd28f57648b0a7d5ea2737487e3b3093d47935e67506b78291042d1dd2f9ea",
        secret_key="b36dc15c333bd5950addaf92a0f9dc96d8ed59ea6835386c59a6e63e1ae26aa1",
        req_only=True,
    )
    oh = OrderHandler(cl.request_client, Account(cl.request_client), "ETHUSDT")
    # oh._market(OrderSide.BUY, PositionSide.SHORT, quantity=0.3)
    # oh._stop_market(OrderSide.SELL, PositionSide.LONG, stop_price=3050, quantity=0.032)
    # oh._limit(OrderSide.BUY, PositionSide.LONG, price=3120, quantity=0.05)

    start = time.time()
    thread = threading.Thread(target=oh._market, args=("ETHUSDT", OrderSide.SELL, PositionSide.SHORT, 0.03))
    thread.start()
    print("Elapsed Time: %s" % (time.time() - start))
    thread.join()
    print("Elapsed Time: %s" % (time.time() - start))

    # from concurrent import futures

    # executor = futures.ThreadPoolExecutor()
    # start = time.time()
    # future1 = executor.submit(oh._market, OrderSide.SELL, PositionSide.SHORT, 0.03)
    # #future2 = executor.submit(oh._market, OrderSide.SELL, PositionSide.SHORT, 0.03)
    # print("Elapsed Time: %s" % (time.time() - start))

    # # res = future.result()
    # # res = futures.as_completed(future).result()

    # while True:
    #     print("----------")
    #     print(future1.running())
    #     #print(future2.running())
    #     time.sleep(0.1)
