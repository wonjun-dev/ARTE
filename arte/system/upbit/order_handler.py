import time
import secrets
from decimal import Decimal, getcontext

from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *

from arte.system.utils import symbolize_upbit


def get_timestamp():
    return int(time.time())  # * 1000)


class UpbitOrderHandler:
    def __init__(self, request_client, account):
        self.request_client = request_client
        self.account = account

    def buy_market(self, symbol: str, krw=None, ratio=None):
        if bool(krw) ^ bool(ratio):
            if ratio:
                krw = round(self.account["KRW"] * ratio)
            order_result = self.request_client.Order.Order_new(
                market=symbolize_upbit(symbol),
                side=UpbitOrderSide.BUY,
                ord_type=UpbitOrderType.PRICE,
                price=str(krw),
                # identifier=self._generate_order_id(symbol)
            )
            if "error" in order_result["result"]:
                raise ValueError(order_result["result"])
            else:
                return order_result
        else:
            raise ValueError("You have to pass either krw or ratio.")

    def sell_market(self, symbol: str, ratio):
        if symbol not in self.account.symbols:
            raise ValueError(f"Cannot sell {symbol} - not exist in your account")
        if self.account[symbol] > 0:
            order_result = self.request_client.Order.Order_new(
                market=symbolize_upbit(symbol),
                side=UpbitOrderSide.SELL,
                ord_type=UpbitOrderType.MARKET,
                volume=self._asset_ratio_to_quantity(symbol, ratio)
                # identifier=self._generate_order_id(symbol)
            )
            if "error" in order_result["result"]:
                raise ValueError(order_result["result"])
            else:
                return order_result
        else:
            raise ValueError(
                f"Cannot execute sell {symbol}:{self.account[symbol]}, you dont have any position or not enough size to sell."
            )

    def _asset_ratio_to_quantity(self, symbol: str, ratio, unit_float=8):
        getcontext().prec = unit_float + 1
        asset_quantity = self.account[symbol]
        full_unit_quantity = str(asset_quantity * Decimal(ratio))
        div_float = full_unit_quantity.split(".")
        _quantity = div_float[0] + "." + div_float[1][:unit_float]
        return _quantity

    def _generate_order_id(self, symbol: str):
        _id = symbolize_upbit(symbol) + str(get_timestamp()) + f"-{secrets.token_hex(4)}"
        return _id


if __name__ == "__main__":
    import time
    import configparser
    from upbit.client import Upbit
    from arte.system.upbit.account import UpbitAccount

    cfg = configparser.ConfigParser()
    cfg.read("/media/park/hard2000/arte_config/config.ini")
    config = cfg["REAL_JAEHAN"]
    access_key = config["UPBIT_ACCESS_KEY"]
    secret_key = config["UPBIT_SECRET_KEY"]

    client = Upbit(access_key, secret_key)
    acc = UpbitAccount(client)
    oh = UpbitOrderHandler(client, acc)

    st = time.time()
    order_result = oh.buy_market(symbol="KRW-EOS", krw=40000)
    if order_result:
        print("Buy!")
    # order_result = oh.sell_market(symbol="KRW-EOS", ratio=1.0)
    # if order_result:
    #     print("Sell!")
    print(order_result)
    print(time.time() - st)  # XRP usually under 0.01, once 0.33 / EOS 0.1 /

