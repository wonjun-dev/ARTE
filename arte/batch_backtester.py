import os
import gc
import copy

import pandas as pd

from arte.system.utils import generate_intervals, random_choice


class BatchBacktester:
    def __init__(self, main_loop, root_path, strategy_name, markets, symbols, start_date, end_date):
        self.main_loop = main_loop
        self.root_path = root_path
        self.strategy_name = strategy_name
        self.markets = markets
        self.symbols = symbols
        self.wanted_date_range = set(
            [dt.strftime("%Y-%m-%d") for dt in pd.date_range(start=start_date, end=end_date, freq="D")]
        )

    def get_possible_date_range(self, symbol):
        symbol_dates = dict()
        for market in self.markets:
            _l = os.listdir(os.path.join(self.root_path, market, symbol))
            _dates = sorted([fname.split("-", 1)[1].split(".")[0] for fname in _l])
            symbol_dates[market] = _dates

        intersect_date_range = copy.copy(self.wanted_date_range)
        for _dates in symbol_dates.values():
            intersect_date_range = intersect_date_range & set(_dates)
        return intersect_date_range

    def start(self):
        possible_dates_symbols = dict()
        for symbol in self.symbols:
            possible_dates_symbols[symbol] = self.get_possible_date_range(symbol)

        for symbol in self.symbols:
            if not possible_dates_symbols[symbol]:
                print(f"There is no possible dates for {symbol}. Break.")
                break
            else:
                pos_dates = sorted(list(possible_dates_symbols[symbol]))
                start_date = pos_dates[0]
                end_date = pos_dates[-1]
                periods = (len(pos_dates) // 7) + 1
                backtest_id = f'{self.strategy_name}_{start_date.replace("-", "")[2:]}-{end_date.replace("-", "")[2:]}_{random_choice()}'
                self.main_loop.__init__(backtest_id=backtest_id)
                intervals = generate_intervals(start_date, end_date, periods)
                print(
                    f"Start Backtest of {symbol}. date range is from {start_date} to {end_date}. By {periods} divided manner"
                )
                for intv in intervals:
                    gc.collect()  # prevent memory explosion
                    print(intv)
                    self.main_loop.start([symbol], intv[0], intv[1])
