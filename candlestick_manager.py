from collections import deque


class CandlestickManager:
    """
    Class CandlestickManager
        Candlestick data를 관리하는 함수. 각 data들을 deque로 관리함

    Attributes:
        open
        close
        high
        low
        volume
        등 candlestick의 정보들을 포함
    """

    def __init__(self, maxlen: int = 21):
        """deque의 최대 길이를 maxlen으로 설정하고, deque초기화"""
        self.maxlen = maxlen
        self.startTime = deque(maxlen=maxlen)
        self.closeTime = deque(maxlen=maxlen)
        self.open = deque(maxlen=maxlen)
        self.close = deque(maxlen=maxlen)
        self.high = deque(maxlen=maxlen)
        self.low = deque(maxlen=maxlen)
        self.volume = deque(maxlen=maxlen)
        self.numTrades = deque(maxlen=maxlen)
        self.quoteAssetVolume = deque(maxlen=maxlen)
        self.takerBuyBaseAssetVolume = deque(maxlen=maxlen)
        self.takerBuyQuoteAssetVolume = deque(maxlen=maxlen)
        self.ignore = deque(maxlen=maxlen)

    def init_candlestick(self, init_candle):
        """초기값을 request로 받아와 저장하는 함수"""
        for index_candlestick in range(self.maxlen):
            self.startTime.append(float(init_candle[index_candlestick].openTime))
            self.closeTime.append(float(init_candle[index_candlestick].closeTime))
            self.open.append(float(init_candle[index_candlestick].open))
            self.close.append(float(init_candle[index_candlestick].close))
            self.high.append(float(init_candle[index_candlestick].high))
            self.low.append(float(init_candle[index_candlestick].low))
            self.volume.append(float(init_candle[index_candlestick].volume))
            self.numTrades.append(float(init_candle[index_candlestick].numTrades))
            self.quoteAssetVolume.append(float(init_candle[index_candlestick].quoteAssetVolume))
            self.ignore.append(float(init_candle[index_candlestick].ignore))
            self.takerBuyBaseAssetVolume.append(float(init_candle[index_candlestick].takerBuyBaseAssetVolume))
            self.takerBuyQuoteAssetVolume.append(float(init_candle[index_candlestick].takerBuyQuoteAssetVolume))

    def update_candlestick(self, event):
        """다음 candlestick으로 바뀌었을 때 update를 위한 함수"""
        self.startTime.append(event.data.startTime)
        self.closeTime.append(event.data.closeTime)
        self.open.append(event.data.open)
        self.close.append(event.data.close)
        self.high.append(event.data.high)
        self.low.append(event.data.low)
        self.volume.append(event.data.volume)
        self.numTrades.append(event.data.numTrades)
        self.quoteAssetVolume.append(event.data.quoteAssetVolume)
        self.takerBuyBaseAssetVolume.append(event.data.takerBuyBaseAssetVolume)
        self.takerBuyQuoteAssetVolume.append(event.data.takerBuyQuoteAssetVolume)
        self.ignore.append(event.data.ignore)

    def update_next_candlestick(self, event):
        """현재 candlestick 업데이트"""
        self.startTime.pop()
        self.closeTime.pop()
        self.open.pop()
        self.close.pop()
        self.high.pop()
        self.low.pop()
        self.volume.pop()
        self.numTrades.pop()
        self.quoteAssetVolume.pop()
        self.takerBuyBaseAssetVolume.pop()
        self.takerBuyQuoteAssetVolume.pop()
        self.ignore.pop()

        self.startTime.append(event.data.startTime)
        self.closeTime.append(event.data.closeTime)
        self.open.append(event.data.open)
        self.close.append(event.data.close)
        self.high.append(event.data.high)
        self.low.append(event.data.low)
        self.volume.append(event.data.volume)
        self.numTrades.append(event.data.numTrades)
        self.quoteAssetVolume.append(event.data.quoteAssetVolume)
        self.takerBuyBaseAssetVolume.append(event.data.takerBuyBaseAssetVolume)
        self.takerBuyQuoteAssetVolume.append(event.data.takerBuyQuoteAssetVolume)
        self.ignore.append(event.data.ignore)
