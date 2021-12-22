# data loader

import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from tqdm import tqdm

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

        if market == 'upbit':
            _df['isbuyermaker'] = np.where(_df['ask_bid']=='BID', True, False)

        return _df


class DataProcessor:
    def __init__(self, root_path, symbols, start_date, end_date, freq='1S'):
        self.silence = False
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.freq = freq
        self.trade_loader = TradeLoader(root_path)
        self.ex = ExchangeRate(root_path)
        self.ex_freq = self.ex.get_freq_divided_date_range(self.start_date, self.end_date, freq=freq)

    def process(self, process_future=True, silence=False):
        self.silence = silence

        d = dict()
        d["binance_spot"] = self.process_market("binance_spot")
        d["upbit"] = self.process_market('upbit')
        if process_future:
            d["binance_futures"] = self.process_market("binance_futures")
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

        if 'binance' in market:
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
        if 'binance' in market:
            fake_trade = {
                "tradeid": 999999999,
                "price": np.nan,
                "quantity": 0,
                "quoteqty": 0,
                "timestamp": 0,
                "isbuyermaker": False,
                "isbestmatch": False,
            }
        elif market == 'upbit':
            fake_trade = {
                'market':'NONE',
                'trade_date_utc':'0000-00-00',
                'trade_time_utc':'00:00:00',
                'timestamp':0,
                'price':np.nan,
                'quantity':0,
                'prev_closing_price':0,
                'change_price':0,
                'ask_bid':None,
                'sequantial_id':0,
                'isbuyermaker':False
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

