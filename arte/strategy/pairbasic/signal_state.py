import numpy as np
from transitions import Machine
import transitions


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
                "conditions": ["spread_diverge"],
                "after": "open_position",
            },
            {
                "trigger": "proceed",
                "source": "sell_state",
                "dest": "sell_order_state",
                "conditions": ["spread_converge"],
                "after": "close_position",
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

    def auto_proceed(self, **kwargs):
        if not self.state == "idle":
            if not self.proceed(**kwargs):
                self.initialize()

    def have_open_position(self, **kwargs):
        return self.is_open

    # conditions
    def spread_diverge(self, **kwargs):
        pass

    def spread_converge(self, **kwargs):
        pass

    # order
    def open_position(self, **kwargs):
        pass

    def close_position(self, **kwargs):
        pass
