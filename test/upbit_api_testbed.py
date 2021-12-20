# import os
# import jwt
# import uuid
# import hashlib

# from urllib.parse import urlencode

# import requests
import configparser

cfg = configparser.ConfigParser()
cfg.read("/media/park/hard2000/arte_config/config.ini")
config = cfg["REAL_JAEHAN"]
access_key = config["UPBIT_ACCESS_KEY"]
secret_key = config["UPBIT_SECRET_KEY"]
server_url = "https://api.upbit.com/"  # os.environ['UPBIT_OPEN_API_SERVER_URL']

# query = {
#     'market': 'KRW-ETH',
# }
# query_string = urlencode(query).encode()

# m = hashlib.sha512()
# m.update(query_string)
# query_hash = m.hexdigest()

# payload = {
#     'access_key': access_key,
#     'nonce': str(uuid.uuid4()),
#     'query_hash': query_hash,
#     'query_hash_alg': 'SHA512',
# }

# jwt_token = jwt.encode(payload, secret_key)
# authorize_token = 'Bearer {}'.format(jwt_token)
# headers = {"Authorization": authorize_token}

# res = requests.get(server_url + "/v1/orders/chance", params=query, headers=headers)

# print(res.json())

from upbit.client import Upbit
from arte.system.upbit.account import UpbitAccount
import json


def json_parse(response):
    result_dict = {}
    for position in response:
        result_dict[position["currency"]] = position["balance"]
    return result_dict


client = Upbit(access_key, secret_key)
acc = UpbitAccount(client)
print(acc)

# order_result = client.Order.Order_new(market="KRW-XRP", side="bid", ord_type="price", price="5400")
# print(order_result)
# print(order_result["result"])

order_result = client.Order.Order_new(market="KRW-XRP", side="ask", ord_type="market", volume=str(acc["XRP"]))
print(type(order_result))

# order_dict = json.load(order_result['text'])
resp = client.Order.Order_info(
    uuid="8b8bde6d-3753-4922-b574-ffb0dfe8ce0d"
)  # market='KRW-XRP', uuids=["944fc2ff-feff-4a16-8032-881cb45e8388"])
print(resp["result"])


# acc.update_by_thread()

# resp = client.Account.Account_info()
# result = json_parse(resp['result'])
# print(result)

# import json
# result_json = {'remaining_request': {'group': 'order', 'min': '198', 'sec': '7'}, 'response': {'url': 'https://api.upbit.com/v1/orders?market=KRW-XRP&side=bid&ord_type=price&price=5000&identifier=test01', 'headers': {'Date': 'Sun, 19 Dec 2021 07:53:27 GMT', 'Content-Type': 'application/json', 'Content-Length': '328', 'Connection': 'keep-alive', 'Remaining-Req': 'group=order; min=198; sec=7', 'Access-Control-Allow-Origin': '*', 'X-Request-Id': '0c27ad25-2cbf-427d-88e0-a593c2e36ac3', 'X-Runtime': '0.083699', 'Vary': 'Origin'}, 'status_code': 201, 'reason': 'Created', 'text': '{"uuid":"944fc2ff-feff-4a16-8032-881cb45e8388","side":"bid","ord_type":"price","price":"5000.0","state":"wait","market":"KRW-XRP","created_at":"2021-12-19T16:53:27+09:00","volume":null,"remaining_volume":null,"reserved_fee":"2.5","remaining_fee":"2.5","paid_fee":"0.0","locked":"5002.5","executed_volume":"0.0","trades_count":0}', 'content': b'{"uuid":"944fc2ff-feff-4a16-8032-881cb45e8388","side":"bid","ord_type":"price","price":"5000.0","state":"wait","market":"KRW-XRP","created_at":"2021-12-19T16:53:27+09:00","volume":null,"remaining_volume":null,"reserved_fee":"2.5","remaining_fee":"2.5","paid_fee":"0.0","locked":"5002.5","executed_volume":"0.0","trades_count":0}', 'ok': True}, 'result': {'uuid': '944fc2ff-feff-4a16-8032-881cb45e8388', 'side': 'bid', 'ord_type': 'price', 'price': '5000.0', 'state': 'wait', 'market': 'KRW-XRP', 'created_at': '2021-12-19T16:53:27+09:00', 'volume': None, 'remaining_volume': None, 'reserved_fee': '2.5', 'remaining_fee': '2.5', 'paid_fee': '0.0', 'locked': '5002.5', 'executed_volume': '0.0', 'trades_count': 0}}
# #print(result_json['response']['text'])

# resp = client.Order.Order_info(uuid='f1fee0f0-bee4-4993-9cc5-40be981a1b78')#market='KRW-XRP', uuids=["944fc2ff-feff-4a16-8032-881cb45e8388"])
# print(resp['result'])

# resp = client.Order.Order_info_all(states=['watch'], limit=3) #, uuids=["944fc2ff-feff-4a16-8032-881cb45e8388"])
# for res in resp['result']:
#     print(res)
