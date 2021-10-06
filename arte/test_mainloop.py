import traceback
import time

from arte.data.common_symbol_collector import CommonSymbolCollector

from arte.test_system.test_data_loader import TestDataLoader
from arte.test_system.test_trade_manager import TestTradeManager

from arte.strategy import ArbitrageBasic


class TestMainloop:
    def __init__(self):
        self.test_data_manager = TestDataLoader("D:\\12days\\data")
        self.symbol_collector = CommonSymbolCollector()

        self.tm = TestTradeManager(init_usdt=1000, max_order_count=3)
        self.strategy = ArbitrageBasic(trade_manager=self.tm)

        # self.upbit_symbols, self.binance_symbols = self.symbol_collector.get_future_symbol()
        self.except_list = []
        self.exchange_rate = 1188.7

    def mainloop(self):
        try:
            # print(self.test_data_manager.current_time)
            self.strategy.update(
                upbit_price=self.test_data_manager.upbit_trade,
                binance_spot_price=self.test_data_manager.binance_trade,
                binance_future_price=self.test_data_manager.binance_trade,
                exchange_rate=self.exchange_rate,
                except_list=self.except_list,
            )
            self.strategy.run()

        except Exception:
            traceback.print_exc()

    def start(self, symbols, start_date, end_date):
        self.test_data_manager.init_test_data_loader(symbols, start_date, end_date)
        usdt_symbol = [symbol + "USDT" for symbol in symbols]
        self.strategy.initialize(usdt_symbol, self.except_list)

        cur_t = time.time()
        while 1:
            if self.test_data_manager.load_next() == False:
                break
            self.mainloop()
        print(time.time() - cur_t)


if __name__ == "__main__":
    test_main_loop = TestMainloop()
    test_main_loop.start(["EOS", "BTC"], "2021-10-04", "2021-10-04")
