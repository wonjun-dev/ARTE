from collections import deque

from arte.strategy.core.base_strategy import BaseStrategy
from arte.strategy.core.base_strategy import CrossDirection


class BollingerTouch(BaseStrategy):
    def __init__(
        self,
        indicator_manager,
        buy_ratio: float = 0.1,
        sell_ratio: float = 1.0,
    ):
        super().__init__(indicator_manager, buy_ratio, sell_ratio)

        # 전략 특화 초기화
        self.patience = 3  # 첫번째 매수 시그널 발생후 patience 만큼의 캔들 업데이트 이내에 두번째 매수 시그널이 나오지 않으면 첫번째 시그널 무효화
        self.price_idxs = deque(maxlen=2)
        self.signals = {
            "firstSignal": None,
            "finalSignal": None,
        }
        self.enter_cur_candle = False
        self.first_signal_this_candle = False

    def run(self, data):
        super().run(data)
        print(
            f"Signals: {self.signals}, FirstSignalThisCandle: {self.first_signal_this_candle}, EnterCurrentCandle: {self.enter_cur_candle}, Price: {self.current_price}, Idxs: {self.price_idxs}"
        )

    def _make_signals(self, indicators: dict):
        assert self.patience >= 0
        # 볼밴에서 현재가 위치
        pidx = self.__find_current_price_location(self.current_price, indicators["Bollinger"][-1])

        # 가격 큐 업데이트
        if self.data.candle_closed:
            self.price_idxs.append(pidx)
            self.enter_cur_candle = False
            self.first_signal_this_candle = False

            if self.signals["firstSignal"]:
                self.patience -= 1
                if self.patience == 0:
                    self.__reset()
        else:
            try:
                self.price_idxs.pop()
            except:
                pass
            self.price_idxs.append(pidx)

        # 아르떼 시작 후, 다음 캔들 부터 매수 시그널 생성
        if len(self.price_idxs) > 1:
            past_idx = self.price_idxs[0]
            cur_idx = self.price_idxs[-1]

            # 첫번째 매수 시그널 발생
            if not self.signals["firstSignal"]:
                if past_idx == 2 and cur_idx == 3:  # 숏 포지션 진입 첫번째 시그널 발생
                    self.signals["firstSignal"] = "SHORT_READY"
                    self.first_signal_this_candle = True
                elif past_idx == 1 and cur_idx == 0:  # 롱 포지션 진입 첫번째 시그널 발생
                    self.signals["firstSignal"] = "LONG_READY"
                    self.first_signal_this_candle = True

            else:  # 최종 매수 시그널 발생
                print("Ready")
                if not self.first_signal_this_candle:  # 첫번째 시그널 발생 이후 다음 캔들 부터 최종 시그널 생성
                    if self.signals["firstSignal"] == "SHORT_READY":
                        if cur_idx == 2:
                            self.signals["finalSignal"] = "SHORT"
                    elif self.signals["firstSignal"] == "LONG_READY":
                        if cur_idx == 1:
                            self.signals["finalSignal"] = "LONG"

        return self.signals

    def _order(self, signals: dict):
        if signals["firstSignal"] and signals["finalSignal"]:
            if signals["finalSignal"] == "SHORT":  # 롱 포지션 종료 후 숏 포지션 진입
                self.manager.sell_long_market(ratio=self.SELL_RATIO)
                if not self.enter_cur_candle:  # 현재 캔들에 매수를 하지 않았을 경우에만 포지션 진입
                    print("Try to buy short market.")
                    if self.manager.buy_short_market(ratio=self.BUY_RATIO):
                        print("Success.")
                        self.enter_cur_candle = True
                        self.__reset()

            elif signals["finalSignal"] == "LONG":  # 숏 포지션 종료 후 롱 포지션 진입
                self.manager.sell_short_market(ratio=self.SELL_RATIO)
                if not self.enter_cur_candle:  # 현재 캔들에 매수를 하지 않았을 경우에만 포지션 진입
                    print("Try to buy long market.")
                    if self.manager.buy_long_market(ratio=self.BUY_RATIO):
                        print("Success.")
                        self.enter_cur_candle = True
                        self.__reset()

        # 볼밴 중앙에서 부분 포지션 종료
        past_idx, cur_idx = self.price_idxs[0], self.price_idxs[-1]
        if past_idx == 1 and cur_idx == 2:
            self.manager.sell_long_market(ratio=self.SELL_RATIO * 0.5)
        if past_idx == 2 and cur_idx == 1:
            self.manager.sell_short_market(ratio=self.SELL_RATIO * 0.5)

    def __find_current_price_location(self, current_price: float, bband: tuple):
        """
        Find location of current price in the bband.
        Args:
            current_price
        Return:
            where: (int) location of current price in the bband. 0: lower, 1: low~midddle, 2: middle~up, 3: upper
        """
        tmp = list(bband)
        tmp.append(current_price)
        tmp.sort()
        where = tmp.index(current_price)

        return where

    def __reset(self):
        "아무런 포지션을 들고 있지 않은(매수 대기) 상태로 복귀."
        self.patience = 3
        self.signals["firstSignal"] = None
        self.signals["finalSignal"] = None
        self.first_signal_this_candle = False
