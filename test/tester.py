import configparser

from arte.client import Client
from arte.system.telegram_bot import SimonManager
from arte.bbtt_trader_scheduler import BBTTTrader


# configuration
cfg = configparser.ConfigParser()
cfg.read('test/config.ini')
config = cfg['TEST']

mode = config['MODE']
api_key = config['API_KEY']
secret_key = config['SECRET_KEY']
use_bot = config['USE_BOT']

def main():
    clients = Client(mode, api_key, secret_key)
    if use_bot:
        bot = SimonManager()
        trader = BBTTTrader(clients, symbol="ethusdt", bot=bot)
    else:
        trader = BBTTTrader(clients, symbol="ethusdt")
    trader.run()


if __name__ == "__main__":
    main()