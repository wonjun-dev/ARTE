from pyupbit.exchange_api import Upbit


class Order:
    def __init__(self):
        self.price = 0.0
        self.qty = 0.0


class UpbitOrderbook:
    def __init__(self):
        self.type = None
        self.code = None
        self.total_ask_size = 0
        self.total_bid_size = 0
        self.timestamp = 0
        self.asks = list()
        self.bids = list()

    @staticmethod
    def json_parse(json_data):
        result = UpbitOrderbook()
        result.type = json_data.get_string("type")
        result.code = json_data.get_string("code")
        result.total_ask_size = json_data.get_float("total_ask_size")
        result.total_bid_size = json_data.get_float("total_bid_size")
        result.timestamp = json_data.get_float("timestamp")

        list_array = json_data.get_array("orderbook_units")
        bid_list = list()
        ask_list = list()

        for item in list_array.get_items():
            bid_order = Order()
            ask_order = Order()
            val = item.convert_2_dict()
            bid_order.price = val["bid_price"]
            bid_order.qty = val["bid_size"]
            ask_order.price = val["ask_price"]
            ask_order.qty = val["ask_size"]
            bid_list.append(bid_order)
            ask_list.append(ask_order)

        result.asks = ask_list
        result.bids = bid_list
        return result
