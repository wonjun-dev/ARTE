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
        self.enter_cur_candle = False
        self.enter_price = None
        self.signal_atr = None
        self.max_buy_long = None
        self.min_buy_short = None
        self.min_sell_long = None
        self.max_sell_short = None

    def run(self, data):
        super().run(data)
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

        if self.data.candle_closed:
            self.enter_cur_candle = False

        print("stop 1")

        self.max_buy_long = max(list(self.data.high)[-20:-1])
        self.min_buy_short = min(list(self.data.low)[-20:-1])
        self.min_sell_long = min(list(self.data.low)[-10:-1])
        self.max_sell_short = max(list(self.data.high)[-10:-1])

        signal_buy_long = self.__compare(self.current_price, self.max_buy_long)
        signal_buy_short = self.__compare(self.current_price, self.min_buy_short)

        signal_sell_long = self.__compare(self.current_price, self.min_sell_long)
        signal_sell_short = self.__compare(self.current_price, self.max_sell_short)

        if self.enter_cur_candle:
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

        self.signals["signal_buy_long"] = signal_buy_long
        self.signals["signal_buy_short"] = signal_buy_short
        self.signals["signal_sell_long"] = signal_sell_long
        self.signals["signal_sell_short"] = signal_sell_short

        return self.signals

    def _order(self, signals: dict):
        if not self.enter_cur_candle:
            if self.manager.positionSide == PositionSide.INVALID:
                if signals["signal_buy_long"] == CrossDirection.UP:
                    if self.manager.buy_long_market(ratio=self.BUY_RATIO):
                        self.enter_price = self.current_price
                        self.enter_cur_candle = True
                elif signals["signal_buy_short"] == CrossDirection.DOWN:
                    if self.manager.buy_short_market(ratio=self.BUY_RATIO):
                        self.enter_price = self.current_price
                        self.enter_cur_candle = True
            elif self.manager.positionSide == PositionSide.LONG:
                if self.manager.order_count < self.manager.max_order_count:
                    if signals["signal_sell_long"] == CrossDirection.DOWN:
                        if self.manager.sell_long_market(ratio=self.SELL_RATIO):
                            self.enter_price = None
                            self.enter_cur_candle = True
                    elif signals["signal_sell_long_atr"] == CrossDirection.DOWN:
                        if self.manager.sell_long_market(ratio=self.SELL_RATIO):
                            self.enter_price = None
                            self.enter_cur_candle = True
                    elif signals["signal_add_long"] == CrossDirection.UP:
                        if self.manager.buy_long_market(ratio=self.BUY_RATIO):
                            self.enter_price = self.current_price
                            self.enter_cur_candle = True
                    elif signals["signal_buy_long"] == CrossDirection.UP:
                        if self.manager.buy_long_market(ratio=self.BUY_RATIO):
                            self.enter_price = self.current_price
                            self.enter_cur_candle = True
            elif self.manager.positionSide == PositionSide.SHORT:
                if self.manager.order_count < self.manager.max_order_count:
                    if signals["signal_sell_short"] == CrossDirection.UP:
                        if self.manager.sell_short_market(ratio=self.SELL_RATIO):
                            self.enter_price = None
                            self.enter_cur_candle = True
                    elif signals["signal_sell_short_atr"] == CrossDirection.UP:
                        if self.manager.sell_short_market(ratio=self.SELL_RATIO):
                            self.enter_price = None
                            self.enter_cur_candle = True
                    elif signals["signal_add_short"] == CrossDirection.DOWN:
                        if self.manager.buy_short_market(ratio=self.BUY_RATIO):
                            self.enter_price = self.current_price
                            self.enter_cur_candle = True
                    elif signals["signal_buy_short"] == CrossDirection.DOWN:
                        if self.manager.buy_short_market(ratio=self.BUY_RATIO):
                            self.enter_price = self.current_price
                            self.enter_cur_candle = True

    def __compare(self, variable, standard):
        if variable > standard:
            return CrossDirection.UP
        elif variable < standard:
            return CrossDirection.DOWN
        else:
            return CrossDirection.NO
