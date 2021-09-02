from arte.client import Client
from arte.turtle_trader_scheduler import TurtleTrader


def main():
    clients = Client(mode="TEST")
    trader = TurtleTrader(clients, symbol="ethusdt")
    trader.run()


if __name__ == "__main__":
    main()

