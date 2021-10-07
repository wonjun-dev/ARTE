import pandas as pd
import os
from tqdm import tqdm
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

    def init_test_data_loader(self, symbols, start_date, end_date, ohlcv_interval=250):

        self.symbols = [symbol.upper() for symbol in symbols]
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.freq = str(ohlcv_interval) + "ms"
        self.ohlcv_interval = ohlcv_interval

        self.upbit_trade = TradeParser(symbols=self.symbols)
        self.binance_trade = TradeParser(symbols=self.symbols)

        self.init_upbit_test_loader()
        self.init_binance_test_loader()

        self.current_time = pd.to_datetime(start_date)
        self.end_current_time = pd.to_datetime(end_date) + timedelta(days=1)
        self.count = 0

        for symbol in tqdm(self.symbols, ncols=100):
            self.upbit_ohlcv_list[symbol] = self.upbit_ohlcv[symbol].to_dict("records")
            self.binance_ohlcv_list[symbol] = self.binance_ohlcv[symbol].to_dict("records")

        self.exchange_rate_df = pd.read_csv(os.path.join(self.root_data_path, "market_index.csv"), index_col=0)
        # self.exchange_rate = float(self.exchange_rate_df.loc[start_date].value)
        print("Complete Data Loading")

    def init_upbit_test_loader(self):

        for symbol in tqdm(self.symbols, ncols=100):
            ohlcv_list = []

            current_date = self.start_date
            while current_date <= self.end_date:
                trade_df = self.load_trade_data(symbol, current_date, is_upbit=True)
                oneday_ohlcv = self.upbit_convert_to_ohlcv(trade_df, current_date)
                ohlcv_list.append(oneday_ohlcv)
                current_date += timedelta(days=1)

            self.upbit_ohlcv[symbol] = pd.concat(ohlcv_list)
            self.upbit_ohlcv[symbol].reset_index(drop=True, inplace=True)

    def upbit_convert_to_ohlcv(self, upbit_trade_df, current_date):
        gp = make_group(upbit_trade_df, freq=self.freq)
        temp_upbit_ohlcv = gp["price"].ohlc()
        temp_upbit_ohlcv["volume"] = gp["quantity"].sum()
        temp_upbit_ohlcv["trade_num"] = gp["trade_num"].sum()

        temp_upbit_ohlcv.fillna(
            dict.fromkeys(temp_upbit_ohlcv.columns.tolist(), temp_upbit_ohlcv.close.ffill()),
            inplace=True,
        )

        start_stamp = pd.to_datetime(current_date)
        end_stamp = temp_upbit_ohlcv.index[0]
        temp = temp_upbit_ohlcv.iloc[0]["open"]

        while start_stamp < end_stamp:
            temp_upbit_ohlcv.loc[start_stamp] = [temp, temp, temp, temp, 0.0, 0]
            start_stamp += timedelta(milliseconds=self.ohlcv_interval)

        temp_upbit_ohlcv.sort_index(inplace=True)

        start_stamp = temp_upbit_ohlcv.index[-1] + timedelta(milliseconds=self.ohlcv_interval)
        end_stamp = pd.to_datetime(current_date) + timedelta(days=1)
        temp = temp_upbit_ohlcv.iloc[-1]["close"]

        while start_stamp < end_stamp:
            temp_upbit_ohlcv.loc[start_stamp] = [temp, temp, temp, temp, 0.0, 0]
            start_stamp += timedelta(milliseconds=self.ohlcv_interval)

        return temp_upbit_ohlcv

    def init_binance_test_loader(self):
        for symbol in tqdm(self.symbols, ncols=100):
            ohlcv_list = []

            current_date = self.start_date
            while current_date <= self.end_date:
                trade_df = self.load_trade_data(symbol, current_date, is_upbit=False)
                oneday_ohlcv = self.binance_convert_to_ohlcv(trade_df, current_date)
                ohlcv_list.append(oneday_ohlcv)
                current_date += timedelta(days=1)

            self.binance_ohlcv[symbol] = pd.concat(ohlcv_list)
            self.binance_ohlcv[symbol].reset_index(drop=True, inplace=True)

    def binance_convert_to_ohlcv(self, binance_trade_df, current_date):
        gp = make_group(binance_trade_df, freq=self.freq)
        temp_binance_ohlcv = gp["price"].ohlc()
        temp_binance_ohlcv["volume"] = gp["quantity"].sum()
        temp_binance_ohlcv["trade_num"] = gp["trade_num"].sum()

        temp_binance_ohlcv.fillna(
            dict.fromkeys(temp_binance_ohlcv.columns.tolist(), temp_binance_ohlcv.close.ffill()),
            inplace=True,
        )

        start_stamp = pd.to_datetime(current_date)
        end_stamp = temp_binance_ohlcv.index[0]
        temp = temp_binance_ohlcv.iloc[0]["open"]

        while start_stamp < end_stamp:
            temp_binance_ohlcv.loc[start_stamp] = [temp, temp, temp, temp, 0.0, 0]
            start_stamp += timedelta(milliseconds=self.ohlcv_interval)

        temp_binance_ohlcv.sort_index(inplace=True)

        start_stamp = temp_binance_ohlcv.index[-1] + timedelta(milliseconds=self.ohlcv_interval)
        end_stamp = pd.to_datetime(current_date) + timedelta(days=1)
        temp = temp_binance_ohlcv.iloc[-1]["close"]

        while start_stamp < end_stamp:
            temp_binance_ohlcv.loc[start_stamp] = [temp, temp, temp, temp, 0.0, 0]
            start_stamp += timedelta(milliseconds=self.ohlcv_interval)

        return temp_binance_ohlcv

    def load_trade_data(self, symbol, current_date, is_upbit):

        if is_upbit:
            market_path = "upbit"
        else:
            market_path = "binance_spot"

        file_path = os.path.join(
            self.root_data_path,
            market_path,
            symbol,
            f"{symbol}-"
            + "{0:04d}-{1:02d}-{2:02d}.csv".format(current_date.year, current_date.month, current_date.day),
        )
        try:
            output_df = pd.read_csv(file_path)

        except:
            print(f"Error : Do not exist {file_path}!\n")

        output_df["trade_num"] = [1] * len(output_df)

        return output_df

    def load_next(self):
        self.load_exchange_rate()
        if self.current_time < self.end_current_time:
            for symbol in self.symbols:

                self.upbit_trade.price[symbol] = self.upbit_ohlcv_list[symbol][self.count]["close"]
                self.binance_trade.price[symbol] = self.binance_ohlcv_list[symbol][self.count]["close"]

            self.count += 1
            self.current_time += timedelta(milliseconds=self.ohlcv_interval)
            return True
        else:
            return False

    def get_counter(self):
        td = self.end_current_time - self.current_time
        counter = td / timedelta(milliseconds=self.ohlcv_interval)
        return int(counter)

    def load_next_by_counter(self, counter):
        self.load_exchange_rate()
        for symbol in self.symbols:
            self.upbit_trade.price[symbol] = self.upbit_ohlcv_list[symbol][counter]["close"]
            self.binance_trade.price[symbol] = self.binance_ohlcv_list[symbol][counter]["close"]

        self.current_time += timedelta(milliseconds=self.ohlcv_interval)

    def load_exchange_rate(self):
        temp_time = self.current_time

        if temp_time.hour + temp_time.minute + temp_time.second + temp_time.microsecond == 0:
            while temp_time.strftime("%Y-%m-%d") not in self.exchange_rate_df.index:
                temp_time -= timedelta(days=1)
            self.exchange_rate = float(self.exchange_rate_df.loc[temp_time.strftime("%Y-%m-%d")].value.replace(",", ""))
