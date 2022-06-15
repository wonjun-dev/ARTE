from binance_f import SubscriptionClient
from binance_f import RequestClient


class Client:
    def __init__(self, mode: str, req_only: bool = False):
        if mode == "TEST":
            _g_api_key = ""
            _g_secret_key = ""
            url = "https://testnet.binancefuture.com"
        elif mode == "REAL":
            _g_api_key = ""
            _g_secret_key = ""
            url = "https://fapi.binance.com"  # production base url

        self.request_client = RequestClient(api_key=_g_api_key, secret_key=_g_secret_key, url=url)
        if not req_only:
            self.sub_client = SubscriptionClient(api_key=_g_api_key, secret_key=_g_secret_key, url=url)
