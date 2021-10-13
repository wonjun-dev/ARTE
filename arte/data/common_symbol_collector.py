import pyupbit
from binance import Client
from binance_f import RequestClient


class CommonSymbolCollector:
    """
    Class RequestDataManager
        Upbit, Binance-spot, Binance-future의 공통된 암호화폐 리스트를 받아오는 함수들을 관리하는 모듈

    Functions:
        get_common_fiat_symbol : Upbit-kor 마켓과 Binance-spot의 usdt 마켓에서 공통된 암호화폐들의 pure symbol(대문자) list ( ex : ["BTC", "ETH", "EOS"])
        get_common_btc_symbol : Upbit-btc 마켓과 Binance-spot의 btc 마켓에서 공통된 암호화폐들의 pure symbol(대문자) list
        get_future_symbol : Upbit-kor 마켓과 Binance-future의 usdt 마켓에서 공통된 암호화폐들의 pure symbol(대문자) list

    """

    def __init__(self):
        self.binance_spot_client = Client()
        self.binance_future_client = RequestClient()

        self.upbit_ticker = pyupbit.get_tickers()
        self.binance_ticker = [tickers["symbol"] for tickers in self.binance_spot_client.get_all_tickers()]

        self.common_fiat_symbol = None
        self.common_btc_symbol = None
        self.common_future_symbol = None

    def get_common_fiat_symbol(self):
        upbit_krw_symbol = [symbol[4:] for symbol in self.upbit_ticker if "KRW-" in symbol]
        binance_usdt_symbol = [symbol[:-4] for symbol in self.binance_ticker if symbol[-4:] == "USDT"]

        self.common_fiat_symbol = list(set(upbit_krw_symbol) & set(binance_usdt_symbol))

        # upbit_common_fiat_symbol = ["KRW-" + symbol for symbol in self.common_fiat_symbol]
        # binance_common_fiat_symbol = [symbol + "USDT" for symbol in self.common_fiat_symbol]

        return self.common_fiat_symbol

    def get_common_btc_symbol(self):
        upbit_btc_symbol = [symbol[4:] for symbol in self.upbit_ticker if "BTC-" in symbol]
        binance_btc_symbol = [tickers[:-3] for tickers in self.binance_ticker if tickers[-3:] == "BTC"]

        self.common_btc_symbol = list(set(upbit_btc_symbol) & set(binance_btc_symbol))

        # upbit_common_btc_symbol = ["BTC-" + symbol for symbol in self.common_btc_symbol]
        # binance_common_btc_symbol = [symbol + "BTC" for symbol in self.common_btc_symbol]

        return self.common_btc_symbol

    def get_future_symbol(self):
        self.get_common_fiat_symbol()
        binance_future_ticker = self.binance_future_client.get_exchange_information()

        binance_future_symbol = [symbol.symbol[:-4] for symbol in binance_future_ticker.symbols]

        self.common_future_symbol = list(set(binance_future_symbol) & set(self.common_fiat_symbol))

        # upbit_common_future_symbol = ["KRW-" + symbol for symbol in self.common_future_symbol]
        # binance_common_future_symbol = [symbol + "USDT" for symbol in self.common_future_symbol]

        return self.common_future_symbol
