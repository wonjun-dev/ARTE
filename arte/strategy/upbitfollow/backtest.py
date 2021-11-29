import os
import glob
import traceback

from tqdm import tqdm

from arte.data.common_symbol_collector import CommonSymbolCollector

from arte.data.test_data_loader import TestDataLoader

from arte.test_system_upbit import TestUpbitTradeManager
from arte.strategy.upbitfollow.strategy import ArbitrageBasic
from arte.system.batch_backtester import BatchBacktester

DATA_PATH = "/home/park/Projects/data"


class TestMainloop:
    def __init__(self, **kwargs):
        self.symbol_collector = CommonSymbolCollector()

        self.backtest_id = None
        if "backtest_id" in kwargs:
            self.backtest_id = kwargs["backtest_id"]

        self.tm = TestUpbitTradeManager(init_krw=400000, max_order_count=3, backtest_id=self.backtest_id)
        self.strategy = ArbitrageBasic(trade_manager=self.tm)

        # self.common_symbols = self.symbol_collector.get_future_symbol()
        self.except_list = []

    def mainloop(self):
        try:
            self.tm.update(
                test_current_time=self.test_data_manager.current_time,
                trade_prices=self.test_data_manager.upbit_trade.price,
                last_askbid=self.test_data_manager.upbit_last_askbid,
            )
            self.strategy.update(
                upbit_price=self.test_data_manager.upbit_trade,
                binance_spot_price=self.test_data_manager.binance_trade,
                exchange_rate=self.test_data_manager.exchange_rate,
                except_list=self.except_list,
                current_time=self.test_data_manager.current_time,
            )
            self.strategy.run()

        except Exception:
            traceback.print_exc()

    def start(self, symbols, start_date, end_date):
        self.test_data_manager = TestDataLoader(DATA_PATH)
        self.test_data_manager.init_test_data_loader(symbols, start_date, end_date, ohlcv_interval=1000)
        self.strategy.initialize(symbols, self.except_list)

        for i in tqdm(range(self.test_data_manager.get_counter()), ncols=100):
            self.test_data_manager.load_next_by_counter(i)
            self.mainloop()


if __name__ == "__main__":
    # selected_assets = 'BTC ETH BCH AAVE SOL LTC AXS ETC NEO DOT ATOM LINK QTUM OMG KAVA MANA EOS 1INCH ADA'
    # selected_assets = selected_assets.split(' ')

    strategy_name = "upbitfollow"
    start_date = "2021-10-01"
    end_date = "2021-10-31"
    symbols = ["AXS", "EOS", "SOL"]

    bbt = BatchBacktester(
        TestMainloop(), DATA_PATH, strategy_name, ["upbit", "binance_spot"], symbols, start_date, end_date
    )
    bbt.start()
