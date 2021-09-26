import configparser

from arte.client import Client
from arte.arbi_scheduler import ArbiTrader
from arte.system.telegram_bot import DominicBot

# configuration
cfg = configparser.ConfigParser()
cfg.read("test/config.ini")
config = cfg["REAL"]

mode = config["MODE"]
api_key = config["API_KEY"]
secret_key = config["SECRET_KEY"]
use_bot = config.getboolean("USE_BOT")


def main():
    clients = Client(mode, api_key, secret_key)

    if use_bot:
        bot = DominicBot()
        trader = ArbiTrader(clients, bot=bot)
    else:
        trader = ArbiTrader(clients)
    trader.start()


if __name__ == "__main__":
    main()
