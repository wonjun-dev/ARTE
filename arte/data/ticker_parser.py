class TickerParser:
    def __init__(self, symbols):

        # self.event_time = dict()
        # self.change_price = dict()
        # self.change_price_percent = dict()
        self.price = dict()
        for symbol in symbols:
            self.price[symbol] = None
        # self.trade_quantity = dict()
        # self.open = dict()
        # self.high = dict()
        # self.low = dict()
        # self.volume = dict()

    def update_ticker_upbit(self, event):
        symbol = event.symbol[4:]
        self.price[symbol] = event.lastPrice
        # self.event_time[symbol] = msg["timestamp"]
        # self.change_price[symbol] = msg["signed_change_price"]
        # self.change_price_percent[symbol] = msg["signed_change_rate"]
        # self.trade_price[symbol] = float(msg["trade_price"])
        # self.trade_quantity[symbol] = msg["trade_volume"]
        # self.open[symbol] = msg["opening_price"]
        # self.high[symbol] = msg["high_price"]
        # self.low[symbol] = msg["low_price"]
        # self.volume[symbol] = msg["acc_trade_volume"]

    def update_ticker_binance(self, event):
        symbol = event.symbol[:-4]
        self.price[symbol] = event.lastPrice
