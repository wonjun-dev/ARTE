class UpbitOrderbookParser:
    def __init__(self, symbols: list):
        self._orderbook = dict()
        for symbol in symbols:
            self._orderbook[symbol] = None

    def update_upbit_orderbook(self, event):
        # askl = [[ask.price, ask.qty] for ask in event.asks]
        # bidl = [[bid.price, bid.qty] for bid in event.asks]
        askl = [event.asks[0].price, event.asks[0].qty]
        bidl = [event.bids[0].price, event.bids[0].qty]
        self._orderbook[event.code[4:]] = {
            "ask_list": askl,
            "bid_list": bidl,
            "total_ask_size": event.total_ask_size,
            "total_bid_size": event.total_bid_size,
        }

    def __getitem__(self, key):
        return self._orderbook[key]

    def __repr__(self):
        return str(self._orderbook)
