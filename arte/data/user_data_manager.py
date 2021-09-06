import threading

from apscheduler.schedulers.background import BackgroundScheduler

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
        self.sched = BackgroundScheduler()

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
                elif event.eventType == "ORDER_TRADE_UPDATE":
                    self.order_recorder.get_event(event)
                    self.order_recorder.update_csv(event)
            elif event.eventType == "listenKeyExpired":
                print("listenKey Expired, Reconnect Socket again.")
                self.open_user_data_socket()

        def error(e: "BinanceApiException"):
            print(e.error_code + e.error_message)

        self.client.sub_client.subscribe_user_data_event(
            listenKey=self.listen_key, callback=callback, error_handler=error
        )
        self._schedule_keepalive()

    def _keepalive(self):
        self.client.request_client.keep_user_data_stream()
        print("send put keepalive")

    def _close_listenkey(self):
        self.client.request_client.close_user_data_stream()

    def _schedule_keepalive(self):
        self.sched.add_job(self._keepalive, "interval", minutes=30, id="put_keepalive_userdata")
        self.sched.start()


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
