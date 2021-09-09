from arte.data.trade_manager import TradeManager
import threading

from pyupbit import WebSocketManager
from binance import ThreadedWebsocketManager
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException

from arte.data.candlestick_manager import CandlestickManager
from arte.data.ticker_manager import TickerManager
from arte.data.trade_manager import TradeManager


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
