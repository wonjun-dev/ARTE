import math
import time
import secrets
from decimal import Decimal, getcontext

from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *


def get_timestamp():
    return int(time.time())  # * 1000)


class UpbitOrderHandler:
    def __init__(self, request_client, account):
        self.request_client = request_client
        self.account = account
        self.manager = None

    def buy_market(self, symbol: str, krw=None, ratio=None):
        if bool(krw) ^ bool(ratio):
            if ratio:
                krw = self.account["KRW"] * ratio
            return self.request_client.Order.Order_new(
                market=symbol,
                side=UpbitOrderSide.BUY,
                ord_type=UpbitOrderType.PRICE,
                price=str(krw),
                # identifier=self._generate_order_id(symbol)
            )
        else:
            raise ValueError("You have to pass either quantity or ratio.")

    def sell_market(self, symbol: str, ratio):
        pure_symbol = symbol[4:]
        if pure_symbol not in self.account.symbols():
            return dict(error=None)
        if self.account[pure_symbol] > 0:
            return self.request_client.Order.Order_new(
                market=symbol,
                side=UpbitOrderSide.SELL,
                ord_type=UpbitOrderType.MARKET,
                volume=self._asset_ratio_to_quantity(pure_symbol, ratio)
                # identifier=self._generate_order_id(symbol)
            )
        else:
            print(f"Cannot execute sell {symbol}, you dont have any position.")
            return dict(error=None)

    def _asset_ratio_to_quantity(self, symbol: str, ratio, unit_float=8):
        getcontext().prec = unit_float + 1
        asset_quantity = self.account[symbol]
        full_unit_quantity = str(asset_quantity * Decimal(ratio))
        div_float = full_unit_quantity.split(".")
        _quantity = div_float[0] + "." + div_float[1][:unit_float]
        return _quantity

    def _generate_order_id(self, symbol: str):
        _id = symbol + str(get_timestamp()) + f"-{secrets.token_hex(4)}"
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
    # order_result = oh.buy_market(symbol="KRW-EOS", krw=5300)
    order_result = oh.sell_market(symbol="KRW-EOS", ratio=1.0)
    print(order_result)
    print(time.time() - st)  # XRP usually under 0.01, once 0.33 / EOS 0.1 /

