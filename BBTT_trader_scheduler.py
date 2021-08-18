import time
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

# import telegram

from data_manager import DataManager

from order_manager import OrderManager
from account import Account

from indicator_manager import Bollinger
from strategy import BollingerTouch
from telegram_bot import SimonManager


class BBTTTrader:
    """
    Class BBTTTrader
        실시간 트레이딩 모듈

    Attributes:
        client: API를 사용하는 client 정보
        data_manager: 데이터 관리 모듈
    """

    def __init__(self, client, symbol):
        """초기화 함수"""
        self.symbol = symbol
        self.client = client
        self.data_manager = DataManager(self.client)
        self.scheduler = BlockingScheduler()

        # init bot manager
        self.bot_manager = SimonManager()
        self.bot_manager.trader = self

        # Init OM
        self.account = Account(client.request_client)
        self.om = OrderManager(
            client.request_client,
            self.account,
            self.bot_manager,
            symbol=self.symbol.upper(),
        )

        # Init strategy
        INDICATORS = [Bollinger()]
        self.strategy = BollingerTouch(
            indicators=INDICATORS, account=self.account, order_manager=self.om
        )

    def mainloop(self):
        """주기적으로 실행되는 함수"""
        try:
            # 여기에 로직을 넣으시오
            # print(self.data_manager.candlestick.close)
            self.strategy.run(self.data_manager.candlestick.close)
            # print(datetime.now())
            # print(self.data_manager.candlestick.close[-1])
            # print(self.strategy.signal_hub.value_dict["Bollinger"][-1])

        except:
            print(f"error message")

    def run(self, maxlen: int = 21, interval: str = "1m", watch_interval: int = 2):
        """
        mainloop를 watch_interval마다 실행시켜주는 함수
        """
        self.data_manager.open_candlestick_socket(
            symbol=self.symbol.lower(), maxlen=maxlen, interval=interval
        )
        self.runner = self.scheduler.add_job(
            self.mainloop, "interval", seconds=watch_interval, id="mainloop"
        )
        self.bot_runner = self.scheduler.add_job(self.bot_manager.bot_manager_setting)
        self.scheduler.start()
