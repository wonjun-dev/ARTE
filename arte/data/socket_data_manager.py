import threading

from pyupbit import WebSocketManager
from binance import ThreadedWebsocketManager
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException

from arte.data.candlestick_manager import CandlestickManager
from arte.data.ticker_manager import TickerManager


class SocketDataManager:
    def __init__(self, client) -> None:
        self.client = client

    def open_candlestick_socket(self, symbol: str = "btcusdt", maxlen: int = 21, interval: str = "1m"):
        self.candlestick = CandlestickManager(maxlen=maxlen)

        # 소켓을 열기 이전의 candlestick 데이터를 받아 저장
        init_candle = self.client.request_client.get_candlestick_data(symbol=symbol, limit=maxlen, interval=interval)
        self.candlestick.init_candlestick(init_candle)

        def callback(data_type: "SubscribeMessageType", event: "any"):
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
            print(e.error_code + e.error_message)

        # candlestick 데이터를 받는 socket 열기
        self.client.sub_client.subscribe_candlestick_event(
            symbol=symbol, interval=interval, callback=callback, error_handler=error
        )

    def open_upbit_ticker_socket(self, symbols):
        self.upbit_ticker = TickerManager(symbols=symbols)

        def subscribe_upbit_ticker():
            while self.upbit_ticker_socket_state == True:
                data = self.upbit_ticker_socket.get()
                self.upbit_ticker.update_ticker_upbit(data)
            self.upbit_ticker_socket.close()

        self.upbit_ticker_socket = WebSocketManager("ticker", symbols)
        self.upbit_ticker_socket_thread = threading.Thread(target=subscribe_upbit_ticker)
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
