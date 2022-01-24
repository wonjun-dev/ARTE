import configparser
import threading
import time

from binance_f.model.constant import *
from arte.system.client import Client
from arte.data import SocketDataManager
from arte.data.common_symbol_collector import CommonSymbolCollector

cfg = configparser.ConfigParser()
cfg.read("D:/arte_config/config.ini")
config = cfg["REAL"]

mode = config["MODE"]
api_key = config["API_KEY"]
secret_key = config["SECRET_KEY"]
use_bot = config.getboolean("USE_BOT")

cl = Client(mode, api_key, secret_key, req_only=True)

reqc = cl.request_client
# symbols =['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'XRP', 'DOT', 'LUNA', 'AVAX', 'DOGE', '1000SHIB', 'MATIC', 'LINK', 'ATOM',
#               'ALGO', 'NEAR', 'LTC', 'UNI', 'BCH', 'FTM', 'TRX', 'XLM', 'ICP', 'AXS', 'VET', 'HBAR',  'FIL',
#               'SAND', 'EGLD', 'THETA', 'ETC', 'XTZ', 'HNT', 'MANA', 'XMR', 'KLAY', 'GRT', 'ONE', 'AAVE', 'GALA', 'AR',
#               'EOS',  'BTT',  'KSM', 'LRC',  'ENJ',  'CRV', 'RUNE', 'MKR',
#               'CELO',  'BAT', 'NEO', 'ZEC', 'CHZ',  'SUSHI', 'WAVES', 'COMP', 'ROSE', 'DASH',
#               'RVN', 'SNX', 'HOT', 'YFI',  'IOTX', 'XEM', 'LPT', '1INCH', 'ZIL']
# symbols_usdt = [s.lower()+'usdt' for s in symbols]
# for symbol in symbols_usdt:    
#     reqc.change_initial_leverage(symbol=symbol, leverage=1)

# for symbol in symbols_usdt:
#     print(symbol)
#     try:
#         reqc.change_margin_type(symbol=symbol, marginType=FuturesMarginType.ISOLATED)
#     except Exception as e:
#         print(e)


ex_info_per_symbol = reqc.get_exchange_information().symbols

for ex_info in ex_info_per_symbol:
    # print(
    #     ex_info.symbol, ex_info.status, ex_info.baseAsset, ex_info.quoteAsset, ex_info.quantityPrecision,
    # )
    print(ex_info.symbol, ex_info.filters[2]['stepSize'], ex_info.quantityPrecision)

"""
self.symbol = ""
self.status = ""
self.maintMarginPercent = 0.0
self.requiredMarginPercent = 0.0
self.baseAsset = ""
self.quoteAsset = ""
self.pricePrecision = None
self.quantityPrecision = None
self.baseAssetPrecision = None
self.quotePrecision = None
self.orderTypes = list()
self.timeInForce = list()
self.filters = list()

"""
