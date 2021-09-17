from collections import deque

from transitions import Machine

from arte.indicator import Indicator
from arte.strategy.core.base_strategy import BaseStrategy


def _symbolize_upbit(symbol):
    return "KRW-" + symbol.upper()


def _symbolize_binance(symbol):
    return symbol.lower() + "usdt"


class SignalState:

    states = ["idle", "stg_1", "stg_order"]

    def __init__(self, symbol, manager):
        self.symbol = symbol
        self.manager = manager

        transitions = [
            {"trigger": "proceed", "source": "idle", "dest": "stg_1", "conditions": "premium_over_threshold"},
            {
                "trigger": "proceed",
                "source": "stg_1",
                "dest": "stg_order",
                "conditions": "upbit_price_up",
                "after": "go_order",
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

    def print_end(self, **kwargs):
        print(f"From {self.state} go back to Idle state.")

    def auto_proceed(self, **kwargs):
        if not self.state == "idle":
            if not self.proceed(**kwargs):
                self.initialize()

    def premium_over_threshold(self, **kwargs):
        premium = kwargs["premium"]
        criteria_premium = kwargs["criteria_premium"]
        return premium > criteria_premium * 1.2

    def upbit_price_up(self, **kwargs):
        price_q = kwargs["price_q"]
        change_rate = (price_q[-1] - price_q[-40]) / price_q[-40]  # price change rate in 20 sec
        return change_rate > 1.03

    def go_order(self, **kwargs):
        print("Passed all signals, Ordering start...")
        self.manager.buy_long_market(price=kwargs["future_price"][self.symbol], usdt=100)
        self.initialize()


class ArbitrageBasic(BaseStrategy):
    """
    Upbit-Binance Pair Arbitrage 기초 전략
    """

    def __init__(self, indicator_manager, buy_ratio: float = 0.15, sell_ratio: float = 1.0):
        self.im = indicator_manager
        self.BUY_RATIO = buy_ratio
        self.SELL_RATIO = sell_ratio
        self.manager = None

        self.premium_threshold = 2.5
        self.premium_assets = []
        self.asset_signals = {}
        self.q_maxlen = 100
        self.init_price_counter = 0
        self.dict_price_q = {}

    def run(self, **kwargs):
        self.upbit_price = kwargs["upbit_price"]
        self.binance_spot_price = kwargs["binance_spot_price"]
        self.binance_future_price = kwargs["binance_future_price"]
        self.exchange_rate = kwargs["exchange_rate"]
        self.except_list = kwargs["except_list"]
        self.bot = kwargs["bot"]
        self.im.update_premium(self.upbit_price, self.binance_spot_price, self.exchange_rate)

    def initialize_strategy(self, common_binance_symbols, except_list):
        self.except_list = except_list
        self.pure_symbols_wo_excepted = []
        for symbol in common_binance_symbols:
            pure_symbol = symbol[:-4]
            if pure_symbol not in self.except_list:
                self.pure_symbols_wo_excepted.append(pure_symbol)

        for symbol in self.pure_symbols_wo_excepted:
            self.asset_signals[symbol] = SignalState(symbol=symbol + "usdt", manager=self.manager)
            self.dict_price_q[symbol] = deque(maxlen=self.q_maxlen)

    def run_strategy(self):
        premium_dict = self.im[Indicator.PREMIUM][-1]
        btc_premium = premium_dict["btcusdt"]

        for symbol in self.pure_symbols_wo_excepted:
            self.dict_price_q[symbol].append(self.upbit_price.price[_symbolize_upbit(symbol)])
            self.init_price_counter += 1

        if self.init_price_counter == self.q_maxlen:
            for symbol in self.pure_symbols_wo_excepted:
                bi_full_symbol = _symbolize_binance(symbol)
                self.asset_signals[symbol].proceed(
                    premium=premium_dict[bi_full_symbol],
                    criteria_premium=btc_premium,
                    price_q=self.dict_price_q[symbol],
                    future_price=self.binance_future_price.price[bi_full_symbol],
                )
