from arte.client import Client
from arte.bbtt_trader_scheduler import BBTTTrader


def main():
    clients = Client(mode="TEST")
    trader = BBTTTrader(clients, symbol="ethusdt")
    trader.run()


if __name__ == "__main__":
    main()

