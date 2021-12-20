from binance_f import SubscriptionClient
from binance_f import RequestClient
from upbit.client import Upbit


class Client:
    def __init__(self, mode: str, api_key: str, secret_key: str, req_only: bool = False):
        if mode == "TEST":
            _g_api_key = api_key
            _g_secret_key = secret_key
            url = "https://testnet.binancefuture.com"
            uri = "wss://stream.binancefuture.com/ws"
        elif mode == "REAL":
            _g_api_key = api_key
            _g_secret_key = secret_key
            url = "https://fapi.binance.com"  # production base url
            uri = "wss://fstream.binance.com/ws"

        self.request_client = RequestClient(api_key=_g_api_key, secret_key=_g_secret_key, url=url)
        if not req_only:
            self.sub_client = SubscriptionClient(api_key=_g_api_key, secret_key=_g_secret_key, uri=uri, receive_limit_ms=1000*3600)

        # For temporary use
        _upbit_api_key = "xou3PRNskZ2wzJls3emcvd0xx3lA1eWxvsj4U2yX"
        _upbit_secret_key = "Fo2VKAuEx9yNux6hTN8i3ovX9BAZcDKsmC5qaAt8"
        self.upbit_request_client = Upbit(_upbit_api_key, _upbit_secret_key)


class UpbitClient:
    def __init__(self, api_key, secret_key):
        self.request_client = Upbit(api_key, secret_key)
