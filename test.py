class Account:
    def __init__(self):
        self.positionAmt = 1


if __name__ == "__main__":
    from collections import deque

    import numpy as np

    from indicator_manager import Bollinger
    from strategy import BollingerTouch

    INDICATORS = [Bollinger()]

    bbtt = BollingerTouch(indicators=INDICATORS, account=Account())

    # main loop
    for _ in range(100):
        price = deque(np.random.rand(100), maxlen=100)
        bbtt.run(price)
