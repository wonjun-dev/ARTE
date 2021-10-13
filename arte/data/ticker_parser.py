class TickerParser:
    """
    Class TickerParser
        Ticker data를 관리하는 모듈. 각 data들을 dictionary 형태로 관리.

    Attributes:
        price : 현재 Ticker의 price 값을 저장하고 있는 dictionary. ( key : pure symbol, value : price) (ex : {"BTC":10000, "ETH":21342})

    Functions:
        __init__ : Class 선언 시 pure symbol의 list 입력 필요 (ex : ["BTC", "EOS", "ETH"])
        update_ticker_upbit : upbit 소켓의 callback message를 받아 price 값을 업데이트
        update_ticker_binance : binance 소켓의 callback message를 받아 price 값을 업데이트

    """

    def __init__(self, symbols: list):

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
