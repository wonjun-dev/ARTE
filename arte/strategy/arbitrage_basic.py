from arte.indicator import Indicator
from arte.strategy.core.base_strategy import BaseStrategy


class ArbitrageBasic(BaseStrategy):
    """
    Upbit-Binance Pair Arbitrage 기초 전략
    """

    def __init__(self, indicator_manager, buy_ratio: float = 0.15, sell_ratio: float = 1.0):
        super().__init__(indicator_manager, buy_ratio, sell_ratio)
        self.premium_threshold = 0.5
        self.premium_assets = []

    def run(self, **kwargs):
        self.upbit_ticker = kwargs["upbit_ticker"]
        self.binance_ticker = kwargs["binance_ticker"]
        self.exchange_rate = kwargs["exchange_rate"]
        self.except_list = kwargs["except_list"]
        self.im.update_premium(self.upbit_ticker, self.binance_ticker, self.exchange_rate)
        self._make_signals()

    def _make_signals(self):
        """
        Cond 1. 업비트 프리미엄이 일정 값 이상
        Cond 2. 바이낸스 가격 하락으로 인한것이 아닌 업비트 가격 상승으로 인한 것일 것

        필요 값
        - 업비트/바이낸스 프리미엄
        - 업비트 가격, 바이낸스 가격
        """
        premium_dict = self.im[Indicator.PREMIUM][-1]
        for symbol, p_rate in premium_dict.items():
            pure_symbol = symbol[:-4]
            if p_rate > self.premium_threshold:
                if (pure_symbol not in self.except_list) and (symbol not in self.premium_assets):
                    self.premium_assets.append(symbol)
            else:
                if symbol in self.premium_assets:
                    self.premium_assets.remove(symbol)
        print(self.premium_assets)

    def _order(self, signals: dict):
        """
        - 시그널이 True일때, Buy Long
        - 업비트 프리미엄이 기준값 이하로 하락하면 Sell Long
        """
        pass

    # def update_higher_coins(self, kimp_dict):
    #     for keys in kimp_dict:
    #         if kimp_dict[keys] > self.threshold:
    #             if keys[:-4] not in self.except_list:
    #                 if keys not in self.higher_coins:
    #                     self.higher_coins.append(keys)
    #                     message1 = "[***" + keys[:-4] + "***] :\n 현재 김프 " + str(kimp_dict[keys]) + "%\n"
    #                     message2 = (
    #                         "현재 Upbit 가격 :" + str(self.data_manager.upbit_ticker.trade_price["KRW-" + keys[:-4]]) + "\n"
    #                     )
    #                     message3 = (
    #                         "현재 Binance 가격 :"
    #                         + str(self.data_manager.binance_ticker.trade_price[keys] * self.exchange_rate)
    #                         + "\n"
    #                         + "현재 환율 : "
    #                         + str(self.exchange_rate)
    #                     )
    #                     self.bot.sendMessage(message1 + message2 + message3)
    #                     print(self.higher_coins)
    #         else:
    #             if keys in self.higher_coins:
    #                 self.higher_coins.remove(keys)
    #                 print(self.higher_coins)
