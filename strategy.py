import numpy as np
from collections import deque

from signal_hub import SignalHub


class BaseStrategy:
    def __init__(self):
        pass


class BollingerTouch(BaseStrategy):
    def __init__(self, account, indicators: list, order_manager):
        self.signal_hub = SignalHub(indicators)
        self.account = account
        self.om = order_manager

        # hyper-params
        self.MAX_POS = 2
        self.ENTER_RATIO = 0.15
        self.EXIT_RATIO = 1
        self.num_pos = 0
        self.enter_cur_candle = False
        self.past_price = None

    def run(self, price: deque):
        """
        Run trade algorithms
        Args:
            price: (deque)
        """
        self.signal_hub.update(price)
        signal = self.signal_hub.get_signal("Bollinger")
        recent_signal = list(signal)[-1]

        if self.past_price is None:
            self.past_price = np.array(list(price)[:5])

        else:
            diff = self.past_price - np.array(list(price)[:5])

            if not np.all((diff == 0)):
                self.enter_cur_candle = False

        if self.num_pos < self.MAX_POS and self.enter_cur_candle == False:

            try:
                direction, volt, past = recent_signal[0], recent_signal[1], recent_signal[2]
                print(direction, volt, past)

                if direction.name == "UP":
                    if volt + past == 3:  # upper band touch
                        if self.account.positions["ETHUSDT"].positionAmt == 0:
                            if self.om.buy_short_market(ratio=self.ENTER_RATIO):
                                self.num_pos += 1
                                self.enter_cur_candle = True
                        elif (
                            self.account.positions["ETHUSDT"].positionAmt > 0
                        ):  # current position -> long
                            # exit and open
                            if self.om.sell_long_market(ratio=self.EXIT_RATIO):
                                self.num_pos = 0
                            if self.om.buy_short_market(ratio=self.ENTER_RATIO):
                                self.num_pos += 1
                                self.enter_cur_candle = True
                        else:  # current position -> short
                            # increase short position
                            if self.om.buy_short_market(ratio=self.ENTER_RATIO):
                                self.num_pos += 1
                                self.enter_cur_candle = True

                elif direction.name == "DOWN":
                    if past - volt == 0:  # lower band touch
                        if self.account.positions["ETHUSDT"].positionAmt == 0:
                            if self.om.buy_long_market(ratio=self.ENTER_RATIO):
                                self.num_pos += 1
                                self.enter_cur_candle = True
                        elif (
                            self.account.positions["ETHUSDT"].positionAmt > 0
                        ):  # current position -> long
                            # increase long position
                            if self.om.buy_long_market(ratio=self.ENTER_RATIO):
                                self.num_pos += 1
                                self.enter_cur_candle = True
                        else:  # current position -> short
                            # exit and open
                            if self.om.sell_short_market(ratio=self.EXIT_RATIO):
                                self.num_pos = 0
                            if self.om.buy_long_market(ratio=self.ENTER_RATIO):
                                self.num_pos += 1
                                self.enter_cur_candle = True

                else:  # NO
                    print(f"IDLE")

            except:
                print(f"No enough data")

        else:
            print(
                f"Trade is alreay filled => # of positions {self.num_pos}, enter current candle: {self.enter_cur_candle}"
            )
