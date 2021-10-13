import requests


class RequestDataManager:
    """
    Class RequestDataManager
        Request를 통해 data를 받아오는 함수들을 관리하는 모듈

    Attributes:
        client : upbit, binance-spot, binance-future의 client 정보를 담은 클래스

    Functions:
        get_usdt_to_kor : 두나무 API에서 제공하는 현재 실시간 환율을 받아오는 함수
        get_closed_symbols : Upbit에서 현재 입출금이 지원되지 않는 암호화폐의 list를 받아오는 함수

    """

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
