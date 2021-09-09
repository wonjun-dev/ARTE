from arte.data.trade_manager import TradeManager
import threading
import requests

from pyupbit import WebSocketManager
from binance import ThreadedWebsocketManager
from upbit.client import Upbit
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException

from arte.data.candlestick_manager import CandlestickManager
from arte.data.ticker_manager import TickerManager
from arte.data.trade_manager import TradeManager


class DataManager:
    """
    Class DataManager
        Binance 서버로부터 데이터를 받고, 이 데이터를 관리하는 모듈

    Attributes:
        data: 서버에서 수신된 데이터의 list
        client: API를 사용하는 client 정보
    """

    def __init__(self, client) -> None:
        """
        client:
            client.sub_client = SubscriptionClient
            client.request_client = RequestClient
        """
        self.client = client
        self.candlestick = None

    def open_candlestick_socket(self, symbol: str = "btcusdt", maxlen: int = 21, interval: str = "1m"):
        """
        candlestick websocket을 열고 데이터를 받아 저장하는 함수
        """
        self.candlestick = CandlestickManager(maxlen=maxlen)

        # 소켓을 열기 이전의 candlestick 데이터를 받아 저장
        init_candle = self.client.request_client.get_candlestick_data(symbol=symbol, limit=maxlen, interval=interval)
        self.candlestick.init_candlestick(init_candle)

        def callback(data_type: "SubscribeMessageType", event: "any"):
            """
            서버에서 데이터가 수신되었을 때 실행되는 callback 함수
            """
            if data_type == SubscribeMessageType.RESPONSE:
                print("Event ID: ", event)
            elif data_type == SubscribeMessageType.PAYLOAD:
                # 현재 candlestick이 끝났는지를 판단하여 새로운 candlestick 생성
                if event.data.isClosed:
                    self.candlestick.update_candlestick(event)
                else:
                    self.candlestick.update_next_candlestick(event)
            else:
                print("Unknown Data:")

        def error(e: "BinanceApiException"):
            """
            서버에서 error가 수신되었을 떄 실행되는 함수
            """
            print(e.error_code + e.error_message)

        # candlestick 데이터를 받는 socket 열기
        self.client.sub_client.subscribe_candlestick_event(
            symbol=symbol, interval=interval, callback=callback, error_handler=error
        )

    def open_upbit_trade_socket(self, symbols):
        self.upbit_trade = TradeManager(symbols=symbols)

        def callback(event):
            self.upbit_trade.update_trade(event)
            # print(self.upbit_trade.price)

        def error(e: "BinanceApiException"):
            """
            서버에서 error가 수신되었을 떄 실행되는 함수
            """
            print(e.error_code + e.error_message)

        self.client.sub_client.subscribe_upbit_trade_event(symbols=symbols, callback=callback, error_handler=error)

    def open_upbit_ticker_socket(self, symbols):
        self.upbit_ticker = TickerManager(symbols=symbols)

        def callback(event):
            self.upbit_ticker.update_ticker(event)
            # print(self.upbit_ticker.price)

        def error(e: "BinanceApiException"):
            """
            서버에서 error가 수신되었을 떄 실행되는 함수
            """
            print(e.error_code + e.error_message)

        self.client.sub_client.subscribe_upbit_ticker_event(symbols=symbols, callback=callback, error_handler=error)

    def open_binanace_spot_trade_socket(self, symbols):
        self.binance_spot_trade = TradeManager(symbols=symbols)

        def callback(data_type: "SubscribeMessageType", event: "any"):
            """
            서버에서 데이터가 수신되었을 때 실행되는 callback 함수
            """
            if data_type == SubscribeMessageType.RESPONSE:
                print("Event ID: ", event)
            elif data_type == SubscribeMessageType.PAYLOAD:
                self.binance_spot_trade.update_trade(event)
                # print(self.binance_spot_trade.price)
            else:
                print("Unknown Data:")

        def error(e: "BinanceApiException"):
            """
            서버에서 error가 수신되었을 떄 실행되는 함수
            """
            print(e.error_code + e.error_message)

        self.client.sub_client.subscribe_spot_multi_aggregate_trade_event(
            symbols=symbols, callback=callback, error_handler=error
        )

    def open_binanace_spot_ticker_socket(self, symbols):
        self.binance_spot_ticker = TickerManager(symbols=symbols)

        def callback(data_type: "SubscribeMessageType", event: "any"):
            """
            서버에서 데이터가 수신되었을 때 실행되는 callback 함수
            """
            if data_type == SubscribeMessageType.RESPONSE:
                print("Event ID: ", event)
            elif data_type == SubscribeMessageType.PAYLOAD:
                self.binance_spot_ticker.update_ticker(event)
                # print(self.binance_spot_ticker.price)
            else:
                print("Unknown Data:")

        def error(e: "BinanceApiException"):
            """
            서버에서 error가 수신되었을 떄 실행되는 함수
            """
            print(e.error_code + e.error_message)

        self.client.sub_client.subscribe_spot_multi_ticker_event(
            symbols=symbols, callback=callback, error_handler=error
        )

    """
    def open_upbit_ticker_socket(self, symbols):
        self.upbit_ticker = TickerManager(symbols=symbols)

        def upbit_ticker_subscribe():
            while self.upbit_ticker_socket_state == True:
                data = self.upbit_ticker_socket.get()
                self.upbit_ticker.update_ticker_upbit(data)
            self.upbit_ticker_socket.close()

        self.upbit_ticker_socket = WebSocketManager("ticker", symbols)
        self.upbit_ticker_socket_thread = threading.Thread(target=upbit_ticker_subscribe)
        self.upbit_ticker_socket_state = True
        self.upbit_ticker_socket_thread.start()

    def open_binance_ticker_socket(self, symbols):
        self.streams = [x.lower() + "@ticker" for x in symbols]
        self.binance_ticker = TickerManager(symbols=symbols)

        def callback(msg):
            self.binance_ticker.update_ticker_binance(msg)

        self.binance_ticker_socket = ThreadedWebsocketManager()
        self.binance_ticker_socket.start()
        self.binance_ticker_socket.start_multiplex_socket(callback=callback, streams=self.streams)

    def get_usdt_to_kor(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
        }
        url = "https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD"
        exchange = requests.get(url, headers=headers).json()
        return float(exchange[0]["basePrice"])

    def get_closed_symbols(self):
        client = Upbit("xou3PRNskZ2wzJls3emcvd0xx3lA1eWxvsj4U2yX", "Fo2VKAuEx9yNux6hTN8i3ovX9BAZcDKsmC5qaAt8")
        resp = client.Account.Account_wallet()
        closed_list = list()
        for status in resp["result"]:
            if status["wallet_state"] != "working":
                closed_list.append(status["currency"])

        return closed_list
    """


if __name__ == "__main__":
    # test code
    import sys

    sys.path.append("..")
    from arte.client import Client

    cl = Client(mode="TEST")
    dm = DataManager(client=cl)
    dm.open_candlestick_socket()
