"""
오더를 레코드 합니다.
"""

import os
import csv
from datetime import datetime
from decimal import Decimal

from arte.system.realized_pnl import RealizedPnl
from binance_f.model.orderupdate import OrderUpdate
from binance_f.model.constant import *


class UpbitPseudoOrderUpdate(OrderUpdate):
    def __init__(self):
        super().__init__()


class UpbitOrderRecorder:
    def __init__(self):
        if not os.path.exists("./db"):
            os.makedirs("./db")

        self.pair_dict = {}

        self.order_fields = [
            "orderStatus",
            "symbol",
            "clientOrderId",
            "eventTime",
            "side_positionSide_type",
            "origQty",
            "avgPrice",
            "KRW_Qty",
            "commissionAmount",
            "realized_pnl",
            "total_realized_pnl",
            "ROE_pnl",
            "win_rate_pnl",
            "real_profit",
            "total_real_profit",
            "ROE_profit",
            "win_rate_profit",
            "strategy_name",
            "message",
        ]

        self.realized_pnl = RealizedPnl()

        self.current_strategy_name = "arbi"
        self.start_date = datetime.today().strftime("%Y%m%d%H%M%S")

    def _calc_avgPrice(self, order_info):
        trades = order_info["trades"]
        if order_info["trades_count"] == 1:
            return float(trades[0]["price"])
        else:
            whole_volume = Decimal(order_info["executed_volume"])
            whole_price = Decimal(0)
            for trade in trades:
                whole_price += Decimal(trade["price"]) * Decimal(trade["volume"])
            return float(whole_price / whole_volume)

    def get_event(self, order_info):  # event):
        event = UpbitPseudoOrderUpdate()
        if order_info["trades_count"] > 0:
            event.orderStatus = "FILLED"
            event.positionSide = PositionSide.LONG
            event.type = OrderType.MARKET
            event.eventTime = order_info["created_at"]
            event.clientOrderId = order_info["uuid"]
            event.symbol = order_info["market"]
            event.side = OrderSide.BUY if order_info["side"] == UpbitOrderSide.BUY else OrderSide.SELL
            event.origQty = float(order_info["executed_volume"])
            event.commissionAmount = float(order_info["paid_fee"])
            event.avgPrice = self._calc_avgPrice(order_info)

        # orderUpdate event to dict(event_dict)
        event_dict = dict(item for item in event.__dict__.items())
        order_dict = {}

        # get basic data from orderUpdate event
        for key in event_dict.keys():
            if key in self.order_fields:
                order_dict[key] = event_dict[key]

        # making side - positionSide - type data
        if event.positionSide == "LONG":
            order_dict["side_positionSide_type"] = (
                event_dict["side"] + "_" + event_dict["positionSide"] + "_" + event_dict["type"]
            )
            order_dict["KRW_Qty"] = round(order_dict["origQty"] * order_dict["avgPrice"], 4) - event.commissionAmount
        elif event.positionSide == "SHORT":
            if event.side == "SELL":  # open short position
                order_dict["side_positionSide_type"] = "BUY_" + event_dict["positionSide"] + "_" + event_dict["type"]
                order_dict["KRW_Qty"] = 0
            elif event.side == "BUY":  # close short position
                order_dict["side_positionSide_type"] = "SELL_" + event_dict["positionSide"] + "_" + event_dict["type"]
                order_dict["KRW_Qty"] = 0

        # calc PNL and Profit when
        if event.orderStatus == "FILLED":
            self.realized_pnl.proceeding(event)

            # PNL calc
            order_dict["realized_pnl"] = round(self.realized_pnl.pnl_dict[event.symbol]["realized_pnl"], 8)
            order_dict["total_realized_pnl"] = round(self.realized_pnl.pnl_dict[event.symbol]["total_realized_pnl"], 8)
            # order_dict["ROE_pnl"] = round(self.realized_pnl.pnl_dict[event.symbol]["realized_pnl_rate"], 8)
            if order_dict["KRW_Qty"] != 0:
                order_dict["ROE_pnl"] = (order_dict["realized_pnl"] / order_dict["KRW_Qty"]) * 100
            else:
                order_dict["ROE_pnl"] = 0
            order_dict["win_rate_pnl"] = round(self.realized_pnl.pnl_dict[event.symbol]["winrate_pnl"], 8)

            # Profit calc incl commission
            order_dict["real_profit"] = round(self.realized_pnl.pnl_dict[event.symbol]["real_profit"], 8)
            order_dict["total_real_profit"] = round(self.realized_pnl.pnl_dict[event.symbol]["total_real_profit"], 8)
            # order_dict["ROE_profit"] = round(self.realized_pnl.pnl_dict[event.symbol]["real_profit_rate"], 8)
            if order_dict["KRW_Qty"] != 0:
                order_dict["ROE_profit"] = (order_dict["real_profit"] / order_dict["KRW_Qty"]) * 100
            else:
                order_dict["ROE_profit"] = 0
            order_dict["win_rate_profit"] = round(self.realized_pnl.pnl_dict[event.symbol]["winrate_profit"], 8)

            # strategy_name
            order_dict["strategy_name"] = self.current_strategy_name

            # reset if all sold
            if self.realized_pnl.pnl_dict[event.symbol]["quantity"] == 0:
                self.realized_pnl.close_position(event.symbol)

        # update_csv
        self.update_csv(self.current_strategy_name, self.start_date, order_dict)

        return event  # for telegram message

    def get_message(self, message):
        pass

    def update_csv(self, strategy: str, start_date: str, order_dict: dict):
        symbol = order_dict["symbol"]
        path = f"./db/{strategy}_{symbol}_{start_date}.csv"
        with open(path, "a", newline="") as f_object:
            writer_object = csv.DictWriter(f_object, fieldnames=self.order_fields)
            if os.stat(path).st_size == 0:
                writer_object.writeheader()
            writer_object.writerow(order_dict)
