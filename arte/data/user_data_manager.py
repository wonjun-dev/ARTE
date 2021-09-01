import threading

from binance_f import RequestClient
from binance_f import SubscriptionClient
from binance_f.constant.test import *
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException
from binance_f.base.printobject import *


class UserDataManager:
    def __init__(self, client, account) -> None:
        self.client = client
        self.account = account
        self.listen_key = None

    def open_user_data_socket(self):
        self.listen_key = self.client.request_client.start_user_data_stream()

        def callback(data_type: "SubscribeMessageType", event: "any"):
            if data_type == SubscribeMessageType.RESPONSE:
                print("UserDataStream Event ID: ", event)
            elif data_type == SubscribeMessageType.PAYLOAD:
                if event.eventType == "ACCOUNT_UPDATE":
                    self.account.update(event)
                    print("USDT: ", self.account["USDT"])
                    print("ETHUSDT: ", self.account["ETHUSDT"])
                    # print("Event Type: ", event.eventType)
                    # print("Event time: ", event.eventTime)
                    # print("Transaction time: ", event.transactionTime)
                    # print("=== Balances ===")
                    # PrintMix.print_data(event.balances)
                    # print("================")
                    # print("=== Positions ===")
                    # PrintMix.print_data(event.positions)
                    # print("================")
                elif event.eventType == "ORDER_TRADE_UPDATE":
                    if event.orderStatus == "NEW":
                        pass
                        # self.order_handler.update_not_signed_order(event)  # update not signed order
                    elif event.orderStatus == "FILLED":
                        if event.side == "BUY":
                            pass
                            # self.order_handler.update_signed_order(event)  # update signed order
                            # self.order_handler.delete_not_signed_order(event.clientOrderId)  # delete not signed order
                        elif event.side == "SELL":
                            pass
                            # self.order_handler.delete_signed_order(event.clientOrderId)  # delete signed order
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
    udm = UserDataManager(cli, acc)
    udm.open_user_data_socket()

    for t in threading.enumerate():
        if t is threading.current_thread():
            continue
        t.join()

