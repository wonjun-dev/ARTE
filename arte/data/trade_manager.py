class TradeManager:
    def __init__(self, symbols):
        self.price = dict()
        for symbol in symbols:
            self.price[symbol.upper()] = None

    def init_trade(self, mark_prices, is_future=True):

        if is_future:
            for mp in mark_prices:
                if mp.symbol in self.price:
                    self.price[mp.symbol] = mp.markPrice
        else:
            for mp in mark_prices:
                if str(mp["symbol"]) in self.price:
                    self.price[str(mp["symbol"])] = float(mp["price"])

    def update_trade(self, event):
        symbol = event.symbol
        self.price[symbol] = event.price
