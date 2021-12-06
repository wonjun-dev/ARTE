import os
import copy
from datetime import datetime
import functools
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

import pandas as pd

from arte.system.utils import generate_intervals, random_choice

TEST_DB_PATH = "./test_db"

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
        self.n_cpu = multiprocessing.cpu_count()

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
                actual_start_date = pos_dates[0]
                actual_end_date = pos_dates[-1]
                periods = self.n_cpu # (len(pos_dates) // 7) + 1
                
                
                intervals = generate_intervals(actual_start_date, actual_end_date, periods)
                print(
                    f"Start Backtest of {symbol}. date range is from {actual_start_date} to {actual_end_date}. By {periods} divided manner"
                )
                print(intervals)
                
                full_records = []
                
                partial_start = functools.partial(self.main_loop.start, [symbol])
                with ProcessPoolExecutor(max_workers=self.n_cpu) as executor:
                    records = executor.map(partial_start, intervals)
                    for record in records:
                        full_records += record

                self.save_records(full_records, actual_start_date, actual_end_date)

    def save_records(self, full_records, start_date, end_date):
        symbol = full_records[0]["symbol"]
        backtest_id = f'{self.strategy_name}-{start_date.replace("-", "")[2:]}_{end_date.replace("-", "")[2:]}_{random_choice()}'
        dirpath = os.path.join(TEST_DB_PATH, f"{backtest_id.split('-')[0]}_{datetime.today().strftime('%Y%m%d')}")
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        fpath = os.path.join(dirpath, f"BT_{symbol}_{backtest_id}.csv")

        df = pd.DataFrame(full_records, columns=list(full_records[0].keys()))
        df.sort_values(by=['updateTime'], inplace=True)
        df.to_csv(fpath, index=False)