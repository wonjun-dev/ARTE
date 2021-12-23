import numpy as np
from transitions import Machine
import transitions

from arte.system.utils import symbolize_binance

class SignalState:

    states = ["idle", "buy_state", "buy_order_state", "sell_state", "sell_order_state"]

    def __init__(self, symbols, tm):
        self.symbols = symbols
        self.symbol_A = self.symbols[0]
        self.symbol_B = self.symbols[1]
        # self.symbol_A = symbolize_binance(self.pure_symbol_A)
        # self.symbol_B = symbolize_binance(self.pure_symbol_B)
        self.tm = tm

        transitions = [
            {"trigger": "proceed", "source": "idle", "dest": "sell_state", "conditions": "have_open_position", "after": "print_state"},
            {"trigger": "proceed", "source": "idle", "dest": "buy_state", "after": "print_state"},
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
        self.spread_at_buy = None
        self.price_at_buy = {symbol: None for symbol in self.symbols}
        self.positions = {symbol: None for symbol in self.symbols}

    def auto_proceed(self, **kwargs):
        if not self.state == "idle":
            if not self.proceed(**kwargs):
                self.initialize()

    def have_open_position(self, **kwargs):
        return self.is_open

    # conditions
    def spread_diverge(self, **kwargs):
        spread_q = kwargs["spread_q"]
        threshold = kwargs["threshold"]
        return abs(spread_q[-1]) > threshold

    def spread_converge(self, **kwargs):
        spread_q = kwargs["spread_q"]
        eps = 0.001
        return abs(spread_q[-1]) < eps

    # order
    def open_position(self, **kwargs):
        self.initialize()
        spread_q = kwargs["spread_q"]
        dict_price_q = kwargs["dict_price_q"]
        # gamma = kwargs["gamma"]
        symbol_A_price = dict_price_q[self.symbol_A][-1]
        symbol_B_price = dict_price_q[self.symbol_B][-1]

        if spread_q[-1] > 0:
            if self.tm.buy_long_market(symbol=self.symbol_B, usdt=20) and self.tm.buy_short_market(symbol=self.symbol_A, usdt=20):
                self.is_open = True
                self.spread_at_buy = spread_q[-1]
                self.price_at_buy[self.symbol_A] = symbol_A_price
                self.price_at_buy[self.symbol_B] = symbol_B_price
                self.positions[self.symbol_A] = 'SHORT'
                self.positions[self.symbol_B] = 'LONG'

        else:
            if self.tm.buy_long_market(symbol=self.symbol_A, usdt=20) and self.tm.buy_short_market(symbol=self.symbol_B, usdt=20):
                self.is_open = True
                self.spread_at_buy = spread_q[-1]
                self.price_at_buy[self.symbol_A] = symbol_A_price
                self.price_at_buy[self.symbol_B] = symbol_B_price
                self.positions[self.symbol_A] = 'LONG'
                self.positions[self.symbol_B] = 'SHORT'


    def close_position(self, **kwargs):
        self.initialize()
        if self.positions[self.symbol_A] == "LONG":
            if self.tm.sell_long_market(symbol=self.symbol_A, ratio=1) and self.tm.sell_short_market(symbol=self.symbol_B, ratio=1):
                self.is_open = False
                self.spread_at_buy = None
                self.price_at_buy[self.symbol_A] = None
                self.price_at_buy[self.symbol_B] = None
                self.positions[self.symbol_A] = None
                self.positions[self.symbol_B] = None
        else:
            if self.tm.sell_long_market(symbol=self.symbol_B, ratio=1) and self.tm.sell_short_market(symbol=self.symbol_A, ratio=1):
                self.is_open = False
                self.spread_at_buy = None
                self.price_at_buy[self.symbol_A] = None
                self.price_at_buy[self.symbol_B] = None
                self.positions[self.symbol_A] = None
                self.positions[self.symbol_B] = None


    def print_state(self, **kwargs):
        spread_q = kwargs["spread_q"]
        print(f"Spread: {spread_q[-1]} Is open: {self.is_open}")