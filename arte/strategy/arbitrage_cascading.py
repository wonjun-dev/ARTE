import numpy as np
from collections import deque
from pandas.core import series
from scipy import stats
from transitions import Machine

from arte.indicator import IndicatorManager
from arte.indicator import Indicator

from arte.system.utils import Timer
from statsmodels.tsa.stattools import coint


def _symbolize_binance(pure_symbol, upper=False):
    bsymbol = pure_symbol.lower() + "usdt"
    if upper:
        bsymbol = bsymbol.upper()
    return bsymbol


class SignalState:

    states = [
        "idle",
        "buy_long_c",
        "buy_short_c",
        "buy_long_v",
        "buy_short_v",
        "buy_long_order",
        "buy_short_order",
        "sell_long_c",
        "sell_short_c",
        "sell_long_stop",
        "sell_short_stop",
    ]

    def __init__(self, symbol, tm):
        self.symbol = symbol
        self.tm = tm

        transitions = [
            {"trigger": "proceed", "source": "idle", "dest": "buy_long_c", "conditions": ["order_state_valid_buy_long","z_score_valid","premium_overshoot_min" ]},
            {"trigger": "proceed", "source": "idle", "dest": "buy_short_c", "conditions": ["order_state_valid_buy_short","z_score_valid","premium_undershoot_min"]},
            {"trigger": "proceed", "source": "buy_long_c", "dest":"buy_long_order", "conditions": "upbit_price_up", "after":"buy_long"},
            {"trigger": "proceed", "source": "buy_short_c", "dest":"buy_short_order", "conditions": "upbit_price_down", "after":"buy_short"},
            {"trigger": "proceed", "source": "idle", "dest": "sell_long_c", "conditions":["order_state_valid_sell_long","premium_decrease"], "after":"sell_long"},
            {"trigger": "proceed", "source": "idle", "dest": "sell_short_c", "conditions":[ "order_state_valid_sell_short","premium_increase"], "after":"sell_short"},
            {"trigger": "proceed", "source": "idle", "dest": "sell_long_stop", "conditions":[ "order_state_valid_sell_long","stop_loss_long"], "after":"sell_long"},
            {"trigger": "proceed", "source": "idle", "dest": "sell_short_stop", "conditions":[ "order_state_valid_sell_short", "stop_loss_short"], "after":"sell_short"},
            {"trigger": "initialize", "source": "*", "dest": "idle"},  # , "before": "print_end"},
        ]
        m = Machine(
            model=self,
            states=SignalState.states,
            transitions=transitions,
            initial="idle",
            after_state_change="auto_proceed",
        )

        self.premium_at_buy = None
        self.price_at_buy = None
        self.order_state = 0
        #self.zscore = None

        # wallet status에 따라서
        # self.timer = Timer()

    def print_end(self, **kwargs):
        print(f"From {self.state} go back to Idle state.")

    def auto_proceed(self, **kwargs):
        if not self.state == "idle":
            if not self.proceed(**kwargs):
                self.initialize()

    def order_state_valid_buy_long(self, **kwargs):
        return (self.order_state >= 0)and(self.order_state<4)

    def order_state_valid_buy_short(self, **kwargs):
        return (self.order_state <= 0)and(self.order_state>-4)

    def order_state_valid_sell_long(self, **kwargs):
        return self.order_state >0

    def order_state_valid_sell_short(self, **kwargs):
        return self.order_state <0

    def z_score_valid(self, **kwargs):
        if self.symbol == _symbolize_binance("BTC"):
            return False
        _, pvalue, _ = coint(list(kwargs["premium_q"]), list(kwargs["criteria_premium_q"]))
        if pvalue < 0.05:
            return True
        else:
            return False

    def premium_overshoot_min(self, **kwargs):
        if kwargs["zscore"][-1] != None:
            return kwargs["zscore"][-1] >= (self.order_state +1)
        else:
            return False
        #premium_q = list(kwargs["premium_q"])
        #criteria_premium_q = list(kwargs["criteria_premium_q"])
        #premium_dif = premium_q[-1] - criteria_premium_q[-1]
        #return premium_dif > self.sigma * (self.order_state+1)

    def premium_undershoot_min(self, **kwargs):
        if kwargs["zscore"][-1] != None:
            return kwargs["zscore"][-1] <= (self.order_state-1)
        else:
            return False
        #premium_q = list(kwargs["premium_q"])
        #criteria_premium_q = list(kwargs["criteria_premium_q"])
        #premium_dif = premium_q[-1] - criteria_premium_q[-1]
        #return premium_dif < -self.sigma * (self.order_state+1)

    def upbit_price_up(self, **kwargs):
        price_q = kwargs["price_q"]
        change_rate = price_q[-1] / min(price_q)  # price change rate in 20 sec
        return change_rate > 1

    def upbit_price_down(self, **kwargs):
        price_q = kwargs["price_q"]
        change_rate = price_q[-1] / max(price_q)  # price change rate in 20 sec
        return change_rate < 1

    def buy_long(self, **kwargs):
        self.order_state += 1
        self.initialize()
        print("Passed all signals, Order Buy long")
        self.tm.buy_long_market(symbol=self.symbol, usdt=100)
        self.premium_at_buy = kwargs["premium_q"][-1]
        self.price_at_buy = kwargs["future_price"]  # temp val - it need to change to result of order
        # self.timer.start(kwargs["current_time"], "600s")

    def buy_short(self, **kwargs):
        self.order_state -= 1
        self.initialize()
        print("Passed all signals, Order Buy short")
        self.tm.buy_short_market(symbol=self.symbol, usdt=100)
        self.premium_at_buy = kwargs["premium_q"][-1]
        self.price_at_buy = kwargs["future_price"]  # temp val - it need to change to result of order
        # self.timer.start(kwargs["current_time"], "600s")

    # Sell logic and ordering
    def premium_decrease(self, **kwargs):
        if kwargs["zscore"][-1] != None:
            return kwargs["zscore"][-1] <= (self.order_state)
        else:
            return False
        #premium_q = list(kwargs["premium_q"])
        #criteria_premium_q = list(kwargs["criteria_premium_q"])
        #premium_dif = premium_q[-1] - criteria_premium_q[-1]
        #return premium_dif < self.sigma * (self.order_state)

    def premium_increase(self, **kwargs):
        if kwargs["zscore"][-1] != None:
            return kwargs["zscore"][-1] <= (self.order_state)
        else:
            return False
        #premium_q = list(kwargs["premium_q"])
        #criteria_premium_q = list(kwargs["criteria_premium_q"])
        #premium_dif = premium_q[-1] - criteria_premium_q[-1]
        #return premium_dif > -self.sigma * (self.order_state)

    # def check_timeup(self, **kwargs):
    #    return self.timer.check_timeup(kwargs["current_time"])

    # def high_price(self, **kwargs):
    #     return kwargs["future_price"][self.symbol] > self.price_at_buy

    def sell_long(self, **kwargs):
        self.order_state = 0
        self.initialize()
        print("Passed all signals, Order Sell long")
        self.tm.sell_long_market(symbol=self.symbol, ratio=1)
        #self.premium_at_buy = None
        #self.price_at_buy = None

    def sell_short(self, **kwargs):
        self.order_state = 0
        self.initialize()
        print("Passed all signals, Order Sell short")
        self.tm.sell_short_market(symbol=self.symbol, ratio=1)
        #self.premium_at_buy = None
        #self.price_at_buy = None

    def stop_loss_long(self, **kwargs):
        hard_stop_loss = kwargs["hard_stop_loss"]
        cur_price = kwargs["future_price"]

        if self.price_at_buy != None:
            pnl = (cur_price - self.price_at_buy) / self.price_at_buy
            return pnl < -hard_stop_loss
        else:
            return False

    def stop_loss_short(self, **kwargs):
        hard_stop_loss = kwargs["hard_stop_loss"]
        cur_price = kwargs["future_price"]

        if self.price_at_buy != None:
            pnl = -(cur_price - self.price_at_buy) / self.price_at_buy
            return pnl < -hard_stop_loss
        else:
            return False

