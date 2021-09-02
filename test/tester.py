from arte.client import Client
from arte.system.telegram_bot import SimonManager
from arte.bbtt_trader_scheduler import BBTTTrader


def main():
    clients = Client(mode="TEST")
    # bot = SimonManager()
    # trader = BBTTTrader(clients, symbol="ethusdt", bot=bot)
    trader = BBTTTrader(clients, symbol="ethusdt")
    trader.run()


if __name__ == "__main__":
    main()

