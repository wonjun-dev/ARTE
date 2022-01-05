import math
import time
import secrets
import traceback

from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *
from arte.system.utils import symbolize_binance


def get_timestamp():
    return int(time.time())  # * 1000)


class BinanceOrderHandler:
    """
    실제 헷지 모드 세팅에서만 작동하며, 가상의 원웨이 모드를 구성
    """

    def __init__(self, request_client, account):
        self.request_client = request_client
        self.account = account
        self._quantity_precisions = dict()
        self._initialize_quantity_precision()

    def _initialize_quantity_precision(self):
        ex_info_per_symbol = self.request_client.get_exchange_information().symbols
        for ex in ex_info_per_symbol:
            if ex.quoteAsset == "USDT":
                self._quantity_precisions[ex.baseAsset] = ex.quantityPrecision

    def _limit(self, symbol: str, order_side: OrderSide, position_side: PositionSide, price: float, quantity: float):
        result = self.request_client.post_order(
            symbol=symbolize_binance(symbol),
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
            symbol=symbolize_binance(symbol),
            side=order_side,
            positionSide=position_side,
            ordertype=OrderType.MARKET,
            quantity=quantity,
            newClientOrderId=self._generate_order_id(symbol),
            newOrderRespType=OrderRespType.RESULT,
        )
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
            if self.account[symbol]["positionSide"] in [PositionSide.INVALID, position_side]:
                return self._limit(
                    symbol,
                    order_side,
                    position_side,
                    price,
                    self._usdt_to_quantity(usdt, price, unit_float=self._quantity_precisions[symbol]),
                )
            else:
                raise ValueError(
                    f"Cannot execute BUY_{position_side}, you have already opened {self.manager.positionSide} position."
                )

        else:
            raise ValueError("You have to pass either quantity or ratio.")

    def buy_market(self, symbol: str, order_side: OrderSide, position_side: PositionSide, price, usdt=None, ratio=None):
        if bool(usdt) ^ bool(ratio):
            if ratio:
                usdt = self.account["USDT"] * ratio
            if self.account[symbol]["positionSide"] in [PositionSide.INVALID, position_side]:
                return self._market(
                    symbol,
                    order_side,
                    position_side,
                    self._usdt_to_quantity(usdt, price, unit_float=self._quantity_precisions[symbol]),
                )
            else:
                raise ValueError(
                    f"Cannot execute BUY_{position_side}, you have already opened {self.manager.positionSide} position."
                )

        else:
            raise ValueError("You have to pass either quantity or ratio.")

    def sell_limit(self, symbol: str, order_side: OrderSide, position_side: PositionSide, price, ratio):
        if self.account[symbol]["positionSide"] == position_side:
            return self._limit(
                symbol,
                order_side,
                position_side,
                price,
                self._asset_ratio_to_quantity(
                    symbol, position_side, ratio, unit_float=self._quantity_precisions[symbol]
                ),
            )
        else:
            raise ValueError(f"Cannot execute SELL_{position_side}, you don't have any {position_side} position.")

    def sell_market(self, symbol: str, order_side: OrderSide, position_side: PositionSide, ratio):
        if self.account[symbol]["positionSide"] == position_side:
            return self._market(
                symbol,
                order_side,
                position_side,
                self._asset_ratio_to_quantity(
                    symbol, position_side, ratio, unit_float=self._quantity_precisions[symbol]
                ),
            )
        else:
            raise ValueError(f"Cannot execute SELL_{position_side}, you don't have any {position_side} position.")

    def _usdt_to_quantity(self, usdt, price, unit_float=3):
        return math.floor((usdt / price) * (10 ** unit_float)) / (10 ** unit_float)

    def _asset_ratio_to_quantity(self, symbol: str, position_side: PositionSide, ratio, unit_float=3):
        asset_quantity = abs(self.account[symbol][position_side])
        return math.floor((asset_quantity * ratio) * (10 ** unit_float)) / (10 ** unit_float)

    def _generate_order_id(self, symbol: str):
        _id = symbol + str(get_timestamp()) + f"-{secrets.token_hex(4)}"
        return _id
