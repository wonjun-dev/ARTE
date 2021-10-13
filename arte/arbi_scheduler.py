import traceback
from apscheduler.schedulers.blocking import BlockingScheduler
from pandas import Timestamp

from arte.data import SocketDataManager
from arte.data import RequestDataManager
from arte.data.common_symbol_collector import CommonSymbolCollector

from arte.system.trade_manager import TradeManager


from arte.strategy import ArbitrageBasic


class ArbiTrader:
    """
    Class ArbiTrader:
        실시간 Arbi 거래를 위한 모듈
        scheduler 기반으로 지정한 interval 마다 mainloop을 실행.

    Attributes:
        bot : Telegram Bot 관리를 위한 모듈
        except_list : 현재 Upbit에서 입출금이 막힌 symbol list
        exchange_rate : 실시간 현재 환율
        common_symbols : upbit과 binance future에서 공통으로 거래되는 암호화폐 리스트

    Functions:
        mainloop : 실제 전략이 돌아가는 함수. start에서 정한 interval 마다 실행되는 함수
        start : 거래를 위해 필요한 socket들을 열고 mainloop을 주기적으로 실행하기 위한 scheduler를 초기화하는 함수
        get_exchange_rate : 현재 환율 업데이트
        update_closed_list : 현재 Upbit에서 입출금이 막힌 symbol list 업데이트

    """

    def __init__(self, client, **kwargs):

        self.client = client
        self.scheduler = BlockingScheduler()

        self.socket_data_manager = SocketDataManager(self.client)
        self.request_data_manager = RequestDataManager(self.client)
        self.symbol_collector = CommonSymbolCollector()

        # Init bot
        self.bot = None
        if "bot" in kwargs:
            self.bot = kwargs["bot"]
            self.bot.trader = self

        self.tm = TradeManager(client=self.client)
        self.tm.environment = self
        self.strategy = ArbitrageBasic(trade_manager=self.tm)

        # Init required data
        self.except_list = self.request_data_manager.get_closed_symbols()
        self.exchange_rate = self.request_data_manager.get_usdt_to_kor()
        self.common_symbols = self.symbol_collector.get_future_symbol()

    def mainloop(self):
        try:
            self.strategy.update(
                upbit_price=self.socket_data_manager.upbit_trade,
                binance_spot_price=self.socket_data_manager.binance_spot_trade,
                binance_future_price=self.socket_data_manager.binance_future_trade,
                exchange_rate=self.exchange_rate,
                except_list=self.except_list,
                current_time=Timestamp.now(),
            )
            self.strategy.run()

        except Exception:
            traceback.print_exc()

    def start(self, watch_interval: float = 1.0):
        """
        Upbit, Binance-spot, Binance-future socket을 열고,
        mainloop을 watch_interval 마다 실행시키고,
        get_exchange_rate을 매 시 정각마다 실행히키고
        update_closed_list를 매 시 정각 1초 후에 실행시킴
        """
        self.socket_data_manager.open_upbit_trade_socket(symbols=self.common_symbols)
        self.socket_data_manager.open_binanace_spot_trade_socket(symbols=self.common_symbols)
        self.socket_data_manager.open_binanace_future_trade_socket(symbols=self.common_symbols)

        self.strategy.initialize(self.common_symbols, self.except_list)

        self.scheduler.add_job(self.mainloop, "interval", seconds=watch_interval)
        self.scheduler.add_job(self.get_exchange_rate, "cron", minute="0")
        self.scheduler.add_job(self.update_closed_list, "cron", minute="0", second="1")
        if self.bot:
            self.bot.bot_manager_setting()
        self.scheduler.start()

    def get_exchange_rate(self):
        self.exchange_rate = self.request_data_manager.get_usdt_to_kor()

    def update_closed_list(self):
        self.except_list = self.request_data_manager.get_closed_symbols()
