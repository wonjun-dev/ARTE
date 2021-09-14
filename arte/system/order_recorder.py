"""
오더를 레코드 합니다.
"""

import os
import csv
from datetime import datetime

from arte.system.realized_pnl import RealizedPnl


class OrderRecorder:
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
            "USDT_Qty",
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
        ]

        self.realized_pnl = RealizedPnl()

        self.current_strategy_name = "arbi"
        self.start_date = datetime.today().strftime("%Y%m%d%H%M%S")

    def get_event(self, event):
        # order update event to order list
        self.event_to_order_dict(event)

        if event.orderStatus == "NEW":
            self.pair_dict[event.clientOrderId] = {"beforeFill": event, "afterFill": None}

        elif event.orderStatus == "FILLED":
            self.pair_dict[event.clientOrderId]["afterFill"] = event

    def event_to_order_dict(self, event):
        # orderUpdate event to dict(event_dict)
        event_dict = dict(item for item in event.__dict__.items())
        order_dict = {}

        # get basic data from orderUpdate event
        for key in event_dict.keys():
            if key in self.order_fields:
                order_dict[key] = event_dict[key]

        # USDT qunatity calc
        order_dict["USDT_Qty"] = round(order_dict["origQty"] * order_dict["avgPrice"], 4)

        # making side - positionSide - type data
        if event.positionSide == "LONG":
            order_dict["side_positionSide_type"] = (
                event_dict["side"] + "_" + event_dict["positionSide"] + "_" + event_dict["type"]
            )
        elif event.positionSide == "SHORT":
            if event.side == "SELL":  # open short position
                order_dict["side_positionSide_type"] = "BUY_" + event_dict["positionSide"] + "_" + event_dict["type"]
            elif event.side == "BUY":  # close short position
                order_dict["side_positionSide_type"] = "SELL_" + event_dict["positionSide"] + "_" + event_dict["type"]

        # calc PNL and Profit when
        if event.orderStatus == "FILLED":
            self.realized_pnl.proceeding(event)

            # PNL calc
            order_dict["realized_pnl"] = round(self.realized_pnl.pnl_dict[event.symbol]["realized_pnl"], 8)
            order_dict["total_realized_pnl"] = round(self.realized_pnl.pnl_dict[event.symbol]["total_realized_pnl"], 8)
            order_dict["ROE_pnl"] = round(self.realized_pnl.pnl_dict[event.symbol]["realized_pnl_rate"], 8)
            order_dict["win_rate_pnl"] = round(self.realized_pnl.pnl_dict[event.symbol]["winrate_pnl"], 8)

            # Profit calc incl commission
            order_dict["real_profit"] = round(self.realized_pnl.pnl_dict[event.symbol]["real_profit"], 8)
            order_dict["total_real_profit"] = round(self.realized_pnl.pnl_dict[event.symbol]["total_real_profit"], 8)
            order_dict["ROE_profit"] = round(self.realized_pnl.pnl_dict[event.symbol]["real_profit_rate"], 8)
            order_dict["win_rate_profit"] = round(self.realized_pnl.pnl_dict[event.symbol]["winrate_profit"], 8)

            # strategy_name
            order_dict["strategy_name"] = self.current_strategy_name

            # reset if all sold
            if self.realized_pnl.pnl_dict[event.symbol]["quantity"] == 0:
                self.realized_pnl.close_position(event.symbol)

        # update_csv
        self.update_csv(self.current_strategy_name, self.start_date, order_dict)

    def update_csv(self, strategy: str, start_date: str, order_dict: dict):
        symbol = order_dict["symbol"]
        path = f"./db/{strategy}_{symbol}_{start_date}.csv"
        with open(path, "a", newline="") as f_object:
            writer_object = csv.DictWriter(f_object, fieldnames=self.order_fields)
            if os.stat(path).st_size == 0:
                writer_object.writeheader()
            writer_object.writerow(order_dict)
