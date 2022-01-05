"""
Spread Indictor
"""


class Spread:
    @staticmethod
    def calc(symbol_A_price, symbol_B_price, gamma, mu):
        return symbol_A_price - gamma * symbol_B_price - mu