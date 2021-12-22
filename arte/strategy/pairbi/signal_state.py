import numpy as np
from transitions import Machine
from collections import deque

from arte.system.utils import Timer
from arte.system.utils import symbolize_upbit
from arte.system.utils import symbolize_binance


class SignalState:

    states = ["idle", "buy_state", "buy_order_state", "sell_state", "sell_order_state"]

    def __init__(self, symbol, tm_upbit, tm_binance):
        self.symbol = symbol
        self.tm_upbit = tm_upbit
        self.tm_binance = tm_binance
#작아지면 업ㅣ트 롱  바이난스 숏
        transitions = [
            {"trigger": "proceed", "source": "idle", "dest": "sell_state", "conditions": "have_open_position"},
            {"trigger": "proceed", "source": "idle", "dest": "buy_state"},
            {
                "trigger": "proceed",
                "source": "buy_state",
                "dest": "buy_order_state",
                "conditions": ["zscore_down"], 
                # "conditions": ["premium_undershoot_mean"],
                "after": "buy_long",
            },
            {
                "trigger": "proceed",
                "source": "sell_state",
                "dest": "sell_order_state",
                "conditions": ["zscore_comeback"],
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

    def halflife_valid(self, **kwargs):
        print(kwargs["half_life"])
        return kwargs["half_life"] > 180

    def zscore_down(self, **kwargs):
        spread = list(kwargs["spread"])
        #halflife = int(kwargs["half_life"])
        #spread = spread[-halflife:]
        zscore = (spread[-1]-np.mean(spread))/np.std(spread)
        print(zscore)
        return zscore < -4

    def zscore_comeback(self, **kwargs):
        
        spread = list(kwargs["spread"])
        #halflife = int(kwargs["half_life"])
        #spread = spread[-halflife:]
        zscore = (spread[-1]-np.mean(spread))/np.std(spread)
        return zscore >= 0
        
    def premium_undershoot_mean(self, **kwargs):
        premium_q = list(kwargs["premium_q"])
        change_rate = premium_q[-1] / (np.mean(premium_q[:9]))
        return change_rate < 0.7

    def binance_price_up(self, **kwargs):
        binance_price_q = kwargs["binance_price_q"]
        change_rate = binance_price_q[-1] / binance_price_q[0]
        # change_rate = binance_price_q[-1] / np.mean([binance_price_q[i] for i in range(3, 8)])
        return change_rate > 1.005

    def upbit_price_stay(self, **kwargs):
        price_q = kwargs["price_q"]
        change_rate = price_q[-1] / price_q[0]
        # change_rate = price_q[-1] / np.mean([price_q[i] for i in range(4, 9)])
        return change_rate < 1.001

    def buy_long(self, **kwargs):
        self.initialize()
        # print("Passed all signals, Order Buy long")
        if self.tm_upbit.buy_long_market(symbol=symbolize_upbit(self.symbol), krw=25000):
            self.is_open = True

        #self.tm_binance.buy_short_market(symbol=symbolize_binance(self.symbol), usdt=20)

    def sell_long(self, **kwargs):
        self.initialize()
        # print("Passed all signals, Order Sell long")
        if self.tm_upbit.sell_long_market(symbol=symbolize_upbit(self.symbol), ratio=1):
            # print(f'{kwargs["premium_q"][-1]}')
            self.is_open = False

        #self.tm_binance.sell_short_market(symbol=symbolize_binance(self.symbol), ratio=1)
