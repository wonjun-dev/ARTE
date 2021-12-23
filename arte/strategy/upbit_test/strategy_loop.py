from signal_state import SignalState


class StrategyLoop:
    def __init__(self, symbols, tm):
        self.tm = tm
        self.ss1 = SignalState(symbol=symbols[0], tm=self.tm)
        self.ss2 = SignalState(symbol=symbols[1], tm=self.tm)

    def update(self, **kwargs):
        self.upbit_price = kwargs["upbit_price"]
        self.current_time = kwargs["current_time"]

    def run(self):
        print(self.upbit_price.price)
        self.ss1.proceed(current_time=self.current_time)
        self.ss2.proceed(current_time=self.current_time)
