import pandas as pd
import os
from datetime import datetime, timedelta

from arte.data.trade_parser import TradeParser
from arte.test_system.grouping import make_group


class TestDataLoader:
    def __init__(self, root_data_path):
        self.root_data_path = root_data_path
        self.upbit_ohlcv = dict()
        self.binance_ohlcv = dict()

        self.upbit_ohlcv_list = dict()
        self.binance_ohlcv_list = dict()

    def init_test_data_loader(self, symbols, start_date, end_date, freq="250ms"):

        self.symbols = [symbol.upper() for symbol in symbols]
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.freq = freq

        # self.upbit_symbols = ["KRW-" + symbol for symbol in symbols]
        # self.binance_symbols = [symbol + "USDT" for symbol in symbols]

        self.upbit_trade = TradeParser(symbols=self.symbols)
        self.binance_trade = TradeParser(symbols=self.symbols)

        self.init_upbit_test_loader()
        self.init_binance_test_loader()

        self.current_time = pd.to_datetime(start_date)
        self.end_current_time = pd.to_datetime(end_date) + timedelta(days=1)
        self.count = 0

        for symbol in self.symbols:
            self.upbit_ohlcv_list[symbol] = self.upbit_ohlcv[symbol].to_dict("records")
            self.binance_ohlcv_list[symbol] = self.binance_ohlcv[symbol].to_dict("records")

        print("Complete Data Loading")

    def init_upbit_test_loader(self):
        for symbol in self.symbols:
            trade_df = self.load_trade_data(symbol, is_upbit=True)
            self.upbit_convert_to_ohlcv(symbol, trade_df)

    def upbit_convert_to_ohlcv(self, symbol, upbit_trade_df):
        gp = make_group(upbit_trade_df, freq=self.freq)
        self.upbit_ohlcv[symbol] = gp["price"].ohlc()
        self.upbit_ohlcv[symbol]["volume"] = gp["quantity"].sum()
        self.upbit_ohlcv[symbol]["trade_num"] = gp["trade_num"].sum()

        self.upbit_ohlcv[symbol].fillna(
            dict.fromkeys(self.upbit_ohlcv[symbol].columns.tolist(), self.upbit_ohlcv[symbol].close.ffill()),
            inplace=True,
        )

        start_stamp = pd.to_datetime(self.start_date)
        end_stamp = self.upbit_ohlcv[symbol].index[0]
        temp = self.upbit_ohlcv[symbol].iloc[0]["open"]

        while start_stamp < end_stamp:
            self.upbit_ohlcv[symbol].loc[start_stamp] = [temp, temp, temp, temp, 0.0, 0]
            start_stamp += timedelta(milliseconds=250)

        self.upbit_ohlcv[symbol].sort_index(inplace=True)

        start_stamp = self.upbit_ohlcv[symbol].index[-1] + timedelta(milliseconds=250)
        end_stamp = pd.to_datetime(self.end_date) + timedelta(days=1)
        temp = self.upbit_ohlcv[symbol].iloc[-1]["close"]

        while start_stamp < end_stamp:
            self.upbit_ohlcv[symbol].loc[start_stamp] = [temp, temp, temp, temp, 0.0, 0]
            start_stamp += timedelta(milliseconds=250)

    def init_binance_test_loader(self):
        for symbol in self.symbols:
            trade_df = self.load_trade_data(symbol, is_upbit=False)
            self.binance_conver_to_ohlcv(symbol, trade_df)

    def binance_conver_to_ohlcv(self, symbol, binance_trade_df):
        gp = make_group(binance_trade_df, freq=self.freq)
        self.binance_ohlcv[symbol] = gp["price"].ohlc()
        self.binance_ohlcv[symbol]["volume"] = gp["quantity"].sum()
        self.binance_ohlcv[symbol]["trade_num"] = gp["trade_num"].sum()

        self.binance_ohlcv[symbol].fillna(
            dict.fromkeys(self.binance_ohlcv[symbol].columns.tolist(), self.binance_ohlcv[symbol].close.ffill()),
            inplace=True,
        )

        start_stamp = pd.to_datetime(self.start_date)
        end_stamp = self.binance_ohlcv[symbol].index[0]
        temp = self.binance_ohlcv[symbol].iloc[0]["open"]

        while start_stamp < end_stamp:
            self.binance_ohlcv[symbol].loc[start_stamp] = [temp, temp, temp, temp, 0.0, 0]
            start_stamp += timedelta(milliseconds=250)

        self.binance_ohlcv[symbol].sort_index(inplace=True)

        start_stamp = self.binance_ohlcv[symbol].index[-1] + timedelta(milliseconds=250)
        end_stamp = pd.to_datetime(self.end_date) + timedelta(days=1)
        temp = self.binance_ohlcv[symbol].iloc[-1]["close"]

        while start_stamp < end_stamp:
            self.binance_ohlcv[symbol].loc[start_stamp] = [temp, temp, temp, temp, 0.0, 0]
            start_stamp += timedelta(milliseconds=250)

    def load_trade_data(self, symbol, is_upbit):

        if is_upbit:
            market_path = "upbit"
        else:
            market_path = "binance_spot"

        trade_dataframe_list = []
        current_date = self.start_date

        while current_date <= self.end_date:
            file_path = os.path.join(
                self.root_data_path,
                market_path,
                symbol,
                f"{symbol}-"
                + "{0:04d}-{1:02d}-{2:02d}.csv".format(current_date.year, current_date.month, current_date.day),
            )

            try:
                current_df = pd.read_csv(file_path)

            except:
                print(f"Error : Do not exist {file_path}!\n")
                break

            trade_dataframe_list.append(current_df)
            current_date += timedelta(days=1)

        output_df = pd.concat(trade_dataframe_list)
        output_df.reset_index(drop=True, inplace=True)

        output_df["trade_num"] = [1] * len(output_df)

        return output_df

    def load_next(self):

        if self.current_time < self.end_current_time:
            for symbol in self.symbols:

                self.upbit_trade.price[symbol] = self.upbit_ohlcv_list[symbol][self.count]["close"]
                self.binance_trade.price[symbol] = self.binance_ohlcv_list[symbol][self.count]["close"]

            self.count += 1
            self.current_time += timedelta(milliseconds=250)
            return True
        else:
            return False

    def get_counter(self):
        td = self.end_current_time - self.current_time
        counter = td / timedelta(milliseconds=250)
        return int(counter)

    def load_next_by_counter(self, counter):
        for symbol in self.symbols:
            self.upbit_trade.price[symbol] = self.upbit_ohlcv_list[symbol][counter]["close"]
            self.binance_trade.price[symbol] = self.binance_ohlcv_list[symbol][counter]["close"]
