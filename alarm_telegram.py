'''
텔레그램 api 기반의 오더 및 체결 알람
1. 오더매니저와 어떻게 공존할지
2. 시큐리티 - 프라이빗 봇이 되어야 함
'''
import telegram

TOKEN = '1908253406:AAFDtBdONqBrwKfAfB6PKfaP06giT7XqonQ'
CHAT_ID = '1925633139'
bot = telegram.Bot(token = TOKEN)

text = '안녕하세요? 저는 알람 하인입니다.'
bot.sendMessage(chat_id=CHAT_ID, text=text)


# updates = chat.getUpdates()
# for u in updates:
#     print(u.message['chat']['id'])

