class TradeParser:
    def __init__(self, symbols):
        self.price = dict()
        for symbol in symbols:
            self.price[symbol.upper()] = None

    def init_trade(self, mark_prices, is_future=True):

        if is_future:
            for mp in mark_prices:
                temp_symbol = mp.symbol[:-4]
                if temp_symbol in self.price:
                    self.price[temp_symbol] = mp.markPrice
        else:
            for mp in mark_prices:
                temp_symbol = str(mp["symbol"])[:-4]
                if temp_symbol in self.price:
                    self.price[temp_symbol] = float(mp["price"])

    def update_trade_upbit(self, event):
        symbol = event.symbol[4:]
        self.price[symbol] = event.price

    def update_trade_binance(self, event):
        symbol = event.symbol[:-4]
        self.price[symbol] = event.price
