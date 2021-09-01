from binance_f import SubscriptionClient
from binance_f import RequestClient


class Client:
    def __init__(self, mode: str, req_only: bool = False):
        if mode == "TEST":
            # _g_api_key = "0dcd28f57648b0a7d5ea2737487e3b3093d47935e67506b78291042d1dd2f9ea"
            # _g_secret_key = "b36dc15c333bd5950addaf92a0f9dc96d8ed59ea6835386c59a6e63e1ae26aa1"
            _g_api_key = "36771756cc6f17e0650daf4895104e7aae6f1901211fe9f57d7ed3e224395ed8"
            _g_secret_key = "9203436b66c6fbd627f96672ca90f363bccbd3d103e599baa9aa1ef7eef068e7"
            url = "https://testnet.binancefuture.com"
        elif mode == "REAL":
            _g_api_key = "kBspRLNvPEr3ukGX95ytlxSPdYSj7WlFPvWBgjtP8ujqsTUOmCdMVzCDCDGoVoq5"
            _g_secret_key = "pfDIPiQ1leG6X5jbXMp3xTDRiYRhID5CSc5rRfhjcnUT2GMOtAnv3xZc5gYsjywC"
            url = "https://fapi.binance.com"  # production base url

        self.request_client = RequestClient(api_key=_g_api_key, secret_key=_g_secret_key, url=url)
        if not req_only:
            self.sub_client = SubscriptionClient(
                api_key=_g_api_key, secret_key=_g_secret_key, url=url
            )
