import pandas as pd
import time
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
