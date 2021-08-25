import copy

from binance_f.model.constant import *


class OrderPairState:
    """
    한 페어 오더의 상태
    """

    OPEN = 0
    CLOSE = 1


class UnitOrder:
    """
    UnitOrder : 하나의 페어의 오더를 관리하는 객체

    Attributes:
        strategy_name : UnitOrder를 사고파는데 사용된 전략 이름
        open_order : UnitOrder를 open한 order 객체
        close_order : UnitOrder를 close한 order 객체
        state : 유닛 오더의 상태 (open or close)
        pnl_fiat : fiat(usdt)단위 유닛 오더의 PNL
        pnl_rate : PNL rate
    """

    def __init__(self, strategy_name, order):
        self.strategy_name = strategy_name
        self.open_order = order
        self.close_order = None
        self.state = OrderPairState.OPEN
        self.pnl_fiat = None
        self.pnl_rate = None

    def close_unitorder(self, order):
        """
        closing UnitOrder
        Args:
            order : should be SELL order

        returns:
            order의 quantity > open_order :
                UnitOrder를 닫고 True, 남은order
            order의 quantity == open_oder :
                UnitOrder를 닫고 True, None(남은거 없음)
            order의 quantity < open_order :
                UnitOrder를 닫을 수 없음 False, order
        """
        if order.origQty > self.open_order.origQty:
            closing_order = copy.deepcopy(order)
            closing_order.origQty = self.open_order.origQty
            self.close_order = closing_order
            order.origQty = order.origQty - self.open_order.origQty
            self.update_pnl()
            return True, order
        elif order.origQty == self.open_order.origQty:
            self.close_order = order
            self.state = OrderPairState.CLOSED
            self.update_pnl()
            return True, None
        else:
            print("Invalid closing order")
            return False, order

    def update_pnl(self):
        """
        UnitOrder가 닫혔을 때 PNL 을 업데이트 해줌
        """
        self.pnl_fiat = self.open_order.quantity * (self.close_order.avgPrice - self.open_order.avgPrice)
        self.pnl_rate = (self.close_order.avgPrice - self.open_order.avgPrice) / self.open_order.avgPrice


class OrderFactory:
    """
    OrderFactory: Unity Order들을 관리해주는 공장

    Attributes:
        factoried_order : {strategy_name:list(UnitOrder1, UnitOrder2...)}
    """

    def __init__(self):
        self.factoried_order = dict()
        # How to manage the pairs..?

    def handling_order(self, strategy, order):
        """
        order가 들어왔을 때, UnitOrder를 handling
        """
        if strategy.name not in self.factoried_order:
            self.factoried_order[strategy.name] = list()

        if order.type == TradeDirection.BUY:
            open_order = UnitOrder(strategy_name=strategy.name, order=order)
            self.factoried_order[strategy.name].append(open_order)
        elif order.type == TradeDirection.SELL:
            # 어떤 Order를 불러와서 닫을지를 모르겠다
            pass
