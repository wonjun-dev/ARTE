from collections import deque
from pandas.core.frame import DataFrame
import statsmodels.api as sm
import numpy as np
import pandas as pd

from arte.indicator import IndicatorManager
from arte.indicator import Indicator
from arte.system.utils import symbolize_upbit

from signal_state import SignalState
from kalman_avg import KalmanAvg
from kalman_reg import KalmanReg



class StrategyLoop:
    def __init__(self, trade_manager_upbit, trade_manager_binance):
        self.tm_upbit = trade_manager_upbit
        self.tm_binance = trade_manager_binance
        self.im = IndicatorManager(indicators=[Indicator.PREMIUM])

        self.premium_threshold = 3
        self.premium_assets = []
        self.asset_signals = {}
        self.q_maxlen = 18000
        self.dict_price_q = {}
        self.dict_binance_price_q = {}

        self.kalman_avg_upbit = {}
        self.kalman_avg_binance = {}
        self.kalman_reg = {}
        self.spread = {}

    def initialize(self, common_symbols, except_list):
        self.init_price_counter = 0
        self.except_list = except_list
        self.symbols_wo_excepted = []
        for symbol in common_symbols:
            if symbol not in self.except_list:
                self.symbols_wo_excepted.append(symbol)

        for symbol in self.symbols_wo_excepted:
            self.asset_signals[symbol] = SignalState(symbol=symbol, tm_upbit=self.tm_upbit, tm_binance=self.tm_binance)
            self.dict_price_q[symbol] = deque(maxlen=self.q_maxlen)
            self.dict_binance_price_q[symbol] = deque(maxlen=self.q_maxlen)

            self.kalman_avg_upbit[symbol] = KalmanAvg(maxlen=self.q_maxlen)
            self.kalman_avg_binance[symbol] = KalmanAvg(maxlen=self.q_maxlen)
            self.kalman_reg[symbol] = KalmanReg(maxlen=self.q_maxlen)
            self.spread[symbol] = deque(maxlen=self.q_maxlen)

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

            if self.init_price_counter ==1:
                self.kalman_avg_upbit[symbol].initialize(self.upbit_price.price[symbol])
                self.kalman_avg_binance[symbol].initialize(self.binance_spot_price.price[symbol])
                self.kalman_reg[symbol].initialize( self.kalman_avg_upbit[symbol].his_state_means[-1][0], self.kalman_avg_binance[symbol].his_state_means[-1][0] )
            else:
                self.kalman_avg_upbit[symbol].update(self.upbit_price.price[symbol])
                self.kalman_avg_binance[symbol].update(self.binance_spot_price.price[symbol])
                self.kalman_reg[symbol].update( self.kalman_avg_upbit[symbol].his_state_means[-1][0], self.kalman_avg_binance[symbol].his_state_means[-1][0] )
            self.spread[symbol].append( self.upbit_price.price[symbol]*self.kalman_reg[symbol].his_state_means[-1,0] - self.binance_spot_price.price[symbol] )

        if self.init_price_counter >= self.q_maxlen:
            for symbol in self.symbols_wo_excepted:
                self.asset_signals[symbol].proceed(
                    price_q=self.dict_price_q[symbol],
                    binance_price_q=self.dict_binance_price_q[symbol],
                    current_time=self.current_time,
                    spread = self.spread[symbol],
                    #half_life = self.cal_half_life(self.spread[symbol])
                )

    def print_state(self):
        print(f'Upbit: {self.upbit_price.price}')
        print(f'Bspot: {self.binance_spot_price.price}')

    def cal_half_life(self, spread_deque):
    
        spread_df = pd.DataFrame()
        spread_df["spread"] = spread_deque
        spread = spread_df["spread"]
        spread_lag = spread.shift(1)
        spread_lag.iloc[0] = spread_lag.iloc[1]
        spread_ret = spread - spread_lag
        spread_ret.iloc[0] = spread_ret.iloc[1]
        spread_lag2 = sm.add_constant(spread_lag)
        model = sm.OLS(spread_ret,spread_lag2)
        res = model.fit()
        halflife = int(round(-np.log(2) / res.params[1],0))
        
        if halflife <= 0:
            halflife = 1
            
        return halflife