"""
Upbit
"""
from decimal import Decimal


class Account:
    def __init__(self, init_balance=100000):
        self.assets = dict()
        self._initialize_position("KRW", init_val=init_balance)

    def __getitem__(self, symbol):
        return self.assets[symbol]

    def __repr__(self):
        return str(self.assets)

    def _initialize_position(self, symbol, init_val=0):
        self.assets[symbol] = Decimal(init_val)

    def deposit(self, symbol, quantity):
        if symbol not in self.assets.keys():
            self._initialize_position(symbol)
        self.assets[symbol] += quantity

    def withdraw(self, symbol, quantity):
        if self.has_asset(symbol, quantity):
            self.assets[symbol] -= quantity

    def has_asset(self, symbol, quantity):
        if symbol not in self.assets.keys():
            return False
        else:
            return False if self.assets[symbol] < quantity else True


if __name__ == "__main__":
    acc = Account(init_balance=100000)
    acc.deposit(symbol="KRW-BTC", quantity=Decimal("1.0"))
    print(acc)

