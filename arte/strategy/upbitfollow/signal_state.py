import numpy as np
from transitions import Machine

from arte.system.utils import Timer


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
                "conditions": ["binance_price_up", "upbit_price_stay"], 
                # "conditions": ["premium_undershoot_mean"],
                "after": "buy_long",
            },
            # {
            #     "trigger": "proceed",
            #     "source": "sell_state",
            #     "dest": "sell_order_state",
            #     "conditions": ["price_decrease"],
            #     "after": "sell_long",
            # },
            {
                "trigger": "proceed",
                "source": "sell_state",
                "dest": "sell_order_state",
                "conditions": ["premium_converge"],
                "after": "sell_long",
            },
            {
                "trigger": "proceed",
                "source": "sell_state",
                "dest": "sell_order_state",
                "conditions": ["check_timeup"],
                "after": "sell_long",
            },
            {"trigger": "initialize", "source": "*", "dest": "idle"},  # , "before": "print_end"},
        ]
        m = Machine(
            model=self,
            states=SignalState.states,
            transitions=transitions,
            initial="idle",
            after_state_change="auto_proceed",
        )

        self.is_open = False
        self.premium_at_buy = None
        self.price_at_buy = None
        self.timer = Timer()

    def print_end(self, **kwargs):
        print(f"From {self.state} go back to Idle state.")

    def auto_proceed(self, **kwargs):
        if not self.state == "idle":
            if not self.proceed(**kwargs):
                self.initialize()

    def have_open_position(self, **kwargs):
        return self.is_open

    # Buy logic and ordering
    # def premium_over_threshold(self, **kwargs):
    #     premium = kwargs["premium_q"][-1]
    #     criteria_premium = kwargs["criteria_premium"]
    #     return premium > criteria_premium * 1.2

    def premium_undershoot_mean(self, **kwargs):
        premium_q = list(kwargs["premium_q"])
        change_rate = premium_q[-1] / (np.mean(premium_q[:9]))
        return change_rate < 0.7

    def binance_price_up(self, **kwargs):
        binance_price_q = kwargs["binance_price_q"]
        # change_rate = binance_price_q[-1] / binance_price_q[0]
        change_rate = binance_price_q[-1] / np.mean([binance_price_q[i] for i in range(0, 12)])
        return change_rate > 1.005

    def upbit_price_stay(self, **kwargs):
        price_q = kwargs["price_q"]
        # change_rate = price_q[-1] / price_q[0]
        change_rate = price_q[-1] / np.mean([price_q[i] for i in range(0, 16)])
        return change_rate < 1.001

    def buy_long(self, **kwargs):
        self.initialize()
        # print("Passed all signals, Order Buy long")
        if self.tm.buy_long_market(symbol=self.symbol, krw=100000):
            self.is_open = True
            self.premium_at_buy = kwargs["premium_q"][-1]
            self.premium_before_buy = np.mean(list(kwargs["premium_q"])[:5])
            # print(f"Premium at buy: {self.premium_at_buy}, before: {self.premium_before_buy}")
            # print(f'{kwargs["premium_q"]}')
            self.price_at_buy = kwargs["trade_price"]  # temp val - it need to change to result of order
            self.timer.start(kwargs["current_time"], "60S")

    # Sell logic and ordering
    def price_decrease(self, **kwargs):
        cur_price = kwargs["price_q"][-1]
        return cur_price < self.price_at_buy

    def premium_increase(self, **kwargs):
        premium_q = kwargs["premium_q"]
        return premium_q[-1] > (self.premium_at_buy * 1.2)

    def premium_converge(self, **kwargs):
        premium_q = kwargs["premium_q"]
        diff_premium = np.abs(premium_q[-1] - self.premium_before_buy)
        return diff_premium < 0.15

    def check_timeup(self, **kwargs):
        return self.timer.check_timeup(kwargs["current_time"])

    # def high_price(self, **kwargs):
    #     return kwargs["future_price"][self.symbol] > self.price_at_buy

    def sell_long(self, **kwargs):
        self.initialize()
        # print("Passed all signals, Order Sell long")
        if self.tm.sell_long_market(symbol=self.symbol, ratio=1):
            # print(f'{kwargs["premium_q"][-1]}')
            self.is_open = False
            self.premium_at_buy = None
            self.premium_before_buy = None
            self.price_at_buy = None
