from abc import ABCMeta, abstractmethod
from enum import Enum


class TouchDirection(Enum):
    NO = 0
    UP = 1
    DOWN = 2


class BaseIndicator(metaclass=ABCMeta):
    @abstractmethod
    def calc(self):
        pass
