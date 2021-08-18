from collections import deque

from signal_hub import SignalHub


class BaseStrategy:
    def __init__(self):
        pass


# class OM:
#     def __init__(self) -> None:
#         pass

#     def buy_short_market(self):
#         pass

#     def buy_long_market(self):
#         pass

#     def sell_short_market(self):
#         pass

#     def sell_short_market(self):
#         pass


class BollingerTouch(BaseStrategy):
    def __init__(self, account, indicators: list, order_manager):
        self.signal_hub = SignalHub(indicators)
        self.account = account
        self.om = order_manager

        # hyper-params
        self.MAX_POS = 5
        self.ENTER_RATIO = 0.1
        self.EXIT_RATIO = 1
        self.num_pos = 0

    def run(self, price: deque):
        """
        Run trade algorithms
        Args:
            price: (deque)
        """
        self.signal_hub.update(price)
        signal = self.signal_hub.get_signal("Bollinger")
        recent_signal = list(signal)[-1]

        if self.num_pos < self.MAX_POS:

            try:
                direction, volt, past = recent_signal[0], recent_signal[1], recent_signal[2]

                if direction.name == "UP":
                    if volt + past == 3:  # upper band touch
                        if self.account.positions["BTCUSDT"].positionAmt == 0:
                            self.om.buy_short_market(ratio=self.ENTER_RATIO)
                            self.num_pos += 1
                        elif (
                            self.account.positions["BTCUSDT"].positionAmt > 0
                        ):  # current position -> long
                            # exit and open
                            self.om.sell_long_market(ratio=self.EXIT_RATIO)
                            self.num_pos -= 1
                            self.om.buy_short_market(ratio=self.ENTER_RATIO)
                            self.num_pos += 1
                        else:  # current position -> short
                            # increase short position
                            self.om.buy_short_market(ratio=self.ENTER_RATIO)
                            self.num_pos += 1

                elif direction.name == "DOWN":
                    if past - volt == 0:  # lower band touch
                        if self.account.positions["BTCUSDT"].positionAmt == 0:
                            self.om.buy_long_market(ratio=self.ENTER_RATIO)
                            self.num_pos += 1
                        elif (
                            self.account.positions["BTCUSDT"].positionAmt > 0
                        ):  # current position -> long
                            # increase long position
                            self.om.buy_long_market(ratio=self.ENTER_RATIO)
                            self.num_pos += 1
                        else:  # current position -> short
                            # exit and open
                            self.om.sell_short_market(ratio=self.EXIT_RATIO)
                            self.num_pos -= 1
                            self.om.buy_long_market(ratio=self.ENTER_RATIO)
                            self.num_pos += 1

                else:  # NO
                    print(f"IDLE")

            except:
                print(f"No enough data")

        else:
            print("Max position")
