from arte.client import Client
from arte.arbi_scheduler import ArbiTrader


def main():
    clients = Client(mode="TEST")
    trader = ArbiTrader(clients)
    trader.run()


if __name__ == "__main__":
    main()
