"""
오더를 레코드 합니다.
"""
from collections import namedtuple


class OrderRecorder:
    def __init__(self):
        self.pair_dict = {}

    def get_event(self, event):
        if event.orderStatus == "NEW":
            self.pair_dict[event.clientOrderId] = {"beforeFill": event, "afterFill": None}
        elif event.orderStatus == "FILLED":
            self.pair_dict[event.clientOrderId]["afterFill"] = event
