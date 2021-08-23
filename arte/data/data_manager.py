

from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException

from arte.data.candlestick_manager import CandlestickManager


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


if __name__ == "__main__":
    # test code
    import sys

    sys.path.append("..")
    from arte.client import Client

    cl = Client(mode="TEST")
    dm = DataManager(client=cl)
    dm.open_candlestick_socket()
