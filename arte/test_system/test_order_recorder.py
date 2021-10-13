"""
오더를 레코드 합니다.
"""

import os
import csv
from datetime import datetime

from arte.test_system.test_realized_pnl import TestRealizedPnl


class TestOrderRecorder:
    def __init__(self):
        if not os.path.exists("./arte/test_system/db"):
            os.makedirs("./arte/test_system/db")

        self.order_fields = [
            "symbol",
            "clientOrderId",
            "updateTime",
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

        self.test_realized_pnl = TestRealizedPnl()
        self.start_date = datetime.today().strftime("%Y%m%d%H%M")

    def test_order_to_order_dict(self, order, test_current_time):
        # test order class to dict(event_dict)
        event_dict = dict(item for item in order.__dict__.items())
        order_dict = {}

        # get basic data from orderUpdate event
        for key in event_dict.keys():
            if key in self.order_fields:
                order_dict[key] = event_dict[key]

        # USDT qunatity calc
        order_dict["USDT_Qty"] = round(order_dict["origQty"] * order_dict["avgPrice"], 4)

        # making side - positionSide - type data
        if order.positionSide == "LONG":
            order_dict["side_positionSide_type"] = (
                event_dict["side"] + "_" + event_dict["positionSide"] + "_" + event_dict["type"]
            )
        elif order.positionSide == "SHORT":
            if order.side == "SELL":  # open short position
                order_dict["side_positionSide_type"] = "BUY_" + event_dict["positionSide"] + "_" + event_dict["type"]
            elif order.side == "BUY":  # close short position
                order_dict["side_positionSide_type"] = "SELL_" + event_dict["positionSide"] + "_" + event_dict["type"]

        # commisionAmount calc
        if order.type == "MARKET":
            order_dict["commissionAmount"] = order_dict["USDT_Qty"] * 0.0004
        else:
            order_dict["commissionAmount"] = order_dict["USDT_Qty"] * 0.0002

        # calc PNL and Profit
        self.test_realized_pnl.proceeding(order, order_dict["commissionAmount"])

        # PNL calc
        order_dict["realized_pnl"] = round(self.test_realized_pnl.pnl_dict[order.symbol]["realized_pnl"], 8)
        order_dict["total_realized_pnl"] = round(self.test_realized_pnl.pnl_dict[order.symbol]["total_realized_pnl"], 8)
        order_dict["ROE_pnl"] = round(self.test_realized_pnl.pnl_dict[order.symbol]["realized_pnl_rate"], 8)
        order_dict["win_rate_pnl"] = round(self.test_realized_pnl.pnl_dict[order.symbol]["winrate_pnl"], 8)

        # Profit calc incl commission
        order_dict["real_profit"] = round(self.test_realized_pnl.pnl_dict[order.symbol]["real_profit"], 8)
        order_dict["total_real_profit"] = round(self.test_realized_pnl.pnl_dict[order.symbol]["total_real_profit"], 8)
        order_dict["ROE_profit"] = round(self.test_realized_pnl.pnl_dict[order.symbol]["real_profit_rate"], 8)
        order_dict["win_rate_profit"] = round(self.test_realized_pnl.pnl_dict[order.symbol]["winrate_profit"], 8)

        # reset if all sold
        if self.test_realized_pnl.pnl_dict[order.symbol]["quantity"] == 0:
            self.test_realized_pnl.close_position(order.symbol)

        # test current time
        order_dict["updateTime"] = test_current_time

        # update_csv
        self.update_csv(self.start_date, order_dict)

    def update_csv(self, start_date: str, order_dict: dict):
        symbol = order_dict["symbol"]
        path = f"./arte/test_system/db/Test_{symbol}_{start_date}.csv"
        with open(path, "a", newline="") as f_object:
            writer_object = csv.DictWriter(f_object, fieldnames=self.order_fields)
            if os.stat(path).st_size == 0:
                writer_object.writeheader()
            writer_object.writerow(order_dict)
