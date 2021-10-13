import pandas as pd
import os
from pandas.core.frame import DataFrame
from tqdm import tqdm
from datetime import datetime, timedelta

from arte.data.trade_parser import TradeParser
from arte.system.utils import Grouping


class TestDataLoader:
    """
    Class TestDataLoader
        Backtest를 위한 과거 데이터 로딩 모듈
        binance, upbit의 trade data를 받고, 짧은 시간 interval의 candlestick으로 변환하여
        시간 별로 같은 시간의 가격 data를 받아옴.

    Attributes:
        root_data_path : binance, upbit, market_index.csv 등 data의 base 경로
        upbit_ohlcv : upbit의 trade data를 입력한 interval의 ohlcv로 변환한 Dataframe
        binance_ohlcv : binance의 trade data를 입력한 interval의 ohlcv로 변환한 Dataframe
        upbit_trade : TradeParser 객체로 current_time에서의 각 symbol별 upbit의 price를 Dict 형태로 저장함
        binance_trade : TradeParser 객체로 current_time에서의 각 symbol별 binance의 price를 Dict 형태로 저장함
        current_time : 현재 upbit_trade, binance_trade에 들어있는 가격에 해당하는 timestamp
        exchange_rate : 현재 current_time의 USDT/KOR 환율
        exchange_rate_df : 각 일자 별 USDT/KOR 환율 정보를 가지고 있는 Dataframe

    Functions:
        __init__ : Class 선언 시 root_data_path 입력 필요
        init_test_data_loader : symbol의 list, start_date, end_date, ohlcv를 input으로 받아 trade data를 읽어 ohlcv로 변환
        load_next : upbit_trade, binance_trade에 current_time의 가격정보 업데이트
        load_next_by_counter : upbit_trade, binance_trade에 current_time의 가격정보 업데이트 ( tqdm 사용 시 )


    """

    def __init__(self, root_data_path: str):
        """
        root_data_path를 input으로 받음, root_data_path는 binance, upbit, market_index.csv 등 data의 base 경로
        """
        self.root_data_path = root_data_path
        self.upbit_ohlcv = dict()
        self.binance_ohlcv = dict()

        self.upbit_ohlcv_list = dict()
        self.binance_ohlcv_list = dict()

        self.grouping = Grouping()

    def init_test_data_loader(self, symbols: list, start_date: str, end_date: str, ohlcv_interval: int = 250):
        """
        symbols : 데이터를 받을 symbol의 list ( ex : ["BTC", "EOS", "ETH"] )
        start_date : 데이터를 읽어 올 시작 일자 ( ex : "2021-10-03" )
        end_date : 데이터를 읽어 올 끝 일자 ( ex : "2021-10-03" )
        ohlcv_inverval : ohlcv로 가공 할 interval, ms 단위 ( ex : 250 )

        이 함수가 실행 된 후에
        current_time,
        upbit_ohlcv,
        binance_ohlcv,
        exchange_rate_df 에 데이터가 할당되며

        이후에 load_next(), load_next_by_counter() 를 사용 가능

        """
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
        self.load_exchange_rate()
        print("Complete Data Loading")

    def init_upbit_test_loader(self):
        """
        start_date에서부터 end_date 까지의 ohlcv 데이터를 병합
        """

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

    def upbit_convert_to_ohlcv(self, upbit_trade_df: DataFrame, current_date: datetime):
        """
        current_date의 upbit trade 데이터를 ohlcv 데이터로 가공.
        """
        gp = self.grouping.make_group(upbit_trade_df, freq=self.freq)
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
        """
        start_date에서부터 end_date 까지의 ohlcv 데이터를 병합
        """
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

    def binance_convert_to_ohlcv(self, binance_trade_df: DataFrame, current_date: datetime):
        """
        current_date의 binance trade 데이터를 ohlcv 데이터로 가공.
        """
        gp = self.grouping.make_group(binance_trade_df, freq=self.freq)
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

    def load_trade_data(self, symbol: str, current_date: datetime, is_upbit: bool):
        """
        특정 symbol의 current_data의 trade data csv를 읽어오는 함수
        """

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
        """
        current time에 해당하는 가격을 binance_trade, upbit_trade에 업데이트하고
        current_time을 한 timedelta 이후로 미루는 함수
        """
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

    def load_next_by_counter(self, counter: int):
        """
        current time에 해당하는 가격을 binance_trade, upbit_trade에 업데이트하고
        current_time을 한 timedelta 이후로 미루는 함수
        tqdm 사용 시 사용
        """
        self.load_exchange_rate()
        for symbol in self.symbols:
            self.upbit_trade.price[symbol] = self.upbit_ohlcv_list[symbol][counter]["close"]
            self.binance_trade.price[symbol] = self.binance_ohlcv_list[symbol][counter]["close"]

        self.current_time += timedelta(milliseconds=self.ohlcv_interval)

    def load_exchange_rate(self):
        """
        일자 별 알맞은 환율(usdt/kor)을 불러오는 함수
        """
        temp_time = self.current_time

        if temp_time.hour + temp_time.minute + temp_time.second + temp_time.microsecond == 0:
            while temp_time.strftime("%Y-%m-%d") not in self.exchange_rate_df.index:
                temp_time -= timedelta(days=1)
            self.exchange_rate = float(self.exchange_rate_df.loc[temp_time.strftime("%Y-%m-%d")].value.replace(",", ""))
