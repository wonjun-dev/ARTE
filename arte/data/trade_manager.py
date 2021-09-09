class TradeManager:
    def __init__(self, symbols):
        self.price = dict()
        for symbol in symbols:
            self.price[symbol.upper()] = None

    def update_trade(self, event):
        symbol = event.symbol
        self.price[symbol] = event.price
