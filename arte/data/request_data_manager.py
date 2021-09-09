import requests


class RequestDataManager:
    def __init__(self, client) -> None:
        self.client = client

    def get_usdt_to_kor(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
        }
        url = "https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD"
        exchange = requests.get(url, headers=headers).json()
        return float(exchange[0]["basePrice"])

    def get_closed_symbols(self):
        resp = self.client.upbit_request_client.Account.Account_wallet()
        closed_list = list()
        for status in resp["result"]:
            if status["wallet_state"] != "working":
                closed_list.append(status["currency"])

        return closed_list
