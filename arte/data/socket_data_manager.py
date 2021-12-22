from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException
from binance import Client

from arte.data.candlestick_parser import CandlestickParser
from arte.data.ticker_parser import TickerParser
from arte.data.trade_parser import TradeParser
from arte.data.upbit_orderbook_parser import UpbitOrderbookParser


class SocketDataManager:
    """
    Class TestDataLoader
        Upbit, Binance-spot, Binance-future의 Websocket을 관리하는 모듈

    Attributes:
        client : upbit, binance-spot, binance-future의 client 정보를 담은 클래스

    Functions:
        unsubscribe_all: 현재 구독하고 있는 모든 websocket 끊기
        open_candlestick_socket: binance의 candlestick data 소켓을 여는 함수
        open_upbit_trade_socket: upbit의 trade data 소켓을 여는 함수
        open_upbit_ticker_socket: upbit의 ticker data 소켓을 여는 함수
        open_binanace_spot_trade_socket: binance-spot의 trade data 소켓을 여는 함수
        open_binanace_spot_ticker_socket: binance-spot의 ticker data 소켓을 여는 함수
        open_binanace_future_trade_socket: binance-future의 trade data 소켓을 여는 함수

    """

    def __init__(self, client) -> None:
        self.client = client

    def unsubscribe_all(self):
        """
        구독한 전체 소켓에 대해 구독 취소
        """
        self.client.sub_client.unsubscribe_all()

    def open_candlestick_socket(self, symbol: str = "BTC", maxlen: int = 21, interval: str = "1m"):
        """
        binance future socket의 data를 받아 받을 때 마다 self.candlestick에 값을 업데이트 하는 함수

        symbol : str 타입의 단일 pure symbol, (ex : "BTC")
        maxlen : candlestick queue에 저장할 최대 길이
        interval : str 타입의 candlestick interval (ex : "1m")
        """
        self.candlestick = CandlestickParser(maxlen=maxlen)
        binance_symbol = symbol.lower() + "usdt"

        # 소켓을 열기 이전의 candlestick 데이터를 받아 저장
        init_candle = self.client.request_client.get_candlestick_data(
            symbol=binance_symbol, limit=maxlen, interval=interval
        )
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
            symbol=binance_symbol, interval=interval, callback=callback, error_handler=error
        )

    def open_upbit_orderbook_socket(self, symbols: list):
        self.upbit_orderbook = UpbitOrderbookParser(symbols=symbols)
        upbit_symbol = ["KRW-" + symbol for symbol in symbols]

        def callback(event):
            self.upbit_orderbook.update_upbit_orderbook(event)
            # print(self.upbit_orderbook["ETH"])

        def error(e: "BinanceApiException"):
            print(e.error_code + e.error_message)

        self.client.sub_client.subscribe_upbit_orderbook_event(
            symbols=upbit_symbol, callback=callback, error_handler=error
        )

    def open_upbit_trade_socket(self, symbols: list):
        """
        upbit의 trade 소켓을 열어 self.upbit_trade에 값을 업데이트 하는 함수
        symbols : str타입의 pure symbol의 list 형태 (ex : ["BTC", "ETH", "EOS"])
        """
        self.upbit_trade = TradeParser(symbols=symbols)
        upbit_symbol = ["KRW-" + symbol for symbol in symbols]

        def callback(event):
            self.upbit_trade.update_trade_upbit(event)
            #print(self.upbit_trade.price)

        def error(e: "BinanceApiException"):
            print(e.error_code + e.error_message)

        self.client.sub_client.subscribe_upbit_trade_event(symbols=upbit_symbol, callback=callback, error_handler=error)

    def open_upbit_ticker_socket(self, symbols: list):
        """
        upbit의 ticker 소켓을 열어 self.upbit_ticker에 값을 업데이트 하는 함수
        symbols : str타입의 pure symbol의 list 형태 (ex : ["BTC", "ETH", "EOS"])
        """
        self.upbit_ticker = TickerParser(symbols=symbols)
        upbit_symbol = ["KRW-" + symbol for symbol in symbols]

        def callback(event):
            self.upbit_ticker.update_ticker_upbit(event)

        def error(e: "BinanceApiException"):
            print(e.error_code + e.error_message)

        self.client.sub_client.subscribe_upbit_ticker_event(
            symbols=upbit_symbol, callback=callback, error_handler=error
        )

    def open_binanace_spot_trade_socket(self, symbols: list):
        """
        binance-spot의 trade 소켓을 열어 self.binanace_spot_trade에 값을 업데이트 하는 함수
        symbols : str타입의 pure symbol의 list 형태 (ex : ["BTC", "ETH", "EOS"])
        """
        self.binance_spot_trade = TradeParser(symbols=symbols)
        binance_symbol = [symbol.lower() + "usdt" for symbol in symbols]

        spot_client = Client()
        init_spot_trade = spot_client.get_all_tickers()
        self.binance_spot_trade.init_trade(init_spot_trade, is_future=False)

        def callback(data_type: "SubscribeMessageType", event: "any"):
            if data_type == SubscribeMessageType.RESPONSE:
                print("Event ID: ", event)
            elif data_type == SubscribeMessageType.PAYLOAD:
                self.binance_spot_trade.update_trade_binance(event)
            else:
                print("Unknown Data:")

        def error(e: "BinanceApiException"):
            print(e.error_code + e.error_message)

        self.client.sub_client.subscribe_spot_multi_aggregate_trade_event(
            symbols=binance_symbol, callback=callback, error_handler=error
        )

    def open_binanace_spot_ticker_socket(self, symbols: list):
        """
        binance-spot의 ticker 소켓을 열어 self.binanace_spot_ticker에 값을 업데이트 하는 함수
        symbols : str타입의 pure symbol의 list 형태 (ex : ["BTC", "ETH", "EOS"])
        """
        self.binance_spot_ticker = TickerParser(symbols=symbols)
        binance_symbol = [symbol.lower() + "usdt" for symbol in symbols]

        def callback(data_type: "SubscribeMessageType", event: "any"):
            if data_type == SubscribeMessageType.RESPONSE:
                print("Event ID: ", event)
            elif data_type == SubscribeMessageType.PAYLOAD:
                self.binance_spot_ticker.update_ticker_binance(event)
            else:
                print("Unknown Data:")

        def error(e: "BinanceApiException"):
            print(e.error_code + e.error_message)

        self.client.sub_client.subscribe_spot_multi_ticker_event(
            symbols=binance_symbol, callback=callback, error_handler=error
        )

    def open_binanace_future_trade_socket(self, symbols: list):
        """
        binance-future의 trade 소켓을 열어 self.binanace_future_trade에 값을 업데이트 하는 함수
        symbols : str타입의 pure symbol의 list 형태 (ex : ["BTC", "ETH", "EOS"])
        """
        self.binance_future_trade = TradeParser(symbols=symbols)
        binance_symbol = [symbol.lower() + "usdt" for symbol in symbols]

        init_mark_prices = self.client.request_client.get_all_mark_price()
        self.binance_future_trade.init_trade(init_mark_prices)

        def callback(data_type: "SubscribeMessageType", event: "any"):
            if data_type == SubscribeMessageType.RESPONSE:
                print("Event ID: ", event)
            elif data_type == SubscribeMessageType.PAYLOAD:
                self.binance_future_trade.update_trade_binance(event)
                #print(self.binance_future_trade.price)

            else:
                print("Unknown Data:")

        def error(e: "BinanceApiException"):
            print(e.error_code + e.error_message)

        self.client.sub_client.subscribe_future_multi_aggregate_trade_event(
            symbols=binance_symbol, callback=callback, error_handler=error
        )
