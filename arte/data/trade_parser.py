class TradeParser:
    """
    Class TradeParser
        Trade data를 관리하는 모듈. 각 data들을 dictionary 형태로 관리.

    Attributes:
        price : 현재 Trade의 price 값을 저장하고 있는 dictionary. ( key : pure symbol, value : price) (ex : {"BTC":10000, "ETH":21342})

    Functions:
        __init__ : Class 선언 시 pure symbol의 list 입력 필요 (ex : ["BTC", "EOS", "ETH"])
        init_trade : 호출 시 현재의 trade price를 price에 업데이트
        update_trade_upbit : upbit 소켓의 callback message를 받아 price 값을 업데이트
        update_trade_binance : binance 소켓의 callback message를 받아 price 값을 업데이트

    """

    def __init__(self, symbols):
        self.price = dict()
        self.volume = dict()
        for symbol in symbols:
            self.price[symbol.upper()] = None
            self.volume[symbol.upper()] = None

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
