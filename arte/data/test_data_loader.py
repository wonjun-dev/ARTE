import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from tqdm import tqdm

from arte.data.trade_parser import TradeParser
import arte.system.utils as utils

MARKETS = ["binance_spot", "binance_futures", "upbit"]


class ExchangeRate:
    """
    ex = ExchangeRate(ROOT)
    ex_freq = ex.get_freq_divided_date_range(start_date, end_date)
    """

    def __init__(self, root_path):
        self._root = root_path
        self.ex_df = self._load()

    def _load(self):
        def float_with_comma(x):
            return float(x.replace(",", ""))

        _df = pd.read_csv(
            os.path.join(self._root, "market_index.csv"), index_col=0, converters={"value": float_with_comma}
        )
        _df.index = pd.to_datetime(_df.index)
        _df.sort_index(inplace=True)
        _df = _df.reindex(pd.date_range(_df.index[0], _df.index[-1], freq="D"))
        _df = _df.ffill()
        return _df

    def get_freq_divided_date_range(self, start_date, end_date, freq="1S"):
        def date_range(start_date, end_date, freq):
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            new_end_date = str(end_dt.date())
            return pd.date_range(start_date, new_end_date, freq=freq, closed="left")

        # need to chekc start_date, end_date in ex_df.index
        slice_df = self.ex_df[start_date:end_date]
        slice_df = slice_df.reindex(date_range(start_date, end_date, freq))
        slice_df = slice_df.ffill()
        return slice_df


class TradeLoader:
    def __init__(self, root_path):
        self._root = root_path

    def load(self, market, symbol, start_date, end_date, silence=False):
        def _load_single_day(root_path, market, symbol, date):
            fpath = os.path.join(
                root_path, market, symbol, f"{symbol}-{date.year:04d}-{date.month:02d}-{date.day:02d}.csv"
            )
            try:
                _df = pd.read_csv(fpath)
            except:
                print(f"Error: Do not exist {fpath}!\n")
            return _df

        _dates = pd.date_range(start_date, end_date).tolist()
        _df = pd.DataFrame()
        for _dt in tqdm(_dates, disable=silence):
            _df = _df.append(_load_single_day(self._root, market, symbol, _dt))
        _df["datetime"] = pd.to_datetime(_df["timestamp"].apply(lambda x: x), unit="ms")
        _df.set_index("datetime", inplace=True)

        if market == "upbit":
            _df["isbuyermaker"] = np.where(_df["ask_bid"] == "BID", True, False)

        return _df


