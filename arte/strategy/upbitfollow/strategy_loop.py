from collections import deque

from arte.indicator import IndicatorManager
from arte.indicator import Indicator
from arte.system.utils import symbolize_upbit

from signal_state import SignalState


class StrategyLoop:
    def __init__(self, trade_manager):
        self.tm = trade_manager
        self.im = IndicatorManager(indicators=[Indicator.PREMIUM])

        self.premium_threshold = 3
        self.premium_assets = []
        self.asset_signals = {}
        self.q_maxlen = 20
        self.dict_price_q = {}
        self.dict_binance_price_q = {}
        self.dict_premium_q = {}

    def initialize(self, common_symbols, except_list):
        self.init_price_counter = 0
        self.except_list = except_list
        self.symbols_wo_excepted = []
        for symbol in common_symbols:
            if symbol not in self.except_list:
                self.symbols_wo_excepted.append(symbol)

        for symbol in self.symbols_wo_excepted:
            self.asset_signals[symbol] = SignalState(symbol=symbolize_upbit(symbol), tm=self.tm)
            self.dict_price_q[symbol] = deque(maxlen=self.q_maxlen)
            self.dict_binance_price_q[symbol] = deque(maxlen=self.q_maxlen)
            self.dict_premium_q[symbol] = deque(maxlen=self.q_maxlen)

    def update(self, **kwargs):
        self.upbit_price = kwargs["upbit_price"]
        self.binance_spot_price = kwargs["binance_spot_price"]
        self.exchange_rate = kwargs["exchange_rate"]
        self.except_list = kwargs["except_list"]
        self.current_time = kwargs["current_time"]
        self.im.update_premium(self.upbit_price, self.binance_spot_price, self.exchange_rate)

    def run(self):
        self.init_price_counter += 1
        for symbol in self.symbols_wo_excepted:
            self.dict_price_q[symbol].append(self.upbit_price.price[symbol])
            self.dict_binance_price_q[symbol].append(self.binance_spot_price.price[symbol])
            self.dict_premium_q[symbol].append(self.im[Indicator.PREMIUM][-1][symbol])

        if self.init_price_counter >= self.q_maxlen:
            for symbol in self.symbols_wo_excepted:
                self.asset_signals[symbol].proceed(
                    premium_q=self.dict_premium_q[symbol],
                    price_q=self.dict_price_q[symbol],
                    binance_price_q=self.dict_binance_price_q[symbol],
                    trade_price=self.upbit_price.price[symbol],
                    current_time=self.current_time,
                )

    def print_state(self):
        print(f'Upbit: {self.upbit_price.price}')
        print(f'Bspot: {self.binance_spot_price.price}')