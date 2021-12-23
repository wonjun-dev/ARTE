import numpy as np
from transitions import Machine
from collections import deque

from arte.system.utils import Timer
from arte.system.utils import symbolize_upbit


class SignalState:

    states = ["idle", "buy_state", "buy_order_state", "sell_state", "sell_order_state"]

    def __init__(self, symbol, tm):
        self.symbol = symbol
        self.tm = tm
        transitions = [
            {"trigger": "proceed", "source": "idle", "dest": "sell_state", "conditions": "have_open_position"},
            {"trigger": "proceed", "source": "idle", "dest": "buy_state"},
            {
                "trigger": "proceed",
                "source": "buy_state",
                "dest": "buy_order_state",
                "conditions": ["buy_onetime"],
                "after": "buy_long",
            },
            {
                "trigger": "proceed",
                "source": "sell_state",
                "dest": "sell_order_state",
                "conditions": ["check_timeup"],
                "after": "sell_long",
            },
            {"trigger": "initialize", "source": "*", "dest": "idle"},
        ]
        m = Machine(
            model=self,
            states=SignalState.states,
            transitions=transitions,
            initial="idle",
            after_state_change="auto_proceed",
        )

        self.is_open = False
        self.buy_count = -1
        self.timer = Timer()

    def print_end(self, **kwargs):
        print(f"From {self.state} go back to Idle state.")

    def auto_proceed(self, **kwargs):
        if not self.state == "idle":
            if not self.proceed(**kwargs):
                self.initialize()

    def have_open_position(self, **kwargs):
        return self.is_open

    def check_timeup(self, **kwargs):
        return self.timer.check_timeup(kwargs["current_time"])

    def buy_onetime(self, **kwargs):
        return self.buy_count < 1

    def buy_long(self, **kwargs):
        self.initialize()
        print(f"Passed all signals, Order Buy long at {kwargs['current_time']}")
        if self.tm.buy_long_market(symbol=symbolize_upbit(self.symbol), krw=5200):
            self.is_open = True
            self.buy_count += 1
            self.timer.start(kwargs["current_time"], "15S")

    def sell_long(self, **kwargs):
        self.initialize()
        print(f"Passed all signals, Order Sell long at {kwargs['current_time']}")
        if self.tm.sell_long_market(symbol=symbolize_upbit(self.symbol), ratio=1):
            self.is_open = False
