import numpy as np
from collections import deque


class IndicatorManager:
    def __init__(self, indicator_instance: list, deque_maxlen: int = 50):
        """
        Manage various indicators
        Args:
            indicator_instance: (list) list of indicator instance
            deque_maxlen: (int) maxlen of deque
        """
        self.indicator_instance = indicator_instance
        self.used_indicator = []
        self.value_dict = {}

        for ins in indicator_instance:
            name = ins.__class__.__name__
            self.used_indicator.append(name)
            self.value_dict[name] = deque(maxlen=deque_maxlen)

    def update(self, data):
        self._update_value(data)
        return self.value_dict

    def _update_value(self, data):
        """
        Update indicator values.
        Args:
            price_queue: (deque)
        """
        for ins in self.indicator_instance:
            name = ins.__class__.__name__
            res = ins.calc(data)
            self.value_dict[name].append(res)