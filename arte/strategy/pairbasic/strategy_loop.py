from collections import deque

from arte.indicator import IndicatorManager
from arte.indicator import Indicator

from signal_state import SignalState

import time

class StrategyLoop:
    def __init__(self, trade_manager):
        self.tm = trade_manager
        self.im = IndicatorManager(indicators=[Indicator.SPREAD])

        self.spread_threshold = 0.7
        self.q_maxlen = 10
        self.dict_price_q = {}

    def initialize(self, symbols):
        self.symbols = symbols
        self.asset_signals = SignalState(symbols=self.symbols, tm=self.tm)
        self.spread_q = deque(maxlen=self.q_maxlen)

        for symbol in self.symbols:
            self.dict_price_q[symbol] = deque(maxlen=self.q_maxlen)

    def update(self, **kwargs):
        self.future_prices = kwargs["future_prices"].price
        self.symbol_A_price = self.future_prices[self.symbols[0]]
        self.symbol_B_price = self.future_prices[self.symbols[1]]
        self.gamma = kwargs["gamma"]
        self.mu = kwargs["mu"]
        self.im.update_spread(self.symbol_A_price, self.symbol_B_price, self.gamma, self.mu)

    def run(self):
        self.spread_q.append(self.im[Indicator.SPREAD][-1])

        for symbol in self.symbols:
            self.dict_price_q[symbol].append(self.future_prices[symbol])

        self.asset_signals.proceed(dict_price_q=self.dict_price_q, spread_q=self.spread_q, threshold=self.spread_threshold, gamma=self.gamma, mu=self.mu)