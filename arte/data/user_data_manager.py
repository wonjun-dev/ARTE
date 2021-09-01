import threading

from binance_f import RequestClient
from binance_f import SubscriptionClient
from binance_f.constant.test import *
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException
from binance_f.base.printobject import *

from arte.system.order_recorder import OrderRecorder


class UserDataManager:
    def __init__(self, client, account, order_recorder) -> None:
        self.client = client
        self.account = account
        self.order_recorder = order_recorder
        self.listen_key = None

    def open_user_data_socket(self):
        self.listen_key = self.client.request_client.start_user_data_stream()

        def callback(data_type: "SubscribeMessageType", event: "any"):
            if data_type == SubscribeMessageType.RESPONSE:
                print("UserDataStream Event ID: ", event)
            elif data_type == SubscribeMessageType.PAYLOAD:
                if event.eventType == "ACCOUNT_UPDATE":
                    self.account.update(event)
                    # print("USDT: ", self.account["USDT"])
                    # print("ETHUSDT: ", self.account["ETHUSDT"])
                elif event.eventType == "ORDER_TRADE_UPDATE":
                    self.order_recorder.get_event(event)
                    print(self.order_recorder.pair_dict)
                    # print("Event Type: ", event.eventType)
                    # print("Event time: ", event.eventTime)
                    # print("Transaction Time: ", event.transactionTime)
                    # print("Symbol: ", event.symbol)
                    # print("Client Order Id: ", event.clientOrderId)
                    # print("Side: ", event.side)
                    # print("Order Type: ", event.type)
                    # print("Time in Force: ", event.timeInForce)
                    # print("Original Quantity: ", event.origQty)
                    # print("Position Side: ", event.positionSide)
                    # print("Price: ", event.price)
                    # print("Average Price: ", event.avgPrice)
                    # print("Stop Price: ", event.stopPrice)
                    # print("Execution Type: ", event.executionType)
                    # print("Order Status: ", event.orderStatus)
                    # print("Order Id: ", event.orderId)
                    # print("Order Last Filled Quantity: ", event.lastFilledQty)
                    # print("Order Filled Accumulated Quantity: ", event.cumulativeFilledQty)
                    # print("Last Filled Price: ", event.lastFilledPrice)
                    # print("Commission Asset: ", event.commissionAsset)
                    # print("Commissions: ", event.commissionAmount)
                    # print("Order Trade Time: ", event.orderTradeTime)
                    # print("Trade Id: ", event.tradeID)
                    # print("Bids Notional: ", event.bidsNotional)
                    # print("Ask Notional: ", event.asksNotional)
                    # print("Is this trade the maker side?: ", event.isMarkerSide)
                    # print("Is this reduce only: ", event.isReduceOnly)
                    # print("stop price working type: ", event.workingType)
                    # print("Is this Close-All: ", event.isClosePosition)
                    # if not event.activationPrice is None:
                    #     print("Activation Price for Trailing Stop: ", event.activationPrice)
                    # if not event.callbackRate is None:
                    #     print("Callback Rate for Trailing Stop: ", event.callbackRate)
            elif event.eventType == "listenKeyExpired":
                print("listenKey Expired, Reconnect Socket again.")
                self.open_user_data_socket()

        def error(e: "BinanceApiException"):
            print(e.error_code + e.error_message)

        self.client.sub_client.subscribe_user_data_event(
            listenKey=self.listen_key, callback=callback, error_handler=error
        )

    def _keepalive(self):
        self.client.request_client.keep_user_data_stream()

    def _close_listenkey(self):
        self.client.request_client.close_user_data_stream()


if __name__ == "__main__":
    from arte.system.account import Account
    from arte.client import Client

    cli = Client("TEST")
    acc = Account(cli.request_client)
    order_rec = OrderRecorder()
    udm = UserDataManager(cli, acc, order_rec)
    udm.open_user_data_socket()

    for t in threading.enumerate():
        if t is threading.current_thread():
            continue
        t.join()

