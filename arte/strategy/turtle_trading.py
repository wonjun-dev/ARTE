from collections import deque

from binance_f.model.constant import PositionSide
from arte.strategy.core.base_strategy import BaseStrategy
from arte.strategy.core.base_strategy import CrossDirection


class TurtleTrading(BaseStrategy):
    def __init__(
        self, indicator_manager, buy_ratio: float = 0.02, sell_ratio: float = 1.0,
    ):
        super().__init__(indicator_manager, buy_ratio, sell_ratio)

        # 전략 특화 초기화
        self.signals = {
            "signal_buy_long": None,
            "signal_buy_short": None,
            "signal_sell_long": None,
            "signal_sell_short": None,
            "signal_add_long": None,
            "signal_add_short": None,
            "signal_sell_long_atr": None,
            "signal_sell_short_atr": None,
        }
        self.enter_cur_candle = False  # 현재 캔들에서 거래가 이루어 졌는지 확인
        self.enter_price = None  # ATR에 따른 전략을 위한 진입가
        self.signal_atr = None
        self.max_buy_long = None
        self.min_buy_short = None
        self.min_sell_long = None
        self.max_sell_short = None

    def run(self, data):
        super().run(data)
        # Order 현황 출력
        print(
            f"Signals : {self.signals} \
            \nEnterprice : {self.enter_price} \
            \nATR : {self.signal_atr[-1]} \
            \nPositionSide : {self.manager.positionSide} \
            \nOrderCount : {self.manager.order_count} \
            \nLong : {self.max_buy_long, self.min_sell_long} \
            \nShort : {self.min_buy_short, self.max_sell_short}"
        )

    def _make_signals(self, indicators: dict):
        self.signal_atr = indicators["ATR"]

        # 같은 캔들에서 재 진입 하지 않기 위한 조건
        if self.data.candle_closed:
            self.enter_cur_candle = False

        # 터틀트레이딩에서 OHLC에 따른 진입 혹은 청산에 필요한 시그널 생성
        self.max_buy_long = max(list(self.data.high)[-20:-1])
        self.min_buy_short = min(list(self.data.low)[-20:-1])
        self.min_sell_long = min(list(self.data.low)[-10:-1])
        self.max_sell_short = max(list(self.data.high)[-10:-1])

        signal_buy_long = self.__compare(self.current_price, self.max_buy_long)
        signal_buy_short = self.__compare(self.current_price, self.min_buy_short)
        signal_sell_long = self.__compare(self.current_price, self.min_sell_long)
        signal_sell_short = self.__compare(self.current_price, self.max_sell_short)

        self.signals["signal_buy_long"] = signal_buy_long
        self.signals["signal_buy_short"] = signal_buy_short
        self.signals["signal_sell_long"] = signal_sell_long
        self.signals["signal_sell_short"] = signal_sell_short

        # 터틀트레이딩에서 ATR에 따른 추매 혹은 손절을 위한 시그널 생성
        if self.enter_price:
            signal_add_long = self.__compare(self.current_price, self.enter_price + self.signal_atr[-1])
            signal_add_short = self.__compare(self.current_price, self.enter_price - self.signal_atr[-1])
            signal_sell_long_atr = self.__compare(self.current_price, self.enter_price - 2 * self.signal_atr[-1])
            signal_sell_short_atr = self.__compare(self.current_price, self.enter_price + 2 * self.signal_atr[-1])

            self.signals["signal_add_long"] = signal_add_long
            self.signals["signal_add_short"] = signal_add_short
            self.signals["signal_sell_long_atr"] = signal_sell_long_atr
            self.signals["signal_sell_short_atr"] = signal_sell_short_atr
        else:
            self.signals["signal_add_long"] = CrossDirection.NO
            self.signals["signal_add_short"] = CrossDirection.NO
            self.signals["signal_sell_long_atr"] = CrossDirection.NO
            self.signals["signal_sell_short_atr"] = CrossDirection.NO

        return self.signals

    def _order(self, signals: dict):
        """
        signals의 종류에 따른 turtle trading 주문
        Args:
            signals : (dict) 필요한 시그널
        Return:
            pass
        """

        if not self.enter_cur_candle:
            # 첫 진입 시점에서 Long/Short을 시그널에 따라 진입
            if self.manager.positionSide == PositionSide.INVALID:
                if signals["signal_buy_long"] == CrossDirection.UP:
                    if self.manager.buy_long_market(ratio=self.BUY_RATIO):
                        self.enter_price = self.current_price
                        self.enter_cur_candle = True
                elif signals["signal_buy_short"] == CrossDirection.DOWN:
                    if self.manager.buy_short_market(ratio=self.BUY_RATIO):
                        self.enter_price = self.current_price
                        self.enter_cur_candle = True

            # 첫 진입 시점이 Long인 경우
            elif self.manager.positionSide == PositionSide.LONG:
                if signals["signal_sell_long"] == CrossDirection.DOWN:  # OHLC 시그널에 따른 long 청산 신호 발생
                    if self.manager.sell_long_market(ratio=self.SELL_RATIO):
                        self.enter_price = None
                        self.enter_cur_candle = True
                elif signals["signal_sell_long_atr"] == CrossDirection.DOWN:  # ATR 시그널에 따른 long 청산 신호 발생
                    if self.manager.sell_long_market(ratio=self.SELL_RATIO):
                        self.enter_price = None
                        self.enter_cur_candle = True
                elif signals["signal_add_long"] == CrossDirection.UP:  # ATR 시그널에 따른 long 추가매수 신호 발생
                    if self.manager.buy_long_market(ratio=self.BUY_RATIO):
                        self.enter_price = self.current_price
                        self.enter_cur_candle = True

            # 첫 진입 시점이 Long인 경우
            elif self.manager.positionSide == PositionSide.SHORT:
                if signals["signal_sell_short"] == CrossDirection.UP:  # OHLC 시그널에 따른 short 청산 신호 발생
                    if self.manager.sell_short_market(ratio=self.SELL_RATIO):
                        self.enter_price = None
                        self.enter_cur_candle = True
                elif signals["signal_sell_short_atr"] == CrossDirection.UP:  # ATR 시그널에 따른 short 청산 신호 발생
                    if self.manager.sell_short_market(ratio=self.SELL_RATIO):
                        self.enter_price = None
                        self.enter_cur_candle = True
                elif signals["signal_add_short"] == CrossDirection.DOWN:  # ATR 시그널에 따른 short 추가 매수 신호 발생
                    if self.manager.buy_short_market(ratio=self.BUY_RATIO):
                        self.enter_price = self.current_price
                        self.enter_cur_candle = True

    def __compare(self, variable, standard):
        """
        기준값 대비 변화값의 위치를 확인
        Args:
            variable: (float) 변화값
            standard: (float) 기준값
        Return:
            CrossDirection.UP : 변화값이 기준가보다 위에 있음
            CrossDirection.DOWN : 변화값이 기준가보다 아래에 있음
            CrossDirection.NO : 변화값이 기준가와 같음
        """
        if variable > standard:
            return CrossDirection.UP
        elif variable < standard:
            return CrossDirection.DOWN
        else:
            return CrossDirection.NO