class DataProcessor:
    def __init__(self, root_path, symbols, start_date, end_date, freq="1S"):
        self.silence = False
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.freq = freq
        self.trade_loader = TradeLoader(root_path)
        self.ex = ExchangeRate(root_path)
        self.ex_freq = self.ex.get_freq_divided_date_range(self.start_date, self.end_date, freq=freq)

    def process(self, markets: list, silence=False):
        self.silence = silence
        d = dict()
        for market in markets:
            d[market] = self.process_market(market)
        return d

    def process_market(self, market):
        d = dict()
        for symbol in self.symbols:
            df = self.trade_loader.load(market, symbol, self.start_date, self.end_date, silence=self.silence)
            d[symbol] = self.process_single(market, df)
        return d

    def process_single(self, market, df):
        df = self._add_fake_trades(market, df)
        r = df.resample(self.freq)
        ohlc = r["price"].ohlc()
        ohlc = ohlc.fillna(dict.fromkeys(ohlc.columns.tolist(), ohlc.close.ffill()))

        if "binance" in market:
            ohlc = ohlc.multiply(self.ex_freq["value"], axis=0)

        volume = r["quantity"].sum()
        n_trade = r.size()
        n_trade[0] -= 2
        n_trade[-1] -= 2

        r_buy = df[~df["isbuyermaker"]].resample(self.freq)
        volume_buy = r_buy["quantity"].sum()
        n_trade_buy = r_buy.size()
        n_trade_buy[0] -= 1
        n_trade_buy[-1] -= 1

        r_sell = df[df["isbuyermaker"]].resample(self.freq)
        volume_sell = r_sell["quantity"].sum()
        n_trade_sell = r_sell.size()
        n_trade_sell[0] -= 1
        n_trade_sell[-1] -= 1

        result_df = pd.DataFrame(
            {
                "o": ohlc["open"],
                "h": ohlc["high"],
                "l": ohlc["low"],
                "c": ohlc["close"],
                "v": volume,
                "vb": volume_buy,
                "vs": volume_sell,
                "n": n_trade,
                "nb": n_trade_buy,
                "ns": n_trade_sell,
            }
        )
        return result_df

    def _add_fake_trades(self, market, df):
        if "binance" in market:
            fake_trade = {
                "tradeid": 999999999,
                "price": np.nan,
                "quantity": 0,
                "quoteqty": 0,
                "timestamp": 0,
                "isbuyermaker": False,
                "isbestmatch": False,
            }
        elif market == "upbit":
            fake_trade = {
                "market": "NONE",
                "trade_date_utc": "0000-00-00",
                "trade_time_utc": "00:00:00",
                "timestamp": 0,
                "price": np.nan,
                "quantity": 0,
                "prev_closing_price": 0,
                "change_price": 0,
                "ask_bid": None,
                "sequantial_id": 0,
                "isbuyermaker": False,
            }
        dt_fake_start_trade = pd.Timestamp(self.start_date)
        dt_fake_end_trade = pd.Timestamp(self.end_date) + pd.Timedelta("1D") - pd.Timedelta("1ms")
        # Front fake trade insert
        fake_trade_sell = fake_trade.copy()
        fake_trade_sell["isbuyermaker"] = True
        df_fake = pd.DataFrame([fake_trade, fake_trade_sell], index=[dt_fake_start_trade] * 2)
        df = df_fake.append(df)
        # Back fake trade insert
        df_fake = pd.DataFrame([fake_trade, fake_trade_sell], index=[dt_fake_end_trade] * 2)
        df = df.append(df_fake)
        return df


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
        self.root_data_path = root_data_path
        self.upbit_ohlcv = dict()
        self.binance_ohlcv = dict()

        self.upbit_ohlcv_list = dict()
        self.binance_ohlcv_list = dict()

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

        # self.upbit_trade = TradeParser(symbols=self.symbols)
        self.binance_trade = TradeParser(symbols=self.symbols)

        # self.upbit_last_askbid = {symbol: None for symbol in self.symbols}

        # self.init_upbit_test_loader()
        self.init_binance_test_loader()

        self.start_time = pd.to_datetime(start_date)
        self.current_time = pd.to_datetime(start_date)
        self.end_current_time = pd.to_datetime(end_date) + timedelta(days=1)
        self.count = 0

        for symbol in tqdm(self.symbols, ncols=100):
            # self.upbit_ohlcv_list[symbol] = self.upbit_ohlcv[symbol].to_dict("records")
            self.binance_ohlcv_list[symbol] = self.binance_ohlcv[symbol].to_dict("records")

        # self.exchange_rate_df = pd.read_csv(os.path.join(self.root_data_path, "market_index.csv"), index_col=0)
        # self.load_exchange_rate()
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
        gp = utils.make_group(upbit_trade_df, freq=self.freq)
        temp_upbit_ohlcv = gp["price"].ohlc()
        temp_upbit_ohlcv["volume"] = gp["quantity"].sum()
        temp_upbit_ohlcv["trade_num"] = gp["trade_num"].sum()
        temp_upbit_ohlcv["last_askbid"] = gp["ask_bid"].nth(-1)
        temp_upbit_ohlcv["last_askbid"].ffill(inplace=True)

        temp_upbit_ohlcv.fillna(
            dict.fromkeys(temp_upbit_ohlcv.columns.tolist(), temp_upbit_ohlcv.close.ffill()), inplace=True,
        )
        start_stamp = pd.to_datetime(current_date)
        end_stamp = temp_upbit_ohlcv.index[0]
        temp = temp_upbit_ohlcv.iloc[0]["open"]

        while start_stamp < end_stamp:
            temp_upbit_ohlcv.loc[start_stamp] = [temp, temp, temp, temp, 0.0, 0, "NONE"]
            start_stamp += timedelta(milliseconds=self.ohlcv_interval)

        temp_upbit_ohlcv.sort_index(inplace=True)

        start_stamp = temp_upbit_ohlcv.index[-1] + timedelta(milliseconds=self.ohlcv_interval)
        end_stamp = pd.to_datetime(current_date) + timedelta(days=1)
        temp = temp_upbit_ohlcv.iloc[-1]["close"]

        while start_stamp < end_stamp:
            temp_upbit_ohlcv.loc[start_stamp] = [temp, temp, temp, temp, 0.0, 0, "NONE"]
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
        gp = utils.make_group(binance_trade_df, freq=self.freq)
        temp_binance_ohlcv = gp["price"].ohlc()
        temp_binance_ohlcv["volume"] = gp["quantity"].sum()
        temp_binance_ohlcv["trade_num"] = gp["trade_num"].sum()

        temp_binance_ohlcv.fillna(
            dict.fromkeys(temp_binance_ohlcv.columns.tolist(), temp_binance_ohlcv.close.ffill()), inplace=True,
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

    def _load_trade_data(self, symbol: str, current_date: datetime, is_upbit: bool):
        """
        특정 symbol의 current_data의 trade data csv를 읽어오는 함수
        """

        if is_upbit:
            market_path = "upbit"
        else:
            market_path = "binance_futures"

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
            self.upbit_last_askbid[symbol] = self.upbit_ohlcv_list[symbol][counter]["last_askbid"]
            self.binance_trade.price[symbol] = self.binance_ohlcv_list[symbol][counter]["close"]

        self.current_time = self.start_time + timedelta(milliseconds=self.ohlcv_interval) * counter

    def load_exchange_rate(self):
        """
        일자 별 알맞은 환율(usdt/kor)을 불러오는 함수
        """
        temp_time = self.current_time

        if temp_time.hour + temp_time.minute + temp_time.second + temp_time.microsecond == 0:
            while temp_time.strftime("%Y-%m-%d") not in self.exchange_rate_df.index:
                temp_time -= timedelta(days=1)
            self.exchange_rate = float(self.exchange_rate_df.loc[temp_time.strftime("%Y-%m-%d")].value.replace(",", ""))


if __name__ == "__main__":
    DATA_PATH = "/home/park/Projects/data"
    symbol = "AXS"
    start_date = "2021-10-01"
    end_date = "2021-10-01"
    dl = TestDataLoader(DATA_PATH)
    dl.init_test_data_loader([symbol], start_date, end_date, ohlcv_interval=1000)
    dl.load_next_by_counter(0)
    print(dl.upbit_trade.price)
    print(dl.upbit_last_askbid)
    print(dl.current_time)
