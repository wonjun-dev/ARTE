import time
import numpy as np
import pandas as pd

"""
freq = 'S' for sec / 'T' for min
gp = make_group(df, freq='T')
ohlc = gp['price'].ohlc() # nth(0), nth(-1), max(), min()
volume = gp['quantity'].sum()
"""


def round_unix_date(ts, seconds=60, up=False):
    return int(ts // seconds * seconds + seconds * up)


def np_dt_to_unix_timestamp(dt):
    return int(dt.astype("int64") / 1e9)


def make_group(df, freq="S"):
    df["datetime"] = pd.to_datetime(df["timestamp"].apply(lambda x: x), unit="ms")
    return df.groupby(pd.Grouper(key="datetime", freq=freq))
