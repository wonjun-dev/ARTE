import os
import pandas as pd
from itertools import combinations
from datetime import datetime, timedelta
from math import inf
from tqdm import tqdm
import gc

from statsmodels.tsa.stattools import adfuller

root = '/hdd/binance_futures'

assets = os.listdir(root)
pairs = list(combinations(assets, 2))


# Pair Selection
def concate_dataframes(root_path, symbol, start_date, end_date):
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    while current_date != end_date:
        file_path = os.path.join(root_path, symbol, f"{symbol}-"
                + "{0:04d}-{1:02d}-{2:02d}.csv".format(current_date.year, current_date.month, current_date.day))
        try:
            if current_date == start_date:
                df = pd.read_csv(file_path)
            else:
                df = pd.concat([df, pd.read_csv(file_path)])
        except:
            return None

        current_date += timedelta(days=1)

    return df

def norm_price_dist(price_a, price_b):
    assert len(price_a) == len(price_b)

    init_a = price_a[0]
    init_b = price_b[0]

    norm_a = price_a / init_a
    norm_b = price_b / init_b
    
    npd = (norm_a - norm_b).pow(2).sum()
    return npd

# Cointegration test



# Optimal threshold




if __name__ == "__main__":
    best_npd = inf
    best_pair = None
    invalid_pair = []
    start_date = "2021-09-22"
    end_date = "2021-12-18"

    for p in tqdm(pairs):
        price_a = concate_dataframes(root_path=root, symbol=p[0], start_date=start_date, end_date=end_date)
        price_b = concate_dataframes(root_path=root, symbol=p[1], start_date=start_date, end_date=end_date)

        if price_a is not None and price_b is not None:
            price_a.index = pd.to_datetime(price_a['timestamp'], unit='ms')
            price_b.index = pd.to_datetime(price_b['timestamp'], unit='ms')

            # ohlcv
            ohlc_a = price_a['price'].resample('1min').ohlc()
            ohlc_b = price_b['price'].resample('1min').ohlc()

            try:
                npd = norm_price_dist(ohlc_a['close'], ohlc_b['close'])
            except:
                invalid_pair.append(p)

            if npd < best_npd:
                best_npd = npd
                best_pair = p

                print(best_pair, best_npd)
            
            del price_a
            del price_b
            del ohlc_a
            del ohlc_b
            gc.collect()

        else:
            invalid_pair.append(p)
            
    
    print(f"Best pair: {best_pair}={best_npd}")
    print(f"# Invalid pair: {len(invalid_pair)}")
