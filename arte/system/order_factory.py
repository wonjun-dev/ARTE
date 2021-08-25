import copy

from binance_f.model.constant import *


class OrderPairState:
    OPEN = 0
    CLOSE = 1


class UnitOrder:
    def __init__(self, strategy_name, order):
        self.strategy_name = strategy_name
        self.open_order = order
        self.close_order = None
        self.state = OrderPairState.OPEN
        self.pnl_fiat = None
        self.pnl_rate = None

    def close_order(self, order):
        if order.origQty > self.open_order.origQty:
            closing_order = copy.deepcopy(order)
            closing_order.origQty = self.open_order.origQty
            self.close_order = closing_order
            order.origQty = order.origQty - self.open_order.origQty
            self.update_pnl()
            return order
        elif order.origQty == self.open_order.origQty:
            self.close_order = order
            self.state = OrderPairState.CLOSED
            self.update_pnl()
            return None
        else:
            print("Invalid closing order")
            return order

    def update_pnl(self):
        self.pnl_fiat = self.open_order.quantity * (self.close_order.avgPrice - self.open_order.avgPrice)
        self.pnl_rate = (self.close_order.avgPrice - self.open_order.avgPrice) / self.open_order.avgPrice


class OrderFactory:
    def __init__(self):
        self.factoried_order = dict()
        # How to manage the pairs..?

    def handling_order(self, strategy, order):
        if strategy.name not in self.factoried_order:
            self.factoried_order[strategy.name] = list()

        if order.type == TradeDirection.BUY:
            open_order = UnitOrder(strategy_name=strategy.name, order=order)
            self.factoried_order[strategy.name].append(open_order)
        elif order.type == TradeDirection.SELL:
            # 어떤 Order를 불러와서 닫을지를 모르겠다
            pass
