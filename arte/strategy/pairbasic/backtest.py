from timeit import timeit
import traceback

from tqdm import tqdm

from arte.data.test_data_loader import TestDataLoader
from arte.test_system import BackTestBinanceTradeManager
from arte.test_system import BatchBacktester
from strategy_loop import StrategyLoop

DATA_PATH = ""


class BackTester:
    def __init__(self):
        self.tm = BackTestBinanceTradeManager(init_usdt=10000, max_order_count=1)
        self.strategy = StrategyLoop(trade_manager=self.tm)
        self.except_list = []

    def mainloop(self):
        try:
            self.tm.update(
                test_current_time=self.test_data_manager.current_time,
                trade_prices=self.test_data_manager.binance_trade.price,
                last_askbid=None,
            )
            self.strategy.update()
            self.strategy.run()

        except Exception:
            traceback.print_exc()

    def start(self, symbols, date_range):
        self.test_data_manager = TestDataLoader(DATA_PATH)
        self.test_data_manager.init_test_data_loader(
            symbols, date_range[0], date_range[1], ohlcv_interval=1000
        )
        self.strategy.initialize(symbols, self.except_list)

        for i in tqdm(range(self.test_data_manager.get_counter()), ncols=100):
            self.test_data_manager.load_next_by_counter(i)
            self.mainloop()

        return self.tm.end_bt()

    if __name__ == "__main__":
        strategy_name = "pairbasic_baseline"
        start_date = ""
        end_date = ""
        symbols = [""]

        bbt = BatchBacktester(
            BackTester(),
            DATA_PATH,
            strategy_name,
            ["binance_future"],
            symbols,
            start_date,
            end_date,
        )

        import timeit

        st = timeit.default_timer()
        bbt.start()
        print(timeit.default_timer() - st)
