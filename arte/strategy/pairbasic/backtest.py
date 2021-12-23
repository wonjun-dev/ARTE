from timeit import timeit
import traceback

from tqdm import tqdm

from arte.data.test_data_loader import TestDataLoader
from arte.test_system import BackTestBinanceTradeManager
from arte.test_system import BatchBacktester
from strategy_loop import StrategyLoop

import time

DATA_PATH = "/Users/wonjun/Desktop/crypto_data"


class BackTester:
    def __init__(self, root_path, strategy_name, markets, sybmols, start_date, end_date):
        self.root_path = root_path
        self.strategy_name = strategy_name
        self.markets = markets
        self.symbols = sybmols
        self.tm = BackTestBinanceTradeManager(init_usdt=10000, max_order_count=1)
        self.strategy = StrategyLoop(trade_manager=self.tm)
        self.except_list = []

    def mainloop(self):
        try:
            self.tm.update(
                test_current_time=self.test_data_manager.current_time,
                future_prices=self.test_data_manager.binance_trade.price,
            )
            self.strategy.update(
                future_prices=self.test_data_manager.binance_trade,
                gamma=9.862,
                mu=8.373
            )
            self.strategy.run()

        except Exception:
            traceback.print_exc()

    def start(self, symbols, start_date, end_date):
        self.test_data_manager = TestDataLoader(DATA_PATH)
        self.test_data_manager.init_test_data_loader(
            symbols, start_date, end_date, ohlcv_interval=60000
        )
        self.strategy.initialize(symbols)

        for i in tqdm(range(self.test_data_manager.get_counter()), ncols=100):
            self.test_data_manager.load_next_by_counter(i)
            self.mainloop()

        return self.tm.end_bt()

if __name__ == "__main__":
    strategy_name = "pairbasic_baseline"
    start_date = "2021-11-19"
    end_date = "2021-12-18"
    symbols = ["ETC", "EOS"]

    bbt = BackTester(DATA_PATH, strategy_name, ["binance_futures"], symbols, start_date, end_date)
    saver = BatchBacktester(bbt, DATA_PATH, strategy_name, ["binance_futures"], symbols, start_date, end_date)

    import timeit

    st = timeit.default_timer()
    record = bbt.start(symbols, start_date, end_date)
    print(timeit.default_timer() - st)

    saver.save_records(record, start_date, end_date)
