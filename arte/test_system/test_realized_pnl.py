from binance_f.model.constant import *


class TestRealizedPnl:
    def __init__(self):
        # pnl managing dict (key: symbol, value: pnl data dict -> data_dict)
        self.pnl_dict = {}

    def proceeding(self, order, commissionAmount):
        if order.symbol not in self.pnl_dict.keys():
            # if symbol of order not in pnl_dict
            data_dict = {}
            data_dict["position_side"] = None
            data_dict["avg_price"] = 0
            data_dict["quantity"] = 0
            data_dict["realized_pnl"] = 0
            data_dict["realized_pnl_rate"] = 0
            data_dict["total_realized_pnl"] = 0
            data_dict["winrate_pnl"] = 0
            data_dict["win_count"] = 0
            data_dict["total_count"] = 0
            data_dict["current_commission"] = 0
            data_dict["real_profit"] = 0
            data_dict["real_profit_rate"] = 0
            data_dict["total_real_profit"] = 0
            data_dict["winrate_profit"] = 0
            data_dict["win_count_profit"] = 0
            data_dict["USDT_Qty"] = 0
            data_dict["USDT_Qty_before"] = 0
            # add data for pnl_dict -> key: order.symbol, value: data_dict
            self.pnl_dict[order.symbol] = data_dict

        if order.positionSide == PositionSide.LONG:
            self.pnl_dict[order.symbol]["position_side"] = PositionSide.LONG
            if order.side == OrderSide.BUY:
                # long position open
                self.pnl_dict[order.symbol]["USDT_Qty"] = (order.origQty * order.avgPrice) - commissionAmount

                self.pnl_dict[order.symbol]["avg_price"] = (
                    self.pnl_dict[order.symbol]["avg_price"] * self.pnl_dict[order.symbol]["quantity"]
                    + order.avgPrice * order.origQty
                ) / (self.pnl_dict[order.symbol]["quantity"] + order.origQty)
                self.pnl_dict[order.symbol]["quantity"] += order.origQty
                self.pnl_dict[order.symbol]["realized_pnl"] = 0
                self.pnl_dict[order.symbol]["realized_pnl_rate"] = 0
                self.pnl_dict[order.symbol]["current_commission"] += commissionAmount

            elif order.side == OrderSide.SELL:
                # long position close
                self.pnl_dict[order.symbol]["USDT_Qty"] = (order.origQty * order.avgPrice) - commissionAmount

                abs_pnl = (order.avgPrice - self.pnl_dict[order.symbol]["avg_price"]) * order.origQty
                self.pnl_dict[order.symbol]["realized_pnl"] = abs_pnl
                self.pnl_dict[order.symbol]["realized_pnl_rate"] = (
                    self.pnl_dict[order.symbol]["realized_pnl"] / self.pnl_dict[order.symbol]["USDT_Qty"]
                )

                self.pnl_dict[order.symbol]["total_realized_pnl"] += self.pnl_dict[order.symbol]["realized_pnl"]
                self.pnl_dict[order.symbol]["total_count"] += 1
                if self.pnl_dict[order.symbol]["realized_pnl"] > 0:
                    self.pnl_dict[order.symbol]["win_count"] += 1
                self.pnl_dict[order.symbol]["winrate_pnl"] = (
                    self.pnl_dict[order.symbol]["win_count"] / self.pnl_dict[order.symbol]["total_count"]
                )

                self.pnl_dict[order.symbol]["current_commission"] += commissionAmount

                self.pnl_dict[order.symbol]["real_profit"] = self.pnl_dict[order.symbol]["realized_pnl"] - (
                    self.pnl_dict[order.symbol]["current_commission"]
                    * (order.origQty / self.pnl_dict[order.symbol]["quantity"])
                )
                self.pnl_dict[order.symbol]["real_profit_rate"] = (
                    self.pnl_dict[order.symbol]["real_profit"] / self.pnl_dict[order.symbol]["USDT_Qty"]
                )
                self.pnl_dict[order.symbol]["total_real_profit"] += self.pnl_dict[order.symbol]["real_profit"]

                if self.pnl_dict[order.symbol]["real_profit"] > 0:
                    self.pnl_dict[order.symbol]["win_count_profit"] += 1
                self.pnl_dict[order.symbol]["winrate_profit"] = (
                    self.pnl_dict[order.symbol]["win_count_profit"] / self.pnl_dict[order.symbol]["total_count"]
                )
                self.pnl_dict[order.symbol]["current_commission"] -= self.pnl_dict[order.symbol][
                    "current_commission"
                ] * (order.origQty / self.pnl_dict[order.symbol]["quantity"])

                self.pnl_dict[order.symbol]["quantity"] = self.pnl_dict[order.symbol]["quantity"] - order.origQty

        elif order.positionSide == PositionSide.SHORT:
            self.pnl_dict[order.symbol]["position_side"] = PositionSide.SHORT
            if order.side == OrderSide.BUY:
                # short position close
                self.pnl_dict[order.symbol]["USDT_Qty"] = (
                    self.pnl_dict[order.symbol]["USDT_Qty_before"] + self.pnl_dict[order.symbol]["real_profit"]
                )
                self.pnl_dict[order.symbol]["USDT_Qty_before"] = 0

                abs_pnl = (order.avgPrice - self.pnl_dict[order.symbol]["avg_price"]) * order.origQty
                self.pnl_dict[order.symbol]["realized_pnl"] = -abs_pnl
                self.pnl_dict[order.symbol]["realized_pnl_rate"] = (
                    self.pnl_dict[order.symbol]["realized_pnl"] / self.pnl_dict[order.symbol]["USDT_Qty"]
                )

                self.pnl_dict[order.symbol]["total_realized_pnl"] += self.pnl_dict[order.symbol]["realized_pnl"]
                self.pnl_dict[order.symbol]["total_count"] += 1
                if self.pnl_dict[order.symbol]["realized_pnl"] > 0:
                    self.pnl_dict[order.symbol]["win_count"] += 1
                self.pnl_dict[order.symbol]["winrate_pnl"] = (
                    self.pnl_dict[order.symbol]["win_count"] / self.pnl_dict[order.symbol]["total_count"]
                )

                self.pnl_dict[order.symbol]["current_commission"] += commissionAmount

                self.pnl_dict[order.symbol]["real_profit"] = self.pnl_dict[order.symbol]["realized_pnl"] - (
                    self.pnl_dict[order.symbol]["current_commission"]
                    * (order.origQty / self.pnl_dict[order.symbol]["quantity"])
                )
                self.pnl_dict[order.symbol]["real_profit_rate"] = (
                    self.pnl_dict[order.symbol]["real_profit"] / self.pnl_dict[order.symbol]["USDT_Qty"]
                )
                self.pnl_dict[order.symbol]["total_real_profit"] += self.pnl_dict[order.symbol]["real_profit"]

                if self.pnl_dict[order.symbol]["real_profit"] > 0:
                    self.pnl_dict[order.symbol]["win_count_profit"] += 1
                self.pnl_dict[order.symbol]["winrate_profit"] = (
                    self.pnl_dict[order.symbol]["win_count_profit"] / self.pnl_dict[order.symbol]["total_count"]
                )
                self.pnl_dict[order.symbol]["current_commission"] -= self.pnl_dict[order.symbol][
                    "current_commission"
                ] * (order.origQty / self.pnl_dict[order.symbol]["quantity"])

                self.pnl_dict[order.symbol]["quantity"] = self.pnl_dict[order.symbol]["quantity"] - order.origQty

            elif order.side == OrderSide.SELL:
                # short position open
                self.pnl_dict[order.symbol]["USDT_Qty"] = (order.origQty * order.avgPrice) - commissionAmount
                self.pnl_dict[order.symbol]["USDT_Qty_before"] = self.pnl_dict[order.symbol]["USDT_Qty"]

                self.pnl_dict[order.symbol]["avg_price"] = (
                    self.pnl_dict[order.symbol]["avg_price"] * self.pnl_dict[order.symbol]["quantity"]
                    + order.avgPrice * order.origQty
                ) / (self.pnl_dict[order.symbol]["quantity"] + order.origQty)
                self.pnl_dict[order.symbol]["quantity"] += order.origQty
                self.pnl_dict[order.symbol]["realized_pnl"] = 0
                self.pnl_dict[order.symbol]["realized_pnl_rate"] = 0
                self.pnl_dict[order.symbol]["current_commission"] += commissionAmount

    def close_position(self, symbol: str):
        # reset when all position closed
        self.pnl_dict[symbol]["position_side"] = None
        self.pnl_dict[symbol]["avg_price"] = 0
        self.pnl_dict[symbol]["quantity"] = 0
        self.pnl_dict[symbol]["realized_pnl"] = 0
        self.pnl_dict[symbol]["realized_pnl_rate"] = 0
        self.pnl_dict[symbol]["winrate_pnl"] = 0
        self.pnl_dict[symbol]["real_profit"] = 0
        self.pnl_dict[symbol]["real_profit_rate"] = 0
        self.pnl_dict[symbol]["winrate_profit"] = 0
