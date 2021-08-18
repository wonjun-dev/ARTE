from client import Client
from BBTT_trader_scheduler import BBTTTrader


def main():
    client = Client()
    trader = BBTTTrader(client, symbol="ethusdt")
    trader.run()


if __name__ == "__main__":
    main()
