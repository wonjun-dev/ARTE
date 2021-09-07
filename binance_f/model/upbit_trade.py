class UpbitTrade:
    def __init__(self):
        self.type = None
        self.code = None
        self.trade_price = 0
        self.trade_volume = 0
        self.ask_bid = None
        self.prev_closing_price = 0
        self.change = None
        self.change_price = 0
        self.trade_date = None
        self.trade_time = None
        self.trade_timestamp = 0
        self.timestamp = 0
        self.sequential_id = 0
        self.stream_type = None

    @staticmethod
    def json_parse(json_data):
        result = UpbitTrade()
        result.type = json_data.get_string("type")
        result.code = json_data.get_string("code")
        result.trade_price = json_data.get_float("trade_price")
        result.trade_volume = json_data.get_float("trade_volume")
        result.ask_bid = json_data.get_string("ask_bid")
        result.prev_closing_price = json_data.get_float("prev_closing_price")
        result.change = json_data.get_string("change")
        result.change_price = json_data.get_float("change_price")
        result.trade_date = json_data.get_string("trade_date")
        result.trade_time = json_data.get_string("trade_time")
        result.trade_timestamp = json_data.get_float("trade_timestamp")
        result.timestamp = json_data.get_float("timestamp")
        result.sequential_id = json_data.get_float("sequential_id")
        result.stream_type = json_data.get_string("stream_type")

        return result
