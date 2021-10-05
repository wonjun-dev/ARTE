from binance_f.model.constant import PositionSide


class TestAccount:
    def __init__(self, init_balance=5000):
        self.assets = dict()
        self.assets["USDT"] = init_balance

    def __getitem__(self, symbol):
        return self.assets[symbol]

    def __repr__(self):
        return str(self.assets)

    def _initialize_position(self, symbol):
        self.assets[symbol] = {PositionSide.LONG: 0, PositionSide.SHORT: 0}

    def deposit_usdt(self, quantity):
        self.assets["USDT"] += quantity

    def withdraw_usdt(self, quantity):
        if self.assets["USDT"] >= quantity:
            self.assets["USDT"] -= quantity

    def deposit(self, symbol, positionSide, quantity):
        if symbol not in self.assets.keys():
            self._initialize_position(symbol)
        self.assets[symbol][positionSide] += quantity

    def withdraw(self, symbol, positionSide, quantity):
        if self.has_asset(symbol, positionSide, quantity):
            self.assets[symbol][positionSide] -= quantity

    def has_asset(self, symbol, positionSide, quantity):
        if symbol not in self.assets.keys():
            return False
        else:
            if self.assets[symbol][positionSide] < quantity:
                return False
            else:
                return True


if __name__ == "__main__":
    acc = TestAccount(init_balance=10000)
    print(acc)

