import pandas as pd


class Timer:
    def __init__(self):
        pass

    def start(self, start_time, target_interval):
        self.start_time = start_time
        self.finish_time = self.start_time + pd.Timedelta(target_interval)

    def check_finish(self, current_time):
        return True if current_time >= self.finish_time else False
