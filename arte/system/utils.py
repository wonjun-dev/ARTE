import random
import string
import threading

import pandas as pd
import numpy as np


class Timer:
    def __init__(self):
        pass

    def start(self, start_time, target_interval):
        self.start_time = start_time
        self.finish_time = self.start_time + pd.Timedelta(target_interval)

    def check_timeup(self, current_time):
        return True if current_time >= self.finish_time else False


class Grouping:
    def __init__(self):
        pass

    def round_unix_date(self, ts, seconds=60, up=False):
        return int(ts // seconds * seconds + seconds * up)

    def np_dt_to_unix_timestamp(self, dt):
        return int(dt.astype("int64") / 1e9)

    def make_group(self, df, freq="S"):
        df["datetime"] = pd.to_datetime(df["timestamp"].apply(lambda x: x), unit="ms")
        return df.groupby(pd.Grouper(key="datetime", freq=freq))


def generate_intervals(start, end, periods):
    def str_dt(dt):
        return dt.strftime("%Y-%m-%d")

    dt_range = pd.date_range(start=start, end=end, periods=periods + 1)
    intervals = []
    for i in range(len(dt_range) - 1):
        start_dt = str_dt(dt_range[i])
        if i + 1 == len(dt_range) - 1:
            end_dt = str_dt(dt_range[i + 1])
        else:
            end_dt = str_dt(dt_range[i + 1] - pd.Timedelta("1D"))
        intervals.append([start_dt, end_dt])
    return intervals


def random_choice():
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choices(alphabet, k=8))


def symbolize_binance(pure_symbol, upper=False):
    bsymbol = pure_symbol.lower() + "usdt"
    if upper:
        bsymbol = bsymbol.upper()
    return bsymbol


def symbolize_upbit(pure_symbol):
    usymbol = "KRW-" + pure_symbol.upper()
    return usymbol


def purify_binance_symbol(bsymbol):
    return bsymbol[:-4].upper()


def purify_upbit_symbol(usymbol):
    return usymbol[4:].upper()


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper
