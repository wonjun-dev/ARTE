class UpbitTicker:
    def __init__(self):
        self.type = None
        self.symbol = None
        self.opening_price = 0
        self.high_price = 0
        self.low_price = 0
        self.lastPrice = 0
        self.prev_closing_price = 0
        self.change = None
        self.change_price = 0
        self.signed_change_price = 0
        self.change_rate = 0
        self.signed_change_rate = 0
        self.lastQty = 0
        self.acc_trade_volume = 0
        self.acc_trade_volume_24h = 0
        self.acc_trade_price = 0
        self.acc_trade_price_24h = 0
        self.trade_date = None
        self.trade_time = None
        self.trade_timestamp = 0
        self.ask_bid = None
        self.acc_ask_volume = 0
        self.acc_bid_volume = 0
        self.highest_52_week_price = 0
        self.highest_52_week_date = None
        self.lowest_52_week_price = 0
        self.lowest_52_week_date = None
        self.trade_status = None
        self.market_state = None
        self.market_state_for_ios = None
        self.is_trading_suspended = None
        self.delisting_date = None
        self.market_warning = None
        self.timestamp = 0
        self.stream_type = None

    @staticmethod
    def json_parse(json_data):
        result = UpbitTicker()
        result.type = json_data.get_string("type")
        result.symbol = json_data.get_string("code")
        result.opening_price = json_data.get_float("opening_price")
        result.high_price = json_data.get_float("high_price")
        result.low_price = json_data.get_float("low_price")
        result.lastPrice = json_data.get_float("trade_price")
        result.prev_closing_price = json_data.get_float("prev_closing_price")
        result.change = json_data.get_string("change")
        result.change_price = json_data.get_float("change_price")
        result.signed_change_price = json_data.get_float("signed_change_price")
        result.change_rate = json_data.get_float("change_rate")
        result.signed_change_rate = json_data.get_float("signed_change_rate")
        result.lastQty = json_data.get_float("trade_volume")
        result.acc_trade_volume = json_data.get_float("acc_trade_volume")
        result.acc_trade_volume_24h = json_data.get_float("acc_trade_volume_24h")
        result.acc_trade_price = json_data.get_float("acc_trade_price")
        result.acc_trade_price_24h = json_data.get_float("acc_trade_price_24h")
        result.trade_date = json_data.get_string("trade_date")
        result.trade_time = json_data.get_string("trade_time")
        result.trade_timestamp = json_data.get_float("trade_timestamp")
        result.ask_bid = json_data.get_string("ask_bid")
        result.acc_ask_volume = json_data.get_float("acc_ask_volume")
        result.acc_bid_volume = json_data.get_float("acc_bid_volume")
        result.highest_52_week_price = json_data.get_float("highest_52_week_price")
        result.highest_52_week_date = json_data.get_string("highest_52_week_date")
        result.lowest_52_week_price = json_data.get_float("lowest_52_week_price")
        result.lowest_52_week_date = json_data.get_string("lowest_52_week_date")
        result.trade_status = json_data.get_string("trade_status")
        result.market_state = json_data.get_string("market_state")
        result.market_state_for_ios = json_data.get_string("market_state_for_ios")
        result.is_trading_suspended = json_data.get_boolean("is_trading_suspended")
        result.market_warning = json_data.get_string("market_warning")
        result.timestamp = json_data.get_float("timestamp")
        result.stream_type = json_data.get_string("stream_type")

        return result
