from binance_f.model.constant import *


class RealizedPnl:
    def __init__(self, strategy_name):
        self.strategy_name = strategy_name
        self.position_side = None
        self.avg_price = 0
        self.quantity = 0

        self.realized_pnl = 0
        self.realized_pnl_rate = 0

        self.total_realized_pnl = 0

        self.winrate = 0
        self.win_count = 0
        self.total_count = 0

    def proceeding(self, order):
        if order.positionSide == PositionSide.LONG:
            self.position_side = PositionSide.LONG
            is_long = True
        elif order.positionSide == PositionSide.SHORT:
            self.position_side = PositionSide.SHORT
            is_long = False

        if order.side == OrderSide.BUY:
            self.avg_price = (self.avg_price * self.quantity + order.avgPrice * order.origQty) / (
                self.quantity + order.origQty
            )
            self.quantity = self.quantity + order.origQty
            self.realized_pnl = 0
            self.realized_pnl_rate = 0
        elif order.side == OrderSide.SELL:
            abs_pnl = (order.avgPrice - self.avg_price) * order.origQty
            self.realized_pnl = abs_pnl if is_long else -abs_pnl
            self.realized_pnl_rate = self.realized_pnl / self.avg_price

            self.total_realized_pnl += self.realized_pnl
            self.total_count += 1
            if self.realized_pnl > 0:
                self.win_count += 1
            self.winrate = self.win_count / self.total_count

            print(self.realized_pnl, self.realized_pnl_rate, self.winrate, self.avg_price)
            if self.quantity == order.origQty:
                self.close_position()

    def close_position(self):
        self.position_side = None
        self.avg_price = 0
        self.quantity = 0

        self.realized_pnl = 0
        self.realized_pnl_rate = 0

    # 다 팔때 초기화하기
