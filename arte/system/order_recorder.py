"""
오더를 레코드 합니다.
"""

import os
import csv

from collections import namedtuple


class OrderRecorder:
    def __init__(self):
        if not os.path.exists("./db"):
            os.makedirs("./db")
        self.pair_dict = {}

    def get_event(self, event):
        if event.orderStatus == "NEW":
            self.pair_dict[event.clientOrderId] = {"beforeFill": event, "afterFill": None}
        elif event.orderStatus == "FILLED":
            self.pair_dict[event.clientOrderId]["afterFill"] = event

    def update_csv(self, event):
        order_dict = dict(x for x in event.__dict__.items())
        fields = order_dict.keys()
        with open("./db/order_5m.csv", "a", newline="") as f_object:
            writer_object = csv.DictWriter(f_object, fieldnames=fields)
            if os.stat("./db/order_5m.csv").st_size == 0:
                writer_object.writeheader()
            writer_object.writerow(order_dict)
            f_object.close()
