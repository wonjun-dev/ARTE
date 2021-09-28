from collections import deque

from transitions import Machine

from arte.indicator import IndicatorManager
from arte.indicator import Indicator


def _symbolize_upbit(pure_symbol):
    return "KRW-" + pure_symbol.upper()


def _symbolize_binance(pure_symbol, upper=False):
    bsymbol = pure_symbol.lower() + "usdt"
    if upper:
        bsymbol = bsymbol.upper()
    return bsymbol


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
                "conditions": ["premium_overshoot_min", "upbit_price_up"],
                "after": "buy_long",
            },
            {
                "trigger": "proceed",
                "source": "sell_state",
                "dest": "sell_order_state",
                "conditions": ["premium_decrease"],
                "after": "sell_long",
            },
            {"trigger": "initialize", "source": "*", "dest": "idle", "before": "print_end"},
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

    def premium_overshoot(self, **kwargs):
        premium_q = kwargs["premium_q"]
        change_rate = (premium_q[-1] - premium_q[0]) / premium_q[0]
        return change_rate > 1.3

    def premium_overshoot_min(self, **kwargs):
        premium_q = kwargs["premium_q"]
        change_rate = premium_q[-1] / (min(premium_q[0:-1]))
        return change_rate > 1.4

    def upbit_price_up(self, **kwargs):
        price_q = kwargs["price_q"]
        change_rate = (price_q[-1] - price_q[0]) / price_q[0]  # price change rate in 20 sec
        return change_rate > 1.03

    def buy_long(self, **kwargs):
        print("Passed all signals, Order Buy long")
        self.tm.buy_long_market(symbol=self.symbol, price=kwargs["future_price"][self.symbol], usdt=10)
        self.is_open = True
        self.premium_at_buy = kwargs["premium_q"][-1]
        self.price_at_buy = kwargs["future_price"][self.symbol]  # temp val - it need to change to result of order
        self.initialize()

    # Sell logic and ordering
    def premium_decrease(self, **kwargs):
        premium_q = kwargs["premium_q"]
        return premium_q[-1] < (self.premium_at_buy * 0.9)

    # def high_price(self, **kwargs):
    #     return kwargs["future_price"][self.symbol] > self.price_at_buy

    def sell_long(self, **kwargs):
        print("Passed all signals, Order Sell long")
        self.tm.sell_long_market(symbol=self.symbol, ratio=1)
        self.is_open = False
        self.premium_at_buy = None
        self.price_at_buy = None
        self.initialize()


class ArbitrageBasic:
    """
    Upbit-Binance Pair Arbitrage 기초 전략
    """

    def __init__(self, trade_manager):
        self.tm = trade_manager
        self.im = IndicatorManager(indicators=[Indicator.PREMIUM])

        self.premium_threshold = 3
        self.premium_assets = []
        self.asset_signals = {}
        self.q_maxlen = 60
        self.init_price_counter = 0
        self.dict_price_q = {}
        self.dict_premium_q = {}

    def update(self, **kwargs):
        self.upbit_price = kwargs["upbit_price"]
        self.binance_spot_price = kwargs["binance_spot_price"]
        self.binance_future_price = kwargs["binance_future_price"]
        self.exchange_rate = kwargs["exchange_rate"]
        self.except_list = kwargs["except_list"]
        self.im.update_premium(self.upbit_price, self.binance_spot_price, self.exchange_rate)

    def initialize(self, common_binance_symbols, except_list):
        self.except_list = except_list
        self.pure_symbols_wo_excepted = []
        for symbol in common_binance_symbols:
            pure_symbol = symbol[:-4]
            if pure_symbol not in self.except_list:
                self.pure_symbols_wo_excepted.append(pure_symbol)

        for symbol in self.pure_symbols_wo_excepted:
            self.asset_signals[symbol] = SignalState(symbol=_symbolize_binance(symbol), tm=self.tm)
            self.dict_price_q[symbol] = deque(maxlen=self.q_maxlen)
            self.dict_premium_q[symbol] = deque(maxlen=self.q_maxlen)

    def run(self):
        # print(len(self.im[Indicator.PREMIUM][-1].keys()))
        # print(len(self.pure_symbols_wo_excepted))
        print(self.binance_future_price.price)
        btc_premium = self.im[Indicator.PREMIUM][-1]["BTCUSDT"]

        for symbol in self.pure_symbols_wo_excepted:
            self.dict_price_q[symbol].append(self.upbit_price.price[_symbolize_upbit(symbol)])
            self.dict_premium_q[symbol].append(self.im[Indicator.PREMIUM][-1][_symbolize_binance(symbol, upper=True)])
            self.init_price_counter += 1

        if self.init_price_counter == self.q_maxlen:
            for symbol in self.pure_symbols_wo_excepted:
                self.asset_signals[symbol].proceed(
                    premium_q=self.dict_premium_q[symbol],
                    criteria_premium=btc_premium,
                    price_q=self.dict_price_q[symbol],
                    future_price=self.binance_future_price.price[_symbolize_binance(symbol)],
                )
