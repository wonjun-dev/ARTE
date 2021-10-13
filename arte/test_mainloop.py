import traceback
import time

from tqdm import tqdm

from arte.data.common_symbol_collector import CommonSymbolCollector

from arte.data.test_data_loader import TestDataLoader
from arte.test_system.test_trade_manager import TestTradeManager

from arte.strategy import ArbitrageBasic


class TestMainloop:
    """
    Class ArbiTrader:
        Arbi 거래 Backtest를 위한 모듈
        for문을 돌며 time_interval마다 mainloop를 실행시킴.

    Attributes:
        test_data_manager : 선언 시 data 절대 경로 필요

    Functions:
        mainloop : 실제 전략이 돌아가는 함수. start에서 정한 interval 마다 실행되는 함수
        start : Backtest를 위한 init_test_data_loader 함수를 호출하고, mainloop을 interval 마다 실행시킴.

    """

    def __init__(self):
        self.test_data_manager = TestDataLoader("/media/park/hard2000/data")
        self.symbol_collector = CommonSymbolCollector()

        self.tm = TestTradeManager(init_usdt=400, max_order_count=3)
        self.strategy = ArbitrageBasic(trade_manager=self.tm)

        # self.common_symbols = self.symbol_collector.get_future_symbol()
        self.except_list = []

    def mainloop(self):
        try:
            self.tm.update(
                test_current_time=self.test_data_manager.current_time,
                future_prices=self.test_data_manager.binance_trade.price,
            )
            self.strategy.update(
                upbit_price=self.test_data_manager.upbit_trade,
                binance_spot_price=self.test_data_manager.binance_trade,
                binance_future_price=self.test_data_manager.binance_trade,
                exchange_rate=self.test_data_manager.exchange_rate,
                except_list=self.except_list,
                current_time=self.test_data_manager.current_time,
            )
            self.strategy.run()

        except Exception:
            traceback.print_exc()

    def start(self, symbols, start_date, end_date):
        self.test_data_manager.init_test_data_loader(symbols, start_date, end_date, ohlcv_interval=1000)
        self.strategy.initialize(symbols, self.except_list)

        for i in tqdm(range(self.test_data_manager.get_counter()), ncols=100):
            self.test_data_manager.load_next_by_counter(i)
            self.mainloop()


if __name__ == "__main__":
    test_main_loop = TestMainloop()
    test_main_loop.start(["EOS", "BTC", "ETH"], "2021-10-01", "2021-10-04")