class ArbitrageCascading:
    """
    Upbit-Binance Pair Arbitrage 기초 전략
    """

    def __init__(self, trade_manager):
        self.tm = trade_manager
        self.im = IndicatorManager(indicators=[Indicator.PREMIUM])

        self.premium_threshold = 3
        self.premium_assets = []
        self.asset_signals = {}
        self.q_maxlen = 20
        self.q_maxlen_kimp = 900
        self.init_price_counter = 0
        self.dict_price_q = {}
        self.dict_premium_q = {}

    def update(self, **kwargs):
        self.upbit_price = kwargs["upbit_price"]
        self.binance_spot_price = kwargs["binance_spot_price"]
        self.binance_future_price = kwargs["binance_future_price"]
        self.exchange_rate = kwargs["exchange_rate"]
        self.except_list = kwargs["except_list"]
        self.current_time = kwargs["current_time"]
        self.im.update_premium(self.upbit_price, self.binance_spot_price, self.exchange_rate)

    def initialize(self, common_symbols, except_list):
        self.except_list = except_list
        self.symbols_wo_excepted = []
        for symbol in common_symbols:
            if symbol not in self.except_list:
                self.symbols_wo_excepted.append(symbol)

        for symbol in self.symbols_wo_excepted:
            self.asset_signals[symbol] = SignalState(symbol=_symbolize_binance(symbol), tm=self.tm)
            self.dict_price_q[symbol] = deque(maxlen=self.q_maxlen)
            self.dict_premium_q[symbol] = deque(maxlen=self.q_maxlen_kimp)

    def run(self):
        for symbol in self.symbols_wo_excepted:
            self.dict_price_q[symbol].append(self.upbit_price.price[symbol])
            self.dict_premium_q[symbol].append(self.im[Indicator.PREMIUM][-1][symbol])
            self.init_price_counter += 1

        if self.init_price_counter >= self.q_maxlen_kimp:
            for symbol in self.symbols_wo_excepted:

                kimp_q = np.array(self.dict_premium_q[symbol]) - np.array(self.dict_premium_q["BTC"])
                #zscore = (kimp_q - kimp_q.mean()) / np.std(kimp_q)
                zscore = stats.zscore(kimp_q)
                self.asset_signals[symbol].proceed(
                    premium_q=self.dict_premium_q[symbol],
                    criteria_premium_q=self.dict_premium_q["BTC"],
                    price_q=self.dict_price_q[symbol],
                    future_price=self.binance_future_price.price[symbol],
                    current_time=self.current_time,
                    hard_stop_loss=0.03,
                    zscore = 0.5*zscore
                )
